# NodeRush Authentication & Authorization

## Overview

NodeRush implements a comprehensive authentication and authorization system using **JWT tokens**, **Redis sessions**, and **permission-based access control**.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  AUTHENTICATION FLOW                    │
└─────────────────────────────────────────────────────────┘

1. User Login
   ↓
2. Backend validates credentials
   ↓
3. Generate JWT token with permissions
   ↓
4. Store session in Redis (7 days TTL)
   ↓
5. Return token to client
   ↓
6. Client sends token in Authorization header
   ↓
7. Middleware validates token + checks permissions
   ↓
8. Auto-refresh session TTL on activity
```

---

## JWT Token Structure

Tokens follow the **ARCHITECTURE.md** specification:

```json
{
  "sub": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "tier": "free",
  "permissions": [
    "read:agents",
    "write:agents",
    "execute:agents",
    "read:integrations"
  ],
  "iat": 1234567890,
  "exp": 1235172690
}
```

### Fields:
- **sub**: User UUID (subject)
- **email**: User email address
- **tier**: Subscription tier (`free`, `pro`, `enterprise`)
- **permissions**: Array of permission strings
- **iat**: Issued at timestamp
- **exp**: Expiration timestamp (7 days from `iat`)

---

## Permission System

### Permission Format

Permissions follow the pattern: `<action>:<resource>`

Examples:
- `read:agents` - View agents
- `write:agents` - Create/update agents
- `delete:agents` - Delete agents
- `execute:agents` - Execute agent workflows
- `deploy:agents` - Deploy agents to production
- `admin:users` - Manage users (admin only)

### Default Permissions by Tier

#### Free Tier
```python
[
    "read:agents",
    "write:agents",
    "execute:agents",
    "read:integrations",
]
```

#### Pro Tier
```python
[
    "read:agents",
    "write:agents",
    "execute:agents",
    "deploy:agents",           # NEW
    "read:integrations",
    "write:integrations",      # NEW
    "read:analytics",          # NEW
]
```

#### Enterprise Tier
```python
[
    "read:agents",
    "write:agents",
    "execute:agents",
    "deploy:agents",
    "delete:agents",           # NEW
    "read:integrations",
    "write:integrations",
    "delete:integrations",     # NEW
    "read:analytics",
    "write:analytics",         # NEW
    "admin:users",             # NEW
    "admin:billing",           # NEW
]
```

---

## Using Permission Decorators

### 1. Require Specific Permissions

```python
from app.core.auth_middleware import require_permissions

@router.post("/agents")
@require_permissions("write:agents")
async def create_agent(
    request: Request,  # Required for permission check
    current_user: User = Depends(get_current_user),
    ...
):
    # Only users with "write:agents" permission can access
    pass
```

### 2. Require Multiple Permissions

```python
@router.post("/agents/{id}/deploy")
@require_permissions("deploy:agents", "execute:agents")
async def deploy_agent(
    request: Request,
    current_user: User = Depends(get_current_user),
    ...
):
    # User must have BOTH permissions
    pass
```

### 3. Require Minimum Tier

```python
from app.core.auth_middleware import require_tier

@router.get("/analytics/advanced")
@require_tier("pro")
async def advanced_analytics(
    request: Request,
    current_user: User = Depends(get_current_user),
    ...
):
    # Only pro and enterprise users can access
    # free tier users get 403 Forbidden
    pass
```

### 4. Combine Decorators

```python
@router.delete("/agents/{id}")
@require_tier("pro")
@require_permissions("delete:agents")
async def delete_agent(
    request: Request,
    current_user: User = Depends(get_current_user),
    ...
):
    # Must be pro tier AND have delete permission
    pass
```

---

## Session Management

### Redis Session Storage

**Key Pattern**: `session:{user_id}`

**TTL**: 7 days (604,800 seconds)

**Data Structure**:
```python
{
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "subscription_tier": "free",
    "login_time": "2025-12-09T10:30:00"
}
```

### Auto-Refresh on Activity

Every authenticated request **automatically refreshes** the session TTL:

```python
async def verify_session(user_id: str) -> dict:
    session_data = await redis_service.get_session(user_id)

    if session_data:
        # Refresh TTL to 7 days from now
        await redis_service.set_session(
            session_id=user_id,
            user_data=session_data,
            expire_seconds=604800
        )

    return session_data
```

This means users stay logged in as long as they're active (within 7 days of last activity).

---

## Authentication Flow

### 1. Registration

```bash
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "strongpassword123"
}
```

**Response**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "subscription_tier": "free",
  "subscription_status": "active",
  "created_at": "2025-12-09T10:30:00"
}
```

### 2. Login

```bash
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "strongpassword123"
}
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "subscription_tier": "free",
    "subscription_status": "active"
  }
}
```

### 3. Authenticated Requests

```bash
GET /api/agents
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 4. Logout

```bash
POST /api/auth/logout
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response**:
```json
{
  "message": "Logged out successfully"
}
```

---

## Error Responses

### 401 Unauthorized

**Token missing or invalid**:
```json
{
  "detail": "Could not validate credentials"
}
```

**Session expired**:
```json
{
  "detail": "Session expired. Please login again."
}
```

**Token expired**:
```json
{
  "detail": "Token has expired"
}
```

### 403 Forbidden

**Missing permission**:
```json
{
  "detail": "Missing required permissions: delete:agents"
}
```

**Tier too low**:
```json
{
  "detail": "This feature requires 'pro' tier or higher. Your tier: 'free'"
}
```

---

## Security Best Practices

✅ **Implemented**:
- JWT tokens with 7-day expiration
- Redis session verification (prevents token reuse after logout)
- Permission-based access control
- Tier-based feature gating
- Auto-refresh session TTL on activity
- bcrypt password hashing
- Token payload in request state for permission checks

🔐 **Recommendations**:
- Store tokens in `httpOnly` cookies (more secure than localStorage)
- Implement token refresh mechanism
- Add 2FA for sensitive operations
- Log all authentication events
- Monitor for suspicious login patterns
- Implement account lockout after N failed attempts

---

## Testing Authentication

### Test Login
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123"}'
```

### Test Authenticated Request
```bash
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

curl http://localhost:8000/api/agents \
  -H "Authorization: Bearer $TOKEN"
```

### Test Permission Denial
```bash
# As free tier user, try to access pro-only feature
curl http://localhost:8000/api/analytics/advanced \
  -H "Authorization: Bearer $TOKEN"

# Expected: 403 Forbidden
```

---

## Troubleshooting

### "Session expired. Please login again"
- User logged out
- Redis session was deleted
- Redis connection lost
- **Solution**: Login again

### "Missing required permissions: X"
- User's tier doesn't include this permission
- **Solution**: Upgrade tier or contact admin

### "Token has expired"
- Token is older than 7 days
- **Solution**: Login again

### "Could not validate credentials"
- Token is malformed
- Token signature is invalid
- SECRET_KEY changed
- **Solution**: Login again

---

## File Structure

```
backend/
├── app/
│   ├── core/
│   │   ├── auth_middleware.py    # Auth middleware & decorators
│   │   └── config.py             # JWT settings
│   └── api/
│       └── auth.py               # Auth endpoints
└── AUTHENTICATION.md             # This file
```

---

## References

- [JWT.io](https://jwt.io/)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
