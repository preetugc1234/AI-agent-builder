"""
NodeRush - Main FastAPI Application
Production-ready backend for AI Agent Builder Platform
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging
import asyncio
from contextlib import asynccontextmanager

from app.core.config import settings
from app.db.database import init_database, engine, Base
from app.api import agents, auth

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

    # Initialize database
    db_initialized = False
    for attempt in range(3):
        try:
            if init_database():
                # Create tables
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)
                logger.info("✅ Database tables created")
                db_initialized = True
                break
        except Exception as e:
            logger.warning(f"Database init attempt {attempt + 1} failed: {e}")
            await asyncio.sleep(2)

    if not db_initialized:
        logger.warning("⚠️ Database initialization failed - running in limited mode")

    logger.info("✅ Backend ready!")

    yield

    # Shutdown
    logger.info("✅ Shutdown complete")


# Initialize FastAPI app
app = FastAPI(
    title="NodeRush API",
    description="AI-powered agent builder platform with 3-agent workflow",
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
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "noderush-backend",
        "version": "1.0.0"
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
