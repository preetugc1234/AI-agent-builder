# Row-Level Security (RLS) Documentation

## Overview

NodeRush implements **application-level row-level security** to ensure complete data isolation between users. Each user can only access their own data across all endpoints.

**Security Model**:
- Users can only view/modify their own resources
- All queries filter by `user_id`
- Foreign key cascades ensure cleanup
- Audit logging tracks all access attempts

---

## Table of Contents

1. [Security Architecture](#security-architecture)
2. [Implementation Strategy](#implementation-strategy)
3. [Protected Resources](#protected-resources)
4. [Code Examples](#code-examples)
5. [Testing RLS](#testing-rls)
6. [Database Constraints](#database-constraints)

---

## Security Architecture

### Multi-Layer Security

```
Layer 1: Authentication
  ├─ JWT token validation
  ├─ Session verification (Redis)
  └─ User extraction from token

Layer 2: Authorization
  ├─ Permission checks (tier-based)
  └─ Resource ownership verification

Layer 3: Row-Level Security ← We implement this
  ├─ Filter by user_id in all queries
  ├─ Ownership checks before mutations
  └─ Cascade delete on user deletion

Layer 4: Database Constraints
  ├─ Foreign key constraints
  ├─ Unique constraints
  └─ NOT NULL constraints
```

---

## Implementation Strategy

### Application-Level RLS

We implement RLS at the **application level** rather than database level because:

1. **Flexibility**: Can implement complex business logic
2. **Compatibility**: Works with any database (PostgreSQL, MySQL, SQLite)
3. **Performance**: Single query with JOIN instead of subquery per policy
4. **Auditability**: Can log all access attempts
5. **Testing**: Easier to test and debug

### Pattern

**All queries follow this pattern**:

```python
# SELECT queries - Filter by user_id
result = await db.execute(
    select(Resource).where(
        and_(
            Resource.id == resource_id,
            Resource.user_id == current_user.id  # ← RLS enforcement
        )
    )
)

# INSERT queries - Set user_id
new_resource = Resource(
    user_id=current_user.id,  # ← RLS enforcement
    # ... other fields
)

# UPDATE/DELETE queries - Check ownership first
resource = await db.get(Resource, resource_id)
if resource.user_id != current_user.id:  # ← RLS enforcement
    raise AuthorizationError("Access denied")
```

---

## Protected Resources

### Direct User Ownership

These tables have a `user_id` column that directly identifies the owner:

| Table | Owner Field | RLS Implementation |
|-------|-------------|-------------------|
| `users` | `id` | Users can only access their own profile |
| `agents` | `user_id` | Users can only access their own agents |
| `user_integrations` | `user_id` | Users can only access their own integrations |
| `token_usage` | `user_id` | Users can only view their own token usage |
| `security_logs` | `user_id` | Users can only view their own security logs |
| `rate_limits` | `user_id` | Users can only view their own rate limits |

### Indirect User Ownership (via Foreign Keys)

These tables are owned indirectly through the `agents` table:

| Table | Ownership Chain | RLS Implementation |
|-------|----------------|-------------------|
| `deployments` | `agent_id` → `agents.user_id` | Check agent ownership first |
| `execution_logs` | `agent_id` → `agents.user_id` | Check agent ownership first |

---

## Code Examples

### Example 1: Direct User Ownership (Agents)

**File**: `backend/app/api/agents.py`

```python
@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # RLS: Filter by user_id
    result = await db.execute(
        select(Agent).where(
            Agent.id == agent_id,
            Agent.user_id == current_user.id  # ← Row-level security
        )
    )
    agent = result.scalar_one_or_none()

    if not agent:
        raise ResourceNotFoundError("Agent", str(agent_id))

    return agent
```

**Security**: User can only retrieve their own agents. If they try to access another user's agent, it returns 404 (not found) instead of 403 (forbidden) to prevent information leakage.

### Example 2: Agent Creation

```python
@router.post("/", response_model=AgentResponse)
async def create_agent(
    agent_data: AgentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # RLS: Set user_id from authenticated user
    new_agent = Agent(
        user_id=current_user.id,  # ← Row-level security
        name=agent_data.name,
        description=agent_data.description,
        vibe_prompt=agent_data.vibe_prompt,
        status="draft"
    )

    db.add(new_agent)
    await db.commit()

    return new_agent
```

**Security**: User cannot create agents for other users. The `user_id` is always set from the authenticated token.

### Example 3: Indirect Ownership (Deployments)

```python
@router.get("/deployments/{deployment_id}")
async def get_deployment(
    deployment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # RLS: Join with agents table to verify ownership
    result = await db.execute(
        select(Deployment)
        .join(Agent, Deployment.agent_id == Agent.id)
        .where(
            and_(
                Deployment.id == deployment_id,
                Agent.user_id == current_user.id  # ← Row-level security via JOIN
            )
        )
    )
    deployment = result.scalar_one_or_none()

    if not deployment:
        raise ResourceNotFoundError("Deployment", str(deployment_id))

    return deployment
```

**Security**: User can only access deployments for their own agents. Ownership is verified via JOIN with the agents table.

### Example 4: List with RLS

```python
@router.get("/", response_model=List[AgentResponse])
async def list_agents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # RLS: Filter all results by user_id
    result = await db.execute(
        select(Agent)
        .where(Agent.user_id == current_user.id)  # ← Row-level security
        .order_by(Agent.created_at.desc())
    )
    agents = result.scalars().all()

    return agents
```

**Security**: User only sees their own agents in the list. No other user's data is exposed.

---

## Testing RLS

### Manual Testing

**Test 1: User A Cannot Access User B's Agent**

```bash
# User A creates an agent
USER_A_TOKEN="token_for_user_a"
AGENT_RESPONSE=$(curl -X POST http://localhost:8000/api/agents/ \
  -H "Authorization: Bearer $USER_A_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "User A Agent",
    "vibe_prompt": "Create a test agent"
  }')

AGENT_ID=$(echo $AGENT_RESPONSE | jq -r '.id')

# User B tries to access User A's agent
USER_B_TOKEN="token_for_user_b"
curl -X GET http://localhost:8000/api/agents/$AGENT_ID \
  -H "Authorization: Bearer $USER_B_TOKEN"

# Expected: 404 Not Found (agent not visible to User B)
```

**Test 2: User Cannot Modify Another User's Agent**

```bash
# User B tries to update User A's agent
curl -X PUT http://localhost:8000/api/agents/$AGENT_ID \
  -H "Authorization: Bearer $USER_B_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Hacked Agent"
  }'

# Expected: 404 Not Found
```

**Test 3: User Can Only See Their Own Agents**

```bash
# User A creates 3 agents
# User B creates 2 agents

# User A lists agents
curl -X GET http://localhost:8000/api/agents/ \
  -H "Authorization: Bearer $USER_A_TOKEN" | jq 'length'

# Expected: 3 (only User A's agents)

# User B lists agents
curl -X GET http://localhost:8000/api/agents/ \
  -H "Authorization: Bearer $USER_B_TOKEN" | jq 'length'

# Expected: 2 (only User B's agents)
```

### Automated Testing

```python
import pytest
from app.models.models import User, Agent
from app.core.exceptions import ResourceNotFoundError

@pytest.mark.asyncio
async def test_user_cannot_access_other_user_agent(db_session):
    """Test that User A cannot access User B's agent"""
    # Create User A and their agent
    user_a = User(email="usera@example.com", password_hash="hash")
    db_session.add(user_a)
    await db_session.flush()

    agent_a = Agent(
        user_id=user_a.id,
        name="User A Agent",
        vibe_prompt="Test"
    )
    db_session.add(agent_a)
    await db_session.flush()

    # Create User B
    user_b = User(email="userb@example.com", password_hash="hash")
    db_session.add(user_b)
    await db_session.flush()

    # User B tries to query User A's agent
    result = await db_session.execute(
        select(Agent).where(
            and_(
                Agent.id == agent_a.id,
                Agent.user_id == user_b.id  # RLS check
            )
        )
    )
    agent = result.scalar_one_or_none()

    # Agent should not be found
    assert agent is None
```

---

## Database Constraints

### Foreign Key Cascades

All child tables have CASCADE delete to ensure cleanup:

```sql
-- Agents cascade to deployments and execution logs
CREATE TABLE deployments (
    id UUID PRIMARY KEY,
    agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
    -- ...
);

CREATE TABLE execution_logs (
    id UUID PRIMARY KEY,
    agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
    -- ...
);

-- Users cascade to all user-owned data
CREATE TABLE agents (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    -- ...
);

CREATE TABLE user_integrations (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    -- ...
);
```

**Benefit**: When a user is deleted, all their data is automatically deleted via cascade.

### Indexes for Performance

All tables with RLS have indexes on `user_id` for fast filtering:

```sql
CREATE INDEX idx_agents_user_id ON agents(user_id);
CREATE INDEX idx_user_integrations_user_id ON user_integrations(user_id);
CREATE INDEX idx_token_usage_user_id ON token_usage(user_id);
CREATE INDEX idx_security_logs_user_id ON security_logs(user_id);
```

**Benefit**: Fast queries when filtering by `user_id`.

---

## Security Audit Checklist

Use this checklist to verify RLS is properly implemented:

### Endpoint Review

- [ ] Does the endpoint require authentication (`Depends(get_current_user)`)?
- [ ] Are SELECT queries filtered by `user_id`?
- [ ] Are INSERT queries setting `user_id` from `current_user.id`?
- [ ] Are UPDATE/DELETE queries checking ownership first?
- [ ] Does the endpoint log unauthorized access attempts?
- [ ] Does the endpoint return 404 (not 403) for unauthorized access?

### Database Review

- [ ] Do all user-owned tables have a `user_id` column?
- [ ] Do all `user_id` columns have foreign key constraints?
- [ ] Are cascade deletes configured correctly?
- [ ] Are there indexes on `user_id` columns for performance?

### Testing Review

- [ ] Are there tests for cross-user access attempts?
- [ ] Are there tests for ownership verification?
- [ ] Are there tests for cascade deletion?

---

## Common Pitfalls

### ❌ Don't: Query without user_id filter

```python
# BAD: Returns all agents (data leak!)
result = await db.execute(select(Agent).where(Agent.id == agent_id))
```

### ✅ Do: Always filter by user_id

```python
# GOOD: Only returns agent if user owns it
result = await db.execute(
    select(Agent).where(
        Agent.id == agent_id,
        Agent.user_id == current_user.id
    )
)
```

### ❌ Don't: Set user_id from request body

```python
# BAD: User can set any user_id!
new_agent = Agent(
    user_id=agent_data.user_id,  # ← Security vulnerability!
    name=agent_data.name
)
```

### ✅ Do: Set user_id from authenticated user

```python
# GOOD: user_id always comes from token
new_agent = Agent(
    user_id=current_user.id,  # ← From JWT token
    name=agent_data.name
)
```

### ❌ Don't: Return 403 for missing resources

```python
# BAD: Leaks information (agent exists but user doesn't own it)
if agent and agent.user_id != current_user.id:
    raise HTTPException(status_code=403, detail="Forbidden")
```

### ✅ Do: Return 404 for missing resources

```python
# GOOD: Same error whether agent doesn't exist or user doesn't own it
if not agent:
    raise ResourceNotFoundError("Agent", str(agent_id))
```

---

## Benefits of Application-Level RLS

1. **Simplicity**: Easy to understand and maintain
2. **Performance**: Single query with JOIN vs multiple policy checks
3. **Flexibility**: Can implement complex business logic
4. **Debugging**: Easy to trace with logging
5. **Testability**: Can mock authentication in tests
6. **Portability**: Works with any database
7. **Audit Trail**: Can log all access attempts

---

## References

- [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [SQLAlchemy Security](https://docs.sqlalchemy.org/en/14/faq/security.html)

---

## Changelog

### Version 1.0.0 (2025-12-09)
- Initial RLS documentation
- Application-level RLS implementation
- Security patterns and examples
- Testing guidelines
- Common pitfalls guide
