"""
Intelligent caching system for RentCache with multiple backend support.
Supports SQLite/PostgreSQL for persistent storage and Redis for performance.
"""
import asyncio
import json
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List, Union
import logging

import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.orm import selectinload

from .models import CacheEntry, APIKey, RateLimit, UsageStats, CacheStats

logger = logging.getLogger(__name__)


class CacheBackend:
    """Base class for cache backends."""
    
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached data by key."""
        raise NotImplementedError
    
    async def set(
        self, 
        key: str, 
        data: Dict[str, Any], 
        ttl: Optional[int] = None
    ) -> bool:
        """Set cached data with optional TTL."""
        raise NotImplementedError
    
    async def delete(self, key: str) -> bool:
        """Delete cached data by key."""
        raise NotImplementedError
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear keys matching pattern. Returns count of deleted keys."""
        raise NotImplementedError
    
    async def health_check(self) -> bool:
        """Check if cache backend is healthy."""
        raise NotImplementedError


class SQLiteCacheBackend(CacheBackend):
    """SQLite-based cache backend for persistent storage."""
    
    def __init__(self, session_factory):
        self.SessionLocal = session_factory
    
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached data from SQLite."""
        async with self.SessionLocal() as db:
            try:
                stmt = select(CacheEntry).where(
                    and_(
                        CacheEntry.cache_key == key,
                        CacheEntry.is_valid == True
                    )
                )
                result = await db.execute(stmt)
                entry = result.scalar_one_or_none()
                
                if not entry:
                    return None
                
                # Check expiration
                if entry.is_expired():
                    logger.debug(f"Cache entry expired: {key}")
                    # Mark as invalid but don't delete (soft delete)
                    await self._mark_invalid(entry.id, db)
                    return None
                
                # Update access statistics
                entry.increment_hit()
                await db.commit()
                
                logger.debug(f"Cache hit: {key}")
                return {
                    'data': entry.get_response_data(),
                    'status_code': entry.status_code,
                    'headers': json.loads(entry.headers_json) if entry.headers_json else {},
                    'cached_at': entry.created_at,
                    'expires_at': entry.expires_at,
                    'hit_count': entry.hit_count
                }
                
            except Exception as e:
                logger.error(f"Error getting cache entry {key}: {e}")
                return None
    
    async def set(
        self, 
        key: str, 
        data: Dict[str, Any], 
        ttl: Optional[int] = None
    ) -> bool:
        """Store data in SQLite cache."""
        async with self.SessionLocal() as db:
            try:
                ttl = ttl or 3600  # Default 1 hour
                expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl)
                
                # Check if entry exists
                stmt = select(CacheEntry).where(CacheEntry.cache_key == key)
                result = await db.execute(stmt)
                existing_entry = result.scalar_one_or_none()
                
                if existing_entry:
                    # Update existing entry
                    existing_entry.response_data = json.dumps(data.get('data', {}))
                    existing_entry.status_code = data.get('status_code', 200)
                    existing_entry.headers_json = json.dumps(data.get('headers', {}))
                    existing_entry.is_valid = True
                    existing_entry.expires_at = expires_at
                    existing_entry.ttl_seconds = ttl
                    existing_entry.updated_at = datetime.now(timezone.utc)
                    existing_entry.estimated_cost = data.get('estimated_cost', 0.0)
                else:
                    # Create new entry
                    new_entry = CacheEntry(
                        cache_key=key,
                        endpoint=data.get('endpoint', ''),
                        method=data.get('method', 'GET'),
                        params_hash=data.get('params_hash', ''),
                        params_json=json.dumps(data.get('params', {})),
                        response_data=json.dumps(data.get('data', {})),
                        status_code=data.get('status_code', 200),
                        headers_json=json.dumps(data.get('headers', {})),
                        expires_at=expires_at,
                        ttl_seconds=ttl,
                        estimated_cost=data.get('estimated_cost', 0.0),
                        fetched_by_key_hash=data.get('fetched_by_key_hash'),
                    )
                    db.add(new_entry)
                
                await db.commit()
                logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
                return True
                
            except Exception as e:
                logger.error(f"Error setting cache entry {key}: {e}")
                await db.rollback()
                return False
    
    async def delete(self, key: str) -> bool:
        """Soft delete cache entry."""
        async with self.SessionLocal() as db:
            try:
                stmt = update(CacheEntry).where(
                    CacheEntry.cache_key == key
                ).values(is_valid=False)
                await db.execute(stmt)
                await db.commit()
                logger.debug(f"Cache deleted: {key}")
                return True
            except Exception as e:
                logger.error(f"Error deleting cache entry {key}: {e}")
                await db.rollback()
                return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear cache entries matching pattern."""
        async with self.SessionLocal() as db:
            try:
                # Escape SQL LIKE special characters first, then convert glob wildcards
                escaped = pattern.replace('%', r'\%').replace('_', r'\_')
                sql_pattern = escaped.replace('*', '%')

                stmt = update(CacheEntry).where(
                    CacheEntry.cache_key.like(sql_pattern, escape='\\')
                ).values(is_valid=False)

                result = await db.execute(stmt)
                await db.commit()

                count = result.rowcount
                logger.info(f"Cleared {count} cache entries matching pattern: {pattern}")
                return count

            except Exception as e:
                logger.error(f"Error clearing cache pattern {pattern}: {e}")
                await db.rollback()
                return 0

    async def health_check(self) -> bool:
        """Check SQLite database health."""
        async with self.SessionLocal() as db:
            try:
                await db.execute(select(1))
                return True
            except Exception as e:
                logger.error(f"SQLite health check failed: {e}")
                return False
    
    async def _mark_invalid(self, entry_id: int, db: AsyncSession):
        """Mark specific entry as invalid."""
        stmt = update(CacheEntry).where(
            CacheEntry.id == entry_id
        ).values(is_valid=False)
        await db.execute(stmt)
    
    async def _mark_invalid_by_key(self, key: str):
        """Mark entry invalid by cache key."""
        stmt = update(CacheEntry).where(
            CacheEntry.cache_key == key
        ).values(is_valid=False)
        await self.db.execute(stmt)


class RedisCacheBackend(CacheBackend):
    """Redis-based cache backend for high performance."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self._redis: Optional[redis.Redis] = None
    
    async def connect(self):
        """Connect to Redis."""
        if not self._redis:
            self._redis = redis.from_url(self.redis_url, decode_responses=True)
    
    async def disconnect(self):
        """Disconnect from Redis."""
        if self._redis:
            await self._redis.close()
            self._redis = None
    
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached data from Redis."""
        try:
            await self.connect()
            data = await self._redis.get(f"rentcache:{key}")
            
            if not data:
                return None
            
            cached_data = json.loads(data)
            logger.debug(f"Redis cache hit: {key}")
            
            # Increment hit counter in Redis
            await self._redis.incr(f"rentcache:hits:{key}")
            
            return cached_data
            
        except Exception as e:
            logger.error(f"Error getting Redis cache entry {key}: {e}")
            return None
    
    async def set(
        self, 
        key: str, 
        data: Dict[str, Any], 
        ttl: Optional[int] = None
    ) -> bool:
        """Store data in Redis cache."""
        try:
            await self.connect()
            
            # Add metadata
            cache_data = {
                **data,
                'cached_at': datetime.now(timezone.utc).isoformat(),
                'ttl': ttl or 3600
            }
            
            success = await self._redis.set(
                f"rentcache:{key}",
                json.dumps(cache_data, default=str),
                ex=ttl or 3600
            )
            
            if success:
                logger.debug(f"Redis cache set: {key} (TTL: {ttl or 3600}s)")
            
            return bool(success)
            
        except Exception as e:
            logger.error(f"Error setting Redis cache entry {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete cache entry from Redis."""
        try:
            await self.connect()
            result = await self._redis.delete(f"rentcache:{key}")
            
            if result:
                logger.debug(f"Redis cache deleted: {key}")
            
            return bool(result)
            
        except Exception as e:
            logger.error(f"Error deleting Redis cache entry {key}: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear Redis keys matching pattern."""
        try:
            await self.connect()
            redis_pattern = f"rentcache:{pattern}"
            
            # Get matching keys
            keys = await self._redis.keys(redis_pattern)
            
            if keys:
                result = await self._redis.delete(*keys)
                logger.info(f"Cleared {result} Redis keys matching pattern: {pattern}")
                return result
            
            return 0
            
        except Exception as e:
            logger.error(f"Error clearing Redis pattern {pattern}: {e}")
            return 0
    
    async def health_check(self) -> bool:
        """Check Redis health."""
        try:
            await self.connect()
            await self._redis.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False


class HybridCacheBackend(CacheBackend):
    """
    Hybrid cache backend using Redis for speed + SQLite for persistence.
    Redis serves as L1 cache, SQLite as L2 cache with analytics.
    """
    
    def __init__(self, db_session: AsyncSession, redis_url: Optional[str] = None):
        self.sqlite_backend = SQLiteCacheBackend(db_session)
        self.redis_backend = RedisCacheBackend(redis_url) if redis_url else None
    
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get from Redis first, fallback to SQLite."""
        # Try Redis first (L1 cache)
        if self.redis_backend:
            data = await self.redis_backend.get(key)
            if data:
                return data
        
        # Fallback to SQLite (L2 cache)
        data = await self.sqlite_backend.get(key)
        
        # If found in SQLite, populate Redis
        if data and self.redis_backend:
            await self.redis_backend.set(key, data, ttl=3600)
        
        return data
    
    async def set(
        self, 
        key: str, 
        data: Dict[str, Any], 
        ttl: Optional[int] = None
    ) -> bool:
        """Set in both Redis and SQLite."""
        results = []
        
        # Set in SQLite (persistent)
        results.append(await self.sqlite_backend.set(key, data, ttl))
        
        # Set in Redis (fast access)
        if self.redis_backend:
            results.append(await self.redis_backend.set(key, data, ttl))
        
        return any(results)  # Success if at least one backend succeeds
    
    async def delete(self, key: str) -> bool:
        """Delete from both backends."""
        results = []
        
        results.append(await self.sqlite_backend.delete(key))
        
        if self.redis_backend:
            results.append(await self.redis_backend.delete(key))
        
        return any(results)
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear from both backends."""
        total_cleared = 0
        
        total_cleared += await self.sqlite_backend.clear_pattern(pattern)
        
        if self.redis_backend:
            total_cleared += await self.redis_backend.clear_pattern(pattern)
        
        return total_cleared
    
    async def health_check(self) -> bool:
        """Check health of both backends."""
        sqlite_healthy = await self.sqlite_backend.health_check()
        redis_healthy = True
        
        if self.redis_backend:
            redis_healthy = await self.redis_backend.health_check()
        
        return sqlite_healthy and redis_healthy


class CacheManager:
    """
    High-level cache manager with intelligent caching strategies.
    """
    
    def __init__(
        self, 
        backend: CacheBackend,
        default_ttl: int = 3600,
        stale_while_revalidate: bool = True
    ):
        self.backend = backend
        self.default_ttl = default_ttl
        self.stale_while_revalidate = stale_while_revalidate
        
    async def get_or_fetch(
        self,
        key: str,
        fetch_func,
        ttl: Optional[int] = None,
        serve_stale_on_error: bool = True,
        **fetch_kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached data or fetch from upstream with intelligent fallback strategies.
        """
        # Try to get from cache first
        cached_data = await self.backend.get(key)
        
        if cached_data:
            return cached_data
        
        # Cache miss - need to fetch from upstream
        try:
            logger.debug(f"Cache miss, fetching: {key}")
            fresh_data = await fetch_func(**fetch_kwargs)
            
            if fresh_data:
                # Store in cache
                await self.backend.set(key, fresh_data, ttl or self.default_ttl)
            
            return fresh_data
            
        except Exception as e:
            logger.error(f"Error fetching data for key {key}: {e}")
            
            if serve_stale_on_error:
                # Try to serve stale data from persistent storage
                stale_data = await self._get_stale_data(key)
                if stale_data:
                    logger.warning(f"Serving stale data for key {key}")
                    return stale_data
            
            raise  # Re-raise if no stale data available
    
    async def invalidate(self, key: str) -> bool:
        """Invalidate specific cache entry."""
        return await self.backend.delete(key)
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate cache entries matching pattern."""
        return await self.backend.clear_pattern(pattern)
    
    async def warm_cache(
        self,
        keys_and_fetch_funcs: List[tuple],
        concurrency: int = 5
    ) -> Dict[str, bool]:
        """
        Warm cache by pre-loading multiple keys concurrently.
        keys_and_fetch_funcs: List of (key, fetch_func, fetch_kwargs) tuples
        """
        results = {}
        semaphore = asyncio.Semaphore(concurrency)
        
        async def warm_single(key: str, fetch_func, fetch_kwargs: Dict[str, Any]):
            async with semaphore:
                try:
                    # Check if already cached
                    if await self.backend.get(key):
                        results[key] = True
                        return
                    
                    # Fetch and cache
                    data = await fetch_func(**fetch_kwargs)
                    if data:
                        success = await self.backend.set(key, data)
                        results[key] = success
                    else:
                        results[key] = False
                        
                except Exception as e:
                    logger.error(f"Error warming cache for key {key}: {e}")
                    results[key] = False
        
        # Execute all warming tasks concurrently
        tasks = [
            warm_single(key, fetch_func, fetch_kwargs or {})
            for key, fetch_func, fetch_kwargs in keys_and_fetch_funcs
        ]
        
        await asyncio.gather(*tasks, return_exceptions=True)
        
        return results
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if hasattr(self.backend, 'db'):  # SQLite backend
            db = self.backend.db
            
            # Total entries
            total_stmt = select(func.count(CacheEntry.id))
            total_result = await db.execute(total_stmt)
            total_entries = total_result.scalar()
            
            # Valid entries
            valid_stmt = select(func.count(CacheEntry.id)).where(CacheEntry.is_valid == True)
            valid_result = await db.execute(valid_stmt)
            valid_entries = valid_result.scalar()
            
            # Hit statistics
            hits_stmt = select(func.sum(CacheEntry.hit_count))
            hits_result = await db.execute(hits_stmt)
            total_hits = hits_result.scalar() or 0
            
            return {
                'total_entries': total_entries,
                'valid_entries': valid_entries,
                'invalid_entries': total_entries - valid_entries,
                'total_hits': total_hits,
                'backend_type': 'sqlite'
            }
        
        return {'backend_type': 'redis', 'details': 'Redis stats not implemented'}
    
    async def cleanup_expired(self, batch_size: int = 1000) -> int:
        """Clean up expired cache entries."""
        if hasattr(self.backend, 'db'):  # SQLite backend
            db = self.backend.db
            
            # Mark expired entries as invalid
            now = datetime.now(timezone.utc)
            stmt = update(CacheEntry).where(
                and_(
                    CacheEntry.expires_at < now,
                    CacheEntry.is_valid == True
                )
            ).values(is_valid=False)
            
            result = await db.execute(stmt)
            await db.commit()
            
            cleaned_count = result.rowcount
            logger.info(f"Marked {cleaned_count} expired cache entries as invalid")
            return cleaned_count
        
        return 0
    
    async def _get_stale_data(self, key: str) -> Optional[Dict[str, Any]]:
        """Try to get stale data from persistent storage."""
        if hasattr(self.backend, 'db'):  # SQLite backend
            db = self.backend.db
            
            # Get entry regardless of validity/expiration
            stmt = select(CacheEntry).where(CacheEntry.cache_key == key)
            result = await db.execute(stmt)
            entry = result.scalar_one_or_none()
            
            if entry:
                return {
                    'data': entry.get_response_data(),
                    'status_code': entry.status_code,
                    'headers': json.loads(entry.headers_json) if entry.headers_json else {},
                    'cached_at': entry.created_at,
                    'expires_at': entry.expires_at,
                    'hit_count': entry.hit_count,
                    'stale': True
                }
        
        return None