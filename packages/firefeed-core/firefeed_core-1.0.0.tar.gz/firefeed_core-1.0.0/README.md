# FireFeed Core

Core utilities and models for FireFeed microservices architecture.

FireFeed Core is a shared library that provides common components for all FireFeed microservices, ensuring consistency, security, and reliability across the distributed system.

## 🚀 Features

- **API Client**: Robust HTTP client with authentication, retry policies, circuit breaker, and rate limiting
- **JWT Authentication**: Service-to-service authentication with token management
- **Exception Handling**: Comprehensive exception hierarchy for consistent error handling
- **Configuration**: Pydantic-based configuration management
- **Interfaces**: Abstract interfaces for service contracts
- **Utilities**: Common utility functions and helpers

## 📦 Installation

```bash
pip install firefeed-core
```

## 🔧 Quick Start

### Basic API Client Usage

```python
import asyncio
from firefeed_core import APIClient

async def main():
    # Initialize API client
    async with APIClient(
        base_url="http://firefeed-api:8000",
        token="your-jwt-token",
        service_id="firefeed-rss-parser"
    ) as client:
        
        # Make authenticated requests
        feeds = await client.get("/api/v1/internal/rss/feeds")
        print(f"Found {len(feeds)} feeds")
        
        # Create new RSS item
        new_item = await client.post("/api/v1/internal/rss/items", {
            "title": "Test Article",
            "content": "This is a test article",
            "feed_id": 123
        })

asyncio.run(main())
```

### JWT Token Management

```python
from firefeed_core import ServiceTokenManager

# Generate token for service
token_manager = ServiceTokenManager(
    secret_key="your-secret-key",
    issuer="firefeed-api"
)

token = token_manager.generate_service_token(
    service_id="firefeed-rss-parser",
    audience="firefeed-api",
    scopes=["rss:read", "rss:write"]
)

# Verify token
payload = token_manager.verify_token(token)
print(f"Token for service: {payload.sub}")
```

### Exception Handling

```python
from firefeed_core import APIException, NotFoundException

try:
    result = await client.get("/api/v1/internal/rss/feeds/999")
except NotFoundException as e:
    print(f"Feed not found: {e.message}")
except APIException as e:
    print(f"API error: {e.message}")
```

## 🔐 Authentication

FireFeed Core uses JWT tokens for service-to-service authentication. Each service needs:

1. **Service Token**: JWT token with appropriate scopes
2. **Service ID**: Unique identifier for the service
3. **Secret Key**: Shared secret for token verification

### Environment Configuration

Each service should have its own `.env` file:

```bash
# firefeed-rss-parser/.env
FIREFEED_API_URL=http://firefeed-api:8000
FIREFEED_API_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
FIREFEED_RSS_PARSER_SERVICE_ID=rss-parser

# firefeed-telegram-bot/.env
FIREFEED_API_URL=http://firefeed-api:8000
FIREFEED_API_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
FIREFEED_TELEGRAM_BOT_SERVICE_ID=telegram-bot
```

### Token Scopes

Services can be granted specific scopes for different operations:

- `rss:read` - Read RSS data
- `rss:write` - Create/modify RSS data
- `users:read` - Read user data
- `users:write` - Modify user data
- `categories:read` - Read categories
- `categories:write` - Modify categories

## 🛠️ Advanced Features

### Circuit Breaker

Automatically prevents requests to failing services:

```python
from firefeed_core import APIClient

client = APIClient(
    base_url="http://service:8000",
    token="token",
    service_id="my-service",
    circuit_breaker_failure_threshold=5,
    circuit_breaker_timeout=60
)
```

### Retry Policies

Configurable retry with exponential backoff:

```python
client = APIClient(
    base_url="http://service:8000",
    token="token",
    service_id="my-service",
    max_retries=3
)
```

### Rate Limiting

Prevents API abuse:

```python
client = APIClient(
    base_url="http://service:8000",
    token="token",
    service_id="my-service",
    rate_limit_requests=100,
    rate_limit_window=60
)
```

## 📊 Monitoring

Each API client provides comprehensive statistics:

```python
stats = client.get_stats()
print(f"Circuit breaker state: {stats['circuit_breaker']['state']}")
print(f"Rate limit usage: {stats['rate_limiter']['current_requests']}")
```

## 🏗️ Architecture

FireFeed Core follows these principles:

1. **API-First**: All services communicate via HTTP APIs only
2. **Zero Direct Database Access**: Services never access databases directly
3. **Token-Based Security**: All inter-service communication is authenticated
4. **Fault Tolerance**: Circuit breakers, retries, and rate limiting
5. **Consistent Error Handling**: Standardized exception hierarchy

### Service Communication Flow

```
┌─────────────────────┐    JWT Token    ┌─────────────────────┐
│  firefeed-rss-parser│ ──────────────→ │   firefeed-api      │
│  (Dumb Service)     │                 │  (Smart Service)    │
│                     │ ←────────────── │                     │
│  - RSS Processing   │    HTTP API     │  - Database Access  │
│  - No DB Access     │                 │  - Business Logic   │
└─────────────────────┘                 └─────────────────────┘
```

## 🧪 Testing

```bash
# Install test dependencies
pip install -e ".[test]"

# Run tests
pytest

# Run with coverage
pytest --cov=firefeed_core
```

## 📝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

## 🔗 Related Projects

- [FireFeed API](https://github.com/firefeed-net/firefeed-api) - Main API service
- [FireFeed RSS Parser](https://github.com/firefeed-net/firefeed-rss-parser) - RSS processing service
- [FireFeed Telegram Bot](https://github.com/firefeed-net/firefeed-telegram-bot) - Telegram bot service

---

**Note**: This is a core library intended for use within the FireFeed microservices ecosystem.