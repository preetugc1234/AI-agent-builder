# NodeRush Backend Middleware Documentation

## Overview

The NodeRush backend implements multiple middleware layers for security, logging, and CORS handling.

## Middleware Stack (Execution Order)

Middleware is executed in **reverse order** of how it's added:

1. **Request Logging Middleware** (outermost)
2. **Security Headers Middleware**
3. **CORS Middleware** (innermost)
4. **Rate Limiting Middleware** (planned for Redis integration)

---

## 1. CORS Middleware

**Purpose**: Handle Cross-Origin Resource Sharing for frontend applications

**Configuration** (`app/core/config.py`):
```python
CORS_ORIGINS: Union[List[str], str] = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:5174",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "https://noderush.vercel.app",
]
```

**Features**:
- ✅ Configurable allowed origins (supports environment variables)
- ✅ Credentials support (cookies, Authorization headers)
- ✅ Specific HTTP methods allowed
- ✅ Custom headers support
- ✅ Preflight request caching (10 minutes)

**Environment Variable**:
```bash
# In Render/Production
CORS_ORIGINS="http://localhost:3000,https://your-app.vercel.app"
```

**Allowed Methods**:
- GET, POST, PUT, DELETE, OPTIONS, PATCH

**Allowed Headers**:
- Authorization
- Content-Type
- X-Request-ID
- X-API-Key

**Exposed Headers**:
- X-Request-ID
- X-Total-Count

---

## 2. Security Headers Middleware

**Purpose**: Add OWASP-recommended security headers to all responses

**Headers Added**:

| Header | Value | Purpose |
|--------|-------|---------|
| `X-Content-Type-Options` | `nosniff` | Prevent MIME type sniffing |
| `X-Frame-Options` | `DENY` | Prevent clickjacking |
| `X-XSS-Protection` | `1; mode=block` | Enable browser XSS protection |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` | Force HTTPS |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Control referrer information |
| `Permissions-Policy` | `geolocation=(), microphone=(), camera=()` | Disable unnecessary browser features |
| `Content-Security-Policy` | See below | Prevent XSS and injection attacks |

**Content Security Policy (CSP)**:
```
default-src 'self';
script-src 'self' 'unsafe-inline' 'unsafe-eval';
style-src 'self' 'unsafe-inline';
img-src 'self' data: https:;
font-src 'self' data:;
connect-src 'self' https:;
frame-ancestors 'none';
```

⚠️ **Note**: CSP is configured permissively for development. Tighten in production.

---

## 3. Request Logging Middleware

**Purpose**: Log all HTTP requests and responses for debugging and monitoring

**Features**:
- ✅ Unique request ID generation (UUID4)
- ✅ Request/response logging with duration
- ✅ Client IP tracking
- ✅ Error logging with stack traces
- ✅ Request ID added to response headers

**Log Format**:
```
[request_id] METHOD /path - Client: IP
[request_id] METHOD /path - Status: 200 - Duration: 0.123s
```

**Response Header**:
```
X-Request-ID: 550e8400-e29b-41d4-a716-446655440000
```

**Usage**:
```python
# Access request ID in endpoints
request_id = request.state.request_id
```

---

## 4. Rate Limiting Middleware (Planned)

**Purpose**: Prevent API abuse and ensure fair usage

**Status**: 🚧 Placeholder (will be implemented with Upstash Redis)

**Planned Features**:
- Per-IP rate limiting
- Per-user rate limiting
- Configurable limits per endpoint
- Distributed rate limiting via Redis
- Graceful rate limit responses

**Configuration** (planned):
```python
RateLimitMiddleware(
    calls=100,  # 100 requests
    period=60   # per 60 seconds
)
```

---

## Testing CORS

### Test with cURL:

```bash
# Preflight request (OPTIONS)
curl -X OPTIONS http://localhost:8000/api/agents \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: GET" \
  -v

# Actual request
curl http://localhost:8000/api/agents \
  -H "Origin: http://localhost:3000" \
  -v
```

### Expected Headers:

```
Access-Control-Allow-Origin: http://localhost:3000
Access-Control-Allow-Credentials: true
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS, PATCH
Access-Control-Allow-Headers: Authorization, Content-Type, X-Request-ID, X-API-Key
X-Request-ID: 550e8400-e29b-41d4-a716-446655440000
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
```

---

## Adding New Origins

### Development:

Edit `backend/app/core/config.py`:
```python
CORS_ORIGINS: Union[List[str], str] = [
    "http://localhost:3000",
    "https://your-new-origin.com",  # Add here
]
```

### Production (Render):

Add environment variable:
```bash
CORS_ORIGINS="http://localhost:3000,https://your-app.vercel.app,https://custom-domain.com"
```

---

## Security Best Practices

✅ **Implemented**:
- CORS whitelist (no wildcards)
- Security headers (OWASP)
- Request logging
- HTTPS enforcement (HSTS)
- XSS protection
- Clickjacking protection

🚧 **TODO**:
- Rate limiting (Redis)
- API key authentication
- Request size limits
- IP blacklisting
- DDoS protection (Cloudflare)

---

## Troubleshooting

### CORS Error: "Origin not allowed"

**Solution**: Add the frontend URL to `CORS_ORIGINS`

### Missing Security Headers

**Solution**: Ensure `setup_security_middleware(app)` is called in `main.py`

### Request ID not in logs

**Solution**: Check that `RequestLoggingMiddleware` is added before other middleware

### Rate limiting not working

**Solution**: Redis integration pending (Day 2 Task 3)

---

## File Structure

```
backend/
├── app/
│   ├── core/
│   │   ├── config.py          # CORS_ORIGINS configuration
│   │   └── middleware.py      # All middleware implementations
│   └── main.py                # Middleware setup
└── MIDDLEWARE.md              # This file
```

---

## References

- [OWASP Secure Headers Project](https://owasp.org/www-project-secure-headers/)
- [FastAPI CORS Middleware](https://fastapi.tiangolo.com/tutorial/cors/)
- [Starlette Middleware](https://www.starlette.io/middleware/)
