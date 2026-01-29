"""
RentCache - Sophisticated FastAPI proxy server for Rentcast API with intelligent caching.
"""

__version__ = "1.0.0"
__author__ = "RentCache Team"
__email__ = "your.email@example.com"

from .server import app
from .models import (
    CacheEntry, APIKey, RateLimit, UsageStats, CacheStats,
    HealthCheckResponse, MetricsResponse, ProxyRequest,
    CreateAPIKeyRequest, UpdateAPIKeyRequest, CacheControlRequest
)
from .cache import CacheManager, SQLiteCacheBackend, RedisCacheBackend, HybridCacheBackend

__all__ = [
    "app",
    "CacheEntry",
    "APIKey", 
    "RateLimit",
    "UsageStats",
    "CacheStats",
    "HealthCheckResponse",
    "MetricsResponse",
    "ProxyRequest",
    "CreateAPIKeyRequest",
    "UpdateAPIKeyRequest", 
    "CacheControlRequest",
    "CacheManager",
    "SQLiteCacheBackend",
    "RedisCacheBackend",
    "HybridCacheBackend",
]