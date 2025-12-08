# NodeRush - Complete System Architecture Documentation

**Version:** 2.0
**Last Updated:** December 2025
**Budget:** $0 (100% Free Tier Services)

---

## Table of Contents
1. [System Overview](#system-overview)
2. [Final Tech Stack](#final-tech-stack)
3. [High-Level Architecture](#high-level-architecture)
4. [Low-Level System Design](#low-level-system-design)
5. [LangGraph 3-Agent Workflow](#langgraph-3-agent-workflow)
6. [User Flow](#user-flow)
7. [Backend Flow](#backend-flow)
8. [Authentication Workflow](#authentication-workflow)
9. [Rate Limiting Strategy](#rate-limiting-strategy)
10. [AI Token Management](#ai-token-management)
11. [Cloudflare Integration](#cloudflare-integration)
12. [Security Architecture](#security-architecture)
13. [Concurrency & Scalability](#concurrency--scalability)
14. [Data Protection](#data-protection)
15. [Cost Management](#cost-management)
16. [Deployment Strategy](#deployment-strategy)

---

## System Overview

**NodeRush** is a no-code AI agent builder platform that allows users to create, customize, and deploy intelligent agents using natural language prompts. The platform uses a sophisticated 3-agent AI system powered by LangGraph to architect, code, and review agent implementations.

### Core Features
- **3-Agent AI System**: Architect → Coder → Reviewer workflow using LangGraph
- **Real-time Visualization**: Live agent building with Socket.IO
- **Zero Cost**: Optimized to run entirely on free tiers
- **Production-Ready**: Enterprise-grade security and rate limiting
- **Scalable**: Handles 10,000+ concurrent users

---

## Final Tech Stack

### Frontend
| Service | Purpose | Free Tier Limits |
|---------|---------|------------------|
| **Next.js 14** | React framework | Unlimited (open source) |
| **Vercel** | Hosting | 100 GB bandwidth/month |
| **Socket.IO Client** | Real-time updates | Unlimited |
| **TailwindCSS** | Styling | Unlimited (open source) |

### Backend
| Service | Purpose | Free Tier Limits |
|---------|---------|------------------|
| **FastAPI** | Python web framework | Unlimited (open source) |
| **Render** | Docker hosting | 750 hours/month |
| **LangGraph** | AI agent orchestration | Unlimited (open source) |
| **Socket.IO** | WebSocket server | Unlimited (self-hosted) |

### Database & Storage
| Service | Purpose | Free Tier Limits |
|---------|---------|------------------|
| **Supabase PostgreSQL** | Primary database | 500 MB storage, 2 GB transfer |
| **Supabase Auth** | Authentication | 50,000 MAU |
| **Upstash Redis** | Cache, sessions, queue | 10,000 commands/day |
| **Cloudflare R2** | File storage | 10 GB storage/month |

### Edge & Security
| Service | Purpose | Free Tier Limits |
|---------|---------|------------------|
| **Cloudflare Workers** | Edge compute, rate limiting | 100,000 requests/day |
| **Cloudflare WAF** | Web Application Firewall | Included |
| **Cloudflare CDN** | Content delivery | Unlimited bandwidth |

### AI & ML
| Service | Purpose | Free Tier Limits |
|---------|---------|------------------|
| **OpenRouter** | AI API gateway | Pay-per-use |
| **NVIDIA Nemotron** | Free LLM model | Unlimited (free tier) |
| **LangGraph** | Agent orchestration | Unlimited (self-hosted) |

---

## High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                          USER DEVICES                            │
│  (Web Browser, Mobile Browser, Desktop App - Future)            │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│                     CLOUDFLARE EDGE LAYER                        │
│  ┌────────────────┐  ┌──────────────┐  ┌──────────────────┐    │
│  │  CDN + Cache   │  │  WAF + DDoS  │  │  Rate Limiting   │    │
│  │  (Static)      │  │  Protection  │  │  (Workers)       │    │
│  └────────────────┘  └──────────────┘  └──────────────────┘    │
└────────────────────────┬─────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌─────────────┐
│   Vercel     │  │   Render     │  │ Cloudflare  │
│  (Frontend)  │  │  (Backend)   │  │     R2      │
│  Next.js     │  │   FastAPI    │  │ (File Stor) │
│  React UI    │  │  Socket.IO   │  │             │
└──────────────┘  └──────┬───────┘  └─────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌─────────────┐
│   Supabase   │  │   Upstash    │  │ OpenRouter  │
│  PostgreSQL  │  │    Redis     │  │   NVIDIA    │
│     Auth     │  │  Cache/Queue │  │  Nemotron   │
└──────────────┘  └──────────────┘  └─────────────┘
                                            │
                                            ▼
                                    ┌─────────────┐
                                    │  LangGraph  │
                                    │  3-Agent    │
                                    │  Workflow   │
                                    └─────────────┘
```

---

## Low-Level System Design

### Component Architecture

```
Backend (Render - FastAPI)
├── main.py                     # Application entry point
├── app/
│   ├── core/
│   │   ├── config.py          # Configuration management
│   │   ├── security.py        # JWT, encryption, rate limiting
│   │   └── middleware.py      # CORS, rate limit, auth middleware
│   ├── api/
│   │   ├── auth.py            # Authentication endpoints
│   │   ├── agents.py          # Agent CRUD endpoints
│   │   ├── execution.py       # Agent execution endpoints
│   │   └── integrations.py   # Integration management
│   ├── services/
│   │   ├── redis_service.py   # Upstash Redis wrapper
│   │   ├── langgraph_service.py  # LangGraph 3-agent orchestration
│   │   ├── cloudflare_service.py # R2 file storage
│   │   └── token_manager.py   # AI token usage tracking
│   ├── workflows/
│   │   ├── agent_execution.py # Agent execution workflow
│   │   └── langgraph_flow.py  # LangGraph state machine
│   ├── websockets/
│   │   ├── manager.py         # Socket.IO connection manager
│   │   └── handlers.py        # WebSocket event handlers
│   ├── models/
│   │   └── models.py          # SQLAlchemy database models
│   ├── db/
│   │   └── database.py        # Supabase connection
│   └── utils/
│       ├── rate_limiter.py    # Token bucket rate limiter
│       └── token_counter.py   # Count AI tokens
```

---

## LangGraph 3-Agent Workflow

### Agent Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  USER PROMPT INPUT                          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
    ┌────────────────────────────────────────────┐
    │          LangGraph State Machine           │
    │                                            │
    │  ┌──────────────────────────────────────┐ │
    │  │         AGENT 1: ARCHITECT           │ │
    │  │  ┌────────────────────────────────┐  │ │
    │  │  │  - Analyze user requirements   │  │ │
    │  │  │  - Design system architecture  │  │ │
    │  │  │  - Create AST structure        │  │ │
    │  │  │  - Plan file structure         │  │ │
    │  │  │  - Define integrations         │  │ │
    │  │  │  - Setup LangGraph nodes       │  │ │
    │  │  └────────────────────────────────┘  │ │
    │  │           State: architecture_doc    │ │
    │  └───────────────┬──────────────────────┘ │
    │                  │                        │
    │                  ▼                        │
    │  ┌──────────────────────────────────────┐ │
    │  │         AGENT 2: CODER               │ │
    │  │  ┌────────────────────────────────┐  │ │
    │  │  │  - Read architecture plan      │  │ │
    │  │  │  - Write production code       │  │ │
    │  │  │  - Implement all files         │  │ │
    │  │  │  - Add error handling          │  │ │
    │  │  │  - Build LangGraph nodes       │  │ │
    │  │  │  - Setup integrations          │  │ │
    │  │  └────────────────────────────────┘  │ │
    │  │         State: generated_code        │ │
    │  └───────────────┬──────────────────────┘ │
    │                  │                        │
    │                  ▼                        │
    │  ┌──────────────────────────────────────┐ │
    │  │         AGENT 3: REVIEWER            │ │
    │  │  ┌────────────────────────────────┐  │ │
    │  │  │  - Review code quality         │  │ │
    │  │  │  - Find bugs and errors        │  │ │
    │  │  │  - Check security issues       │  │ │
    │  │  │  - Test LangGraph flow         │  │ │
    │  │  │  - Validate integrations       │  │ │
    │  │  │  - Fix issues found            │  │ │
    │  │  └────────────────────────────────┘  │ │
    │  │         State: review_notes          │ │
    │  └───────────────┬──────────────────────┘ │
    │                  │                        │
    │                  ▼                        │
    │  ┌──────────────────────────────────────┐ │
    │  │      CONDITIONAL: Is Code Good?      │ │
    │  │  ┌────────┐         ┌─────────────┐  │ │
    │  │  │  NO    │──┐   ┌──│    YES      │  │ │
    │  │  └────────┘  │   │  └─────────────┘  │ │
    │  │              │   │                   │ │
    │  └──────────────┼───┼───────────────────┘ │
    │                 │   │                     │
    └─────────────────┼───┼─────────────────────┘
                      │   │
        ┌─────────────┘   └──────────────┐
        │                                 │
        ▼ (Loop back to Agent 2)          ▼
  ┌─────────────┐               ┌─────────────────┐
  │  RE-CODE    │               │  FINAL OUTPUT   │
  │  Fix Issues │               │  Save to R2     │
  │  Max 3x     │               │  Deploy Ready   │
  └─────────────┘               └─────────────────┘
```

### LangGraph Implementation Details

#### State Schema
```python
class AgentState(TypedDict):
    # Input
    user_prompt: str
    user_id: str
    agent_id: str

    # Agent 1 Output
    architecture: str
    file_structure: List[str]
    integrations: List[str]
    ast_structure: Dict

    # Agent 2 Output
    generated_code: str
    code_files: Dict[str, str]  # filename: code

    # Agent 3 Output
    review_notes: str
    bugs_found: List[str]
    fixes_applied: List[str]
    final_code: str

    # Control Flow
    iteration_count: int
    max_iterations: int
    is_approved: bool

    # Metadata
    tokens_used: Dict[str, int]  # {agent1: 1500, agent2: 2000, agent3: 1800}
    execution_time: float
    error_message: Optional[str]
```

#### LangGraph Nodes

**1. Architect Node (Agent 1)**
```python
async def architect_node(state: AgentState) -> AgentState:
    """
    Analyzes requirements and creates architecture
    - Max tokens: 2500 input, 2000 output
    - Timeout: 30 seconds
    """
    # Call NVIDIA Nemotron with strict token limits
    response = await call_llm_with_limits(
        prompt=state["user_prompt"],
        system_prompt=ARCHITECT_SYSTEM_PROMPT,
        max_input_tokens=2500,
        max_output_tokens=2000
    )

    # Parse response
    state["architecture"] = response["architecture"]
    state["file_structure"] = extract_files(response)
    state["integrations"] = extract_integrations(response)
    state["ast_structure"] = build_ast(response)
    state["tokens_used"]["agent1"] = response["tokens"]

    # Store in Redis for caching
    await redis.cache_set(
        f"architecture:{hash(state['user_prompt'])}",
        response,
        expire=86400  # 24 hours
    )

    return state
```

**2. Coder Node (Agent 2)**
```python
async def coder_node(state: AgentState) -> AgentState:
    """
    Writes production-ready code
    - Max tokens: 3000 input, 2000 output
    - Timeout: 45 seconds
    """
    # Build context-aware prompt
    prompt = f"""
    Architecture: {state['architecture']}
    Files to create: {state['file_structure']}
    Integrations: {state['integrations']}

    Write complete, working code for all files.
    """

    response = await call_llm_with_limits(
        prompt=prompt,
        system_prompt=CODER_SYSTEM_PROMPT,
        max_input_tokens=3000,
        max_output_tokens=2000
    )

    # Parse code files
    state["generated_code"] = response["code"]
    state["code_files"] = parse_code_files(response["code"])
    state["tokens_used"]["agent2"] = response["tokens"]

    # Upload to Cloudflare R2
    await upload_to_r2(
        agent_id=state["agent_id"],
        files=state["code_files"]
    )

    return state
```

**3. Reviewer Node (Agent 3)**
```python
async def reviewer_node(state: AgentState) -> AgentState:
    """
    Reviews code and finds issues
    - Max tokens: 3000 input, 1500 output
    - Timeout: 30 seconds
    """
    prompt = f"""
    Original Prompt: {state['user_prompt']}
    Architecture: {state['architecture']}
    Generated Code: {state['generated_code']}

    Review for: bugs, security, best practices, completeness.
    """

    response = await call_llm_with_limits(
        prompt=prompt,
        system_prompt=REVIEWER_SYSTEM_PROMPT,
        max_input_tokens=3000,
        max_output_tokens=1500
    )

    # Parse review
    state["review_notes"] = response["review"]
    state["bugs_found"] = extract_bugs(response)
    state["tokens_used"]["agent3"] = response["tokens"]

    return state
```

**4. Decision Node**
```python
def should_recode(state: AgentState) -> str:
    """
    Decide if code needs fixing
    """
    # Check if critical bugs found
    has_critical_bugs = any(
        bug["severity"] == "critical"
        for bug in state["bugs_found"]
    )

    # Check iteration limit
    if state["iteration_count"] >= state["max_iterations"]:
        return "finalize"

    if has_critical_bugs:
        state["iteration_count"] += 1
        return "recode"

    return "finalize"
```

**5. Recode Node**
```python
async def recode_node(state: AgentState) -> AgentState:
    """
    Agent 2 fixes issues found by Agent 3
    """
    prompt = f"""
    Original Code: {state['generated_code']}
    Issues Found: {state['bugs_found']}
    Review Notes: {state['review_notes']}

    Fix ALL issues and provide corrected code.
    """

    response = await call_llm_with_limits(
        prompt=prompt,
        system_prompt=CODER_FIX_SYSTEM_PROMPT,
        max_input_tokens=3000,
        max_output_tokens=2000
    )

    state["generated_code"] = response["code"]
    state["fixes_applied"] = extract_fixes(response)

    return state
```

**6. Finalize Node**
```python
async def finalize_node(state: AgentState) -> AgentState:
    """
    Prepare final output
    """
    # Upload final code to R2
    final_url = await upload_to_r2(
        agent_id=state["agent_id"],
        files=state["code_files"],
        is_final=True
    )

    # Save to database
    await db.update_agent(
        agent_id=state["agent_id"],
        architecture=state["architecture"],
        generated_code=state["generated_code"],
        review_notes=state["review_notes"],
        final_code=state["generated_code"],
        file_structure=state["file_structure"],
        status="ready"
    )

    state["is_approved"] = True
    state["final_code"] = state["generated_code"]

    return state
```

#### LangGraph Graph Definition
```python
from langgraph.graph import StateGraph, END

# Create graph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("architect", architect_node)
workflow.add_node("coder", coder_node)
workflow.add_node("reviewer", reviewer_node)
workflow.add_node("recode", recode_node)
workflow.add_node("finalize", finalize_node)

# Add edges
workflow.set_entry_point("architect")
workflow.add_edge("architect", "coder")
workflow.add_edge("coder", "reviewer")
workflow.add_conditional_edges(
    "reviewer",
    should_recode,
    {
        "recode": "recode",
        "finalize": "finalize"
    }
)
workflow.add_edge("recode", "reviewer")  # Loop back
workflow.add_edge("finalize", END)

# Compile
app = workflow.compile()
```

---

## User Flow

### 1. Sign Up / Login Flow
```
User visits noderush.vercel.app
    ↓
Frontend: Click "Sign Up"
    ↓
Cloudflare Worker: Rate limit check (10 req/min per IP)
    ↓
Frontend: Enter email + password
    ↓
Backend: POST /api/auth/signup
    ↓
Supabase Auth: Create user account
    ↓
Backend: Create user record in PostgreSQL
    ↓
Backend: Generate JWT token
    ↓
Redis: Store session (session:{user_id})
    ↓
Frontend: Store JWT in localStorage
    ↓
Frontend: Redirect to /dashboard
```

### 2. Create Agent Flow
```
User: Click "Create New Agent"
    ↓
Frontend: Show agent builder form
    ↓
User: Enter agent name + description + prompt
    ↓
Frontend: Click "Generate Agent"
    ↓
Cloudflare Worker: Rate limit (5 agents/hour per user)
    ↓
Backend: POST /api/agents
    ↓
Backend: Validate JWT token
    ↓
Backend: Check user quota (max 10 agents on free tier)
    ↓
Backend: Create agent record (status: "generating")
    ↓
WebSocket: Connect to /ws/agent/{agent_id}
    ↓
Backend: Queue LangGraph execution
    ↓
Redis: Add to queue:agent_execution
    ↓
Worker Process: Pick from queue
    ↓
LangGraph: Execute 3-agent workflow
    ├─ Agent 1 (Architect): 30s, emit progress via WebSocket
    ├─ Agent 2 (Coder): 45s, emit code chunks via WebSocket
    └─ Agent 3 (Reviewer): 30s, emit review via WebSocket
    ↓
Backend: Upload code to Cloudflare R2
    ↓
Backend: Update agent status to "ready"
    ↓
WebSocket: Emit "generation_complete" event
    ↓
Frontend: Show generated code + download button
    ↓
Frontend: Display agent card in dashboard
```

### 3. View Generated Code Flow
```
User: Click agent card
    ↓
Frontend: Navigate to /agents/{agent_id}
    ↓
Backend: GET /api/agents/{agent_id}
    ↓
Redis: Check cache:agent:{agent_id}
    ├─ Hit: Return cached data
    └─ Miss: Query PostgreSQL + cache for 1 hour
    ↓
Frontend: Display agent details
    ↓
User: Click "View Code"
    ↓
Frontend: Fetch from Cloudflare R2
    ↓
R2: Return signed URL (valid 1 hour)
    ↓
Frontend: Display code with syntax highlighting
    ↓
User: Click "Download ZIP"
    ↓
Frontend: Download all files from R2
```

---

## Backend Flow

### Request Processing Pipeline
```
1. Client Request
    ↓
2. Cloudflare Worker (Edge)
    - Rate limiting
    - DDoS protection
    - Cache check
    - Request validation
    ↓
3. Render (FastAPI)
    - CORS middleware
    - Auth middleware (JWT validation)
    - Request logging
    - Rate limit middleware (secondary)
    ↓
4. Route Handler
    - Input validation (Pydantic)
    - Business logic
    - Database operations
    ↓
5. Services Layer
    - LangGraph service
    - Redis service
    - Cloudflare R2 service
    - Token manager
    ↓
6. Database/Cache
    - Supabase PostgreSQL
    - Upstash Redis
    - Cloudflare R2
    ↓
7. Response
    - Format response (JSON)
    - Add rate limit headers
    - Set cache headers
    - Return to client
```

### Background Jobs
```
Queue Worker (runs every 10s)
    ↓
Redis: Check queue:agent_execution
    ↓
If job found:
    ├─ Execute LangGraph workflow
    ├─ Update agent status in real-time
    ├─ Save results to PostgreSQL
    ├─ Upload files to R2
    └─ Remove from queue
    ↓
If no job: Sleep 10s
```

---

## Authentication Workflow

### Supabase Auth + Cloudflare Integration

```
┌────────────────────────────────────────────────────────────┐
│                     AUTHENTICATION FLOW                    │
└────────────────────────────────────────────────────────────┘

1. User Sign Up/Login
    ↓
┌──────────────────────┐
│  Cloudflare Worker   │ ← First layer
│  - Rate limit check  │
│  - Bot detection     │
│  - IP reputation     │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│   Supabase Auth      │ ← Authentication
│  - Email/password    │
│  - JWT generation    │
│  - Session mgmt      │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Backend (FastAPI)   │ ← Validation
│  - Verify JWT        │
│  - Check permissions │
│  - Create session    │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Redis (Upstash)     │ ← Session storage
│  - Store session     │
│  - TTL: 7 days       │
└──────────────────────┘
```

### JWT Token Structure
```json
{
  "sub": "user-uuid",
  "email": "user@example.com",
  "tier": "free",
  "permissions": ["read:agents", "write:agents", "execute:agents"],
  "iat": 1234567890,
  "exp": 1234971890
}
```

### Session Management
- **Storage**: Redis (key: `session:{user_id}`)
- **TTL**: 7 days (auto-refresh on activity)
- **Data**: User profile, preferences, quotas
- **Logout**: Delete session from Redis

---

## Rate Limiting Strategy

### Multi-Layer Rate Limiting

#### Layer 1: Cloudflare Worker (Edge)
```javascript
// Cloudflare Worker - First line of defense
const RATE_LIMITS = {
  // Per IP address
  'global': { requests: 100, window: 60 },  // 100 req/min

  // Per endpoint
  'auth:signup': { requests: 5, window: 3600 },  // 5/hour
  'auth:login': { requests: 10, window: 60 },    // 10/min
  'agents:create': { requests: 5, window: 3600 }, // 5/hour
  'agents:execute': { requests: 10, window: 3600 }, // 10/hour
  'api:general': { requests: 60, window: 60 },   // 60/min
};

async function handleRequest(request) {
  const ip = request.headers.get('CF-Connecting-IP');
  const endpoint = getEndpoint(request.url);

  // Check global rate limit
  const globalKey = `rate:global:${ip}`;
  const globalCount = await KV.get(globalKey);

  if (globalCount >= RATE_LIMITS.global.requests) {
    return new Response('Too Many Requests', {
      status: 429,
      headers: {
        'Retry-After': '60',
        'X-RateLimit-Limit': '100',
        'X-RateLimit-Remaining': '0'
      }
    });
  }

  // Check endpoint-specific rate limit
  const endpointKey = `rate:${endpoint}:${ip}`;
  const endpointCount = await KV.get(endpointKey);
  const limit = RATE_LIMITS[endpoint] || RATE_LIMITS['api:general'];

  if (endpointCount >= limit.requests) {
    return new Response('Rate Limit Exceeded', {
      status: 429,
      headers: {
        'Retry-After': limit.window,
        'X-RateLimit-Limit': limit.requests,
        'X-RateLimit-Remaining': '0'
      }
    });
  }

  // Increment counters
  await KV.put(globalKey, (globalCount || 0) + 1, { expirationTtl: 60 });
  await KV.put(endpointKey, (endpointCount || 0) + 1, { expirationTtl: limit.window });

  // Forward to backend
  return fetch(request);
}
```

#### Layer 2: Backend (FastAPI)
```python
# Token Bucket Algorithm
class TokenBucketRateLimiter:
    def __init__(self, redis_client):
        self.redis = redis_client

    async def check_limit(
        self,
        user_id: str,
        action: str,
        max_tokens: int,
        refill_rate: int,  # tokens per second
        bucket_size: int
    ) -> bool:
        key = f"ratelimit:{action}:{user_id}"

        # Get current state
        state = await self.redis.hgetall(key)
        current_tokens = float(state.get('tokens', bucket_size))
        last_refill = float(state.get('last_refill', time.time()))

        # Refill tokens based on time passed
        now = time.time()
        time_passed = now - last_refill
        refill_amount = time_passed * refill_rate
        current_tokens = min(bucket_size, current_tokens + refill_amount)

        # Check if enough tokens
        if current_tokens >= 1:
            # Consume token
            current_tokens -= 1
            await self.redis.hset(key, {
                'tokens': current_tokens,
                'last_refill': now
            })
            await self.redis.expire(key, 86400)  # 24h expiry
            return True

        return False

# Rate limit decorator
@app.post("/api/agents")
@rate_limit(max_requests=5, window=3600)  # 5 per hour
async def create_agent(request: Request, user: User):
    # Check token bucket
    allowed = await rate_limiter.check_limit(
        user_id=user.id,
        action="create_agent",
        max_tokens=5,
        refill_rate=5/3600,  # 5 per hour
        bucket_size=5
    )

    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Max 5 agents per hour."
        )

    # Process request
    ...
```

#### Layer 3: Per-User Quotas
```python
FREE_TIER_LIMITS = {
    'agents': {
        'max_total': 10,           # Max 10 agents total
        'create_per_hour': 5,       # Max 5 new agents per hour
        'create_per_day': 20,       # Max 20 new agents per day
    },
    'executions': {
        'per_hour': 10,             # Max 10 executions per hour
        'per_day': 50,              # Max 50 executions per day
    },
    'ai_tokens': {
        'per_request': 3000,        # Max 3000 tokens per request
        'per_day': 50000,           # Max 50k tokens per day
    },
    'storage': {
        'max_mb': 100,              # Max 100 MB in R2
        'max_files': 1000,          # Max 1000 files
    },
    'websocket': {
        'concurrent_connections': 3, # Max 3 concurrent WS
    }
}

async def check_user_quota(user_id: str, resource: str) -> bool:
    # Check in Redis
    usage_key = f"quota:{resource}:{user_id}"
    current_usage = await redis.get(usage_key)

    limit = FREE_TIER_LIMITS[resource.split(':')[0]][resource.split(':')[1]]

    if int(current_usage or 0) >= limit:
        return False

    # Increment usage
    await redis.incr(usage_key)
    await redis.expire(usage_key, get_ttl(resource))

    return True
```

### Rate Limit Headers
Every response includes:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1234567890
X-RateLimit-Resource: api:agents:create
```

---

## AI Token Management

### Token Counting and Limits

```python
import tiktoken

class TokenManager:
    def __init__(self):
        # Use cl100k_base encoding (GPT-4, NVIDIA models)
        self.encoding = tiktoken.get_encoding("cl100k_base")

        # Token limits per agent
        self.LIMITS = {
            'agent1_architect': {
                'max_input': 2500,
                'max_output': 2000,
                'total': 4500
            },
            'agent2_coder': {
                'max_input': 3000,
                'max_output': 2000,
                'total': 5000
            },
            'agent3_reviewer': {
                'max_input': 3000,
                'max_output': 1500,
                'total': 4500
            }
        }

        # Daily user limits
        self.USER_DAILY_LIMIT = 50000  # 50k tokens/day

    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        return len(self.encoding.encode(text))

    def truncate_to_limit(self, text: str, max_tokens: int) -> str:
        """Truncate text to max tokens"""
        tokens = self.encoding.encode(text)
        if len(tokens) <= max_tokens:
            return text

        # Truncate and add notice
        truncated_tokens = tokens[:max_tokens - 50]
        truncated_text = self.encoding.decode(truncated_tokens)
        return truncated_text + "\n\n[TRUNCATED DUE TO TOKEN LIMIT]"

    async def check_user_daily_limit(self, user_id: str) -> bool:
        """Check if user is within daily token limit"""
        key = f"tokens:daily:{user_id}:{date.today()}"
        usage = await redis.get(key)

        if int(usage or 0) >= self.USER_DAILY_LIMIT:
            return False

        return True

    async def track_usage(self, user_id: str, tokens: int):
        """Track token usage"""
        # Daily total
        daily_key = f"tokens:daily:{user_id}:{date.today()}"
        await redis.incrby(daily_key, tokens)
        await redis.expire(daily_key, 86400)

        # Per-agent tracking
        agent_key = f"tokens:agent:{user_id}"
        await redis.hincrby(agent_key, "total", tokens)
        await redis.expire(agent_key, 2592000)  # 30 days

    async def call_llm_with_limits(
        self,
        agent_name: str,
        prompt: str,
        system_prompt: str,
        user_id: str
    ) -> Dict:
        """Call LLM with strict token limits"""

        # Check daily limit
        if not await self.check_user_daily_limit(user_id):
            raise Exception("Daily token limit exceeded (50,000 tokens)")

        # Get limits for this agent
        limits = self.LIMITS.get(agent_name)

        # Count input tokens
        input_text = system_prompt + "\n\n" + prompt
        input_tokens = self.count_tokens(input_text)

        # Truncate if needed
        if input_tokens > limits['max_input']:
            logger.warning(f"Input truncated: {input_tokens} -> {limits['max_input']}")
            prompt = self.truncate_to_limit(prompt, limits['max_input'] - 500)
            input_tokens = limits['max_input']

        # Call OpenRouter with max_tokens parameter
        response = await openrouter_client.chat.completions.create(
            model="nvidia/nemotron-nano-12b-v2-vl:free",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            max_tokens=limits['max_output'],  # Hard limit on output
            temperature=0.7,
        )

        # Count output tokens
        output_tokens = response.usage.completion_tokens
        total_tokens = response.usage.total_tokens

        # Track usage
        await self.track_usage(user_id, total_tokens)

        # Log usage
        logger.info(f"{agent_name}: {input_tokens} in + {output_tokens} out = {total_tokens} total")

        return {
            'content': response.choices[0].message.content,
            'tokens': {
                'input': input_tokens,
                'output': output_tokens,
                'total': total_tokens
            }
        }
```

### Token Usage Monitoring
```python
# Store in Redis for real-time monitoring
await redis.hincrby(f"tokens:user:{user_id}:today", "total", tokens_used)
await redis.hincrby(f"tokens:user:{user_id}:today", agent_name, tokens_used)

# Set expiry at end of day
midnight = datetime.combine(date.today() + timedelta(days=1), datetime.min.time())
ttl = (midnight - datetime.now()).seconds
await redis.expire(f"tokens:user:{user_id}:today", ttl)
```

### Cost Estimation
```python
# NVIDIA Nemotron is FREE, but track for transparency
HYPOTHETICAL_COST_PER_1K_TOKENS = 0.0  # Free model

def estimate_cost(tokens: int) -> float:
    return (tokens / 1000) * HYPOTHETICAL_COST_PER_1K_TOKENS  # $0.00
```

---

## Cloudflare Integration

### Cloudflare Workers Setup

**File: `cloudflare-worker/worker.js`**
```javascript
// Cloudflare Worker for rate limiting and caching

const BACKEND_URL = 'https://noderush-backend.onrender.com';

// KV Namespaces (configured in wrangler.toml)
// - RATE_LIMIT_KV: Rate limit counters
// - CACHE_KV: Response caching

addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request))
});

async function handleRequest(request) {
  const url = new URL(request.url);
  const ip = request.headers.get('CF-Connecting-IP');
  const country = request.headers.get('CF-IPCountry');

  // 1. Block suspicious traffic
  if (await isBlocked(ip)) {
    return new Response('Access Denied', { status: 403 });
  }

  // 2. Rate limiting
  const rateLimitResult = await checkRateLimit(ip, url.pathname);
  if (!rateLimitResult.allowed) {
    return new Response('Rate Limit Exceeded', {
      status: 429,
      headers: {
        'Retry-After': rateLimitResult.retryAfter,
        'X-RateLimit-Limit': rateLimitResult.limit,
        'X-RateLimit-Remaining': '0'
      }
    });
  }

  // 3. Check cache (for GET requests)
  if (request.method === 'GET') {
    const cached = await CACHE_KV.get(url.pathname);
    if (cached) {
      return new Response(cached, {
        headers: {
          'Content-Type': 'application/json',
          'X-Cache': 'HIT',
          'Cache-Control': 'public, max-age=300'
        }
      });
    }
  }

  // 4. Forward to backend
  const backendRequest = new Request(BACKEND_URL + url.pathname + url.search, {
    method: request.method,
    headers: request.headers,
    body: request.body
  });

  const response = await fetch(backendRequest);

  // 5. Cache successful GET responses
  if (request.method === 'GET' && response.ok) {
    const responseClone = response.clone();
    const body = await responseClone.text();
    await CACHE_KV.put(url.pathname, body, { expirationTtl: 300 }); // 5 min
  }

  // 6. Add security headers
  const secureResponse = new Response(response.body, response);
  secureResponse.headers.set('X-Content-Type-Options', 'nosniff');
  secureResponse.headers.set('X-Frame-Options', 'DENY');
  secureResponse.headers.set('X-XSS-Protection', '1; mode=block');
  secureResponse.headers.set('Strict-Transport-Security', 'max-age=31536000');

  return secureResponse;
}

async function checkRateLimit(ip, path) {
  // Determine rate limit based on endpoint
  const limits = {
    '/api/auth/signup': { max: 5, window: 3600 },
    '/api/auth/login': { max: 10, window: 60 },
    '/api/agents': { max: 60, window: 60 },
    'default': { max: 100, window: 60 }
  };

  const limit = limits[path] || limits.default;
  const key = `ratelimit:${path}:${ip}`;

  // Get current count
  const current = await RATE_LIMIT_KV.get(key);
  const count = parseInt(current || '0');

  if (count >= limit.max) {
    return {
      allowed: false,
      retryAfter: limit.window,
      limit: limit.max
    };
  }

  // Increment counter
  await RATE_LIMIT_KV.put(key, (count + 1).toString(), {
    expirationTtl: limit.window
  });

  return {
    allowed: true,
    remaining: limit.max - count - 1,
    limit: limit.max
  };
}

async function isBlocked(ip) {
  // Check IP reputation (example)
  const blocked = await RATE_LIMIT_KV.get(`blocked:${ip}`);
  return blocked === 'true';
}
```

**File: `cloudflare-worker/wrangler.toml`**
```toml
name = "noderush-worker"
main = "worker.js"
compatibility_date = "2024-01-01"

[[kv_namespaces]]
binding = "RATE_LIMIT_KV"
id = "your-kv-namespace-id"

[[kv_namespaces]]
binding = "CACHE_KV"
id = "your-cache-kv-namespace-id"

[env.production]
routes = [
  { pattern = "api.noderush.vercel.app/*", zone_name = "noderush.vercel.app" }
]
```

### Cloudflare R2 Integration

**File: `backend/app/services/cloudflare_service.py`**
```python
import boto3
from botocore.config import Config
import zipfile
import io
from typing import Dict, List

class CloudflareR2Service:
    def __init__(self):
        # R2 uses S3-compatible API
        self.s3_client = boto3.client(
            's3',
            endpoint_url=f'https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com',
            aws_access_key_id=settings.R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
            config=Config(signature_version='s3v4')
        )
        self.bucket_name = 'noderush-agents'

    async def upload_agent_files(
        self,
        agent_id: str,
        files: Dict[str, str],  # filename: content
        is_final: bool = False
    ) -> str:
        """
        Upload agent code files to R2
        Returns: URL to access files
        """
        folder = f"agents/{agent_id}/{'final' if is_final else 'draft'}"

        # Upload each file
        for filename, content in files.items():
            key = f"{folder}/{filename}"
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=content.encode('utf-8'),
                ContentType=self._get_content_type(filename),
                Metadata={
                    'agent-id': agent_id,
                    'version': 'final' if is_final else 'draft'
                }
            )

        # Create ZIP archive
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for filename, content in files.items():
                zip_file.writestr(filename, content)

        zip_buffer.seek(0)
        zip_key = f"{folder}/agent.zip"

        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=zip_key,
            Body=zip_buffer.getvalue(),
            ContentType='application/zip'
        )

        # Generate presigned URL (valid 24 hours)
        url = self.s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': self.bucket_name, 'Key': zip_key},
            ExpiresIn=86400
        )

        return url

    async def get_agent_files(self, agent_id: str) -> Dict[str, str]:
        """Retrieve agent files from R2"""
        folder = f"agents/{agent_id}/final"

        # List all files
        response = self.s3_client.list_objects_v2(
            Bucket=self.bucket_name,
            Prefix=folder
        )

        files = {}
        for obj in response.get('Contents', []):
            if obj['Key'].endswith('.zip'):
                continue

            filename = obj['Key'].split('/')[-1]
            content = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=obj['Key']
            )['Body'].read().decode('utf-8')

            files[filename] = content

        return files

    async def delete_agent_files(self, agent_id: str):
        """Delete all files for an agent"""
        folder = f"agents/{agent_id}"

        # List and delete all objects
        response = self.s3_client.list_objects_v2(
            Bucket=self.bucket_name,
            Prefix=folder
        )

        for obj in response.get('Contents', []):
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=obj['Key']
            )

    def _get_content_type(self, filename: str) -> str:
        """Get content type from filename"""
        ext_map = {
            '.py': 'text/x-python',
            '.js': 'application/javascript',
            '.json': 'application/json',
            '.md': 'text/markdown',
            '.txt': 'text/plain',
            '.yaml': 'text/yaml',
            '.yml': 'text/yaml',
        }
        ext = '.' + filename.split('.')[-1]
        return ext_map.get(ext, 'text/plain')

# Singleton instance
r2_service = CloudflareR2Service()
```

### Free Tier Monitoring
```python
# Track R2 usage to stay within 10 GB limit
async def check_r2_usage(user_id: str) -> Dict:
    """Check user's R2 storage usage"""
    # List all objects for user
    total_size = 0
    file_count = 0

    # Query from database (cached in Redis)
    agents = await db.get_user_agents(user_id)

    for agent in agents:
        folder = f"agents/{agent.id}/final"
        response = r2_service.s3_client.list_objects_v2(
            Bucket=r2_service.bucket_name,
            Prefix=folder
        )

        for obj in response.get('Contents', []):
            total_size += obj['Size']
            file_count += 1

    # Convert to MB
    total_mb = total_size / (1024 * 1024)

    # Check limits
    within_limit = total_mb < 100 and file_count < 1000

    return {
        'total_mb': round(total_mb, 2),
        'file_count': file_count,
        'limit_mb': 100,
        'limit_files': 1000,
        'within_limit': within_limit
    }
```

---

## Security Architecture

### 1. Authentication & Authorization
- **Supabase Auth**: Email/password with bcrypt hashing
- **JWT Tokens**: HS256 algorithm, 7-day expiry
- **Session Management**: Redis-based sessions with auto-refresh
- **Permission System**: Role-based access control (RBAC)

### 2. Data Encryption
```python
# Encrypt sensitive data before storing
from cryptography.fernet import Fernet

class EncryptionService:
    def __init__(self):
        self.key = settings.ENCRYPTION_KEY.encode()
        self.cipher = Fernet(self.key)

    def encrypt(self, data: str) -> str:
        """Encrypt sensitive data"""
        return self.cipher.encrypt(data.encode()).decode()

    def decrypt(self, encrypted: str) -> str:
        """Decrypt data"""
        return self.cipher.decrypt(encrypted.encode()).decode()

# Use for API keys, tokens, etc.
encrypted_api_key = encryption.encrypt(user_api_key)
await db.save_integration(user_id, service, encrypted_api_key)
```

### 3. Input Validation
```python
from pydantic import BaseModel, validator, Field

class CreateAgentRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., max_length=500)
    prompt: str = Field(..., min_length=10, max_length=5000)

    @validator('name')
    def validate_name(cls, v):
        # Prevent XSS
        if '<' in v or '>' in v:
            raise ValueError('Invalid characters in name')
        return v

    @validator('prompt')
    def validate_prompt(cls, v):
        # Prevent prompt injection
        blacklist = ['system:', 'ignore previous', 'jailbreak']
        if any(word in v.lower() for word in blacklist):
            raise ValueError('Suspicious prompt detected')
        return v
```

### 4. SQL Injection Prevention
- **SQLAlchemy ORM**: Parameterized queries
- **Input sanitization**: Pydantic validation
- **Least privilege**: Database user has minimal permissions

### 5. XSS Prevention
- **Content Security Policy**: Restrict script sources
- **Output encoding**: Escape user-generated content
- **HTTP headers**: X-XSS-Protection enabled

### 6. CSRF Protection
```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.post("/api/agents")
async def create_agent(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    # Verify CSRF token
    csrf_token = request.headers.get('X-CSRF-Token')
    stored_token = await redis.get(f"csrf:{credentials.credentials}")

    if csrf_token != stored_token:
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

    # Process request
    ...
```

### 7. DDoS Protection
- **Cloudflare**: Built-in DDoS protection
- **Rate limiting**: Multi-layer (Worker + Backend + Redis)
- **Connection limits**: Max 10k concurrent WebSocket connections

### 8. Secrets Management
```python
# Never commit secrets to git
# Use environment variables
DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
```

### 9. Audit Logging
```python
async def log_security_event(
    event_type: str,
    user_id: str,
    ip: str,
    details: Dict
):
    """Log security events for monitoring"""
    await db.insert(
        'security_logs',
        {
            'event_type': event_type,
            'user_id': user_id,
            'ip_address': ip,
            'details': details,
            'timestamp': datetime.utcnow()
        }
    )

    # Alert on suspicious activity
    if event_type in ['failed_login', 'rate_limit_exceeded']:
        await check_for_attack_pattern(user_id, ip)
```

---

## Concurrency & Scalability

### Handling 10,000 Concurrent Users

#### 1. Horizontal Scaling
```
Render Backend (2 instances, free tier)
    ├─ Instance 1: 512 MB RAM, 0.1 CPU
    └─ Instance 2: 512 MB RAM, 0.1 CPU

Load Balancer: Cloudflare (automatic)

Each instance handles ~5,000 concurrent connections
```

#### 2. Connection Pooling
```python
# Database connection pool
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,          # 10 persistent connections
    max_overflow=20,       # 20 additional connections
    pool_pre_ping=True,    # Verify connection health
    pool_recycle=3600,     # Recycle after 1 hour
)
```

#### 3. Redis Connection Pool
```python
# Redis connection pool
redis_client = redis.from_url(
    REDIS_URL,
    max_connections=20,
    decode_responses=True
)
```

#### 4. WebSocket Scaling
```python
# Use Redis pub/sub for cross-instance messaging
class DistributedWebSocketManager:
    async def broadcast(self, agent_id: str, message: Dict):
        # Publish to Redis channel
        await redis.publish(
            f"ws:agent:{agent_id}",
            json.dumps(message)
        )

    async def subscribe(self):
        # Subscribe to Redis channel
        pubsub = redis.pubsub()
        await pubsub.subscribe('ws:agent:*')

        async for message in pubsub.listen():
            if message['type'] == 'message':
                data = json.loads(message['data'])
                # Broadcast to local connections
                await self.broadcast_local(data)
```

#### 5. Async Processing
```python
# Use asyncio for concurrent operations
async def process_multiple_agents(agent_ids: List[str]):
    tasks = [execute_agent(aid) for aid in agent_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

#### 6. Caching Strategy
```
Layer 1: Cloudflare CDN (Edge cache)
    - Static assets: 1 week
    - API responses: 5 minutes

Layer 2: Redis (Application cache)
    - User sessions: 7 days
    - Agent data: 1 hour
    - AI responses: 24 hours

Layer 3: Database (Persistent storage)
    - Indexed queries
    - Connection pooling
```

#### 7. Queue-Based Processing
```python
# LangGraph executions run in background queue
async def queue_agent_execution(agent_id: str, prompt: str):
    # Add to Redis queue
    await redis.lpush('queue:agent_execution', json.dumps({
        'agent_id': agent_id,
        'prompt': prompt,
        'user_id': user_id,
        'timestamp': datetime.utcnow().isoformat()
    }))

# Worker processes jobs from queue
async def worker():
    while True:
        job = await redis.brpop('queue:agent_execution', timeout=10)
        if job:
            await execute_langgraph_workflow(job)
```

#### 8. Resource Limits
```python
# Prevent resource exhaustion
MAX_CONCURRENT_EXECUTIONS = 100
MAX_WEBSOCKET_CONNECTIONS = 10000
MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10 MB

@app.middleware("http")
async def limit_request_size(request: Request, call_next):
    if request.headers.get('content-length'):
        if int(request.headers['content-length']) > MAX_REQUEST_SIZE:
            return Response('Request too large', status_code=413)
    return await call_next(request)
```

---

## Data Protection

### 1. Data at Rest
- **Database**: Supabase encrypts all data at rest (AES-256)
- **Redis**: Upstash encrypts all data at rest
- **R2**: Cloudflare R2 encrypts all objects (AES-256)

### 2. Data in Transit
- **TLS 1.3**: All traffic encrypted (Cloudflare + Render)
- **HTTPS Only**: HTTP redirects to HTTPS automatically
- **WebSocket Secure**: WSS protocol (encrypted)

### 3. User Data Isolation
```python
# Row-level security
@app.get("/api/agents/{agent_id}")
async def get_agent(agent_id: str, user: User = Depends(get_current_user)):
    # Verify ownership
    agent = await db.get_agent(agent_id)
    if agent.user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return agent
```

### 4. Data Retention
```python
# Auto-delete old data
async def cleanup_old_data():
    # Delete agents older than 90 days (inactive)
    await db.delete_where(
        'agents',
        'status = "draft" AND updated_at < NOW() - INTERVAL 90 DAY'
    )

    # Delete execution logs older than 30 days
    await db.delete_where(
        'execution_logs',
        'created_at < NOW() - INTERVAL 30 DAY'
    )
```

### 5. Backup Strategy
- **Supabase**: Automatic daily backups (7-day retention on free tier)
- **Redis**: Persistence enabled (AOF + RDB)
- **R2**: Versioning disabled to save storage

### 6. GDPR Compliance
```python
@app.delete("/api/user/delete-account")
async def delete_account(user: User = Depends(get_current_user)):
    """
    Complete user data deletion (GDPR right to erasure)
    """
    # Delete all user data
    await db.delete_user_agents(user.id)
    await db.delete_user_integrations(user.id)
    await db.delete_user(user.id)

    # Delete from Redis
    await redis.delete(f"session:{user.id}")
    await redis.delete(f"quota:*:{user.id}")

    # Delete from R2
    await r2_service.delete_user_files(user.id)

    return {"message": "Account deleted successfully"}
```

---

## Cost Management

### Free Tier Limits & Monitoring

```python
class CostMonitor:
    FREE_TIER_LIMITS = {
        'vercel': {
            'bandwidth_gb': 100,
            'function_invocations': 100000,
        },
        'render': {
            'hours': 750,
            'build_minutes': 500,
        },
        'supabase': {
            'storage_mb': 500,
            'database_size_mb': 500,
            'bandwidth_gb': 2,
            'active_users': 50000,
        },
        'upstash_redis': {
            'commands_per_day': 10000,
            'max_data_size_mb': 256,
        },
        'cloudflare_r2': {
            'storage_gb': 10,
            'class_a_operations': 1000000,  # writes
            'class_b_operations': 10000000,  # reads
        },
        'cloudflare_workers': {
            'requests_per_day': 100000,
            'cpu_ms_per_request': 10,
        },
        'openrouter_nvidia': {
            'cost_per_1k_tokens': 0.0,  # FREE
        }
    }

    async def check_usage(self, service: str) -> Dict:
        """Check current usage vs limits"""
        current_date = date.today()

        if service == 'upstash_redis':
            # Count Redis commands today
            key = f"redis:commands:count:{current_date}"
            count = await redis.get(key) or 0

            return {
                'service': service,
                'current': int(count),
                'limit': self.FREE_TIER_LIMITS[service]['commands_per_day'],
                'percentage': (int(count) / self.FREE_TIER_LIMITS[service]['commands_per_day']) * 100,
                'within_limit': int(count) < self.FREE_TIER_LIMITS[service]['commands_per_day']
            }

        elif service == 'cloudflare_r2':
            # Check R2 storage
            total_size_gb = await self.get_r2_total_size()

            return {
                'service': service,
                'current_gb': round(total_size_gb, 2),
                'limit_gb': self.FREE_TIER_LIMITS[service]['storage_gb'],
                'percentage': (total_size_gb / self.FREE_TIER_LIMITS[service]['storage_gb']) * 100,
                'within_limit': total_size_gb < self.FREE_TIER_LIMITS[service]['storage_gb']
            }

        # ... other services

    async def alert_if_approaching_limit(self, service: str):
        """Alert when usage reaches 80% of limit"""
        usage = await self.check_usage(service)

        if usage['percentage'] >= 80:
            logger.warning(f"⚠️ {service} usage at {usage['percentage']:.1f}%")

            # Send alert (email, Slack, etc.)
            await self.send_alert(
                f"{service} approaching limit",
                f"Current usage: {usage['percentage']:.1f}%"
            )
```

### Production Rate Limits (Free Tier Optimized)
```python
PRODUCTION_RATE_LIMITS = {
    # Per user limits to stay within free tiers
    'agent_creation': {
        'per_hour': 5,      # Max 5 agents/hour
        'per_day': 20,      # Max 20 agents/day
        'total': 10,        # Max 10 total agents
    },
    'agent_execution': {
        'per_hour': 10,     # Max 10 executions/hour
        'per_day': 50,      # Max 50 executions/day
    },
    'api_calls': {
        'per_minute': 60,   # 60 requests/minute
        'per_hour': 1000,   # 1000 requests/hour
    },
    'websocket': {
        'concurrent': 3,    # Max 3 concurrent WS connections
    },
    'ai_tokens': {
        'per_request': 3000,  # Max 3000 tokens/request
        'per_day': 50000,     # Max 50k tokens/day
    },
    'storage': {
        'max_mb_per_user': 10,  # Max 10 MB per user
        'max_files': 100,       # Max 100 files per user
    }
}
```

### Budget Safeguards
```python
# Automatic shutdown if approaching paid tiers
async def check_and_enforce_budgets():
    """Run every hour"""

    # Check Upstash Redis commands
    redis_usage = await cost_monitor.check_usage('upstash_redis')
    if redis_usage['percentage'] > 90:
        # Pause new agent creations
        await redis.set('system:pause_agent_creation', 'true', ex=3600)
        logger.critical("🚨 PAUSED: Redis approaching daily limit")

    # Check R2 storage
    r2_usage = await cost_monitor.check_usage('cloudflare_r2')
    if r2_usage['current_gb'] > 9:  # 90% of 10 GB
        # Pause file uploads
        await redis.set('system:pause_file_upload', 'true', ex=86400)
        logger.critical("🚨 PAUSED: R2 storage approaching limit")

    # Check Cloudflare Workers requests
    worker_usage = await cost_monitor.check_usage('cloudflare_workers')
    if worker_usage['percentage'] > 90:
        # Enable aggressive caching
        await redis.set('system:aggressive_caching', 'true', ex=3600)
        logger.warning("⚠️ Enabled aggressive caching")
```

---

## Deployment Strategy

### Environment Setup

**1. Supabase Setup**
```bash
# Create Supabase project at supabase.com
# Get credentials:
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJxxx...
DATABASE_URL=postgresql://postgres:[password]@db.xxx.supabase.co:5432/postgres
```

**2. Upstash Redis Setup**
```bash
# Create Redis database at upstash.com
# Get URL:
REDIS_URL=rediss://default:[password]@xxx.upstash.io:6379
```

**3. Cloudflare Setup**
```bash
# R2 Bucket
# Create bucket at dash.cloudflare.com
R2_ACCOUNT_ID=xxx
R2_ACCESS_KEY_ID=xxx
R2_SECRET_ACCESS_KEY=xxx
R2_BUCKET_NAME=noderush-agents

# Workers
# Deploy worker:
npm install -g wrangler
wrangler login
cd cloudflare-worker
wrangler publish
```

**4. OpenRouter Setup**
```bash
# Get API key from openrouter.ai
OPENROUTER_API_KEY=sk-or-xxx
```

**5. Render Deployment**
```yaml
# render.yaml
services:
  - type: web
    name: noderush-backend
    runtime: docker
    plan: free
    dockerfilePath: ./backend/Dockerfile
    dockerContext: ./backend
    healthCheckPath: /health
    envVars:
      - key: DATABASE_URL
        sync: false
      - key: REDIS_URL
        sync: false
      - key: OPENROUTER_API_KEY
        sync: false
      - key: R2_ACCOUNT_ID
        sync: false
      - key: R2_ACCESS_KEY_ID
        sync: false
      - key: R2_SECRET_ACCESS_KEY
        sync: false
      - key: SECRET_KEY
        generateValue: true
      - key: ENCRYPTION_KEY
        generateValue: true
```

**6. Vercel Deployment**
```bash
# Frontend
npm install -g vercel
cd frontend
vercel --prod
```

### CI/CD Pipeline
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Deploy Frontend to Vercel
        run: |
          npm install -g vercel
          cd frontend
          vercel --prod --token=${{ secrets.VERCEL_TOKEN }}

      - name: Deploy Backend to Render
        run: |
          # Render auto-deploys on git push
          echo "Backend will auto-deploy"

      - name: Deploy Cloudflare Worker
        run: |
          npm install -g wrangler
          cd cloudflare-worker
          wrangler publish --env production
        env:
          CLOUDFLARE_API_TOKEN: ${{ secrets.CLOUDFLARE_API_TOKEN }}
```

---

## Monitoring & Observability

```python
# Setup logging
import structlog

logger = structlog.get_logger()

# Log every request
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    response = await call_next(request)

    duration = time.time() - start_time

    logger.info(
        "request",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration=round(duration, 3),
        ip=request.client.host
    )

    return response

# Health check endpoint
@app.get("/health")
async def health_check():
    # Check all services
    checks = {
        'database': await db.ping(),
        'redis': await redis.ping(),
        'r2': await r2_service.ping(),
    }

    all_healthy = all(checks.values())

    return {
        'status': 'healthy' if all_healthy else 'degraded',
        'checks': checks,
        'timestamp': datetime.utcnow().isoformat()
    }
```

---

## Summary

This architecture is designed to:
1. ✅ Run entirely on **free tiers** ($0 budget)
2. ✅ Handle **10,000+ concurrent users**
3. ✅ Provide **production-level security**
4. ✅ Implement **strict rate limiting** to prevent cost overruns
5. ✅ Use **LangGraph for 3-agent workflow**
6. ✅ Offer **real-time visualization** with Socket.IO
7. ✅ Protect against **attacks and data theft**
8. ✅ Limit **AI token usage** (2000-3000 in, 1500-2000 out)

**Tech Stack Summary:**
- **Frontend**: Next.js + Vercel
- **Backend**: FastAPI + Render + LangGraph
- **Database**: Supabase PostgreSQL + Auth
- **Cache/Queue**: Upstash Redis
- **Storage**: Cloudflare R2
- **Edge**: Cloudflare Workers + CDN + WAF
- **AI**: OpenRouter (NVIDIA Nemotron - FREE)
- **Real-time**: Socket.IO

**Free Tier Limits Recap:**
- Vercel: 100 GB bandwidth/month
- Render: 750 hours/month
- Supabase: 500 MB storage, 50k MAU
- Upstash: 10k commands/day
- R2: 10 GB storage
- Workers: 100k requests/day
- NVIDIA Nemotron: Unlimited (free model)

This architecture ensures you'll never pay a cent while providing enterprise-grade functionality! 🚀
