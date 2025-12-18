# Rate Limiter Documentation

**Token Bucket Rate Limiter for NodeRush**

A sophisticated rate limiting implementation using the Token Bucket Algorithm with Redis backend.

**Last Updated:** December 2025

---

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Algorithm](#algorithm)
4. [Usage](#usage)
5. [Configuration](#configuration)
6. [API Reference](#api-reference)
7. [Best Practices](#best-practices)
8. [Testing](#testing)

---

## Overview

NodeRush uses a **Token Bucket Rate Limiter** to:
- Protect against API abuse and DDoS attacks
- Enforce fair usage across all users
- Support tiered rate limits (free, pro, enterprise)
- Provide smooth traffic shaping with burst allowance

### Why Token Bucket?

| Algorithm | Pros | Cons |
|-----------|------|------|
| **Token Bucket** ✅ | Allows bursts, smooth limiting | Slightly more complex |
| Fixed Window | Simple | Burst at window boundary |
| Sliding Window | Accurate | More Redis operations |

The token bucket algorithm provides the best balance of flexibility and protection.

---

## Features

### 1. Token Bucket Algorithm
- Configurable bucket size (max tokens)
- Continuous token refill over time
- Allows bursts up to bucket size
- Smooth rate limiting without hard edges

### 2. Multiple Limit Types
- **Token Bucket**: Smooth rate limiting with bursts
- **Sliding Window**: Strict limits for sensitive operations
- **Concurrent Limit**: Connection/operation limits

### 3. Tier-Based Multipliers
| Tier | Multiplier | Example (base: 10) |
|------|-----------|-------------------|
| Free | 1.0x | 10 requests |
| Pro | 5.0x | 50 requests |
| Enterprise | 20.0x | 200 requests |

### 4. Resource-Specific Presets
Pre-configured limits for common operations:
- `auth:signup` - 5/hour
- `auth:login` - 10/minute
- `agent:create` - 5/hour
- `agent:execute` - 10/hour
- `api:general` - 60/minute

### 5. Rate Limit Headers
All responses include standard headers:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1702486800
X-RateLimit-Resource: api:general
```

### 6. Fail-Open Design
If Redis fails, requests are **allowed** (not blocked) to prevent service outage.

---

## Algorithm

### Token Bucket Explained

```
┌─────────────────────────────────────────┐
│              TOKEN BUCKET               │
│                                         │
│    ┌─────────────────────────────┐     │
│    │   🪣 Bucket (max: 10)       │     │
│    │   ●●●●●●●○○○                │     │ ← Current: 7 tokens
│    └─────────────────────────────┘     │
│              ↓                          │
│    💧 Refill: 1 token/second            │
│              ↓                          │
│    Request arrives → Take 1 token       │
│              ↓                          │
│    ✅ Allowed (7→6 tokens)              │
└─────────────────────────────────────────┘
```

### How It Works

1. **Initialization**: Bucket starts with `bucket_size` tokens
2. **Refill**: Tokens are added at `refill_rate` per second
3. **Request**: Each request consumes `cost` tokens (default: 1)
4. **Check**:
   - If tokens >= cost → **ALLOW** (consume tokens)
   - If tokens < cost → **DENY** (wait for refill)
5. **Cap**: Bucket never exceeds `bucket_size`

### Example Timeline

```
Time 0s:   [●●●●●] 5 tokens (full bucket)
Request 1: [●●●●○] 4 tokens (consumed 1)
Request 2: [●●●○○] 3 tokens (consumed 1)
Time 1s:   [●●●●○] 4 tokens (refilled 1)
Request 3: [●●●○○] 3 tokens (consumed 1)
...
```

---

## Usage

### Basic Usage

```python
from app.utils.rate_limiter import get_rate_limiter

rate_limiter = get_rate_limiter()

# Check rate limit
result = await rate_limiter.check_limit(
    identifier="user_123",
    resource="api:general"
)

if result.allowed:
    # Process request
    pass
else:
    raise HTTPException(
        status_code=429,
        detail=f"Rate limit exceeded. Retry in {result.retry_after} seconds."
    )
```

### Using the Decorator

```python
from app.utils.rate_limiter import rate_limit, RateLimitWindow

@app.post("/api/agents")
@rate_limit(resource="agent:create")
async def create_agent(request: Request, user: User):
    # Automatically rate limited
    return await create_new_agent(user)

# With custom limits
@app.get("/api/search")
@rate_limit(resource="search", limit=30, window=RateLimitWindow.MINUTE)
async def search(request: Request):
    return await perform_search()
```

### Sliding Window (Strict Limits)

```python
# For operations where bursts are not allowed
result = await rate_limiter.check_sliding_window(
    identifier="user_123",
    resource="auth:signup",
    limit=5,
    window=RateLimitWindow.HOUR
)
```

### Concurrent Limits

```python
# Check if user can open new WebSocket
result = await rate_limiter.check_concurrent_limit(
    identifier="user_123",
    resource="websocket:connect",
    max_concurrent=3
)

if result.allowed:
    # Track the connection
    await rate_limiter.add_concurrent_connection(
        identifier="user_123",
        resource="websocket:connect",
        connection_id="ws_abc123"
    )

# On disconnect
await rate_limiter.remove_concurrent_connection(
    identifier="user_123",
    resource="websocket:connect",
    connection_id="ws_abc123"
)
```

---

## Configuration

### Rate Limit Presets

```python
RATE_LIMIT_PRESETS = {
    # Authentication
    "auth:signup": {
        "per_hour": 5,
        "bucket_size": 5,
        "refill_rate": 5 / 3600,  # 5 per hour
    },
    "auth:login": {
        "per_minute": 10,
        "bucket_size": 10,
        "refill_rate": 10 / 60,  # 10 per minute
    },

    # Agent operations
    "agent:create": {
        "per_hour": 5,
        "bucket_size": 5,
        "refill_rate": 5 / 3600,
    },
    "agent:execute": {
        "per_hour": 10,
        "bucket_size": 10,
        "refill_rate": 10 / 3600,
    },

    # General API
    "api:general": {
        "per_minute": 60,
        "bucket_size": 60,
        "refill_rate": 1,  # 1 per second
    },
}
```

### Tier Multipliers

```python
TIER_MULTIPLIERS = {
    "free": 1.0,
    "pro": 5.0,
    "enterprise": 20.0,
}
```

### Custom Limits

Override presets by passing parameters:

```python
result = await rate_limiter.check_limit(
    identifier="user_123",
    resource="custom:operation",
    max_tokens=100,          # Custom bucket size
    refill_rate=2.0,         # 2 tokens per second
    bucket_size=100,         # Max tokens
    tier="pro",              # Apply 5x multiplier
    cost=5                   # This request costs 5 tokens
)
```

---

## API Reference

### TokenBucketRateLimiter

#### `check_limit()`
```python
async def check_limit(
    identifier: str,       # User ID or IP
    resource: str,         # Resource name
    max_tokens: int = None,
    refill_rate: float = None,
    bucket_size: int = None,
    tier: str = "free",
    cost: int = 1
) -> RateLimitResult
```

#### `check_sliding_window()`
```python
async def check_sliding_window(
    identifier: str,
    resource: str,
    limit: int,
    window: RateLimitWindow,
    tier: str = "free"
) -> RateLimitResult
```

#### `check_concurrent_limit()`
```python
async def check_concurrent_limit(
    identifier: str,
    resource: str,
    max_concurrent: int,
    tier: str = "free"
) -> RateLimitResult
```

#### `reset_limit()`
```python
async def reset_limit(
    identifier: str,
    resource: str
) -> bool
```

### RateLimitResult

```python
@dataclass
class RateLimitResult:
    allowed: bool          # Was request allowed?
    current_tokens: float  # Current token count
    max_tokens: int        # Maximum tokens (bucket size)
    remaining: int         # Remaining requests
    reset_at: int          # Unix timestamp when limit resets
    retry_after: int       # Seconds until retry allowed
    resource: str          # Resource identifier

    def to_headers() -> Dict[str, str]  # Get HTTP headers
```

### RateLimitWindow

```python
class RateLimitWindow(Enum):
    SECOND = 1
    MINUTE = 60
    HOUR = 3600
    DAY = 86400
```

---

## Best Practices

### 1. Use Appropriate Resource Names

```python
# ✅ GOOD - Hierarchical and descriptive
"auth:login"
"agent:create"
"api:users:list"

# ❌ BAD - Too generic
"request"
"action"
```

### 2. Set Cost for Expensive Operations

```python
# Light operation - 1 token
@rate_limit(resource="api:list", cost=1)
async def list_items(): ...

# Heavy operation - 10 tokens
@rate_limit(resource="api:generate", cost=10)
async def generate_content(): ...
```

### 3. Handle Rate Limit Errors Gracefully

```python
@app.exception_handler(HTTPException)
async def rate_limit_handler(request: Request, exc: HTTPException):
    if exc.status_code == 429:
        return JSONResponse(
            status_code=429,
            content={
                "error": "RATE_LIMIT_EXCEEDED",
                "message": "Please slow down",
                "retry_after": exc.headers.get("Retry-After", 60)
            },
            headers=exc.headers
        )
    raise exc
```

### 4. Use Tier Multipliers for Premium Users

```python
result = await rate_limiter.check_limit(
    identifier=user.id,
    resource="api:generate",
    tier=user.subscription_tier  # "free", "pro", or "enterprise"
)
```

### 5. Monitor Rate Limit Status

```python
# Get current status for debugging
status = await rate_limiter.get_limit_status(
    identifier="user_123",
    resource="agent:create"
)
print(f"Tokens: {status['tokens']}/{status['max_tokens']}")
```

---

## Testing

Run the test suite:

```bash
cd backend
python test_rate_limiter.py
```

### Test Coverage

| Test | Description |
|------|-------------|
| Token Bucket Basic | Verify basic allow/deny behavior |
| Token Refill | Verify tokens refill over time |
| Tier Multipliers | Verify tier-based limits |
| Sliding Window | Verify strict window limits |
| Concurrent Limit | Verify connection limits |
| Presets | Verify preset configurations |
| Reset Limit | Verify limit reset functionality |
| Headers | Verify HTTP header generation |
| Fail Open | Verify graceful Redis failure |
| Get Status | Verify status retrieval |

---

## Troubleshooting

### Common Issues

**Rate limit too strict?**
- Check tier multiplier is applied
- Verify preset values
- Consider increasing bucket_size

**Rate limit not working?**
- Check Redis connection
- Verify rate_limiter is initialized in app.state
- Check middleware is applied

**Inconsistent behavior?**
- Check clock synchronization
- Verify identifier is consistent (user ID vs IP)
- Check for race conditions in concurrent requests

### Debug Commands

```python
# Check Redis connection
await redis_service.redis_client.ping()

# Get rate limit key
key = f"ratelimit:bucket:{resource}:{identifier}"
state = await redis_service.redis_client.hgetall(key)
print(state)

# Reset specific limit
await rate_limiter.reset_limit("user_123", "api:general")
```

---

## Additional Resources

- **Architecture**: See `ARCHITECTURE.md` for system overview
- **Redis Service**: See `REDIS_SERVICE.md` for Redis details
- **Integration**: See `INTEGRATION.md` for frontend integration

---

**Last Updated**: December 2025
**Version**: 1.0.0
