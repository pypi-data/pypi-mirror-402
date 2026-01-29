"""
Database models for RentCache - SQLAlchemy models for caching, rate limiting, and analytics.
"""
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
import json
import hashlib

from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, Text, Float, 
    Index, ForeignKey, UniqueConstraint, CheckConstraint
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pydantic import BaseModel, Field, field_validator, ConfigDict

Base = declarative_base()


class TimestampMixin:
    """Mixin to add created_at and updated_at timestamps."""
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class CacheEntry(Base, TimestampMixin):
    """
    Cache storage for Rentcast API responses.
    Supports soft deletion and TTL-based expiration.
    """
    __tablename__ = "cache_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    cache_key = Column(String(255), unique=True, index=True, nullable=False)
    endpoint = Column(String(100), index=True, nullable=False)
    method = Column(String(10), default="GET", nullable=False)
    
    # Request parameters (hashed for key generation)
    params_hash = Column(String(64), index=True, nullable=False)
    params_json = Column(Text)  # Full params for debugging
    
    # Response data
    response_data = Column(Text, nullable=False)  # JSON response
    status_code = Column(Integer, default=200, nullable=False)
    headers_json = Column(Text)  # Cached headers
    
    # Cache management
    is_valid = Column(Boolean, default=True, index=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), index=True)
    ttl_seconds = Column(Integer, default=3600)  # Default 1 hour
    
    # Request tracking
    hit_count = Column(Integer, default=0, nullable=False)
    last_accessed = Column(DateTime(timezone=True))
    
    # Cost tracking (if applicable)
    estimated_cost = Column(Float, default=0.0)

    # Attribution - which Rentcast API key originally fetched this data
    fetched_by_key_hash = Column(String(64), index=True, nullable=True)

    __table_args__ = (
        Index('idx_cache_valid_expires', 'is_valid', 'expires_at'),
        Index('idx_cache_endpoint_method', 'endpoint', 'method'),
        CheckConstraint('ttl_seconds > 0', name='positive_ttl'),
    )
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        if not self.expires_at:
            return False
        
        # Ensure both datetimes are timezone-aware for comparison
        now = datetime.now(timezone.utc)
        expires_at = self.expires_at
        
        # If expires_at is naive, assume it's in UTC
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
            
        return now > expires_at
    
    def increment_hit(self):
        """Increment hit counter and update last accessed."""
        self.hit_count += 1
        self.last_accessed = datetime.now(timezone.utc)
    
    def get_response_data(self) -> Dict[str, Any]:
        """Parse and return response data as dict."""
        return json.loads(self.response_data)
    
    def get_params(self) -> Dict[str, Any]:
        """Parse and return request parameters as dict."""
        return json.loads(self.params_json) if self.params_json else {}
    
    @staticmethod
    def generate_cache_key(endpoint: str, method: str, params: Dict[str, Any]) -> str:
        """Generate consistent cache key from endpoint and parameters."""
        # Create consistent parameter string
        param_str = json.dumps(params, sort_keys=True, separators=(',', ':'))
        key_input = f"{method}:{endpoint}:{param_str}"
        return hashlib.md5(key_input.encode()).hexdigest()


class APIKey(Base, TimestampMixin):
    """
    API key management and tracking.
    """
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    key_name = Column(String(100), unique=True, index=True, nullable=False)
    key_hash = Column(String(255), nullable=False)  # Hashed API key
    
    # Usage limits
    daily_limit = Column(Integer, default=1000)
    monthly_limit = Column(Integer, default=10000)
    
    # Current usage
    daily_usage = Column(Integer, default=0, nullable=False)
    monthly_usage = Column(Integer, default=0, nullable=False)
    last_daily_reset = Column(DateTime(timezone=True))
    last_monthly_reset = Column(DateTime(timezone=True))
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime(timezone=True))
    
    # Relationships
    rate_limits = relationship("RateLimit", back_populates="api_key", cascade="all, delete-orphan")
    usage_stats = relationship("UsageStats", back_populates="api_key", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_apikey_active', 'is_active'),
        CheckConstraint('daily_limit > 0', name='positive_daily_limit'),
        CheckConstraint('monthly_limit > 0', name='positive_monthly_limit'),
    )
    
    def can_make_request(self) -> bool:
        """Check if API key can make another request."""
        if not self.is_active:
            return False
        if self.expires_at and datetime.now(timezone.utc) > self.expires_at:
            return False
        if self.daily_usage >= self.daily_limit:
            return False
        if self.monthly_usage >= self.monthly_limit:
            return False
        return True
    
    def increment_usage(self):
        """Increment usage counters."""
        self.daily_usage += 1
        self.monthly_usage += 1


class RateLimit(Base, TimestampMixin):
    """
    Rate limiting tracking per API key and endpoint.
    """
    __tablename__ = "rate_limits"
    
    id = Column(Integer, primary_key=True, index=True)
    api_key_id = Column(Integer, ForeignKey("api_keys.id", ondelete="CASCADE"), nullable=False)
    endpoint = Column(String(100), index=True, nullable=False)
    
    # Rate limit configuration
    requests_per_minute = Column(Integer, default=60, nullable=False)
    requests_per_hour = Column(Integer, default=3600, nullable=False)
    
    # Current usage
    minute_requests = Column(Integer, default=0, nullable=False)
    hour_requests = Column(Integer, default=0, nullable=False)
    
    # Reset timestamps
    minute_reset_at = Column(DateTime(timezone=True))
    hour_reset_at = Column(DateTime(timezone=True))
    
    # Last request tracking
    last_request_at = Column(DateTime(timezone=True))
    backoff_until = Column(DateTime(timezone=True))  # Exponential backoff
    
    # Relationships
    api_key = relationship("APIKey", back_populates="rate_limits")
    
    __table_args__ = (
        UniqueConstraint('api_key_id', 'endpoint', name='unique_api_key_endpoint'),
        Index('idx_ratelimit_endpoint', 'endpoint'),
        CheckConstraint('requests_per_minute > 0', name='positive_rpm'),
        CheckConstraint('requests_per_hour > 0', name='positive_rph'),
    )
    
    def can_make_request(self) -> bool:
        """Check if rate limit allows another request."""
        now = datetime.now(timezone.utc)
        
        # Check exponential backoff
        if self.backoff_until and now < self.backoff_until:
            return False
        
        # Reset counters if needed
        if self.minute_reset_at and now > self.minute_reset_at:
            self.minute_requests = 0
            self.minute_reset_at = now.replace(second=0, microsecond=0) + timedelta(minutes=1)
        
        if self.hour_reset_at and now > self.hour_reset_at:
            self.hour_requests = 0
            self.hour_reset_at = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        
        # Check limits
        return (self.minute_requests < self.requests_per_minute and 
                self.hour_requests < self.requests_per_hour)
    
    def increment_usage(self):
        """Increment rate limit counters."""
        now = datetime.now(timezone.utc)
        self.minute_requests += 1
        self.hour_requests += 1
        self.last_request_at = now


class UsageStats(Base, TimestampMixin):
    """
    Usage statistics and analytics.
    """
    __tablename__ = "usage_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    api_key_id = Column(Integer, ForeignKey("api_keys.id", ondelete="CASCADE"), nullable=False)
    
    # Request details
    endpoint = Column(String(100), index=True, nullable=False)
    method = Column(String(10), default="GET", nullable=False)
    status_code = Column(Integer, nullable=False)
    
    # Timing
    response_time_ms = Column(Float)
    cache_hit = Column(Boolean, default=False, index=True, nullable=False)
    
    # Cost tracking
    estimated_cost = Column(Float, default=0.0)
    
    # Request metadata
    user_agent = Column(String(255))
    ip_address = Column(String(45))  # IPv6 support
    
    # Relationships
    api_key = relationship("APIKey", back_populates="usage_stats")
    
    __table_args__ = (
        Index('idx_usage_endpoint_date', 'endpoint', 'created_at'),
        Index('idx_usage_cache_hit', 'cache_hit'),
        Index('idx_usage_status_code', 'status_code'),
    )


class CacheStats(Base):
    """
    Aggregated cache statistics for monitoring and analytics.
    """
    __tablename__ = "cache_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime(timezone=True), index=True, nullable=False)
    endpoint = Column(String(100), index=True, nullable=False)
    
    # Cache metrics
    total_requests = Column(Integer, default=0, nullable=False)
    cache_hits = Column(Integer, default=0, nullable=False)
    cache_misses = Column(Integer, default=0, nullable=False)
    
    # Response metrics
    avg_response_time_ms = Column(Float)
    total_cost = Column(Float, default=0.0)
    
    # Cache efficiency
    cache_hit_ratio = Column(Float)  # hits / total_requests
    cost_savings = Column(Float, default=0.0)  # Estimated savings from cache hits
    
    __table_args__ = (
        UniqueConstraint('date', 'endpoint', name='unique_date_endpoint'),
        Index('idx_stats_date', 'date'),
    )


# Pydantic models for API responses
class CacheEntryResponse(BaseModel):
    """Response model for cache entry data."""
    id: int
    cache_key: str
    endpoint: str
    method: str
    status_code: int
    is_valid: bool
    expires_at: Optional[datetime]
    hit_count: int
    last_accessed: Optional[datetime]
    created_at: datetime
    estimated_cost: float
    
    model_config = ConfigDict(from_attributes=True)


class APIKeyResponse(BaseModel):
    """Response model for API key data."""
    id: int
    key_name: str
    daily_limit: int
    monthly_limit: int
    daily_usage: int
    monthly_usage: int
    is_active: bool
    expires_at: Optional[datetime]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class UsageStatsResponse(BaseModel):
    """Response model for usage statistics."""
    endpoint: str
    total_requests: int
    cache_hits: int
    cache_misses: int
    cache_hit_ratio: float
    avg_response_time_ms: Optional[float]
    total_cost: float
    
    model_config = ConfigDict(from_attributes=True)


class HealthCheckResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(..., description="Check timestamp")
    version: str = Field(..., description="Service version")
    database: str = Field(..., description="Database status")
    cache_backend: str = Field(..., description="Cache backend status")
    active_keys: int = Field(..., description="Number of active API keys")
    total_cache_entries: int = Field(..., description="Total cache entries")
    cache_hit_ratio_24h: Optional[float] = Field(None, description="24h cache hit ratio")


class MetricsResponse(BaseModel):
    """Metrics response model."""
    total_requests: int
    cache_hits: int
    cache_misses: int
    cache_hit_ratio: float
    active_api_keys: int
    total_cost_saved: float
    avg_response_time_ms: float
    uptime_seconds: int
    
    # Recent activity (last 24h)
    requests_24h: int
    cache_hits_24h: int
    cost_24h: float
    top_endpoints: List[Dict[str, Any]]


# Request models for API endpoints
class ProxyRequest(BaseModel):
    """Base request model for proxied API calls."""
    force_refresh: bool = Field(False, description="Force refresh from upstream API")
    ttl_override: Optional[int] = Field(None, description="Override default TTL in seconds")


class CreateAPIKeyRequest(BaseModel):
    """Request model for creating API keys."""
    key_name: str = Field(..., min_length=1, max_length=100)
    rentcast_api_key: str = Field(..., min_length=1)
    daily_limit: int = Field(1000, gt=0, le=100000)
    monthly_limit: int = Field(10000, gt=0, le=1000000)
    expires_at: Optional[datetime] = None
    
    @field_validator('key_name')
    @classmethod
    def validate_key_name(cls, v):
        # Only allow alphanumeric and underscores
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Key name must contain only letters, numbers, underscores, and hyphens')
        return v


class UpdateAPIKeyRequest(BaseModel):
    """Request model for updating API keys."""
    daily_limit: Optional[int] = Field(None, gt=0, le=100000)
    monthly_limit: Optional[int] = Field(None, gt=0, le=1000000)
    is_active: Optional[bool] = None
    expires_at: Optional[datetime] = None


class CacheControlRequest(BaseModel):
    """Request model for cache control operations."""
    endpoint: Optional[str] = Field(None, description="Specific endpoint to clear")
    older_than_hours: Optional[int] = Field(None, gt=0, description="Clear entries older than N hours")
    invalid_only: bool = Field(False, description="Only clear invalid entries")