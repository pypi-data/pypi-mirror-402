"""
Configuration management for RentCache.
"""
import os
from typing import Optional, List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application
    app_name: str = "RentCache API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    
    # Database
    database_url: str = "sqlite+aiosqlite:///./rentcache.db"
    database_echo: bool = False
    
    # Redis (optional)
    redis_url: Optional[str] = None
    redis_enabled: bool = False
    
    # Rentcast API
    rentcast_base_url: str = "https://api.rentcast.io"
    rentcast_timeout: int = 30
    rentcast_max_retries: int = 3
    
    # Cache settings
    default_cache_ttl: int = 3600  # 1 hour
    expensive_endpoints_ttl: int = 86400  # 24 hours
    enable_stale_while_revalidate: bool = True
    cache_compression: bool = True
    
    # Rate limiting
    enable_rate_limiting: bool = True
    global_rate_limit: str = "1000/hour"
    per_endpoint_rate_limit: str = "100/minute"
    
    # Security
    allowed_hosts: List[str] = ["*"]
    cors_origins: List[str] = ["*"]
    cors_methods: List[str] = ["*"]
    cors_headers: List[str] = ["*"]
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    access_log: bool = True
    
    # Monitoring
    enable_metrics: bool = True
    metrics_endpoint: str = "/metrics"
    health_endpoint: str = "/health"
    
    # Background tasks
    cleanup_interval_hours: int = 24
    stats_aggregation_interval_hours: int = 1
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.debug or os.getenv("ENVIRONMENT") == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return os.getenv("ENVIRONMENT") == "production"


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings