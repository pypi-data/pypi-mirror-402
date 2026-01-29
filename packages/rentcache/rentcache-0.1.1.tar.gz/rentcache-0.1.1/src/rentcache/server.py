"""
RentCache FastAPI Server - Sophisticated proxy for Rentcast API with intelligent caching.
"""
import asyncio
import json
import logging
import hashlib
import time
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List, Union
from contextlib import asynccontextmanager

import httpx
import structlog
from fastapi import FastAPI, Depends, HTTPException, Header, Query, Path, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, func, and_, case
from pydantic import BaseModel, Field

from .models import (
    Base, CacheEntry, APIKey, RateLimit, UsageStats, CacheStats,
    HealthCheckResponse, MetricsResponse, ProxyRequest,
    CreateAPIKeyRequest, UpdateAPIKeyRequest, CacheControlRequest,
    APIKeyResponse, UsageStatsResponse
)
from .cache import CacheManager, SQLiteCacheBackend, RedisCacheBackend, HybridCacheBackend

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Global variables for app state
engine = None
SessionLocal = None
cache_manager = None
http_client = None
app_start_time = None

# Rentcast API configuration
RENTCAST_BASE_URL = "https://api.rentcast.io"
DEFAULT_TTL_SECONDS = 3600  # 1 hour
EXPENSIVE_ENDPOINTS_TTL = 86400  # 24 hours for expensive endpoints

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
security = HTTPBearer(auto_error=False)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global engine, SessionLocal, cache_manager, http_client, app_start_time
    
    logger.info("Starting RentCache server...")
    app_start_time = time.time()
    
    # Initialize database
    database_url = "sqlite+aiosqlite:///./rentcache.db"
    engine = create_async_engine(database_url, echo=False)
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    SessionLocal = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    # Initialize cache manager
    cache_backend = SQLiteCacheBackend(SessionLocal)
    cache_manager = CacheManager(
        backend=cache_backend,
        default_ttl=DEFAULT_TTL_SECONDS,
        stale_while_revalidate=True
    )
    
    # HTTP client for upstream requests
    http_client = httpx.AsyncClient(
        timeout=30.0,
        limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)
    )
    
    logger.info("RentCache server started successfully")
    
    try:
        yield
    finally:
        # Cleanup
        await http_client.aclose()
        await engine.dispose()
        logger.info("RentCache server shut down")


# Create FastAPI app
app = FastAPI(
    title="RentCache API",
    description="Sophisticated FastAPI proxy server for Rentcast API with intelligent caching",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(SlowAPIMiddleware)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Dependency injection
async def get_db() -> AsyncSession:
    """Get database session."""
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_api_key(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Optional[APIKey]:
    """Validate API key from Authorization header."""
    if not credentials:
        return None
    
    # Hash the provided key
    key_hash = hashlib.sha256(credentials.credentials.encode()).hexdigest()
    
    stmt = select(APIKey).where(
        and_(
            APIKey.key_hash == key_hash,
            APIKey.is_active == True
        )
    )
    result = await db.execute(stmt)
    api_key = result.scalar_one_or_none()
    
    if api_key and api_key.expires_at:
        if datetime.now(timezone.utc) > api_key.expires_at:
            return None
    
    return api_key


async def require_api_key(
    api_key: Optional[APIKey] = Depends(get_api_key)
) -> APIKey:
    """Require valid API key."""
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Valid API key required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return api_key


async def check_rate_limits(
    api_key: APIKey,
    endpoint: str,
    db: AsyncSession
) -> bool:
    """Check if API key is within rate limits."""
    if not api_key.can_make_request():
        return False
    
    # Check endpoint-specific rate limits
    stmt = select(RateLimit).where(
        and_(
            RateLimit.api_key_id == api_key.id,
            RateLimit.endpoint == endpoint
        )
    )
    result = await db.execute(stmt)
    rate_limit = result.scalar_one_or_none()
    
    if rate_limit and not rate_limit.can_make_request():
        return False
    
    return True


async def record_usage(
    api_key: APIKey,
    endpoint: str,
    method: str,
    status_code: int,
    response_time_ms: float,
    cache_hit: bool,
    estimated_cost: float,
    request: Request,
    db: AsyncSession
):
    """Record usage statistics."""
    # Update API key usage
    api_key.increment_usage()
    
    # Record usage stats
    usage_stat = UsageStats(
        api_key_id=api_key.id,
        endpoint=endpoint,
        method=method,
        status_code=status_code,
        response_time_ms=response_time_ms,
        cache_hit=cache_hit,
        estimated_cost=estimated_cost,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None
    )
    
    db.add(usage_stat)
    await db.commit()


# Rentcast API endpoint definitions
RENTCAST_ENDPOINTS = {
    # Property Records
    "properties": {
        "path": "/v1/properties",
        "methods": ["GET"],
        "ttl": EXPENSIVE_ENDPOINTS_TTL,  # 24 hours
        "cost_estimate": 1.0,
        "description": "Search property records"
    },
    "property_by_id": {
        "path": "/v1/properties/{property_id}",
        "methods": ["GET"],
        "ttl": EXPENSIVE_ENDPOINTS_TTL,
        "cost_estimate": 1.0,
        "description": "Get property by ID"
    },
    
    # Value Estimates
    "value_estimate": {
        "path": "/v1/estimates/value",
        "methods": ["GET"],
        "ttl": DEFAULT_TTL_SECONDS,  # 1 hour
        "cost_estimate": 2.0,
        "description": "Get property value estimate"
    },
    "value_estimate_bulk": {
        "path": "/v1/estimates/value/bulk",
        "methods": ["POST"],
        "ttl": DEFAULT_TTL_SECONDS,
        "cost_estimate": 10.0,
        "description": "Bulk value estimates"
    },
    
    # Rent Estimates
    "rent_estimate": {
        "path": "/v1/estimates/rent",
        "methods": ["GET"],
        "ttl": DEFAULT_TTL_SECONDS,
        "cost_estimate": 2.0,
        "description": "Get rent estimate"
    },
    "rent_estimate_bulk": {
        "path": "/v1/estimates/rent/bulk",
        "methods": ["POST"],
        "ttl": DEFAULT_TTL_SECONDS,
        "cost_estimate": 10.0,
        "description": "Bulk rent estimates"
    },
    
    # Listings
    "listings_sale": {
        "path": "/v1/listings/sale",
        "methods": ["GET"],
        "ttl": 1800,  # 30 minutes
        "cost_estimate": 0.5,
        "description": "Search sale listings"
    },
    "listings_rental": {
        "path": "/v1/listings/rental",
        "methods": ["GET"],
        "ttl": 1800,  # 30 minutes
        "cost_estimate": 0.5,
        "description": "Search rental listings"
    },
    "listing_by_id": {
        "path": "/v1/listings/{listing_id}",
        "methods": ["GET"],
        "ttl": 3600,
        "cost_estimate": 0.5,
        "description": "Get listing by ID"
    },
    
    # Market Statistics
    "market_stats": {
        "path": "/v1/markets/stats",
        "methods": ["GET"],
        "ttl": 7200,  # 2 hours
        "cost_estimate": 5.0,
        "description": "Market statistics"
    },
    
    # Comparables
    "comparables": {
        "path": "/v1/comparables",
        "methods": ["GET"],
        "ttl": DEFAULT_TTL_SECONDS,
        "cost_estimate": 3.0,
        "description": "Comparable properties"
    }
}


async def proxy_to_rentcast(
    endpoint_key: str,
    api_key: APIKey,
    request: Request,
    db: AsyncSession,
    method: str = "GET",
    path_params: Optional[Dict[str, str]] = None,
    query_params: Optional[Dict[str, Any]] = None,
    body: Optional[Dict[str, Any]] = None,
    force_refresh: bool = False,
    ttl_override: Optional[int] = None
) -> Dict[str, Any]:
    """
    Proxy request to Rentcast API with intelligent caching.
    """
    start_time = time.time()
    endpoint_config = RENTCAST_ENDPOINTS[endpoint_key]
    
    # Build URL
    path = endpoint_config["path"]
    if path_params:
        for key, value in path_params.items():
            path = path.replace(f"{{{key}}}", str(value))
    
    url = f"{RENTCAST_BASE_URL}{path}"
    
    # Generate cache key
    cache_data = {
        "endpoint": endpoint_key,
        "method": method,
        "path_params": path_params or {},
        "query_params": query_params or {},
        "body": body or {}
    }
    cache_key = CacheEntry.generate_cache_key(endpoint_key, method, cache_data)
    
    # Check cache first (unless force refresh)
    cached_response = None
    if not force_refresh:
        cached_response = await cache_manager.backend.get(cache_key)
    
    if cached_response and not force_refresh:
        # Cache hit
        response_time = (time.time() - start_time) * 1000
        
        await record_usage(
            api_key=api_key,
            endpoint=endpoint_key,
            method=method,
            status_code=cached_response.get('status_code', 200),
            response_time_ms=response_time,
            cache_hit=True,
            estimated_cost=0.0,  # No cost for cache hits
            request=request,
            db=db
        )
        
        return {
            **cached_response,
            "x_cache_hit": True,
            "x_response_time_ms": response_time,
            "x_cached_at": cached_response.get('cached_at')
        }
    
    # Cache miss - check rate limits
    if not await check_rate_limits(api_key, endpoint_key, db):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded"
        )
    
    # Make request to Rentcast API
    # Extract the original Rentcast API key from the request headers
    # The bearer token is the actual Rentcast API key
    auth_header = request.headers.get("authorization", "")
    rentcast_key = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else ""
    
    headers = {
        "X-Api-Key": rentcast_key,
        "Content-Type": "application/json"
    }
    
    try:
        if method == "GET":
            response = await http_client.get(
                url,
                params=query_params,
                headers=headers
            )
        elif method == "POST":
            response = await http_client.post(
                url,
                params=query_params,
                json=body,
                headers=headers
            )
        else:
            raise HTTPException(status_code=405, detail="Method not allowed")
        
        response.raise_for_status()
        
        # Parse response
        response_data = response.json() if response.content else {}
        response_time = (time.time() - start_time) * 1000
        
        # Store in cache with attribution to the key that fetched it
        key_hash = hashlib.sha256(rentcast_key.encode()).hexdigest() if rentcast_key else None
        cache_entry_data = {
            "data": response_data,
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "endpoint": endpoint_key,
            "method": method,
            "params": cache_data,
            "params_hash": hashlib.md5(json.dumps(cache_data, sort_keys=True).encode()).hexdigest(),
            "estimated_cost": endpoint_config["cost_estimate"],
            "fetched_by_key_hash": key_hash,
        }
        
        ttl = ttl_override or endpoint_config["ttl"]
        await cache_manager.backend.set(cache_key, cache_entry_data, ttl)
        
        # Record usage
        await record_usage(
            api_key=api_key,
            endpoint=endpoint_key,
            method=method,
            status_code=response.status_code,
            response_time_ms=response_time,
            cache_hit=False,
            estimated_cost=endpoint_config["cost_estimate"],
            request=request,
            db=db
        )
        
        return {
            "data": response_data,
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "x_cache_hit": False,
            "x_response_time_ms": response_time,
            "x_estimated_cost": endpoint_config["cost_estimate"]
        }
        
    except httpx.HTTPStatusError as e:
        response_time = (time.time() - start_time) * 1000
        
        await record_usage(
            api_key=api_key,
            endpoint=endpoint_key,
            method=method,
            status_code=e.response.status_code,
            response_time_ms=response_time,
            cache_hit=False,
            estimated_cost=endpoint_config["cost_estimate"],
            request=request,
            db=db
        )
        
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Upstream API error: {e.response.text}"
        )
    
    except Exception as e:
        logger.error(f"Error proxying to Rentcast: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Health check and system endpoints
@app.get("/health", response_model=HealthCheckResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    """Health check endpoint."""
    try:
        # Check database
        await db.execute(select(1))
        db_status = "healthy"
        
        # Count active keys
        active_keys_stmt = select(func.count(APIKey.id)).where(APIKey.is_active == True)
        active_keys_result = await db.execute(active_keys_stmt)
        active_keys = active_keys_result.scalar()
        
        # Count cache entries
        cache_entries_stmt = select(func.count(CacheEntry.id)).where(CacheEntry.is_valid == True)
        cache_entries_result = await db.execute(cache_entries_stmt)
        total_cache_entries = cache_entries_result.scalar()
        
        # Calculate 24h cache hit ratio
        twenty_four_hours_ago = datetime.now(timezone.utc) - timedelta(hours=24)
        hit_ratio_stmt = select(
            func.count(UsageStats.id).label('total'),
            func.sum(case((UsageStats.cache_hit == True, 1), else_=0)).label('hits')
        ).where(UsageStats.created_at >= twenty_four_hours_ago)
        
        hit_ratio_result = await db.execute(hit_ratio_stmt)
        hit_ratio_data = hit_ratio_result.first()
        
        cache_hit_ratio_24h = None
        if hit_ratio_data and hit_ratio_data.total > 0:
            cache_hit_ratio_24h = (hit_ratio_data.hits or 0) / hit_ratio_data.total
        
        return HealthCheckResponse(
            status="healthy",
            timestamp=datetime.now(timezone.utc),
            version="1.0.0",
            database=db_status,
            cache_backend="sqlite",
            active_keys=active_keys,
            total_cache_entries=total_cache_entries,
            cache_hit_ratio_24h=cache_hit_ratio_24h
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")


@app.get("/metrics", response_model=MetricsResponse)
@limiter.limit("10/minute")
async def get_metrics(request: Request, db: AsyncSession = Depends(get_db)):
    """Get system metrics."""
    try:
        # Total requests
        total_requests_stmt = select(func.count(UsageStats.id))
        total_requests_result = await db.execute(total_requests_stmt)
        total_requests = total_requests_result.scalar()
        
        # Cache hits/misses
        cache_hits_stmt = select(func.count(UsageStats.id)).where(UsageStats.cache_hit == True)
        cache_hits_result = await db.execute(cache_hits_stmt)
        cache_hits = cache_hits_result.scalar()
        
        cache_misses = total_requests - cache_hits
        cache_hit_ratio = cache_hits / total_requests if total_requests > 0 else 0
        
        # Active API keys
        active_keys_stmt = select(func.count(APIKey.id)).where(APIKey.is_active == True)
        active_keys_result = await db.execute(active_keys_stmt)
        active_api_keys = active_keys_result.scalar()
        
        # Average response time
        avg_response_time_stmt = select(func.avg(UsageStats.response_time_ms))
        avg_response_time_result = await db.execute(avg_response_time_stmt)
        avg_response_time_ms = avg_response_time_result.scalar() or 0
        
        # Uptime
        uptime_seconds = int(time.time() - app_start_time) if app_start_time else 0
        
        # 24h metrics
        twenty_four_hours_ago = datetime.now(timezone.utc) - timedelta(hours=24)
        
        requests_24h_stmt = select(func.count(UsageStats.id)).where(
            UsageStats.created_at >= twenty_four_hours_ago
        )
        requests_24h_result = await db.execute(requests_24h_stmt)
        requests_24h = requests_24h_result.scalar()
        
        cache_hits_24h_stmt = select(func.count(UsageStats.id)).where(
            and_(
                UsageStats.created_at >= twenty_four_hours_ago,
                UsageStats.cache_hit == True
            )
        )
        cache_hits_24h_result = await db.execute(cache_hits_24h_stmt)
        cache_hits_24h = cache_hits_24h_result.scalar()
        
        cost_24h_stmt = select(func.sum(UsageStats.estimated_cost)).where(
            and_(
                UsageStats.created_at >= twenty_four_hours_ago,
                UsageStats.cache_hit == False
            )
        )
        cost_24h_result = await db.execute(cost_24h_stmt)
        cost_24h = cost_24h_result.scalar() or 0
        
        # Top endpoints
        top_endpoints_stmt = select(
            UsageStats.endpoint,
            func.count(UsageStats.id).label('count')
        ).where(
            UsageStats.created_at >= twenty_four_hours_ago
        ).group_by(UsageStats.endpoint).order_by(func.count(UsageStats.id).desc()).limit(5)
        
        top_endpoints_result = await db.execute(top_endpoints_stmt)
        top_endpoints = [
            {"endpoint": row.endpoint, "requests": row.count}
            for row in top_endpoints_result
        ]
        
        return MetricsResponse(
            total_requests=total_requests,
            cache_hits=cache_hits,
            cache_misses=cache_misses,
            cache_hit_ratio=cache_hit_ratio,
            active_api_keys=active_api_keys,
            total_cost_saved=0.0,  # Calculate based on cache hits
            avg_response_time_ms=avg_response_time_ms,
            uptime_seconds=uptime_seconds,
            requests_24h=requests_24h,
            cache_hits_24h=cache_hits_24h,
            cost_24h=cost_24h,
            top_endpoints=top_endpoints
        )
        
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving metrics")


# API Key Management endpoints
@app.post("/admin/api-keys", response_model=APIKeyResponse, status_code=201)
@limiter.limit("5/minute")
async def create_api_key(
    request: Request,
    key_request: CreateAPIKeyRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create a new API key."""
    try:
        # Check if key name already exists
        existing_stmt = select(APIKey).where(APIKey.key_name == key_request.key_name)
        existing_result = await db.execute(existing_stmt)
        if existing_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="API key name already exists")
        
        # Hash the Rentcast API key
        key_hash = hashlib.sha256(key_request.rentcast_api_key.encode()).hexdigest()
        
        # Create new API key
        new_key = APIKey(
            key_name=key_request.key_name,
            key_hash=key_hash,
            daily_limit=key_request.daily_limit,
            monthly_limit=key_request.monthly_limit,
            expires_at=key_request.expires_at,
            last_daily_reset=datetime.now(timezone.utc),
            last_monthly_reset=datetime.now(timezone.utc)
        )
        
        db.add(new_key)
        await db.commit()
        await db.refresh(new_key)
        
        logger.info(f"Created API key: {new_key.key_name}")
        
        return APIKeyResponse.from_orm(new_key)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating API key: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Error creating API key")


# Rentcast API Proxy Endpoints
@app.get("/api/v1/properties")
@limiter.limit("60/minute")
async def search_properties(
    request: Request,
    api_key: APIKey = Depends(require_api_key),
    db: AsyncSession = Depends(get_db),
    # Query parameters
    address: Optional[str] = Query(None),
    zipCode: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    propertyType: Optional[str] = Query(None),
    bedrooms: Optional[int] = Query(None),
    bathrooms: Optional[float] = Query(None),
    squareFootage: Optional[int] = Query(None),
    # Pagination
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    # Cache control
    force_refresh: bool = Query(False),
    ttl_override: Optional[int] = Query(None, gt=0)
):
    """Search property records."""
    query_params = {
        k: v for k, v in {
            "address": address,
            "zipCode": zipCode,
            "city": city,
            "state": state,
            "propertyType": propertyType,
            "bedrooms": bedrooms,
            "bathrooms": bathrooms,
            "squareFootage": squareFootage,
            "offset": offset,
            "limit": limit
        }.items() if v is not None
    }
    
    result = await proxy_to_rentcast(
        endpoint_key="properties",
        api_key=api_key,
        request=request,
        method="GET",
        query_params=query_params,
        force_refresh=force_refresh,
        ttl_override=ttl_override,
        db=db
    )
    
    return JSONResponse(
        content=result["data"],
        status_code=result["status_code"],
        headers={
            "X-Cache-Hit": str(result["x_cache_hit"]),
            "X-Response-Time-MS": str(result["x_response_time_ms"]),
            **({} if result["x_cache_hit"] else {"X-Estimated-Cost": str(result.get("x_estimated_cost", 0))})
        }
    )


@app.get("/api/v1/properties/{property_id}")
@limiter.limit("60/minute")
async def get_property_by_id(
    request: Request,
    property_id: str = Path(..., description="Property ID"),
    api_key: APIKey = Depends(require_api_key),
    db: AsyncSession = Depends(get_db),
    force_refresh: bool = Query(False),
    ttl_override: Optional[int] = Query(None, gt=0)
):
    """Get property by ID."""
    result = await proxy_to_rentcast(
        endpoint_key="property_by_id",
        api_key=api_key,
        request=request,
        method="GET",
        path_params={"property_id": property_id},
        force_refresh=force_refresh,
        ttl_override=ttl_override,
        db=db
    )
    
    return JSONResponse(
        content=result["data"],
        status_code=result["status_code"],
        headers={
            "X-Cache-Hit": str(result["x_cache_hit"]),
            "X-Response-Time-MS": str(result["x_response_time_ms"]),
            **({} if result["x_cache_hit"] else {"X-Estimated-Cost": str(result.get("x_estimated_cost", 0))})
        }
    )


@app.get("/api/v1/estimates/value")
@limiter.limit("30/minute")  # Lower limit for expensive endpoints
async def get_value_estimate(
    request: Request,
    api_key: APIKey = Depends(require_api_key),
    db: AsyncSession = Depends(get_db),
    # Property parameters
    address: Optional[str] = Query(None),
    zipCode: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    propertyType: Optional[str] = Query(None),
    bedrooms: Optional[int] = Query(None),
    bathrooms: Optional[float] = Query(None),
    squareFootage: Optional[int] = Query(None),
    # Cache control
    force_refresh: bool = Query(False),
    ttl_override: Optional[int] = Query(None, gt=0)
):
    """Get property value estimate."""
    query_params = {
        k: v for k, v in {
            "address": address,
            "zipCode": zipCode,
            "city": city,
            "state": state,
            "propertyType": propertyType,
            "bedrooms": bedrooms,
            "bathrooms": bathrooms,
            "squareFootage": squareFootage
        }.items() if v is not None
    }
    
    result = await proxy_to_rentcast(
        endpoint_key="value_estimate",
        api_key=api_key,
        request=request,
        method="GET",
        query_params=query_params,
        force_refresh=force_refresh,
        ttl_override=ttl_override,
        db=db
    )
    
    return JSONResponse(
        content=result["data"],
        status_code=result["status_code"],
        headers={
            "X-Cache-Hit": str(result["x_cache_hit"]),
            "X-Response-Time-MS": str(result["x_response_time_ms"]),
            **({} if result["x_cache_hit"] else {"X-Estimated-Cost": str(result.get("x_estimated_cost", 0))})
        }
    )


@app.get("/api/v1/estimates/rent")
@limiter.limit("30/minute")
async def get_rent_estimate(
    request: Request,
    api_key: APIKey = Depends(require_api_key),
    db: AsyncSession = Depends(get_db),
    # Property parameters
    address: Optional[str] = Query(None),
    zipCode: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    propertyType: Optional[str] = Query(None),
    bedrooms: Optional[int] = Query(None),
    bathrooms: Optional[float] = Query(None),
    squareFootage: Optional[int] = Query(None),
    # Cache control
    force_refresh: bool = Query(False),
    ttl_override: Optional[int] = Query(None, gt=0)
):
    """Get rent estimate."""
    query_params = {
        k: v for k, v in {
            "address": address,
            "zipCode": zipCode,
            "city": city,
            "state": state,
            "propertyType": propertyType,
            "bedrooms": bedrooms,
            "bathrooms": bathrooms,
            "squareFootage": squareFootage
        }.items() if v is not None
    }
    
    result = await proxy_to_rentcast(
        endpoint_key="rent_estimate",
        api_key=api_key,
        request=request,
        method="GET",
        query_params=query_params,
        force_refresh=force_refresh,
        ttl_override=ttl_override,
        db=db
    )
    
    return JSONResponse(
        content=result["data"],
        status_code=result["status_code"],
        headers={
            "X-Cache-Hit": str(result["x_cache_hit"]),
            "X-Response-Time-MS": str(result["x_response_time_ms"]),
            **({} if result["x_cache_hit"] else {"X-Estimated-Cost": str(result.get("x_estimated_cost", 0))})
        }
    )


@app.get("/api/v1/listings/sale")
@limiter.limit("60/minute")
async def search_sale_listings(
    request: Request,
    api_key: APIKey = Depends(require_api_key),
    db: AsyncSession = Depends(get_db),
    # Search parameters
    address: Optional[str] = Query(None),
    zipCode: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    propertyType: Optional[str] = Query(None),
    bedrooms: Optional[int] = Query(None),
    bathrooms: Optional[float] = Query(None),
    # Pagination
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    # Cache control
    force_refresh: bool = Query(False),
    ttl_override: Optional[int] = Query(None, gt=0)
):
    """Search sale listings."""
    query_params = {
        k: v for k, v in {
            "address": address,
            "zipCode": zipCode,
            "city": city,
            "state": state,
            "propertyType": propertyType,
            "bedrooms": bedrooms,
            "bathrooms": bathrooms,
            "offset": offset,
            "limit": limit
        }.items() if v is not None
    }
    
    result = await proxy_to_rentcast(
        endpoint_key="listings_sale",
        api_key=api_key,
        request=request,
        method="GET",
        query_params=query_params,
        force_refresh=force_refresh,
        ttl_override=ttl_override,
        db=db
    )
    
    return JSONResponse(
        content=result["data"],
        status_code=result["status_code"],
        headers={
            "X-Cache-Hit": str(result["x_cache_hit"]),
            "X-Response-Time-MS": str(result["x_response_time_ms"]),
            **({} if result["x_cache_hit"] else {"X-Estimated-Cost": str(result.get("x_estimated_cost", 0))})
        }
    )


@app.get("/api/v1/listings/rental")
@limiter.limit("60/minute")
async def search_rental_listings(
    request: Request,
    api_key: APIKey = Depends(require_api_key),
    db: AsyncSession = Depends(get_db),
    # Search parameters
    address: Optional[str] = Query(None),
    zipCode: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    propertyType: Optional[str] = Query(None),
    bedrooms: Optional[int] = Query(None),
    bathrooms: Optional[float] = Query(None),
    # Pagination
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    # Cache control
    force_refresh: bool = Query(False),
    ttl_override: Optional[int] = Query(None, gt=0)
):
    """Search rental listings."""
    query_params = {
        k: v for k, v in {
            "address": address,
            "zipCode": zipCode,
            "city": city,
            "state": state,
            "propertyType": propertyType,
            "bedrooms": bedrooms,
            "bathrooms": bathrooms,
            "offset": offset,
            "limit": limit
        }.items() if v is not None
    }
    
    result = await proxy_to_rentcast(
        endpoint_key="listings_rental",
        api_key=api_key,
        request=request,
        method="GET",
        query_params=query_params,
        force_refresh=force_refresh,
        ttl_override=ttl_override,
        db=db
    )
    
    return JSONResponse(
        content=result["data"],
        status_code=result["status_code"],
        headers={
            "X-Cache-Hit": str(result["x_cache_hit"]),
            "X-Response-Time-MS": str(result["x_response_time_ms"]),
            **({} if result["x_cache_hit"] else {"X-Estimated-Cost": str(result.get("x_estimated_cost", 0))})
        }
    )


@app.get("/api/v1/markets/stats")
@limiter.limit("20/minute")
async def get_market_stats(
    request: Request,
    api_key: APIKey = Depends(require_api_key),
    db: AsyncSession = Depends(get_db),
    # Location parameters
    zipCode: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    # Cache control
    force_refresh: bool = Query(False),
    ttl_override: Optional[int] = Query(None, gt=0)
):
    """Get market statistics."""
    query_params = {
        k: v for k, v in {
            "zipCode": zipCode,
            "city": city,
            "state": state
        }.items() if v is not None
    }
    
    result = await proxy_to_rentcast(
        endpoint_key="market_stats",
        api_key=api_key,
        request=request,
        method="GET",
        query_params=query_params,
        force_refresh=force_refresh,
        ttl_override=ttl_override,
        db=db
    )
    
    return JSONResponse(
        content=result["data"],
        status_code=result["status_code"],
        headers={
            "X-Cache-Hit": str(result["x_cache_hit"]),
            "X-Response-Time-MS": str(result["x_response_time_ms"]),
            **({} if result["x_cache_hit"] else {"X-Estimated-Cost": str(result.get("x_estimated_cost", 0))})
        }
    )


@app.get("/api/v1/comparables")
@limiter.limit("30/minute")
async def get_comparables(
    request: Request,
    api_key: APIKey = Depends(require_api_key),
    db: AsyncSession = Depends(get_db),
    # Property parameters
    address: Optional[str] = Query(None),
    zipCode: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    propertyType: Optional[str] = Query(None),
    bedrooms: Optional[int] = Query(None),
    bathrooms: Optional[float] = Query(None),
    squareFootage: Optional[int] = Query(None),
    # Cache control
    force_refresh: bool = Query(False),
    ttl_override: Optional[int] = Query(None, gt=0)
):
    """Get comparable properties."""
    query_params = {
        k: v for k, v in {
            "address": address,
            "zipCode": zipCode,
            "city": city,
            "state": state,
            "propertyType": propertyType,
            "bedrooms": bedrooms,
            "bathrooms": bathrooms,
            "squareFootage": squareFootage
        }.items() if v is not None
    }
    
    result = await proxy_to_rentcast(
        endpoint_key="comparables",
        api_key=api_key,
        request=request,
        method="GET",
        query_params=query_params,
        force_refresh=force_refresh,
        ttl_override=ttl_override,
        db=db
    )
    
    return JSONResponse(
        content=result["data"],
        status_code=result["status_code"],
        headers={
            "X-Cache-Hit": str(result["x_cache_hit"]),
            "X-Response-Time-MS": str(result["x_response_time_ms"]),
            **({} if result["x_cache_hit"] else {"X-Estimated-Cost": str(result.get("x_estimated_cost", 0))})
        }
    )


# Cache management endpoints
@app.post("/admin/cache/clear")
@limiter.limit("5/minute")
async def clear_cache(
    request: Request,
    cache_control: CacheControlRequest,
    db: AsyncSession = Depends(get_db)
):
    """Clear cache entries."""
    try:
        if cache_control.endpoint:
            pattern = f"*{cache_control.endpoint}*"
        else:
            pattern = "*"
        
        cleared_count = await cache_manager.invalidate_pattern(pattern)
        
        return {
            "message": f"Cleared {cleared_count} cache entries",
            "pattern": pattern
        }
        
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail="Error clearing cache")


def run():
    """Run the server."""
    import uvicorn
    uvicorn.run(
        "rentcache.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    run()