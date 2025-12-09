# NodeRush Logging & Error Handling

## Overview

NodeRush implements a comprehensive logging and error handling system with:
- **Structured logging** with JSON output
- **Custom exception classes** for domain-specific errors
- **Centralized error handlers** for consistent API responses
- **Audit logging** for security events and compliance
- **Request tracking** with unique request IDs

---

## Table of Contents

1. [Logging System](#logging-system)
2. [Error Handling](#error-handling)
3. [Custom Exceptions](#custom-exceptions)
4. [Audit Logging](#audit-logging)
5. [Usage Examples](#usage-examples)
6. [Configuration](#configuration)
7. [Best Practices](#best-practices)

---

## Logging System

### Features

✅ **Structured logging** - JSON output for production, colored console for development
✅ **Log levels** - DEBUG, INFO, WARNING, ERROR, CRITICAL
✅ **Context binding** - Automatic field injection (request_id, user_id, etc.)
✅ **File logging** - Optional file output with rotation
✅ **Third-party filtering** - Reduced noise from libraries

### Log Formats

**Development (Colored Console)**:
```
2025-12-09 11:30:00 | INFO     | app.api.auth                   | User logged in
2025-12-09 11:30:05 | ERROR    | app.services.redis_service     | Redis connection failed
```

**Production (JSON)**:
```json
{
  "timestamp": "2025-12-09T11:30:00.123456Z",
  "level": "INFO",
  "logger": "app.api.auth",
  "message": "User logged in",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user-123",
  "ip_address": "192.168.1.1"
}
```

### Usage

#### Basic Logging

```python
from app.core.logging_config import get_logger

logger = get_logger(__name__)

# Log messages
logger.debug("Debug information")
logger.info("Informational message")
logger.warning("Warning message")
logger.error("Error occurred")
logger.critical("Critical failure")

# Log exception with traceback
try:
    risky_operation()
except Exception:
    logger.exception("Operation failed")
```

#### Context Binding

```python
# Bind context for automatic field injection
request_logger = logger.bind(
    request_id="550e8400-e29b-41d4-a716-446655440000",
    user_id="user-123"
)

# All logs from this logger include request_id and user_id
request_logger.info("Processing request")
request_logger.error("Request failed")
```

#### Additional Fields

```python
logger.info(
    "Agent created",
    agent_id="agent-456",
    agent_name="Email Bot",
    status="active"
)
```

---

## Error Handling

### Architecture

```
Request → Middleware → Route Handler → Exception
                                          ↓
                                    Error Handler
                                          ↓
                                    Structured JSON Response
```

### Error Response Format

All errors return a consistent JSON format:

```json
{
  "error": "ERROR_CODE",
  "message": "Human-readable error message",
  "details": {
    "field": "specific details"
  },
  "path": "/api/agents",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Error Handlers

NodeRush implements handlers for:

1. **Custom NodeRush Exceptions** - Domain-specific errors
2. **HTTP Exceptions** - 404, 403, etc.
3. **Validation Errors** - Pydantic validation failures
4. **Database Errors** - SQLAlchemy errors
5. **Global Exception Handler** - Catch-all for unexpected errors

---

## Custom Exceptions

### Exception Hierarchy

```
NodeRushException (base)
├── AuthenticationError
│   ├── TokenExpiredError
│   ├── InvalidTokenError
│   └── SessionExpiredError
├── AuthorizationError
├── ResourceNotFoundError
├── ResourceAlreadyExistsError
├── ValidationError
│   └── InvalidInputError
├── RateLimitExceededError
├── QuotaExceededError
├── ServiceUnavailableError
├── DatabaseError
├── RedisError
├── AIGenerationError
├── TokenLimitExceededError
├── ConfigurationError
└── IntegrationError
```

### Usage Examples

#### Authentication Errors

```python
from app.core.exceptions import (
    AuthenticationError,
    TokenExpiredError,
    SessionExpiredError
)

# Generic authentication error
raise AuthenticationError("Invalid credentials")

# Specific token error
raise TokenExpiredError()

# Session error
raise SessionExpiredError()
```

#### Resource Errors

```python
from app.core.exceptions import (
    ResourceNotFoundError,
    ResourceAlreadyExistsError
)

# Resource not found
raise ResourceNotFoundError("Agent", agent_id)
# Returns: "Agent with ID 'agent-123' not found" (404)

# Resource already exists
raise ResourceAlreadyExistsError("User", email)
# Returns: "User already exists" (409)
```

#### Validation Errors

```python
from app.core.exceptions import ValidationError, InvalidInputError

# Generic validation error
raise ValidationError("Invalid request data")

# Field-specific error
raise InvalidInputError("email", "must be a valid email address")
```

#### Rate Limiting

```python
from app.core.exceptions import RateLimitExceededError, QuotaExceededError

# Rate limit exceeded
raise RateLimitExceededError(
    resource="agent_creation",
    limit=5,
    window=3600,  # 1 hour
    retry_after=3600
)

# Quota exceeded
raise QuotaExceededError(
    quota_type="Total agents",
    limit=10,
    current=10
)
```

#### Service Errors

```python
from app.core.exceptions import (
    ServiceUnavailableError,
    DatabaseError,
    RedisError
)

# External service unavailable
raise ServiceUnavailableError("OpenRouter")

# Database error
raise DatabaseError("Failed to insert record")

# Redis error
raise RedisError("Connection timeout")
```

---

## Audit Logging

### Purpose

Audit logging tracks:
- **Security events** (login attempts, permission denials)
- **User actions** (resource creation, updates, deletions)
- **System events** (errors, service failures)

### Event Types

```python
from app.services.audit_service import AuditEventType

# Authentication
AuditEventType.LOGIN_SUCCESS
AuditEventType.LOGIN_FAILED
AuditEventType.LOGOUT
AuditEventType.TOKEN_EXPIRED

# Authorization
AuditEventType.PERMISSION_DENIED
AuditEventType.TIER_RESTRICTION

# Resources
AuditEventType.RESOURCE_CREATED
AuditEventType.RESOURCE_UPDATED
AuditEventType.RESOURCE_DELETED

# Rate Limiting
AuditEventType.RATE_LIMIT_EXCEEDED
AuditEventType.QUOTA_EXCEEDED

# Security
AuditEventType.SUSPICIOUS_ACTIVITY
AuditEventType.INVALID_TOKEN
```

### Usage

```python
from app.services.audit_service import audit_service

# Manual audit logging
await audit_service.log_event(
    event_type=AuditEventType.RESOURCE_CREATED,
    user_id="user-123",
    ip_address="192.168.1.1",
    details={"resource_type": "agent", "agent_id": "agent-456"},
    severity="info"
)

# Convenience methods
await audit_service.log_login_success(user_id, ip_address)
await audit_service.log_login_failed(email, ip_address, reason)
await audit_service.log_permission_denied(user_id, resource, permission)
await audit_service.log_rate_limit_exceeded(user_id, ip_address, resource)
```

### Storage

Audit logs are written to:

1. **Application Logs** (immediate) - For real-time monitoring
2. **Redis** (24 hours) - For real-time analysis
3. **Database** (long-term) - For compliance and auditing

### Suspicious Activity Detection

Automatically detects patterns like:
- Multiple failed login attempts
- Repeated rate limit violations
- Permission denial spikes

Threshold: **5 events within 1 hour**

Action: **Critical log + alert** (TODO: Email/Slack notification)

---

## Usage Examples

### In Route Handlers

```python
from fastapi import APIRouter, Depends, Request
from app.core.exceptions import ResourceNotFoundError, AuthorizationError
from app.core.logging_config import get_logger
from app.services.audit_service import audit_service, AuditEventType

router = APIRouter()
logger = get_logger(__name__)

@router.get("/agents/{agent_id}")
async def get_agent(
    agent_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Get request logger with context
    request_logger = logger.bind(
        request_id=request.state.request_id,
        user_id=current_user.id
    )

    request_logger.info(f"Fetching agent {agent_id}")

    # Fetch agent
    agent = await db.get(Agent, agent_id)

    if not agent:
        request_logger.warning(f"Agent {agent_id} not found")
        raise ResourceNotFoundError("Agent", agent_id)

    # Check ownership
    if agent.user_id != current_user.id:
        request_logger.warning(f"User {current_user.id} denied access to agent {agent_id}")
        await audit_service.log_permission_denied(
            user_id=current_user.id,
            resource=f"agent:{agent_id}",
            required_permission="owner"
        )
        raise AuthorizationError("You don't have access to this agent")

    # Log successful access
    await audit_service.log_event(
        event_type=AuditEventType.RESOURCE_ACCESSED,
        user_id=current_user.id,
        ip_address=request.client.host,
        details={"resource_type": "agent", "agent_id": agent_id}
    )

    request_logger.info(f"Agent {agent_id} fetched successfully")
    return agent
```

### In Services

```python
from app.core.logging_config import get_logger
from app.core.exceptions import AIGenerationError, TokenLimitExceededError

logger = get_logger(__name__)

class AIService:
    async def generate_code(self, prompt: str, user_id: str):
        service_logger = logger.bind(user_id=user_id)

        try:
            service_logger.info("Starting code generation")

            # Check token limit
            tokens_used = count_tokens(prompt)
            if tokens_used > MAX_TOKENS:
                raise TokenLimitExceededError(tokens_used, MAX_TOKENS)

            # Generate code
            result = await openrouter_client.generate(prompt)

            service_logger.info(
                "Code generation completed",
                tokens_used=tokens_used,
                generation_time=result.duration
            )

            return result

        except TokenLimitExceededError:
            service_logger.warning("Token limit exceeded")
            raise

        except Exception as e:
            service_logger.exception("Code generation failed")
            raise AIGenerationError("architect", str(e))
```

---

## Configuration

### Environment Variables

```bash
# Logging level
DEBUG=true  # Enables DEBUG logs and colored console

# Production (set DEBUG=false)
DEBUG=false  # Uses INFO level and JSON logs
```

### Code Configuration

```python
from app.core.logging_config import setup_logging

# Development
setup_logging(
    level="DEBUG",
    json_logs=False,
    colored_console=True
)

# Production
setup_logging(
    level="INFO",
    json_logs=True,
    colored_console=False,
    log_file="/var/log/noderush/app.log"
)
```

---

## Best Practices

### ✅ Do

1. **Use structured logging** with context binding
   ```python
   logger = get_logger(__name__).bind(user_id=user_id)
   logger.info("Action performed", resource_id=resource_id)
   ```

2. **Use custom exceptions** for domain errors
   ```python
   raise ResourceNotFoundError("Agent", agent_id)
   ```

3. **Log at appropriate levels**
   - `DEBUG` - Detailed diagnostic information
   - `INFO` - Confirmation of expected behavior
   - `WARNING` - Unexpected but handled situations
   - `ERROR` - Errors that need attention
   - `CRITICAL` - System-threatening failures

4. **Include context** in error messages
   ```python
   logger.error("Failed to create agent", agent_name=name, reason=str(e))
   ```

5. **Audit security events**
   ```python
   await audit_service.log_login_failed(email, ip_address, "invalid_password")
   ```

### ❌ Don't

1. **Don't log sensitive information**
   ```python
   # Bad
   logger.info(f"User password: {password}")

   # Good
   logger.info("User authenticated successfully")
   ```

2. **Don't use print statements**
   ```python
   # Bad
   print(f"Processing request {request_id}")

   # Good
   logger.info("Processing request", request_id=request_id)
   ```

3. **Don't catch and silently ignore exceptions**
   ```python
   # Bad
   try:
       risky_operation()
   except:
       pass

   # Good
   try:
       risky_operation()
   except Exception as e:
       logger.exception("Operation failed")
       raise
   ```

4. **Don't create generic error messages**
   ```python
   # Bad
   raise HTTPException(status_code=500, detail="Error")

   # Good
   raise DatabaseError("Failed to insert agent record", details={"agent_id": agent_id})
   ```

---

## File Structure

```
backend/
├── app/
│   ├── core/
│   │   ├── logging_config.py       # Logging configuration
│   │   ├── exceptions.py           # Custom exception classes
│   │   ├── error_handlers.py       # Error handlers
│   │   └── middleware.py           # Request logging middleware
│   └── services/
│       └── audit_service.py        # Audit logging service
└── LOGGING_ERROR_HANDLING.md       # This file
```

---

## Monitoring & Alerts

### Log Analysis

**Production logs** are in JSON format and can be analyzed with:
- **ELK Stack** (Elasticsearch, Logstash, Kibana)
- **CloudWatch Logs** (AWS)
- **Render Logs** (built-in)
- **Datadog** (paid service)

### Alert Triggers

Set up alerts for:
- `level: "ERROR"` or `level: "CRITICAL"`
- `event_type: "suspicious_activity"`
- `status_code: 500`
- High error rates

---

## Troubleshooting

### Logs not appearing

**Check logging level**:
```python
# Ensure level is set correctly
setup_logging(level="DEBUG")  # or "INFO"
```

### JSON logs in development

**Disable JSON logs**:
```python
setup_logging(json_logs=False, colored_console=True)
```

### Missing context fields

**Bind context to logger**:
```python
logger = get_logger(__name__).bind(request_id=request_id)
```

### Audit logs not in database

**Check if security_logs table exists**:
```sql
CREATE TABLE security_logs (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(100),
    user_id VARCHAR(100),
    ip_address VARCHAR(50),
    details TEXT,
    severity VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## References

- [Python Logging Documentation](https://docs.python.org/3/library/logging.html)
- [Structlog Documentation](https://www.structlog.org/)
- [FastAPI Error Handling](https://fastapi.tiangolo.com/tutorial/handling-errors/)
- [OWASP Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html)

---

## Changelog

### Version 1.0.0 (2025-12-09)
- Initial logging and error handling implementation
- Structured logging with JSON output
- Custom exception classes
- Centralized error handlers
- Audit logging service
- Request tracking with unique IDs
- Suspicious activity detection
- Comprehensive documentation
