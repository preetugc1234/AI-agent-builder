"""
Database configuration and session management
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Base class for models
Base = declarative_base()

# Initialize engine and session as None
engine = None
AsyncSessionLocal = None

def init_database():
    """Initialize database engine and session factory"""
    global engine, AsyncSessionLocal

    try:
        # Log the DATABASE_URL (without password for security)
        url_parts = settings.DATABASE_URL.split('@')
        safe_url = f"{url_parts[0].split(':')[0]}:***@{url_parts[1]}" if len(url_parts) > 1 else "***"
        logger.info(f"Initializing database connection to: {safe_url}")

        # Create async engine with connection pooling
        # Pool settings optimized for Supabase free tier (500 MB, max 10 connections)
        engine = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.DEBUG,
            future=True,
            pool_pre_ping=True,        # Verify connection health before using
            pool_size=5,                # Reduced to 5 for free tier
            max_overflow=10,            # 10 additional connections on demand
            pool_recycle=3600,          # Recycle connections after 1 hour (Supabase best practice)
            connect_args={
                "server_settings": {
                    "application_name": "noderush_backend"
                }
            }
        )

        # Create async session factory
        AsyncSessionLocal = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False
        )
        logger.info("✅ Database engine initialized successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
        engine = None
        AsyncSessionLocal = None
        return False


# Dependency to get database session
async def get_db() -> AsyncSession:
    """
    Dependency function to get database session
    Usage: db: AsyncSession = Depends(get_db)
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
