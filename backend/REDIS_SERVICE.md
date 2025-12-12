# Redis Service Documentation

**Complete guide to NodeRush Redis integration** - Caching, sessions, queues, rate limiting, and token tracking.

**Last Updated:** December 2025

---

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Setup](#setup)
4. [Usage Examples](#usage-examples)
5. [API Reference](#api-reference)
6. [Key Patterns](#key-patterns)
7. [Performance](#performance)
8. [Cost Monitoring](#cost-monitoring)
9. [Best Practices](#best-practices)

---

## Overview

NodeRush uses **Upstash Redis** for:
- **Session management**: User authentication sessions
- **Caching**: Agent data, AI responses
- **Queue**: Background job processing
- **Rate limiting**: API request throttling
- **Token tracking**: AI usage monitoring
- **Quota management**: User limits enforcement

### Why Upstash Redis?

- ✅ **Free tier**: 10,000 commands/day
- ✅ **Serverless**: No server management
- ✅ **Global**: Low-latency edge deployment
- ✅ **Persistent**: AOF + RDB backups
- ✅ **Encrypted**: Data at rest and in transit

---

## Features

### 1. Session Management

Store user sessions with automatic expiry:

```python
from app.services.redis_service import redis_service

# Store session (7 days default)
await redis_service.set_session(
    session_id="user_123_session",
    user_data={
        "user_id": "user_123",
        "email": "user@example.com",
        "tier": "free"
    },
    expire_seconds=604800  # 7 days
)

# Get session
session = await redis_service.get_session("user_123_session")

# Delete session (logout)
await redis_service.delete_session("user_123_session")
```

**Key pattern**: `session:{session_id}`
**TTL**: 7 days (604800 seconds)

### 2. Caching

Cache expensive computations and database queries:

```python
# Cache agent data (1 hour default)
await redis_service.cache_set(
    key="agent:123",
    value={"id": "123", "name": "Chatbot", "status": "ready"},
    expire_seconds=3600
)

# Get cached data
agent = await redis_service.cache_get("agent:123")
if agent:
    # Cache hit - return immediately
    return agent
else:
    # Cache miss - query database
    agent = await db.query(Agent).filter_by(id="123").first()
    await redis_service.cache_set("agent:123", agent, expire_seconds=3600)
    return agent

# Delete cache
await redis_service.cache_delete("agent:123")
```

**Key pattern**: `cache:{key}`
**TTL**: 1 hour (3600 seconds)

### 3. Queue (Background Jobs)

Process agent generation in background workers:

```python
# Producer: Enqueue job
await redis_service.enqueue_agent_execution(
    agent_id="agent_456",
    execution_data={
        "prompt": "Create a financial analyst",
        "user_id": "user_123"
    }
)

# Worker: Dequeue job (blocking)
while True:
    job = await redis_service.dequeue_agent_execution(timeout=10)
    if job:
        agent_id = job["agent_id"]
        data = job["data"]
        # Process job
        await process_agent_generation(agent_id, data)

# Check queue length
length = await redis_service.get_queue_length("agent_execution")
```

**Key pattern**: `queue:agent_execution`
**Operations**: LPUSH (enqueue), BRPOP (dequeue blocking)

### 4. Rate Limiting

Implement token bucket rate limiting:

```python
# Check rate limit (5 requests per minute)
result = await redis_service.check_rate_limit(
    user_id="user_123",
    resource="api_calls",
    limit=5,
    window_seconds=60
)

if result["allowed"]:
    # Request allowed - proceed
    print(f"Remaining: {result['remaining']}")
else:
    # Rate limit exceeded
    raise HTTPException(
        status_code=429,
        detail=f"Rate limit exceeded. Reset at {result['reset_at']}"
    )

# Reset rate limit (admin only)
await redis_service.reset_rate_limit("user_123", "api_calls")
```

**Key pattern**: `ratelimit:{resource}:{user_id}`
**Response**:
```python
{
    "allowed": True/False,
    "current": 3,
    "limit": 5,
    "remaining": 2,
    "reset_at": 1701234567  # Unix timestamp
}
```

### 5. Token Usage Tracking

Track AI token consumption for billing:

```python
# Track token usage
await redis_service.track_token_usage(
    user_id="user_123",
    agent_id="agent_456",
    tokens=1250,
    model="gpt-4"
)

# Get today's usage
usage = await redis_service.get_token_usage("user_123", period="today")
# Returns: {"total": 5000, "gpt-4": 3000, "gpt-3.5": 2000}

# Get monthly usage
monthly = await redis_service.get_token_usage("user_123", period="month")

# Get per-agent usage
agent_usage = await redis_service.get_agent_token_usage("agent_456")
```

**Key patterns**:
- `tokens:user:{user_id}:day:{YYYY-MM-DD}` - Daily usage
- `tokens:user:{user_id}:month:{YYYY-MM}` - Monthly usage
- `tokens:agent:{agent_id}:total` - Per-agent total

**Data structure**: Hash with fields `total`, `gpt-4`, `gpt-3.5`, etc.

### 6. Quota Management

Enforce user quotas (free tier limits):

```python
# Check quota (free tier: max 10 agents)
quota = await redis_service.check_quota(
    user_id="user_123",
    quota_type="agents",
    limit=10
)

if not quota["allowed"]:
    raise HTTPException(
        status_code=403,
        detail=f"Quota exceeded. {quota['current']}/{quota['limit']} agents created."
    )

# Increment quota (after creating agent)
await redis_service.increment_quota("user_123", "agents", amount=1)

# Reset quota (admin/billing)
await redis_service.reset_quota("user_123", "agents")
```

**Key pattern**: `quota:{quota_type}:{user_id}`
**TTL**: 31 days

### 7. System Flags (Cost Control)

Set system-wide flags for cost management:

```python
# Pause agent creation if costs exceed budget
await redis_service.set_system_flag(
    flag_name="pause_agent_creation",
    value="true",
    expire_seconds=3600
)

# Check flag before expensive operation
paused = await redis_service.get_system_flag("pause_agent_creation")
if paused == "true":
    raise HTTPException(503, "Service temporarily paused")

# Delete flag (resume service)
await redis_service.delete_system_flag("pause_agent_creation")
```

**Key pattern**: `system:{flag_name}`
**Common flags**:
- `system:pause_agent_creation`
- `system:pause_file_upload`
- `system:aggressive_caching`

### 8. Agent Status Tracking

Track real-time agent generation status:

```python
# Set status
await redis_service.set_agent_status(
    agent_id="agent_789",
    status="generating",
    data={"progress": 45, "step": "Coding"}
)

# Get status (for frontend polling)
status = await redis_service.get_agent_status("agent_789")
# Returns: {"status": "generating", "data": {"progress": 45, "step": "Coding"}}
```

**Key pattern**: `agent:status:{agent_id}`
**TTL**: 1 hour

### 9. CSRF Token Management

Secure form submissions:

```python
import secrets

# Generate and store CSRF token
csrf_token = secrets.token_urlsafe(32)
await redis_service.store_csrf_token(
    token=csrf_token,
    user_id="user_123",
    expire_seconds=3600
)

# Verify token (on form submission)
verified_user_id = await redis_service.verify_csrf_token(csrf_token)
if verified_user_id != current_user.id:
    raise HTTPException(403, "Invalid CSRF token")
```

**Key pattern**: `csrf:{token}`
**TTL**: 1 hour
**Note**: Tokens are deleted after verification (one-time use)

### 10. WebSocket Connection Tracking

Track active WebSocket connections:

```python
# Add connection
await redis_service.add_websocket_connection(
    agent_id="agent_123",
    connection_id="conn_abc"
)

# Get all connections for agent
connections = await redis_service.get_websocket_connections("agent_123")

# Remove connection
await redis_service.remove_websocket_connection("agent_123", "conn_abc")
```

**Key pattern**: `ws:agent:{agent_id}`
**Data structure**: Set of connection IDs

### 11. AI Response Caching

Cache AI generation responses to save costs:

```python
import hashlib

# Generate hash of prompt
prompt = "Create a customer support chatbot"
prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()

# Check cache first
cached = await redis_service.get_cached_ai_response(prompt_hash)
if cached:
    return cached  # Return cached response

# Generate new response
response = await generate_ai_response(prompt)

# Cache for 24 hours
await redis_service.cache_ai_response(
    prompt_hash=prompt_hash,
    response=response,
    expire_seconds=86400
)
```

**Key pattern**: `ai:response:{prompt_hash}`
**TTL**: 24 hours

---

## Setup

### 1. Create Upstash Redis Database

1. Go to https://upstash.com
2. Create account (free tier)
3. Create new Redis database
4. Copy the Redis URL

### 2. Configure Environment

Add to `backend/.env`:

```env
REDIS_URL=rediss://default:[password]@[region].upstash.io:6379
```

### 3. Initialize in Application

The Redis service is automatically initialized in `backend/main.py`:

```python
from app.services.redis_service import redis_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await redis_service.connect()

    yield

    # Shutdown
    await redis_service.disconnect()

app = FastAPI(lifespan=lifespan)
```

---

## Key Patterns

All Redis keys follow namespaced patterns:

| Pattern | Example | Purpose |
|---------|---------|---------|
| `session:{id}` | `session:user_123_abc` | User sessions |
| `cache:{key}` | `cache:agent:456` | General caching |
| `queue:{name}` | `queue:agent_execution` | Background jobs |
| `ratelimit:{resource}:{user}` | `ratelimit:api_calls:user_123` | Rate limiting |
| `tokens:user:{user}:day:{date}` | `tokens:user:123:day:2025-12-10` | Daily token usage |
| `tokens:user:{user}:month:{month}` | `tokens:user:123:month:2025-12` | Monthly tokens |
| `tokens:agent:{agent}:total` | `tokens:agent:456:total` | Per-agent tokens |
| `quota:{type}:{user}` | `quota:agents:user_123` | User quotas |
| `agent:status:{agent}` | `agent:status:789` | Agent status |
| `ws:agent:{agent}` | `ws:agent:123` | WebSocket connections |
| `ai:response:{hash}` | `ai:response:abc123...` | AI response cache |
| `csrf:{token}` | `csrf:token_xyz` | CSRF tokens |
| `system:{flag}` | `system:pause_agent_creation` | System flags |
| `redis:commands:count:{date}` | `redis:commands:count:2025-12-10` | Command tracking |

---

## Performance

### Connection Pooling

The Redis service uses connection pooling for optimal performance:

```python
redis.from_url(
    settings.REDIS_URL,
    max_connections=10,  # Pool size
    decode_responses=True,
    encoding="utf-8"
)
```

### Caching Strategy

**Cache-Aside Pattern**:
1. Check cache first
2. If miss, query database
3. Store in cache with TTL
4. Return result

**TTL Guidelines**:
- Sessions: 7 days (604800s)
- Agent data: 1 hour (3600s)
- AI responses: 24 hours (86400s)
- Status updates: 1 hour (3600s)

### Queue Performance

- **LPUSH**: O(1) - Add to queue
- **BRPOP**: O(1) - Block until item available
- **LLEN**: O(1) - Get queue length

For high throughput, use multiple worker processes.

---

## Cost Monitoring

Track Redis usage to stay within free tier (10,000 commands/day):

```python
# Track each command
await redis_service.track_redis_command()

# Get daily count
count = await redis_service.get_redis_command_count()

# Alert if approaching limit
if count > 9000:
    await redis_service.set_system_flag(
        "aggressive_caching",
        "true",
        expire_seconds=3600
    )
```

**Cost Control Strategies**:
1. **Aggressive caching**: Increase TTLs
2. **Pause non-critical features**: Set system flags
3. **Batch operations**: Reduce command count
4. **Use pipelining**: Group multiple commands

---

## Best Practices

### 1. Always Set Expiry

```python
# ✅ GOOD - Has expiry
await redis_client.setex("key", 3600, "value")

# ❌ BAD - No expiry (memory leak)
await redis_client.set("key", "value")
```

### 2. Handle Redis Failures Gracefully

```python
# Fail open - allow request if Redis fails
try:
    result = await redis_service.check_rate_limit(...)
    if not result["allowed"]:
        raise HTTPException(429, "Rate limited")
except Exception:
    # Redis failed - allow request
    logger.error("Redis failed, allowing request")
```

### 3. Use Atomic Operations

```python
# ✅ GOOD - Atomic increment
await redis_client.incr("counter")

# ❌ BAD - Race condition
count = await redis_client.get("counter")
await redis_client.set("counter", int(count) + 1)
```

### 4. Namespace Your Keys

Always use prefixes to avoid key collisions:

```python
# ✅ GOOD
f"cache:agent:{agent_id}"

# ❌ BAD
f"agent_{agent_id}"
```

### 5. Monitor Usage

```python
# Track commands for cost monitoring
await redis_service.track_redis_command()

# Check daily usage
if await redis_service.get_redis_command_count() > 9000:
    # Approaching limit - take action
    pass
```

---

## Testing

Run the test suite:

```bash
cd backend
python test_redis_service.py
```

This tests all features:
- ✅ Connection
- ✅ Sessions
- ✅ Caching
- ✅ Queue (BRPOP)
- ✅ Rate limiting
- ✅ Token tracking
- ✅ Quotas
- ✅ System flags
- ✅ CSRF tokens
- ✅ Agent status
- ✅ Command tracking

---

## Troubleshooting

### Connection Errors

**Problem**: `Failed to connect to Redis`

**Solutions**:
1. Verify `REDIS_URL` in `.env`
2. Check Upstash dashboard - database active?
3. Test connection: `redis-cli -u $REDIS_URL ping`
4. Ensure firewall allows outbound connections

### High Command Count

**Problem**: Approaching 10,000 commands/day limit

**Solutions**:
1. Increase cache TTLs
2. Use pipeline for batch operations
3. Set `system:aggressive_caching` flag
4. Upgrade Upstash plan

### Memory Issues

**Problem**: Redis memory full

**Solutions**:
1. Verify all keys have expiry (`TTL key`)
2. Delete stale data
3. Reduce TTLs for less critical data
4. Use `SCAN` to find keys without expiry

---

## API Reference

See `backend/app/services/redis_service.py` for complete API.

**Main Methods**:
- `connect()` - Initialize connection
- `disconnect()` - Close connection
- `set_session()` - Store session
- `get_session()` - Retrieve session
- `cache_set()` - Cache data
- `cache_get()` - Get cached data
- `enqueue_agent_execution()` - Add to queue
- `dequeue_agent_execution()` - Get from queue (blocking)
- `check_rate_limit()` - Rate limit check
- `track_token_usage()` - Track AI tokens
- `check_quota()` - Check user quota
- `set_system_flag()` - Set system flag
- `store_csrf_token()` - Store CSRF token
- `set_agent_status()` - Update agent status

---

## Additional Resources

- **Upstash Docs**: https://docs.upstash.com/redis
- **Redis Commands**: https://redis.io/commands
- **Architecture**: See `ARCHITECTURE.md`
- **Integration**: See `INTEGRATION.md`

---

**Last Updated**: December 2025
**Version**: 1.0.0
