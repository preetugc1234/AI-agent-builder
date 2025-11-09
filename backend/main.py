"""
VibeAgent Forge - Main FastAPI Application
Production-ready backend for AI Agent Builder Platform
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging
from contextlib import asynccontextmanager

from app.core.config import settings
from app.api import agents, auth, integrations, execution, deployments
from app.websockets.manager import manager
from app.websockets.handlers import handle_websocket_message
from app.db.database import engine, Base

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events - startup and shutdown"""
    # Startup
    logger.info("🚀 Starting VibeAgent Forge Backend...")

    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("✅ Database tables created")
    logger.info("✅ VibeAgent Forge Backend is ready!")

    yield

    # Shutdown
    logger.info("🔄 Shutting down VibeAgent Forge Backend...")
    await engine.dispose()
    logger.info("✅ Shutdown complete")


# Initialize FastAPI app
app = FastAPI(
    title="VibeAgent Forge API",
    description="AI-powered agent builder platform with real-time execution",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for AWS ECS/ALB"""
    return {
        "status": "healthy",
        "service": "vibeagent-forge-backend",
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to VibeAgent Forge API",
        "version": "1.0.0",
        "docs": "/docs"
    }


# WebSocket endpoint for real-time agent operations
@app.websocket("/ws/agent/{agent_id}")
async def websocket_agent_endpoint(websocket: WebSocket, agent_id: str):
    """
    WebSocket endpoint for real-time agent operations
    - AI code generation streaming
    - Agent execution monitoring
    - Deployment progress tracking
    - Terminal output streaming
    """
    connection_id = await manager.connect(websocket, agent_id)
    logger.info(f"WebSocket connected: {connection_id} for agent: {agent_id}")

    try:
        while True:
            # Receive messages from frontend
            data = await websocket.receive_json()

            # Handle the message
            await handle_websocket_message(agent_id, connection_id, data)

    except WebSocketDisconnect:
        await manager.disconnect(websocket, connection_id)
        logger.info(f"WebSocket disconnected: {connection_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await manager.disconnect(websocket, connection_id)


# Include API routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(agents.router, prefix="/api/agents", tags=["Agents"])
app.include_router(integrations.router, prefix="/api/integrations", tags=["Integrations"])
app.include_router(execution.router, prefix="/api/execution", tags=["Execution"])
app.include_router(deployments.router, prefix="/api/deployments", tags=["Deployments"])


# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.DEBUG else "An error occurred"
        }
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )
