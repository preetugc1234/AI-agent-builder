"""
NodeRush - Main FastAPI Application
Production-ready backend for AI Agent Builder Platform
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
import uvicorn
import logging
import asyncio
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.middleware import setup_cors_middleware, setup_security_middleware
from app.db import database as db  # Import module, not variables
from app.api import agents, auth, analytics
from app.services.redis_service import redis_service
from app.websockets.manager import manager

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
    logger.info("🚀 Starting NodeRush Backend...")

    # Initialize Redis (Upstash)
    redis_connected = await redis_service.connect()
    if redis_connected:
        # Inject Redis into WebSocket manager
        manager.set_redis_service(redis_service)
        logger.info("✅ Redis connected and integrated with WebSocket manager")
    else:
        logger.warning("⚠️ Redis connection failed - running without Redis")

    # Initialize database (Supabase PostgreSQL)
    db_initialized = False
    for attempt in range(3):
        try:
            if db.init_database():
                # Create tables (use db.engine which is updated by init_database)
                if db.engine:
                    async with db.engine.begin() as conn:
                        await conn.run_sync(db.Base.metadata.create_all)
                    logger.info("✅ Database tables created")
                    db_initialized = True
                    break
                else:
                    logger.warning(f"Database init attempt {attempt + 1} failed: engine is None")
            else:
                logger.warning(f"Database init attempt {attempt + 1} failed: init_database returned False")
        except Exception as e:
            logger.warning(f"Database init attempt {attempt + 1} failed: {e}")
            await asyncio.sleep(2)

    if not db_initialized:
        logger.warning("⚠️ Database initialization failed - running in limited mode")

    logger.info("✅ Backend ready!")

    yield

    # Shutdown
    logger.info("🛑 Shutting down...")
    await redis_service.disconnect()
    logger.info("✅ Shutdown complete")


# Initialize FastAPI app
app = FastAPI(
    title="NodeRush API",
    description="AI-powered agent builder platform with 3-agent workflow",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Setup CORS middleware (must be added before other middleware)
setup_cors_middleware(app, settings.CORS_ORIGINS)

# Setup security middleware (logging, headers, etc.)
setup_security_middleware(app)


# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Comprehensive health check endpoint

    Checks connectivity to all services:
    - Database (Supabase PostgreSQL)
    - Redis (Upstash)
    - Application status

    Returns:
        - status: "healthy", "degraded", or "unhealthy"
        - checks: Individual service health status
        - timestamp: UTC timestamp of health check
        - version: API version
    """
    from datetime import datetime
    from sqlalchemy import text

    checks = {}

    # Check Database (Supabase PostgreSQL)
    try:
        if db.engine:
            async with db.engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            checks["database"] = {
                "status": "healthy",
                "message": "Connected to Supabase PostgreSQL"
            }
        else:
            checks["database"] = {
                "status": "unhealthy",
                "message": "Database engine not initialized"
            }
    except Exception as e:
        checks["database"] = {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}"
        }

    # Check Redis (Upstash)
    try:
        if redis_service.redis_client:
            await redis_service.redis_client.ping()
            checks["redis"] = {
                "status": "healthy",
                "message": "Connected to Upstash Redis"
            }
        else:
            checks["redis"] = {
                "status": "unhealthy",
                "message": "Redis client not initialized"
            }
    except Exception as e:
        checks["redis"] = {
            "status": "unhealthy",
            "message": f"Redis connection failed: {str(e)}"
        }

    # Determine overall status
    statuses = [check["status"] for check in checks.values()]

    if all(status == "healthy" for status in statuses):
        overall_status = "healthy"
    elif any(status == "healthy" for status in statuses):
        overall_status = "degraded"
    else:
        overall_status = "unhealthy"

    return {
        "status": overall_status,
        "service": "noderush-backend",
        "version": "1.0.0",
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to NodeRush API",
        "version": "1.0.0",
        "docs": "/docs"
    }


# Include API routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(agents.router, prefix="/api/agents", tags=["Agents"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])


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
