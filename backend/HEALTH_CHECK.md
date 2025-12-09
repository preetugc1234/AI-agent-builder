# NodeRush Health Check Endpoint

## Overview

The NodeRush backend provides a comprehensive health check endpoint to monitor the status of all critical services.

**Endpoint**: `GET /health`

**Purpose**:
- Monitor application health
- Check database connectivity
- Verify Redis connection
- Used by Render for automated health monitoring
- Enable uptime monitoring services

---

## Response Format

### Successful Response (200 OK)

```json
{
  "status": "healthy",
  "service": "noderush-backend",
  "version": "1.0.0",
  "checks": {
    "database": {
      "status": "healthy",
      "message": "Connected to Supabase PostgreSQL"
    },
    "redis": {
      "status": "healthy",
      "message": "Connected to Upstash Redis"
    }
  },
  "timestamp": "2025-12-09T10:30:00.123456Z"
}
```

### Degraded Response (200 OK)

When some services are down but the application is partially functional:

```json
{
  "status": "degraded",
  "service": "noderush-backend",
  "version": "1.0.0",
  "checks": {
    "database": {
      "status": "healthy",
      "message": "Connected to Supabase PostgreSQL"
    },
    "redis": {
      "status": "unhealthy",
      "message": "Redis connection failed: Connection refused"
    }
  },
  "timestamp": "2025-12-09T10:30:00.123456Z"
}
```

### Unhealthy Response (200 OK)

When all critical services are down:

```json
{
  "status": "unhealthy",
  "service": "noderush-backend",
  "version": "1.0.0",
  "checks": {
    "database": {
      "status": "unhealthy",
      "message": "Database engine not initialized"
    },
    "redis": {
      "status": "unhealthy",
      "message": "Redis client not initialized"
    }
  },
  "timestamp": "2025-12-09T10:30:00.123456Z"
}
```

---

## Status Levels

### Overall Status

| Status | Description | Condition |
|--------|-------------|-----------|
| `healthy` | All services operational | All checks return "healthy" |
| `degraded` | Partial functionality | Some checks return "healthy", others "unhealthy" |
| `unhealthy` | Critical failure | All checks return "unhealthy" |

### Service-Level Status

Each service check returns:
- `status`: "healthy" or "unhealthy"
- `message`: Descriptive message about the service state

---

## Services Monitored

### 1. Database (Supabase PostgreSQL)

**Check**: Executes `SELECT 1` query to verify connectivity

**Healthy**: Connection established and query executed successfully

**Unhealthy**:
- Database engine not initialized
- Connection timeout
- Authentication failure
- Query execution error

### 2. Redis (Upstash)

**Check**: Executes `PING` command

**Healthy**: Redis responds with `PONG`

**Unhealthy**:
- Redis client not initialized
- Connection timeout
- Authentication failure
- Command execution error

---

## Usage

### Testing Locally

```bash
# Test health check endpoint
curl http://localhost:8000/health

# Pretty print JSON response
curl -s http://localhost:8000/health | python -m json.tool
```

### Production URL

```bash
# Test production health check
curl https://noderush-backend.onrender.com/health
```

### Using with Uptime Monitoring

The health check endpoint is compatible with popular uptime monitoring services:

**UptimeRobot**:
- Monitor Type: HTTP(s)
- URL: `https://noderush-backend.onrender.com/health`
- Keyword: `"status": "healthy"`
- Interval: 5 minutes

**Better Uptime**:
- Create HTTP Monitor
- URL: `https://noderush-backend.onrender.com/health`
- Success Condition: Status code 200 AND Response contains `"healthy"`

**Healthchecks.io**:
```bash
# Ping on success
curl -fsS --retry 3 https://noderush-backend.onrender.com/health | \
  grep -q '"status": "healthy"' && \
  curl -fsS --retry 3 https://hc-ping.com/YOUR-UUID
```

---

## Render Configuration

The health check is configured in `render.yaml`:

```yaml
services:
  - type: web
    name: noderush-backend
    healthCheckPath: /health
```

**How Render Uses It**:
1. Sends GET request to `/health` every 30 seconds
2. Expects 200 OK status code
3. If 3 consecutive failures, marks service as unhealthy
4. Automatically restarts service if unhealthy
5. Traffic routing based on health status (with multiple instances)

---

## Implementation Details

### Location

`backend/main.py` - Lines 88-166

### Dependencies

```python
from datetime import datetime
from sqlalchemy import text
from app.db.database import engine
from app.services.redis_service import redis_service
```

### Code Flow

1. **Initialize checks dictionary**
2. **Check Database**:
   - Verify engine exists
   - Execute `SELECT 1` query
   - Record status and message
3. **Check Redis**:
   - Verify client exists
   - Execute `PING` command
   - Record status and message
4. **Determine Overall Status**:
   - All healthy → "healthy"
   - Mix → "degraded"
   - All unhealthy → "unhealthy"
5. **Return Response**:
   - Status, version, checks, timestamp

---

## Error Handling

### Database Errors

**Connection Timeout**:
```json
{
  "status": "unhealthy",
  "message": "Database connection failed: connection timeout"
}
```

**Authentication Failure**:
```json
{
  "status": "unhealthy",
  "message": "Database connection failed: authentication failed"
}
```

### Redis Errors

**Connection Refused**:
```json
{
  "status": "unhealthy",
  "message": "Redis connection failed: Connection refused"
}
```

**Command Timeout**:
```json
{
  "status": "unhealthy",
  "message": "Redis connection failed: command timeout"
}
```

---

## Performance Considerations

### Response Time

- **Target**: < 100ms
- **Typical**: 10-50ms
- **Degraded**: 100-500ms
- **Timeout**: 5000ms (Render default)

### Optimization

1. **Connection Pooling**: Uses existing database and Redis connections
2. **Simple Queries**: `SELECT 1` and `PING` are minimal operations
3. **No Business Logic**: Pure connectivity checks
4. **Async Execution**: Uses FastAPI's async capabilities

### Load Impact

- **Render Health Checks**: 1 request every 30 seconds
- **External Monitoring**: Typically 1 request per 5 minutes
- **Total**: ~2,000 requests per day (negligible impact)

---

## Troubleshooting

### "Database engine not initialized"

**Cause**: Database initialization failed during startup

**Solution**:
1. Check `DATABASE_URL` environment variable
2. Verify Supabase credentials
3. Check Supabase dashboard for connection limits
4. Review backend logs for initialization errors

```bash
# Check logs
render logs -s noderush-backend
```

### "Redis client not initialized"

**Cause**: Redis connection failed during startup

**Solution**:
1. Check `REDIS_URL` environment variable
2. Verify Upstash credentials
3. Check Upstash dashboard for connection limits
4. Review backend logs for Redis errors

### Health check returns 500 error

**Cause**: Unexpected exception in health check code

**Solution**:
1. Review backend logs for stack traces
2. Check if services are accessible from backend
3. Verify network connectivity

### Health check times out

**Cause**: Slow service response or connection issues

**Solution**:
1. Check Supabase performance metrics
2. Check Upstash response time
3. Consider increasing timeout (Render default: 5s)
4. Review network latency

---

## Best Practices

### ✅ Do

- Use health check for automated monitoring
- Set up alerts for "degraded" or "unhealthy" status
- Monitor response times
- Include health check in CI/CD pipelines
- Test health check after deployments

### ❌ Don't

- Don't use health check for business logic
- Don't add heavy computations to health check
- Don't rely solely on health check for production monitoring
- Don't expose sensitive information in error messages

---

## Integration Examples

### Python Monitoring Script

```python
import requests
import time

def monitor_health():
    url = "https://noderush-backend.onrender.com/health"

    while True:
        try:
            response = requests.get(url, timeout=10)
            data = response.json()

            if data["status"] != "healthy":
                print(f"⚠️ Service {data['status']}: {data}")
                # Send alert (email, Slack, etc.)
            else:
                print(f"✅ Service healthy")

        except Exception as e:
            print(f"❌ Health check failed: {e}")

        time.sleep(300)  # Check every 5 minutes

if __name__ == "__main__":
    monitor_health()
```

### Shell Script

```bash
#!/bin/bash
# health_check_monitor.sh

URL="https://noderush-backend.onrender.com/health"

while true; do
  response=$(curl -s -w "\n%{http_code}" "$URL")
  http_code=$(echo "$response" | tail -n 1)
  body=$(echo "$response" | head -n -1)

  if [ "$http_code" -eq 200 ]; then
    status=$(echo "$body" | jq -r '.status')

    if [ "$status" == "healthy" ]; then
      echo "✅ $(date): Service healthy"
    else
      echo "⚠️ $(date): Service $status"
      # Send alert
    fi
  else
    echo "❌ $(date): HTTP $http_code"
  fi

  sleep 300  # 5 minutes
done
```

### Docker Compose Health Check

```yaml
version: '3.8'

services:
  backend:
    image: noderush-backend
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

---

## Future Enhancements

### Planned Additions

1. **Cloudflare R2 Check**:
   - Test bucket connectivity
   - Verify upload/download permissions

2. **OpenRouter API Check**:
   - Verify API key validity
   - Check rate limit status

3. **WebSocket Health**:
   - Monitor active connections
   - Check pub/sub functionality

4. **Detailed Metrics**:
   - Response times per service
   - Connection pool status
   - Memory usage
   - CPU usage

5. **Version Information**:
   - Git commit hash
   - Build timestamp
   - Deployment environment

---

## Security Considerations

### Information Disclosure

- ✅ Status messages are generic
- ✅ No sensitive credentials exposed
- ✅ Error messages don't reveal internal details
- ✅ No database schema information

### Rate Limiting

Health check endpoint is **exempt** from rate limiting to allow monitoring services and automated checks.

### Authentication

Health check endpoint is **public** (no authentication required) to allow external monitoring services.

---

## References

- [Render Health Checks](https://render.com/docs/health-checks)
- [UptimeRobot Documentation](https://uptimerobot.com/api/)
- [Healthchecks.io Documentation](https://healthchecks.io/docs/)
- [FastAPI Health Checks](https://fastapi.tiangolo.com/advanced/custom-response/)

---

## Changelog

### Version 1.0.0 (2025-12-09)
- Initial health check implementation
- Database connectivity check (Supabase PostgreSQL)
- Redis connectivity check (Upstash)
- Overall status determination (healthy/degraded/unhealthy)
- Timestamp in UTC ISO format
- Comprehensive documentation
