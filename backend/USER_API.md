# User Profile API Documentation

## Overview

NodeRush user profile management API for viewing statistics, updating profiles, and account deletion.

**Base URL**: `/api/users`

**Features**:
- Usage statistics (agents, tokens, deployments, integrations)
- Quota tracking and visualization
- Profile updates (email)
- GDPR-compliant account deletion
- Redis caching for performance
- Comprehensive audit logging

---

## Table of Contents

1. [User Profile Flow](#user-profile-flow)
2. [Endpoints](#endpoints)
3. [Request/Response Examples](#requestresponse-examples)
4. [Error Handling](#error-handling)
5. [Quota Limits](#quota-limits)
6. [Caching](#caching)
7. [Testing](#testing)
8. [GDPR Compliance](#gdpr-compliance)

---

## User Profile Flow

### Viewing Statistics

```
1. User requests stats: GET /api/users/me/stats
   ↓
2. Backend fetches from cache (if available)
   ↓
3. If cache miss:
   - Query agents count and status
   - Query token usage (today, month, total)
   - Query deployments count
   - Query integrations count
   - Calculate quota usage percentages
   ↓
4. Return statistics with quota information
   ↓
5. Cache result for 5 minutes
```

### Updating Profile

```
1. User updates email: PUT /api/users/me
   ↓
2. Validate email format
   ↓
3. Check email uniqueness
   ↓
4. Update database
   ↓
5. Invalidate session and stats cache
   ↓
6. Log audit event
```

### Account Deletion

```
1. User requests deletion: DELETE /api/users/me
   ↓
2. Count user resources (agents, integrations)
   ↓
3. Delete user (cascade deletes all related data)
   ↓
4. Delete Redis sessions and cache
   ↓
5. Log GDPR compliance audit event
   ↓
6. Return deletion summary
```

---

## Endpoints

### 1. Get User Statistics

**GET** `/api/users/me/stats`

Get comprehensive usage statistics and quota information.

**Headers**:
```
Authorization: Bearer <jwt_token>
```

**Response** (200 OK):
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "subscription_tier": "free",
  "subscription_status": "active",
  "member_since": "2025-12-01T10:30:00Z",

  "total_agents": 5,
  "agents_by_status": {
    "draft": 2,
    "ready": 2,
    "generating": 1
  },

  "tokens_today": 12500,
  "tokens_this_month": 125000,
  "tokens_total": 450000,

  "total_deployments": 3,
  "active_deployments": 2,

  "total_integrations": 2,
  "active_integrations": 2,

  "quota_limits": {
    "max_agents": 10,
    "max_deployments": 2,
    "max_ai_tokens_per_day": 50000,
    "max_integrations": 3
  },

  "quota_usage": {
    "agents": {
      "current": 5,
      "limit": 10,
      "percentage": 50.0
    },
    "deployments": {
      "current": 2,
      "limit": 2,
      "percentage": 100.0
    },
    "tokens_today": {
      "current": 12500,
      "limit": 50000,
      "percentage": 25.0
    },
    "integrations": {
      "current": 2,
      "limit": 3,
      "percentage": 66.67
    }
  }
}
```

**Statistics Breakdown**:

| Category | Fields | Description |
|----------|--------|-------------|
| User Info | user_id, email, subscription_tier, subscription_status, member_since | Basic user information |
| Agents | total_agents, agents_by_status | Agent count and status breakdown |
| Tokens | tokens_today, tokens_this_month, tokens_total | AI token consumption |
| Deployments | total_deployments, active_deployments | Deployment statistics |
| Integrations | total_integrations, active_integrations | OAuth/API key integrations |
| Quotas | quota_limits, quota_usage | Tier limits and current usage |

**Quota Usage Percentage**:
- `0-50%`: Green (healthy usage)
- `51-80%`: Yellow (approaching limit)
- `81-100%`: Red (at or near limit)

**Caching**: Results cached in Redis for 5 minutes

**Use Cases**:
- Dashboard statistics
- Quota monitoring
- Usage analytics
- Upgrade prompts

---

### 2. Update User Profile

**PUT** `/api/users/me`

Update user profile information.

**Headers**:
```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Request Body** (all fields optional):
```json
{
  "email": "newemail@example.com"
}
```

**Validation**:
- Email: Must be valid email format, must be unique

**Response** (200 OK):
```json
{
  "message": "Profile updated successfully",
  "updated_fields": ["email"],
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "newemail@example.com",
    "subscription_tier": "free",
    "subscription_status": "active",
    "updated_at": "2025-12-09T15:45:00Z"
  }
}
```

**Response** (200 OK - No Changes):
```json
{
  "message": "No changes made",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "subscription_tier": "free",
    "subscription_status": "active"
  }
}
```

**Errors**:
- `422 VALIDATION_ERROR`: Invalid email format
- `422 VALIDATION_ERROR`: Email already in use

**Note**: Password changes are not supported via this endpoint. Use `/api/auth/change-password` instead (future implementation).

**Cache Invalidation**:
- Clears session cache
- Clears stats cache

**Audit Event**: `profile_updated`

---

### 3. Delete Account (GDPR)

**DELETE** `/api/users/me`

Permanently delete user account and all associated data.

**Headers**:
```
Authorization: Bearer <jwt_token>
```

**Response** (200 OK):
```json
{
  "message": "Account deleted successfully",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "resources_deleted": {
    "agents": 5,
    "integrations": 2
  }
}
```

**Warning**: ⚠️ This action is irreversible!

**Deleted Data**:

| Resource | Details |
|----------|---------|
| User Profile | Email, password hash, subscription info |
| Agents | All agents with their code, architecture, and reviews |
| Deployments | All deployment records and logs |
| Integrations | OAuth tokens and API keys |
| Token Usage | All AI token usage records |
| Execution Logs | All agent execution history |
| Redis Data | Sessions, cache, quota counters |
| R2 Files | Uploaded files (if applicable) |

**GDPR Compliance**: Implements the "Right to Erasure" (Article 17 GDPR)

**Cache Invalidation**:
- Deletes session
- Deletes stats cache
- Deletes agents list cache

**Audit Event**: `account_deleted` (severity: warning)

**Use Cases**:
- User-initiated account deletion
- GDPR compliance requests
- Account cleanup

---

## Request/Response Examples

### cURL Examples

#### Get User Statistics
```bash
TOKEN="your_jwt_token"

curl -X GET http://localhost:8000/api/users/me/stats \
  -H "Authorization: Bearer $TOKEN" | jq
```

#### Update Email
```bash
curl -X PUT http://localhost:8000/api/users/me \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newemail@example.com"
  }' | jq
```

#### Delete Account
```bash
curl -X DELETE http://localhost:8000/api/users/me \
  -H "Authorization: Bearer $TOKEN" | jq
```

### Python Examples

```python
import requests

BASE_URL = "http://localhost:8000/api/users"
TOKEN = "your_jwt_token_here"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Get User Statistics
response = requests.get(f"{BASE_URL}/me/stats", headers=HEADERS)
stats = response.json()

print(f"Total Agents: {stats['total_agents']}")
print(f"Tokens Today: {stats['tokens_today']} / {stats['quota_limits']['max_ai_tokens_per_day']}")
print(f"Agent Quota: {stats['quota_usage']['agents']['percentage']}%")

# Update Email
response = requests.put(f"{BASE_URL}/me", headers=HEADERS, json={
    "email": "newemail@example.com"
})
result = response.json()
print(f"Updated fields: {result['updated_fields']}")

# Delete Account (with confirmation)
confirm = input("Are you sure you want to delete your account? (yes/no): ")
if confirm.lower() == "yes":
    response = requests.delete(f"{BASE_URL}/me", headers=HEADERS)
    result = response.json()
    print(f"Account deleted: {result['message']}")
```

### JavaScript Examples

```javascript
const BASE_URL = "http://localhost:8000/api/users";
const token = localStorage.getItem("auth_token");
const headers = {
  "Authorization": `Bearer ${token}`,
  "Content-Type": "application/json"
};

// Get User Statistics
const getUserStats = async () => {
  const response = await fetch(`${BASE_URL}/me/stats`, { headers });
  const stats = await response.json();

  console.log(`Total Agents: ${stats.total_agents}`);
  console.log(`Tokens Today: ${stats.tokens_today} / ${stats.quota_limits.max_ai_tokens_per_day}`);
  console.log(`Agent Quota: ${stats.quota_usage.agents.percentage}%`);

  // Check if approaching limits
  if (stats.quota_usage.agents.percentage > 80) {
    console.warn("⚠️ Approaching agent quota limit!");
  }

  return stats;
};

// Update Email
const updateEmail = async (newEmail) => {
  const response = await fetch(`${BASE_URL}/me`, {
    method: "PUT",
    headers,
    body: JSON.stringify({ email: newEmail })
  });
  return response.json();
};

// Delete Account
const deleteAccount = async () => {
  if (!confirm("Are you sure you want to delete your account? This cannot be undone!")) {
    return;
  }

  const response = await fetch(`${BASE_URL}/me`, {
    method: "DELETE",
    headers
  });

  const result = await response.json();

  // Clear local storage
  localStorage.removeItem("auth_token");
  localStorage.removeItem("user");

  // Redirect to homepage
  window.location.href = "/";

  return result;
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
    "field": "specific details"
  },
  "path": "/api/users/me",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Common Error Codes

| Code | Status | Description |
|------|--------|-------------|
| `VALIDATION_ERROR` | 422 | Invalid email format or email already in use |
| `AUTHENTICATION_FAILED` | 401 | Invalid or expired JWT token |

### Error Examples

**Invalid Email Format**:
```json
{
  "error": "VALIDATION_ERROR",
  "message": "Invalid email format",
  "details": {
    "field": "email"
  },
  "path": "/api/users/me"
}
```

**Email Already In Use**:
```json
{
  "error": "VALIDATION_ERROR",
  "message": "Email address is already in use",
  "details": {
    "field": "email"
  },
  "path": "/api/users/me"
}
```

---

## Quota Limits

### Tier Comparison

| Feature | Free | Pro | Enterprise |
|---------|------|-----|------------|
| Max Agents | 10 | Unlimited | Unlimited |
| Max Deployments | 2 | 10 | Unlimited |
| AI Tokens/Day | 50,000 | 500,000 | Unlimited |
| Integrations | 3 | 10 | Unlimited |

**Note**: `-1` in quota_limits indicates unlimited.

### Quota Monitoring

Use the `/me/stats` endpoint to monitor quota usage:

```javascript
const stats = await getUserStats();

// Check each quota
Object.entries(stats.quota_usage).forEach(([resource, usage]) => {
  const percentage = usage.percentage;

  if (percentage >= 100) {
    console.error(`❌ ${resource} quota exceeded!`);
  } else if (percentage >= 80) {
    console.warn(`⚠️ ${resource} quota at ${percentage.toFixed(1)}%`);
  } else if (percentage >= 50) {
    console.info(`ℹ️ ${resource} quota at ${percentage.toFixed(1)}%`);
  }
});
```

---

## Caching

### Cache Strategy

| Endpoint | Cache Duration | Cache Key |
|----------|---------------|-----------|
| GET /me/stats | 5 minutes | `user:{user_id}:stats` |
| PUT /me | N/A | Invalidates stats cache |
| DELETE /me | N/A | Deletes all user caches |

### Cache Invalidation

Cache is automatically invalidated on:
- Profile updates (PUT /me)
- Account deletion (DELETE /me)
- Agent creation/update/deletion (affects stats)

---

## Testing

### Test Scenarios

**1. View Statistics**:
```bash
TOKEN="your_jwt_token"

# Get stats
curl -X GET http://localhost:8000/api/users/me/stats \
  -H "Authorization: Bearer $TOKEN" | jq

# Check specific quota
curl -X GET http://localhost:8000/api/users/me/stats \
  -H "Authorization: Bearer $TOKEN" | \
  jq '.quota_usage.agents.percentage'
```

**2. Update Email**:
```bash
# Update to new email
curl -X PUT http://localhost:8000/api/users/me \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newemail@example.com"
  }' | jq

# Verify update by getting stats again
curl -X GET http://localhost:8000/api/users/me/stats \
  -H "Authorization: Bearer $TOKEN" | jq '.email'
```

**3. Test Email Validation**:
```bash
# Invalid email (should fail)
curl -X PUT http://localhost:8000/api/users/me \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "invalid-email"
  }'
# Should return 422 VALIDATION_ERROR
```

**4. Test Duplicate Email**:
```bash
# Try to use another user's email (should fail)
curl -X PUT http://localhost:8000/api/users/me \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "existing@example.com"
  }'
# Should return 422 VALIDATION_ERROR
```

**5. Test Account Deletion**:
```bash
# Create test user first
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "deletetest@example.com",
    "password": "testpassword123"
  }'

# Login to get token
RESPONSE=$(curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "deletetest@example.com",
    "password": "testpassword123"
  }')

TOKEN=$(echo $RESPONSE | jq -r '.access_token')

# Delete account
curl -X DELETE http://localhost:8000/api/users/me \
  -H "Authorization: Bearer $TOKEN" | jq

# Try to use deleted account (should fail)
curl -X GET http://localhost:8000/api/users/me/stats \
  -H "Authorization: Bearer $TOKEN"
# Should return 401 AUTHENTICATION_FAILED
```

**6. Test Stats Caching**:
```bash
# First request (cache miss)
time curl -X GET http://localhost:8000/api/users/me/stats \
  -H "Authorization: Bearer $TOKEN"

# Second request (cache hit - should be faster)
time curl -X GET http://localhost:8000/api/users/me/stats \
  -H "Authorization: Bearer $TOKEN"

# Update profile to invalidate cache
curl -X PUT http://localhost:8000/api/users/me \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"email": "updated@example.com"}'

# Third request (cache miss again due to invalidation)
time curl -X GET http://localhost:8000/api/users/me/stats \
  -H "Authorization: Bearer $TOKEN"
```

---

## GDPR Compliance

### Right to Erasure (Article 17)

The `DELETE /api/users/me` endpoint implements GDPR's "Right to Erasure" (also known as "Right to be Forgotten").

**What gets deleted**:
- ✅ Personal data (email, password)
- ✅ User-generated content (agents, code)
- ✅ Usage data (token usage, execution logs)
- ✅ OAuth tokens and API keys
- ✅ Session data (Redis)
- ✅ Cached data (Redis)

**Audit Trail**:
- Deletion is logged with `event_type: "account_deleted"`
- Includes user_id, email, and resources count
- Severity: "warning" (permanent action)
- Stored for compliance reporting

**Implementation**:
```python
# Cascade deletion via SQLAlchemy relationships
await db.delete(current_user)  # Deletes:
    # - User record
    # - All agents (cascade)
    # - All deployments (cascade)
    # - All integrations (cascade)
    # - All token_usage records (cascade)
    # - All execution_logs (cascade)

# Manual cleanup
await redis_service.delete_session(user_id)
await redis_service.cache_delete(f"user:{user_id}:stats")
await redis_service.cache_delete(f"user:{user_id}:agents:list")
```

**User Notification**:
Frontend should display clear warnings:
```
⚠️ WARNING: This action cannot be undone!

Deleting your account will permanently remove:
- Your profile and settings
- All AI agents (5 agents)
- All deployments (2 deployments)
- All integrations (2 integrations)
- All usage history

Are you absolutely sure?
[ Cancel ]  [ Delete My Account ]
```

---

## References

- [AUTH_API.md](./AUTH_API.md) - Authentication API documentation
- [AGENT_API.md](./AGENT_API.md) - Agent API documentation
- [LOGGING_ERROR_HANDLING.md](./LOGGING_ERROR_HANDLING.md) - Logging and error handling guide
- [GDPR Article 17](https://gdpr-info.eu/art-17-gdpr/) - Right to Erasure

---

## Changelog

### Version 1.0.0 (2025-12-09)
- Initial user profile API implementation
- GET /me/stats endpoint with comprehensive statistics
- PUT /me endpoint for email updates
- DELETE /me endpoint for GDPR-compliant account deletion
- Redis caching (5-minute TTL for stats)
- Quota tracking and percentage calculations
- Audit logging for all profile operations
- Cascade deletion of all user data
