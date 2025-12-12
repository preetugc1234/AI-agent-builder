# Frontend-Backend Integration Guide

**NodeRush** - Complete integration documentation for connecting the Next.js frontend with the FastAPI backend.

**Last Updated:** December 2025

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Setup Instructions](#setup-instructions)
4. [API Integration](#api-integration)
5. [Authentication Flow](#authentication-flow)
6. [Row-Level Security](#row-level-security)
7. [WebSocket Integration](#websocket-integration)
8. [Testing](#testing)
9. [Deployment](#deployment)
10. [Troubleshooting](#troubleshooting)

---

## Overview

NodeRush uses a clean separation between frontend and backend:

- **Frontend**: Next.js 14 + React + TypeScript (deployed on Vercel)
- **Backend**: FastAPI + Python (deployed on Render)
- **Database**: Supabase PostgreSQL with application-level RLS
- **Cache/Sessions**: Upstash Redis
- **Real-time**: Socket.IO for live updates

### Communication Flow

```
┌─────────────────┐          ┌─────────────────┐          ┌──────────────┐
│   Next.js       │   HTTP   │    FastAPI      │          │  Supabase    │
│   Frontend      ├─────────►│    Backend      ├─────────►│  PostgreSQL  │
│  (Vercel)       │   REST   │   (Render)      │          │              │
└────────┬────────┘          └────────┬────────┘          └──────────────┘
         │                            │
         │   WebSocket (Socket.IO)    │
         └────────────────────────────┘
```

---

## Architecture

### Frontend Structure

```
frontend/
├── App.tsx                    # Main app with routing
├── contexts/
│   └── AuthContext.tsx        # Authentication state management
├── services/
│   └── api.ts                 # Centralized API service (ALL backend calls)
├── pages/
│   ├── AuthPage.tsx          # Login/Register
│   ├── AgentBuilderPage.tsx  # Create agents
│   └── HistoryPage.tsx       # View all agents
├── components/
│   ├── ProtectedRoute.tsx    # Route guard for auth
│   └── ...
└── .env                       # VITE_API_URL configuration
```

### Backend Structure

```
backend/
├── main.py                    # FastAPI app entry point
├── app/
│   ├── api/
│   │   ├── auth.py           # POST /api/auth/login, /register, /logout
│   │   ├── agents.py         # CRUD /api/agents/
│   │   ├── analytics.py      # GET /api/analytics/
│   │   └── users.py          # GET /api/users/me
│   ├── core/
│   │   ├── config.py         # Environment configuration
│   │   ├── auth_middleware.py # JWT validation
│   │   └── middleware.py     # CORS, security
│   ├── models/
│   │   └── models.py         # SQLAlchemy models
│   ├── services/
│   │   ├── redis_service.py  # Redis operations
│   │   └── three_agent_service.py # LangGraph 3-agent workflow
│   └── db/
│       └── database.py       # Database connection
├── migrations/
│   └── 001_enable_rls.sql   # Database schema setup
├── requirements.txt          # Python dependencies
└── .env                      # Environment variables
```

---

## Setup Instructions

### Backend Setup

1. **Install Python dependencies**

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure environment variables**

```bash
cp .env.example .env
# Edit .env with your credentials
```

Required variables:
```env
DATABASE_URL=postgresql+asyncpg://postgres.[PROJECT]:password@aws-0-region.pooler.supabase.com:6543/postgres
REDIS_URL=redis://default:password@region.upstash.io:6379
SECRET_KEY=your-secret-jwt-key
OPENROUTER_API_KEY=your-openrouter-api-key
DEBUG=false
```

3. **Run database migrations**

The backend automatically creates tables on startup using SQLAlchemy, but you can also run migrations manually:

```bash
# Connect to your Supabase database
psql $DATABASE_URL

# Run the migration
\i migrations/001_enable_rls.sql
```

4. **Start the backend**

```bash
cd backend
python main.py
```

Backend will be available at: `http://localhost:8000`

API docs: `http://localhost:8000/docs`

### Frontend Setup

1. **Install Node dependencies**

```bash
cd frontend
npm install
```

2. **Configure environment variables**

```bash
cp .env.example .env
```

Required variables:
```env
VITE_API_URL=http://localhost:8000
```

For production:
```env
VITE_API_URL=https://your-backend.onrender.com
```

3. **Start the frontend**

```bash
npm run dev
```

Frontend will be available at: `http://localhost:5173`

---

## API Integration

### API Service (`frontend/services/api.ts`)

All backend communication goes through a centralized API service with:
- JWT token management
- Error handling
- TypeScript type safety

#### Authentication

```typescript
import { login, register, logout, getCurrentUser } from './services/api';

// Login
const { access_token, user } = await login('user@example.com', 'password');
localStorage.setItem('auth_token', access_token);

// Register
await register('user@example.com', 'password');

// Get current user
const user = await getCurrentUser();

// Logout
await logout();
localStorage.removeItem('auth_token');
```

#### Agent Operations

```typescript
import {
  getAgents,
  getAgent,
  createAgent,
  updateAgent,
  deleteAgent,
  generateNewAgent
} from './services/api';

// List all user's agents
const agents = await getAgents();

// Get specific agent
const agent = await getAgent(agentId);

// Create agent
const newAgent = await createAgent({
  name: 'My Agent',
  description: 'Description',
  vibe_prompt: 'Create a financial analyst agent'
});

// Generate agent with AI
const generatedAgent = await generateNewAgent({
  name: 'AI Agent',
  vibe_prompt: 'Build a customer support chatbot'
});

// Update agent
await updateAgent(agentId, { name: 'Updated Name' });

// Delete agent
await deleteAgent(agentId);
```

#### Analytics

```typescript
import { getAnalytics } from './services/api';

const analytics = await getAnalytics();
// Returns:
// {
//   total_agents: 5,
//   time_saved_hours: 12.5,
//   overall_success_rate: 87.5,
//   total_executions: 24
// }
```

### API Endpoints Reference

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/auth/register` | Create new user | No |
| POST | `/api/auth/login` | Login user | No |
| POST | `/api/auth/logout` | Logout user | Yes |
| GET | `/api/auth/me` | Get current user | Yes |
| GET | `/api/agents/` | List all user's agents | Yes |
| POST | `/api/agents/` | Create agent | Yes |
| GET | `/api/agents/{id}` | Get agent by ID | Yes |
| PUT | `/api/agents/{id}` | Update agent | Yes |
| DELETE | `/api/agents/{id}` | Delete agent | Yes |
| POST | `/api/agents/generate` | Create and generate agent | Yes |
| POST | `/api/agents/{id}/generate-code` | Generate code for existing agent | Yes |
| GET | `/api/analytics/` | Get user analytics | Yes |
| GET | `/api/users/me` | Get user profile | Yes |
| PUT | `/api/users/me` | Update user profile | Yes |

---

## Authentication Flow

### How It Works

1. **User registers/logs in** → Backend generates JWT token
2. **Token stored** in `localStorage` as `auth_token`
3. **All API requests** include `Authorization: Bearer {token}` header
4. **Backend validates** token and extracts user info
5. **RLS enforcement** - all queries filter by `user_id` from token

### JWT Token Structure

```json
{
  "sub": "user-uuid",
  "email": "user@example.com",
  "tier": "free",
  "permissions": ["read:agents", "write:agents"],
  "iat": 1701234567,
  "exp": 1701838367
}
```

### Protected Routes (Frontend)

```tsx
// ProtectedRoute.tsx
<Route
  path="/builder"
  element={
    <ProtectedRoute>
      <AgentBuilderPage />
    </ProtectedRoute>
  }
/>
```

### Protected Endpoints (Backend)

```python
# agents.py
@router.get("/")
async def list_agents(
    current_user: User = Depends(get_current_user),  # ← Validates JWT
    db: AsyncSession = Depends(get_db)
):
    # Only returns agents where user_id = current_user.id
    result = await db.execute(
        select(Agent).where(Agent.user_id == current_user.id)
    )
    return result.scalars().all()
```

---

## Row-Level Security

NodeRush implements **application-level RLS** - all security enforcement happens in the FastAPI application layer, not at the database level.

### RLS Pattern

Every query follows this pattern:

**Direct Ownership** (agents, integrations, etc.)
```python
# ✅ CORRECT - Filters by user_id
result = await db.execute(
    select(Agent).where(
        Agent.id == agent_id,
        Agent.user_id == current_user.id  # ← RLS enforcement
    )
)
```

**Indirect Ownership** (deployments, execution logs via agents)
```python
# ✅ CORRECT - JOIN with agents table
result = await db.execute(
    select(Deployment)
    .join(Agent, Deployment.agent_id == Agent.id)
    .where(
        Deployment.id == deployment_id,
        Agent.user_id == current_user.id  # ← RLS via JOIN
    )
)
```

### Security Guarantees

- ✅ Users can only access their own data
- ✅ All queries filter by `user_id` from JWT token
- ✅ Returns 404 (not 403) for unauthorized access to prevent information leakage
- ✅ Foreign key CASCADE deletes ensure cleanup
- ✅ Indexes on `user_id` columns for fast queries

See [ROW_LEVEL_SECURITY.md](./backend/ROW_LEVEL_SECURITY.md) for full documentation.

---

## WebSocket Integration

For real-time agent generation updates (future feature):

```typescript
// Frontend
import { io } from 'socket.io-client';

const socket = io('http://localhost:8000', {
  auth: {
    token: localStorage.getItem('auth_token')
  }
});

socket.on('agent_update', (data) => {
  console.log('Agent status:', data.status);
});
```

```python
# Backend
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    # Emit real-time updates
    await manager.broadcast({
        "type": "agent_update",
        "agent_id": agent_id,
        "status": "generating"
    })
```

---

## Testing

### Backend Testing

```bash
cd backend

# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest tests/

# Test specific endpoint
pytest tests/test_agents.py -v

# Check health
curl http://localhost:8000/health
```

### Frontend Testing

```bash
cd frontend

# Install test dependencies
npm install --save-dev vitest @testing-library/react

# Run tests
npm test

# Test API service
npm test -- api.test.ts
```

### Manual Integration Testing

1. **Test Auth Flow**
```bash
# Register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass123"}'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass123"}'
# Save the access_token

# Get current user
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN"
```

2. **Test Agent CRUD**
```bash
# Create agent
curl -X POST http://localhost:8000/api/agents/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Agent",
    "vibe_prompt": "Create a simple chatbot"
  }'

# List agents
curl http://localhost:8000/api/agents/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get analytics
curl http://localhost:8000/api/analytics/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

3. **Test RLS (Cross-user access)**
```bash
# Create second user and login
# Try to access first user's agent with second user's token
# Should return 404 (not found)
```

---

## Deployment

### Backend Deployment (Render)

1. **Create Render service**
   - Type: Web Service
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

2. **Add environment variables**
   - Copy all from `.env.example`
   - Set production values

3. **Deploy**
   - Push to GitHub
   - Render auto-deploys on push

Backend URL: `https://your-app.onrender.com`

### Frontend Deployment (Vercel)

1. **Update environment variables**
```env
VITE_API_URL=https://your-backend.onrender.com
```

2. **Deploy**
```bash
cd frontend
npm run build
vercel --prod
```

3. **Update backend CORS**

Add your Vercel URL to `backend/app/core/config.py`:
```python
CORS_ORIGINS: List[str] = [
    "https://your-app.vercel.app",
    # ...
]
```

Frontend URL: `https://your-app.vercel.app`

---

## Troubleshooting

### CORS Errors

**Problem**: `Access to fetch at 'http://localhost:8000' from origin 'http://localhost:5173' has been blocked by CORS`

**Solution**: Add your frontend URL to backend CORS origins in `backend/app/core/config.py`

### Authentication Errors

**Problem**: `401 Unauthorized` or `No authentication token found`

**Solution**:
- Check token is stored in localStorage as `auth_token`
- Verify token hasn't expired (7 day expiry)
- Re-login to get fresh token

### Database Connection Errors

**Problem**: `Database connection failed`

**Solution**:
- Verify `DATABASE_URL` in `.env`
- Check Supabase project is active
- Remove `?pgbouncer=true` from connection string (handled automatically)

### RLS Issues

**Problem**: User can't see their own data

**Solution**:
- Verify `get_current_user` dependency is used
- Check query filters by `user_id`
- Look at logs for SQL queries

### Environment Variables Not Loading

**Problem**: Settings using default values

**Solution**:
- Ensure `.env` file exists (copy from `.env.example`)
- Check file is in correct directory (backend root)
- Restart server after changing `.env`

---

## Security Checklist

Before deploying to production:

- [ ] Change `SECRET_KEY` to a strong random value
- [ ] Set `DEBUG=false` in production
- [ ] Use environment variables (never commit secrets)
- [ ] Enable HTTPS for both frontend and backend
- [ ] Verify CORS origins are restrictive
- [ ] Test RLS - users can't access other users' data
- [ ] Review security logs regularly
- [ ] Set up error monitoring (Sentry)
- [ ] Configure rate limiting on sensitive endpoints
- [ ] Use strong password requirements
- [ ] Enable database backups (Supabase automatic backups)

---

## Additional Resources

- **API Documentation**: `http://localhost:8000/docs`
- **RLS Guide**: [ROW_LEVEL_SECURITY.md](./backend/ROW_LEVEL_SECURITY.md)
- **Architecture**: [ARCHITECTURE.md](./ARCHITECTURE.md)
- **Backend README**: [backend/README.md](./backend/README.md)
- **Frontend README**: [frontend/README.md](./frontend/README.md)

---

## Support

For issues or questions:
- Open an issue on GitHub
- Check `/docs` API documentation
- Review error logs in `logs/` directory

---

**Last Updated**: December 2025
**Version**: 1.0.0
