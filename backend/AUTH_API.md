# Authentication API Documentation

## Overview

NodeRush authentication system using JWT tokens with Redis session management.

**Base URL**: `/api/auth`

**Features**:
- Email/password authentication
- JWT tokens (7-day expiration)
- Redis session management
- Audit logging for security events
- Suspicious activity detection

---

## Table of Contents

1. [Authentication Flow](#authentication-flow)
2. [Endpoints](#endpoints)
3. [Request/Response Examples](#requestresponse-examples)
4. [Error Handling](#error-handling)
5. [Security](#security)
6. [Testing](#testing)

---

## Authentication Flow

```
1. Signup: POST /api/auth/signup
   ↓
2. Receive JWT token
   ↓
3. Store token in client (localStorage/cookies)
   ↓
4. Include token in requests: Authorization: Bearer <token>
   ↓
5. Token auto-refreshes session TTL on activity
   ↓
6. Logout: POST /api/auth/logout (deletes session)
```

---

## Endpoints

### 1. Sign Up

**POST** `/api/auth/signup`

Register a new user account.

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Validation**:
- Email: Must be valid email format
- Password: Minimum 8 characters

**Response** (201 Created):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "subscription_tier": "free",
  "subscription_status": "active",
  "created_at": "2025-12-09T10:30:00Z",
  "updated_at": "2025-12-09T10:30:00Z"
}
```

**Errors**:
- `409 RESOURCE_ALREADY_EXISTS`: Email already registered
- `422 VALIDATION_ERROR`: Invalid email or weak password

**Rate Limit**: 5 signups per hour per IP

**Audit Event**: `signup_success` or `signup_failed`

---

### 2. Sign Up (Alias)

**POST** `/api/auth/register`

Alias for `/api/auth/signup`. Identical functionality.

---

### 3. Login

**POST** `/api/auth/login`

Authenticate user and receive JWT token.

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 604800,
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "subscription_tier": "free",
    "subscription_status": "active",
    "created_at": "2025-12-09T10:30:00Z"
  }
}
```

**Token Details**:
- **Type**: JWT (JSON Web Token)
- **Algorithm**: HS256
- **Expiration**: 7 days (604,800 seconds)
- **Payload**:
  ```json
  {
    "sub": "user-uuid",
    "email": "user@example.com",
    "tier": "free",
    "permissions": ["read:agents", "write:agents", "execute:agents"],
    "iat": 1234567890,
    "exp": 1235172690
  }
  ```

**Errors**:
- `401 AUTHENTICATION_FAILED`: Invalid email or password
- `401 AUTHENTICATION_FAILED`: Account not found

**Rate Limit**: 10 attempts per minute per IP

**Audit Event**: `login_success` or `login_failed`

**Suspicious Activity**: 5 failed attempts within 1 hour triggers alert

---

### 4. Get Current User

**GET** `/api/auth/me`

Get authenticated user's profile.

**Headers**:
```
Authorization: Bearer <jwt_token>
```

**Response** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "subscription_tier": "free",
  "subscription_status": "active",
  "created_at": "2025-12-09T10:30:00Z",
  "updated_at": "2025-12-09T10:30:00Z"
}
```

**Errors**:
- `401 AUTHENTICATION_FAILED`: Invalid or expired token
- `401 SESSION_EXPIRED`: Redis session not found

---

### 5. Logout

**POST** `/api/auth/logout`

Logout user and delete Redis session.

**Headers**:
```
Authorization: Bearer <jwt_token>
```

**Response** (200 OK):
```json
{
  "message": "Logged out successfully",
  "user_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Note**: The JWT token will still be valid until it expires, but API requests will fail because the Redis session is deleted.

**Audit Event**: `logout`

---

### 6. Refresh Token

**POST** `/api/auth/refresh`

Refresh JWT access token with extended expiration.

**Headers**:
```
Authorization: Bearer <jwt_token>
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 604800,
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "subscription_tier": "free"
  }
}
```

**Use Case**: Keep users logged in without re-authentication. Call this endpoint before the token expires to maintain session.

**Errors**:
- `401 SESSION_EXPIRED`: Redis session not found

**Audit Event**: `token_refreshed`

---

## Request/Response Examples

### cURL Examples

#### Sign Up
```bash
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "strongpassword123"
  }'
```

#### Login
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "strongpassword123"
  }'
```

#### Get Current User
```bash
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

#### Logout
```bash
curl -X POST http://localhost:8000/api/auth/logout \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

#### Refresh Token
```bash
curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Python Examples

```python
import requests

BASE_URL = "http://localhost:8000/api/auth"

# Sign Up
response = requests.post(f"{BASE_URL}/signup", json={
    "email": "john@example.com",
    "password": "strongpassword123"
})
user = response.json()

# Login
response = requests.post(f"{BASE_URL}/login", json={
    "email": "john@example.com",
    "password": "strongpassword123"
})
data = response.json()
token = data["access_token"]

# Get Current User
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(f"{BASE_URL}/me", headers=headers)
user = response.json()

# Logout
response = requests.post(f"{BASE_URL}/logout", headers=headers)
```

### JavaScript Examples

```javascript
const BASE_URL = "http://localhost:8000/api/auth";

// Sign Up
const signup = async () => {
  const response = await fetch(`${BASE_URL}/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email: "john@example.com",
      password: "strongpassword123"
    })
  });
  return response.json();
};

// Login
const login = async () => {
  const response = await fetch(`${BASE_URL}/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email: "john@example.com",
      password: "strongpassword123"
    })
  });
  const data = await response.json();

  // Store token
  localStorage.setItem("auth_token", data.access_token);

  return data;
};

// Get Current User
const getCurrentUser = async () => {
  const token = localStorage.getItem("auth_token");
  const response = await fetch(`${BASE_URL}/me`, {
    headers: { "Authorization": `Bearer ${token}` }
  });
  return response.json();
};

// Logout
const logout = async () => {
  const token = localStorage.getItem("auth_token");
  const response = await fetch(`${BASE_URL}/logout`, {
    method: "POST",
    headers: { "Authorization": `Bearer ${token}` }
  });

  // Remove token
  localStorage.removeItem("auth_token");

  return response.json();
};
```

---

## Error Handling

### Error Response Format

All errors return consistent JSON format:

```json
{
  "error": "ERROR_CODE",
  "message": "Human-readable error message",
  "details": {
    "field": "additional info"
  },
  "path": "/api/auth/signup"
}
```

### Common Error Codes

| Code | Status | Description |
|------|--------|-------------|
| `AUTHENTICATION_FAILED` | 401 | Invalid credentials |
| `SESSION_EXPIRED` | 401 | Redis session not found |
| `RESOURCE_ALREADY_EXISTS` | 409 | Email already registered |
| `VALIDATION_ERROR` | 422 | Invalid input data |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |

### Error Examples

**Invalid Credentials**:
```json
{
  "error": "AUTHENTICATION_FAILED",
  "message": "Incorrect email or password",
  "details": {
    "email": "john@example.com"
  },
  "path": "/api/auth/login"
}
```

**Weak Password**:
```json
{
  "error": "VALIDATION_ERROR",
  "message": "Password must be at least 8 characters long",
  "details": {
    "field": "password"
  },
  "path": "/api/auth/signup"
}
```

**Email Already Exists**:
```json
{
  "error": "RESOURCE_ALREADY_EXISTS",
  "message": "User already exists",
  "details": {
    "resource_type": "User",
    "identifier": "john@example.com"
  },
  "path": "/api/auth/signup"
}
```

---

## Security

### Password Security

- **Hashing**: bcrypt with automatic salt
- **Minimum Length**: 8 characters
- **Strength**: No complexity requirements in MVP (can be added later)

### JWT Security

- **Algorithm**: HS256 (HMAC with SHA-256)
- **Secret**: Stored in environment variable `SECRET_KEY`
- **Expiration**: 7 days (auto-refresh on activity)
- **Payload**: User ID, email, tier, permissions

### Session Security

- **Storage**: Redis (Upstash)
- **Key Format**: `session:{user_id}`
- **TTL**: 7 days (auto-refresh on activity)
- **Data**: User profile, login time, IP address

### Rate Limiting

- **Signup**: 5 attempts per hour per IP
- **Login**: 10 attempts per minute per IP
- **Refresh**: 60 requests per minute per user

### Audit Logging

All security events are logged:
- Signup success/failure
- Login success/failure
- Logout
- Token refresh
- Suspicious activity (5 failed attempts/hour)

Logs are stored in:
1. Application logs (immediate)
2. Redis (24 hours)
3. Database (long-term, if `security_logs` table exists)

### Suspicious Activity Detection

Automatic detection for:
- Multiple failed login attempts (5 within 1 hour)
- Repeated signup failures
- Invalid token attempts

**Action**: Critical log + alert (TODO: Email/Slack notification)

---

## Testing

### Test User Accounts

Create test users for development:

```bash
# Sign up test user
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "testpass123"}'
```

### Test Scenarios

**1. Successful Registration and Login**:
```bash
# Register
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email": "newuser@example.com", "password": "password123"}'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "newuser@example.com", "password": "password123"}'
```

**2. Duplicate Email**:
```bash
# Try to register same email twice
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password123"}'
# Should return 409 error
```

**3. Invalid Password**:
```bash
# Wrong password
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "wrongpass"}'
# Should return 401 error
```

**4. Token Validation**:
```bash
# Get profile with token
TOKEN="your_jwt_token_here"
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

**5. Logout**:
```bash
# Logout (invalidate session)
curl -X POST http://localhost:8000/api/auth/logout \
  -H "Authorization: Bearer $TOKEN"

# Try to use same token
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer $TOKEN"
# Should return 401 error (session expired)
```

**6. Token Refresh**:
```bash
# Refresh token before expiration
curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Authorization: Bearer $TOKEN"
# Returns new token with extended expiration
```

---

## Integration with Frontend

### Store Token

```javascript
// After successful login
const data = await login(email, password);
localStorage.setItem("auth_token", data.access_token);
localStorage.setItem("user", JSON.stringify(data.user));
```

### Add Token to Requests

```javascript
// Axios interceptor
axios.interceptors.request.use(config => {
  const token = localStorage.getItem("auth_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Fetch wrapper
const authenticatedFetch = async (url, options = {}) => {
  const token = localStorage.getItem("auth_token");
  const headers = {
    ...options.headers,
    "Authorization": `Bearer ${token}`
  };
  return fetch(url, { ...options, headers });
};
```

### Handle Token Expiration

```javascript
// Axios interceptor for 401 errors
axios.interceptors.response.use(
  response => response,
  async error => {
    if (error.response?.status === 401) {
      // Try to refresh token
      try {
        const response = await axios.post("/api/auth/refresh");
        const newToken = response.data.access_token;
        localStorage.setItem("auth_token", newToken);

        // Retry original request
        error.config.headers.Authorization = `Bearer ${newToken}`;
        return axios(error.config);
      } catch (refreshError) {
        // Refresh failed, redirect to login
        localStorage.removeItem("auth_token");
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);
```

---

## References

- [JWT Documentation](https://jwt.io/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Redis Session Management](https://redis.io/docs/manual/patterns/session-management/)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)

---

## Changelog

### Version 1.0.0 (2025-12-09)
- Initial auth API implementation
- JWT authentication with 7-day expiration
- Redis session management
- Audit logging for security events
- Suspicious activity detection
- Signup, login, logout, refresh endpoints
- Comprehensive error handling
- Rate limiting integration
