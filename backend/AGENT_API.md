# Agent API Documentation

## Overview

NodeRush agent management API for creating, managing, and generating AI agents.

**Base URL**: `/api/agents`

**Features**:
- CRUD operations for AI agents
- 3-agent workflow (Architect → Code Generator → Code Reviewer)
- Quota management (free tier: max 10 agents)
- Redis caching for performance
- Comprehensive audit logging
- Structured error handling

---

## Table of Contents

1. [Agent Workflow](#agent-workflow)
2. [Endpoints](#endpoints)
3. [Request/Response Examples](#requestresponse-examples)
4. [Error Handling](#error-handling)
5. [Quotas & Limits](#quotas--limits)
6. [Caching](#caching)
7. [Testing](#testing)

---

## Agent Workflow

### Standard Flow

```
1. User creates agent: POST /api/agents
   ↓
2. Agent saved with status "draft"
   ↓
3. User triggers generation: POST /api/agents/{id}/generate-code
   ↓
4. Status changes to "generating"
   ↓
5. 3-agent workflow executes:
   - Architect: Designs architecture
   - Code Generator: Generates code
   - Code Reviewer: Reviews and refines
   ↓
6. Agent updated with results, status "ready"
```

### Quick Flow (Convenience Endpoint)

```
1. User creates and generates: POST /api/agents/generate
   ↓
2. Agent created with status "generating"
   ↓
3. 3-agent workflow executes immediately
   ↓
4. Returns complete agent with code
```

---

## Endpoints

### 1. Create Agent

**POST** `/api/agents/`

Create a new agent without triggering code generation.

**Headers**:
```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Request Body**:
```json
{
  "name": "Email Bot",
  "description": "Automated email response agent",
  "vibe_prompt": "Create an agent that reads emails from Gmail and sends automated responses based on the content"
}
```

**Validation**:
- Name: Required, max 100 characters
- Vibe prompt: Required, max 5000 characters
- Description: Optional

**Response** (201 Created):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user-123",
  "name": "Email Bot",
  "description": "Automated email response agent",
  "vibe_prompt": "Create an agent that reads emails...",
  "status": "draft",
  "architecture": null,
  "generated_code": null,
  "review_notes": null,
  "final_code": null,
  "file_structure": {},
  "integrations": [],
  "flow_data": {},
  "created_at": "2025-12-09T10:30:00Z",
  "updated_at": "2025-12-09T10:30:00Z"
}
```

**Errors**:
- `422 VALIDATION_ERROR`: Invalid name or vibe prompt
- `429 QUOTA_EXCEEDED`: Max 10 agents reached (free tier)

**Quota Check**: Yes (free tier: max 10 agents)

**Audit Event**: `resource_created`

---

### 2. List Agents

**GET** `/api/agents/`

Get all agents for the current user, ordered by creation date (newest first).

**Headers**:
```
Authorization: Bearer <jwt_token>
```

**Response** (200 OK):
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "user-123",
    "name": "Email Bot",
    "description": "Automated email response agent",
    "status": "ready",
    "created_at": "2025-12-09T10:30:00Z",
    "updated_at": "2025-12-09T10:45:00Z"
  },
  {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "user_id": "user-123",
    "name": "Slack Notifier",
    "description": "Send notifications to Slack",
    "status": "draft",
    "created_at": "2025-12-08T15:20:00Z",
    "updated_at": "2025-12-08T15:20:00Z"
  }
]
```

**Caching**: Results cached in Redis for 5 minutes

---

### 3. Get Agent

**GET** `/api/agents/{agent_id}`

Get a specific agent by ID.

**Headers**:
```
Authorization: Bearer <jwt_token>
```

**Response** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user-123",
  "name": "Email Bot",
  "description": "Automated email response agent",
  "vibe_prompt": "Create an agent that reads emails...",
  "status": "ready",
  "architecture": "{\n  \"agent_type\": \"email_processor\",\n  \"components\": [...]\n}",
  "generated_code": "import os\nfrom langchain...",
  "review_notes": "Code looks good. Added error handling...",
  "final_code": "import os\nimport logging\nfrom langchain...",
  "file_structure": {
    "main.py": "import os...",
    "requirements.txt": "langchain\nopenai..."
  },
  "integrations": ["gmail", "openai"],
  "flow_data": {},
  "created_at": "2025-12-09T10:30:00Z",
  "updated_at": "2025-12-09T10:45:00Z"
}
```

**Errors**:
- `404 RESOURCE_NOT_FOUND`: Agent not found
- `403 AUTHORIZATION_ERROR`: Agent belongs to another user

**Caching**: Results cached in Redis for 10 minutes

---

### 4. Update Agent

**PUT** `/api/agents/{agent_id}`

Update an existing agent. Only provided fields are updated.

**Headers**:
```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Request Body** (all fields optional):
```json
{
  "name": "Email Bot Pro",
  "description": "Advanced email response agent with ML",
  "vibe_prompt": "Create an agent that reads emails and uses ML to generate contextual responses",
  "status": "draft"
}
```

**Validation**:
- Name: Max 100 characters (if provided)
- Vibe prompt: Max 5000 characters (if provided)
- Status: One of "draft", "generating", "ready", "error"

**Response** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Email Bot Pro",
  "description": "Advanced email response agent with ML",
  "vibe_prompt": "Create an agent that reads emails and uses ML...",
  "status": "draft",
  ...
}
```

**Errors**:
- `404 RESOURCE_NOT_FOUND`: Agent not found
- `422 VALIDATION_ERROR`: Invalid field value

**Cache Invalidation**: Clears agent cache and user's agent list cache

**Audit Event**: `resource_updated`

---

### 5. Delete Agent

**DELETE** `/api/agents/{agent_id}`

Delete an agent permanently.

**Headers**:
```
Authorization: Bearer <jwt_token>
```

**Response** (204 No Content):
```
(empty response)
```

**Errors**:
- `404 RESOURCE_NOT_FOUND`: Agent not found

**Note**: Free tier users cannot delete agents (requires `delete:agents` permission). Free tier users should update status to "archived" instead.

**Cache Invalidation**: Clears agent cache and user's agent list cache

**Audit Event**: `resource_deleted`

---

### 6. Generate Code (Existing Agent)

**POST** `/api/agents/{agent_id}/generate-code`

Trigger AI code generation for an existing agent using the 3-agent workflow.

**Headers**:
```
Authorization: Bearer <jwt_token>
```

**Process**:
1. Sets agent status to "generating"
2. Runs 3-agent workflow:
   - **Architect Agent**: Analyzes vibe prompt, designs architecture
   - **Code Generator Agent**: Generates code based on architecture
   - **Code Reviewer Agent**: Reviews code, adds improvements
3. Updates agent with all results
4. Sets status to "ready" (or "error" on failure)

**Response** (200 OK):
```json
{
  "message": "Code generation completed",
  "agent_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "ready",
  "file_structure": {
    "main.py": "import os...",
    "requirements.txt": "langchain\nopenai...",
    "README.md": "# Email Bot..."
  },
  "integrations": ["gmail", "openai"]
}
```

**Errors**:
- `404 RESOURCE_NOT_FOUND`: Agent not found
- `500 AI_GENERATION_ERROR`: AI generation failed

**Cache Invalidation**: Clears agent cache and user's agent list cache

**Audit Events**:
- `agent_generation_success` (on success)
- `agent_generation_failed` (on failure)

**Note**: This is a long-running operation. Consider using WebSocket for real-time updates in production.

---

### 7. Generate New Agent (Convenience)

**POST** `/api/agents/generate`

Create a new agent and run code generation in one call.

**Headers**:
```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Request Body**:
```json
{
  "name": "Email Bot",
  "description": "Automated email response agent",
  "vibe_prompt": "Create an agent that reads emails from Gmail and sends automated responses based on the content"
}
```

**Validation**:
- Name: Required, max 100 characters
- Vibe prompt: Required, max 5000 characters
- Description: Optional

**Response** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Email Bot",
  "status": "ready",
  "architecture": "{\n  \"agent_type\": \"email_processor\"...",
  "generated_code": "import os\nfrom langchain...",
  "review_notes": "Code looks good. Added error handling...",
  "final_code": "import os\nimport logging\nfrom langchain...",
  "file_structure": {
    "main.py": "import os...",
    "requirements.txt": "langchain\nopenai..."
  },
  "integrations": ["gmail", "openai"]
}
```

**Errors**:
- `422 VALIDATION_ERROR`: Invalid name or vibe prompt
- `429 QUOTA_EXCEEDED`: Max 10 agents reached (free tier)
- `500 AI_GENERATION_ERROR`: AI generation failed

**Quota Check**: Yes (free tier: max 10 agents)

**Audit Events**:
- `resource_created`
- `agent_generation_success` / `agent_generation_failed`

**Note**: This combines agent creation and code generation. If generation fails, the agent is created with status "error".

---

## Request/Response Examples

### cURL Examples

#### Create Agent
```bash
curl -X POST http://localhost:8000/api/agents/ \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Email Bot",
    "description": "Automated email response agent",
    "vibe_prompt": "Create an agent that reads emails from Gmail and sends automated responses"
  }'
```

#### List Agents
```bash
curl -X GET http://localhost:8000/api/agents/ \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

#### Get Agent
```bash
curl -X GET http://localhost:8000/api/agents/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

#### Update Agent
```bash
curl -X PUT http://localhost:8000/api/agents/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Email Bot Pro",
    "status": "draft"
  }'
```

#### Delete Agent
```bash
curl -X DELETE http://localhost:8000/api/agents/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

#### Generate Code (Existing Agent)
```bash
curl -X POST http://localhost:8000/api/agents/550e8400-e29b-41d4-a716-446655440000/generate-code \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

#### Generate New Agent
```bash
curl -X POST http://localhost:8000/api/agents/generate \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Slack Notifier",
    "vibe_prompt": "Create an agent that sends notifications to Slack when specific events occur"
  }'
```

### Python Examples

```python
import requests

BASE_URL = "http://localhost:8000/api/agents"
TOKEN = "your_jwt_token_here"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Create Agent
response = requests.post(f"{BASE_URL}/", headers=HEADERS, json={
    "name": "Email Bot",
    "description": "Automated email response agent",
    "vibe_prompt": "Create an agent that reads emails from Gmail..."
})
agent = response.json()
agent_id = agent["id"]

# List Agents
response = requests.get(f"{BASE_URL}/", headers=HEADERS)
agents = response.json()

# Get Agent
response = requests.get(f"{BASE_URL}/{agent_id}", headers=HEADERS)
agent = response.json()

# Update Agent
response = requests.put(f"{BASE_URL}/{agent_id}", headers=HEADERS, json={
    "name": "Email Bot Pro"
})

# Delete Agent
response = requests.delete(f"{BASE_URL}/{agent_id}", headers=HEADERS)

# Generate Code
response = requests.post(
    f"{BASE_URL}/{agent_id}/generate-code",
    headers=HEADERS
)
result = response.json()

# Generate New Agent (Convenience)
response = requests.post(f"{BASE_URL}/generate", headers=HEADERS, json={
    "name": "Slack Notifier",
    "vibe_prompt": "Create an agent that sends notifications to Slack..."
})
agent = response.json()
```

### JavaScript Examples

```javascript
const BASE_URL = "http://localhost:8000/api/agents";
const token = localStorage.getItem("auth_token");
const headers = {
  "Authorization": `Bearer ${token}`,
  "Content-Type": "application/json"
};

// Create Agent
const createAgent = async () => {
  const response = await fetch(`${BASE_URL}/`, {
    method: "POST",
    headers,
    body: JSON.stringify({
      name: "Email Bot",
      description: "Automated email response agent",
      vibe_prompt: "Create an agent that reads emails from Gmail..."
    })
  });
  return response.json();
};

// List Agents
const listAgents = async () => {
  const response = await fetch(`${BASE_URL}/`, { headers });
  return response.json();
};

// Get Agent
const getAgent = async (agentId) => {
  const response = await fetch(`${BASE_URL}/${agentId}`, { headers });
  return response.json();
};

// Update Agent
const updateAgent = async (agentId, updates) => {
  const response = await fetch(`${BASE_URL}/${agentId}`, {
    method: "PUT",
    headers,
    body: JSON.stringify(updates)
  });
  return response.json();
};

// Delete Agent
const deleteAgent = async (agentId) => {
  await fetch(`${BASE_URL}/${agentId}`, {
    method: "DELETE",
    headers
  });
};

// Generate Code
const generateCode = async (agentId) => {
  const response = await fetch(`${BASE_URL}/${agentId}/generate-code`, {
    method: "POST",
    headers
  });
  return response.json();
};

// Generate New Agent
const generateNewAgent = async () => {
  const response = await fetch(`${BASE_URL}/generate`, {
    method: "POST",
    headers,
    body: JSON.stringify({
      name: "Slack Notifier",
      vibe_prompt: "Create an agent that sends notifications to Slack..."
    })
  });
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
    "field": "specific details"
  },
  "path": "/api/agents",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Common Error Codes

| Code | Status | Description |
|------|--------|-------------|
| `RESOURCE_NOT_FOUND` | 404 | Agent not found |
| `AUTHORIZATION_ERROR` | 403 | No access to this agent |
| `VALIDATION_ERROR` | 422 | Invalid input data |
| `QUOTA_EXCEEDED` | 429 | Max agents reached (free tier) |
| `AI_GENERATION_ERROR` | 500 | AI generation failed |

### Error Examples

**Agent Not Found**:
```json
{
  "error": "RESOURCE_NOT_FOUND",
  "message": "Agent with ID '550e8400-e29b-41d4-a716-446655440000' not found",
  "details": {},
  "path": "/api/agents/550e8400-e29b-41d4-a716-446655440000"
}
```

**Quota Exceeded**:
```json
{
  "error": "QUOTA_EXCEEDED",
  "message": "Quota exceeded for Total agents",
  "details": {
    "quota_type": "Total agents",
    "limit": 10,
    "current": 10
  },
  "path": "/api/agents/"
}
```

**Validation Error**:
```json
{
  "error": "VALIDATION_ERROR",
  "message": "Agent name must be 100 characters or less",
  "details": {
    "field": "name"
  },
  "path": "/api/agents/"
}
```

**AI Generation Error**:
```json
{
  "error": "AI_GENERATION_ERROR",
  "message": "Code generation failed: API key invalid",
  "details": {
    "agent_type": "code_generator",
    "original_error": "API key invalid"
  },
  "path": "/api/agents/550e8400-e29b-41d4-a716-446655440000/generate-code"
}
```

---

## Quotas & Limits

### Free Tier Limits

```python
FREE_TIER_LIMITS = {
    'agents': {
        'max_total': 10,              # Max 10 agents total
        'create_per_hour': 5,          # Max 5 new agents per hour
        'create_per_day': 20,          # Max 20 new agents per day
    }
}
```

### Quota Enforcement

- **Agent Creation**: Checked on `POST /api/agents/` and `POST /api/agents/generate`
- **Agent Update**: No quota check (free operation)
- **Agent Deletion**: No quota check (free operation for pro/enterprise)
- **Code Generation**: No quota check (limited by agent creation quota)

### Upgrading Tiers

| Tier | Max Agents | Delete Permission |
|------|-----------|-------------------|
| Free | 10 | No |
| Pro | Unlimited | Yes |
| Enterprise | Unlimited | Yes |

---

## Caching

### Cache Strategy

| Endpoint | Cache Duration | Cache Key |
|----------|---------------|-----------|
| List Agents | 5 minutes | `user:{user_id}:agents:list` |
| Get Agent | 10 minutes | `agent:{agent_id}` |
| Create Agent | N/A | Invalidates list cache |
| Update Agent | N/A | Invalidates agent + list cache |
| Delete Agent | N/A | Invalidates agent + list cache |
| Generate Code | N/A | Invalidates agent + list cache |

### Cache Invalidation

Cache is automatically invalidated on:
- Agent creation
- Agent update
- Agent deletion
- Code generation completion

### Manual Cache Clear

If you need to manually clear cache:

```python
from app.services.redis_service import redis_service

# Clear specific agent
await redis_service.cache_delete(f"agent:{agent_id}")

# Clear user's agent list
await redis_service.cache_delete(f"user:{user_id}:agents:list")
```

---

## Testing

### Test Scenarios

**1. Create Agent and Generate Code**:
```bash
# Step 1: Create agent
TOKEN="your_jwt_token"
curl -X POST http://localhost:8000/api/agents/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Agent",
    "vibe_prompt": "Create a simple hello world agent"
  }' | jq

# Step 2: Extract agent_id from response
AGENT_ID="550e8400-e29b-41d4-a716-446655440000"

# Step 3: Generate code
curl -X POST http://localhost:8000/api/agents/$AGENT_ID/generate-code \
  -H "Authorization: Bearer $TOKEN" | jq
```

**2. Quick Generate (Convenience)**:
```bash
curl -X POST http://localhost:8000/api/agents/generate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Quick Agent",
    "vibe_prompt": "Create a simple weather bot"
  }' | jq
```

**3. List and Update**:
```bash
# List all agents
curl -X GET http://localhost:8000/api/agents/ \
  -H "Authorization: Bearer $TOKEN" | jq

# Update agent
curl -X PUT http://localhost:8000/api/agents/$AGENT_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Agent Name",
    "status": "draft"
  }' | jq
```

**4. Test Quota Limit**:
```bash
# Create 11 agents to trigger quota error
for i in {1..11}; do
  curl -X POST http://localhost:8000/api/agents/ \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
      \"name\": \"Test Agent $i\",
      \"vibe_prompt\": \"Test agent number $i\"
    }"
done
# The 11th request should return 429 QUOTA_EXCEEDED
```

**5. Test Caching**:
```bash
# First request (cache miss)
time curl -X GET http://localhost:8000/api/agents/ \
  -H "Authorization: Bearer $TOKEN"

# Second request (cache hit - should be faster)
time curl -X GET http://localhost:8000/api/agents/ \
  -H "Authorization: Bearer $TOKEN"
```

**6. Test Validation**:
```bash
# Empty name
curl -X POST http://localhost:8000/api/agents/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "",
    "vibe_prompt": "Test"
  }'
# Should return 422 VALIDATION_ERROR

# Name too long
curl -X POST http://localhost:8000/api/agents/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "'$(python3 -c 'print("A" * 101)')'",
    "vibe_prompt": "Test"
  }'
# Should return 422 VALIDATION_ERROR
```

---

## References

- [ARCHITECTURE.md](./ARCHITECTURE.md) - System architecture and design
- [AUTH_API.md](./AUTH_API.md) - Authentication API documentation
- [LOGGING_ERROR_HANDLING.md](./LOGGING_ERROR_HANDLING.md) - Logging and error handling guide
- [LangGraph Documentation](https://python.langchain.com/docs/langgraph) - 3-agent workflow framework

---

## Changelog

### Version 1.0.0 (2025-12-09)
- Initial agent API implementation
- CRUD endpoints with quota management
- 3-agent code generation workflow
- Redis caching for performance
- Structured logging and audit events
- Comprehensive error handling
- Free tier quota enforcement (max 10 agents)
- Validation for all inputs
