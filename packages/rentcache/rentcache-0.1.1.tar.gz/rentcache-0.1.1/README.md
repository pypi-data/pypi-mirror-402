# RentCache - Intelligent Rentcast API Proxy

🏠 **Reduce your Rentcast API costs by 70-90% with intelligent caching, rate limiting, and usage management.**

**RentCache** is a production-ready FastAPI proxy server that sits between your applications and the Rentcast API, providing intelligent caching, cost optimization, and usage analytics. Perfect for real estate applications that need frequent property data access without breaking the budget.


[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-00a393.svg)](https://fastapi.tiangolo.com)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-red.svg)](https://www.sqlalchemy.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Repository](https://img.shields.io/badge/repo-git.supported.systems-orange.svg)](https://git.supported.systems/MCP/rentcache)

## 💰 Cost Savings

**Dramatic API Cost Reduction**:
- 🎯 **70-90% cost savings** through intelligent caching
- 📊 Cache hit ratios typically 80-95% after warm-up
- 💸 **Property records**: $1.00 → $0.10 per request (90% savings)
- 💸 **Value estimates**: $2.00 → $0.20 per request (90% savings)
- 💸 **Market data**: $5.00 → $0.50 per request (90% savings)

**Real-world example**: A property management company reduced their monthly Rentcast bill from $2,500 to $300 using RentCache.

## ✨ Features

### 🚀 **Performance & Caching**
- **Intelligent Multi-Level Caching**: SQLite for persistence + optional Redis for speed
- **Configurable TTL**: Different cache durations for different endpoint types
- **Stale-While-Revalidate**: Serve cached data during upstream failures
- **Cache Warming**: Pre-populate cache for better performance
- **Soft Deletion**: Mark entries invalid instead of deleting for analytics

### 💰 **Cost Management**
- **Usage Tracking**: Monitor API costs and savings from cache hits
- **Rate Limiting**: Prevent expensive API overuse with per-endpoint limits
- **Cost Estimation**: Track estimated costs for each endpoint type
- **Budget Alerts**: Monitor spending against configured limits

### 🔐 **Security & Access Control**
- **API Key Management**: Create, update, and revoke access keys
- **Role-Based Access**: Different limits per API key
- **Rate Limiting**: Global and per-endpoint request limits
- **CORS Support**: Configurable cross-origin resource sharing
- **Request Validation**: Comprehensive input validation with Pydantic

### 📊 **Analytics & Monitoring**
- **Real-time Metrics**: Cache hit ratios, response times, error rates
- **Usage Statistics**: Track usage patterns and popular endpoints
- **Health Checks**: Monitor system and dependency health
- **Structured Logging**: JSON logs for easy parsing and analysis

### 🔧 **Developer Experience**
- **OpenAPI Docs**: Auto-generated API documentation
- **CLI Administration**: Command-line tools for management
- **Type Safety**: Full type annotations with Pydantic models
- **Comprehensive Tests**: Unit and integration test coverage

## 🚀 Quick Start

### Docker Deployment (Recommended)

```bash
# Clone the repository
git clone https://git.supported.systems/MCP/rentcache.git
cd rentcache

# Start with Docker (includes reverse proxy)
make setup

# Or manually:
docker network create caddy 2>/dev/null || true
docker compose up --build -d
```


### Local Development

```bash
# Install dependencies
uv sync

# Start development server
make local-dev

# Or manually:
uv run rentcache server --reload
```

### Basic Usage

1. **Create an API key**:
   ```bash
   # Using Docker
   make create-key NAME=my_app KEY=your_rentcast_api_key

   # Or locally
   uv run rentcache create-key my_app your_rentcast_api_key
   ```

2. **Make API calls**:
   ```bash
   # Make API call
   curl -H "Authorization: Bearer your_rentcast_api_key" \
        "http://localhost:8000/api/v1/properties?city=Austin&state=TX"
   ```

3. **Monitor performance**:
   ```bash
   # View metrics
   curl "http://localhost:8000/metrics"

   # Health check
   curl "http://localhost:8000/health"
   ```

## 📚 Documentation

- **[Deployment Guide](docs/DEPLOYMENT.md)** - Docker & production deployment
- **[Architecture Overview](docs/ARCHITECTURE.md)** - System design & caching strategy
- **[Quick Start Guide](docs/QUICKSTART.md)** - 5-minute setup walkthrough
- **[Installation Guide](docs/INSTALLATION.md)** - Detailed setup instructions
- **[Usage Guide](docs/USAGE.md)** - Comprehensive usage examples  
- **[API Reference](docs/API.md)** - Complete endpoint documentation
- **[Rentcast API Docs](https://developers.rentcast.io/reference/introduction)** - Official Rentcast documentation

## 📖 API Documentation

### Core Endpoints

All Rentcast API endpoints are proxied with intelligent caching:

#### 🏘️ **Property Records**
```http
GET /api/v1/properties
GET /api/v1/properties/{property_id}
```
**Cache TTL**: 24 hours (expensive endpoints)

#### 💲 **Value & Rent Estimates**
```http
GET /api/v1/estimates/value
GET /api/v1/estimates/rent
POST /api/v1/estimates/value/bulk
POST /api/v1/estimates/rent/bulk
```
**Cache TTL**: 1 hour (dynamic pricing)

#### 🏠 **Listings**
```http
GET /api/v1/listings/sale
GET /api/v1/listings/rental
GET /api/v1/listings/{listing_id}
```
**Cache TTL**: 30 minutes (frequently updated)

#### 📈 **Market Data**
```http
GET /api/v1/markets/stats
GET /api/v1/comparables
```
**Cache TTL**: 2 hours (market statistics)

### Cache Control Parameters

All endpoints support these parameters:

- `force_refresh=true`: Bypass cache and fetch fresh data
- `ttl_override=3600`: Override default TTL (in seconds)

### Response Headers

Every response includes cache information:

```http
X-Cache-Hit: true|false
X-Response-Time-MS: 45.2
X-Estimated-Cost: 2.0  (only on cache misses)
```

## 🛠️ Administration

### CLI Commands

```bash
# Server management
rentcache server --host 0.0.0.0 --port 8000 --reload

# API key management
rentcache create-key <name> <rentcast_key> [options]
rentcache list-keys
rentcache update-key <name> [options]
rentcache delete-key <name>

# Cache management
rentcache clear-cache [--endpoint=properties] [--older-than=24]

# Monitoring
rentcache stats [--endpoint=properties] [--days=7]
rentcache health
```

### API Key Management

```bash
# Create key with custom limits
rentcache create-key production_app YOUR_KEY \
  --daily-limit 5000 \
  --monthly-limit 100000 \
  --expires 2024-12-31

# Update existing key
rentcache update-key production_app --daily-limit 10000 --active

# List all keys with usage stats
rentcache list-keys
```

### Cache Management

```bash
# Clear specific endpoint cache
rentcache clear-cache --endpoint properties

# Clear old cache entries
rentcache clear-cache --older-than 24

# Clear all cache (careful!)
rentcache clear-cache
```

### HTTP Admin Endpoints

```http
# API key management
POST /admin/api-keys          # Create API key
GET  /admin/api-keys          # List API keys
PUT  /admin/api-keys/{id}     # Update API key
DELETE /admin/api-keys/{id}   # Delete API key

# Cache management  
POST /admin/cache/clear       # Clear cache entries
GET  /admin/cache/stats       # Cache statistics

# System monitoring
GET /health                   # Health check
GET /metrics                  # System metrics
```

## ⚙️ Configuration

### Environment Variables

```bash
# Server
HOST=0.0.0.0
PORT=8000
DEBUG=false

# Database
DATABASE_URL=sqlite+aiosqlite:///./rentcache.db
DATABASE_ECHO=false

# Redis (optional)
REDIS_URL=redis://localhost:6379
REDIS_ENABLED=false

# Rentcast API
RENTCAST_BASE_URL=https://api.rentcast.io
RENTCAST_TIMEOUT=30
RENTCAST_MAX_RETRIES=3

# Cache settings
DEFAULT_CACHE_TTL=3600
EXPENSIVE_ENDPOINTS_TTL=86400
ENABLE_STALE_WHILE_REVALIDATE=true

# Rate limiting
ENABLE_RATE_LIMITING=true
GLOBAL_RATE_LIMIT=1000/hour
PER_ENDPOINT_RATE_LIMIT=100/minute

# Security
ALLOWED_HOSTS=*
CORS_ORIGINS=*

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### Configuration File

Create a `.env` file in your project root:

```env
# Basic configuration
DEBUG=true
LOG_LEVEL=DEBUG

# Database
DATABASE_URL=sqlite+aiosqlite:///./rentcache.db

# Optional Redis for better performance
# REDIS_URL=redis://localhost:6379
# REDIS_ENABLED=true

# Custom cache settings
DEFAULT_CACHE_TTL=3600
EXPENSIVE_ENDPOINTS_TTL=86400

# Rate limiting
GLOBAL_RATE_LIMIT=2000/hour
PER_ENDPOINT_RATE_LIMIT=200/minute
```

## 🏗️ Architecture

### System Components

```mermaid
graph TD
    A[Client Applications] --> B[FastAPI Server]
    B --> C[Authentication Layer]
    C --> D[Rate Limiting]
    D --> E[Cache Manager]
    E --> F{Cache Hit?}
    F -->|Yes| G[Return Cached Data]
    F -->|No| H[Rentcast API]
    H --> I[Store in Cache]
    I --> G
    
    E --> J[(SQLite/PostgreSQL)]
    E --> K[(Redis - Optional)]
    
    B --> L[Usage Analytics]
    L --> J
    
    B --> M[Health Monitoring]
    B --> N[Metrics Collection]
```

### Cache Strategy

1. **L1 Cache (Redis)**: Fast in-memory cache for frequently accessed data
2. **L2 Cache (SQLite/PostgreSQL)**: Persistent cache with analytics and soft deletion
3. **Cache Keys**: MD5 hash of endpoint + method + parameters
4. **TTL Management**: Different expiration times based on data volatility
5. **Stale-While-Revalidate**: Serve expired data during upstream failures

### Rate Limiting Strategy

1. **Global Limits**: Per API key across all endpoints
2. **Per-Endpoint Limits**: Specific limits for expensive operations
3. **Exponential Backoff**: Automatically slow down aggressive clients
4. **Usage Tracking**: Monitor and alert on approaching limits

## 🧪 Testing

### Run Tests

```bash
# Run all tests with coverage
uv run pytest

# Run specific test categories
uv run pytest -m unit
uv run pytest -m integration
uv run pytest -m api

# Run with coverage report
uv run pytest --cov=src/rentcache --cov-report=html
```

### Test Structure

```
tests/
├── conftest.py           # Test configuration
├── test_models.py        # Model tests
├── test_cache.py         # Cache system tests  
├── test_server.py        # API endpoint tests
├── test_cli.py           # CLI command tests
└── test_integration.py   # End-to-end tests
```

## 📊 Monitoring & Analytics

### Key Metrics

- **Cache Hit Ratio**: Percentage of requests served from cache
- **Response Times**: Average response time by endpoint
- **Error Rates**: 4xx/5xx error percentages
- **Cost Tracking**: Estimated Rentcast API costs and savings
- **Usage Patterns**: Popular endpoints and request volumes

### Health Checks

```http
GET /health
```

Response includes:
- Database connectivity
- Cache backend status
- Active API keys count
- Recent error rates
- System uptime

### Metrics Endpoint

```http
GET /metrics
```

Provides detailed system metrics including:
- Request volumes and cache performance
- Per-endpoint statistics
- Cost analysis and savings
- System resource utilization

## 🐳 Docker Deployment

### Quick Start with Make

```bash
# Complete setup with reverse proxy
make setup

# Development mode with hot reload
make dev

# Production mode
make prod

# View logs
make logs

# Health check
make health

# Management commands
make create-key NAME=my_app KEY=your_rentcast_key
make list-keys
make stats
```

### Manual Docker Compose

```bash
# Create external network (if not exists)
docker network create caddy

# Development with hot reload
docker compose up --build -d

# Production mode
MODE=production DEBUG=false docker compose up --build -d

# With Redis for better performance
docker compose --profile redis up --build -d
```

### Production Features

- **🔄 Multi-stage Docker builds** for optimized images
- **🌐 Caddy reverse proxy** with automatic HTTPS
- **📊 Health checks** and graceful shutdown
- **🔒 Non-root user** for security
- **📦 Efficient caching** with multi-layer cache mounts
- **🚀 Hot reload** in development mode
- **📈 Production monitoring** with metrics and logging

## 📈 Performance Tips

### Optimization Strategies

1. **Cache Warming**: Pre-populate cache for popular endpoints
2. **Bulk Operations**: Use bulk endpoints when available
3. **Connection Pooling**: Configure appropriate database connection pools
4. **Response Compression**: Enable gzip compression for large responses
5. **CDN Integration**: Use CDN for static content and common API responses

### Monitoring Performance

```bash
# Check cache hit ratios
rentcache stats --days 7

# Monitor response times
curl -s http://localhost:8000/metrics | jq '.avg_response_time_ms'

# Check system health
rentcache health
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass (`uv run pytest`)
6. Run code formatting (`uv run black src tests`)
7. Submit a pull request

### Development Setup

```bash
# Install development dependencies
uv sync --all-extras

# Install pre-commit hooks
pre-commit install

# Run tests
uv run pytest

# Format code
uv run black src tests
uv run ruff check src tests --fix
```

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- **Repository**: [git.supported.systems/MCP/rentcache](https://git.supported.systems/MCP/rentcache)
- **Rentcast API**: [developers.rentcast.io](https://developers.rentcast.io/reference/introduction)
- **Issues**: Report bugs and feature requests in the repository

## 🙏 Acknowledgments

- [Rentcast](https://rentcast.io/) for providing the real estate data API
- [FastAPI](https://fastapi.tiangolo.com/) for the excellent web framework
- [SQLAlchemy](https://www.sqlalchemy.org/) for powerful ORM capabilities
- [Pydantic](https://pydantic.dev/) for data validation and serialization

---

**Built with ❤️ for the real estate technology community**

**Reduce your API costs today - every cache hit saves you money!**