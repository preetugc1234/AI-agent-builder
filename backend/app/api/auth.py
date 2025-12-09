"""
Authentication API routes
Supabase Auth integration with Redis sessions
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, List
import logging

from app.db.database import get_db
from app.models.models import User
from app.schemas.schemas import UserCreate, UserLogin, UserResponse
from app.core.config import settings
from app.core.auth_middleware import AuthMiddleware, get_tier_permissions
from app.services.redis_service import redis_service

router = APIRouter()
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
logger = logging.getLogger(__name__)


def hash_password(password: str) -> str:
    """Hash password"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    user_id: str,
    email: str,
    tier: str,
    permissions: Optional[List[str]] = None,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT access token with permissions

    Args:
        user_id: User UUID
        email: User email
        tier: Subscription tier (free, pro, enterprise)
        permissions: Custom permissions (defaults to tier permissions)
        expires_delta: Token expiration time

    Returns:
        Encoded JWT token
    """
    if permissions is None:
        permissions = get_tier_permissions(tier)

    # Token payload matching ARCHITECTURE.md spec
    payload = {
        "sub": user_id,
        "email": email,
        "tier": tier,
        "permissions": permissions,
        "iat": datetime.utcnow(),
    }

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload.update({"exp": expire})

    encoded_jwt = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    return encoded_jwt


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    request: Request = None,
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get current authenticated user
    Validates JWT token and verifies session in Redis
    Auto-refreshes session TTL on activity
    """
    try:
        token = credentials.credentials

        # Decode and validate token
        payload = await AuthMiddleware.decode_token(token)
        user_id: str = payload.get("sub")

        # Verify session in Redis (auto-refreshes TTL)
        session_data = await AuthMiddleware.verify_session(user_id)

        if not session_data:
            logger.warning(f"Session not found for user {user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired. Please login again.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Get user from database
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Store token payload in request state for permission checks
        if request:
            request.state.user_payload = payload

        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db), request: Request = None):
    """
    Register a new user (no email verification required)
    """
    # Check if user exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Validate password strength (minimum 8 characters)
    if len(user_data.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )

    # Create new user
    hashed_password = hash_password(user_data.password)
    new_user = User(
        email=user_data.email,
        password_hash=hashed_password,
        subscription_tier="free",
        subscription_status="active"
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    logger.info(f"New user registered: {user_data.email}")

    return new_user


@router.post("/login")
async def login(user_data: UserLogin, db: AsyncSession = Depends(get_db), request: Request = None):
    """
    Login user and return access token
    Creates Redis session for scalability
    """
    # Find user
    result = await db.execute(select(User).where(User.email == user_data.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(user_data.password, user.password_hash):
        # Log failed login attempt
        logger.warning(f"Failed login attempt for email: {user_data.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    # Create access token with permissions (7 days expiry from ARCHITECTURE.md)
    access_token = create_access_token(
        user_id=str(user.id),
        email=user.email,
        tier=user.subscription_tier
    )

    # Store session in Redis (for real-time session management)
    session_data = {
        "user_id": str(user.id),
        "email": user.email,
        "subscription_tier": user.subscription_tier,
        "login_time": datetime.utcnow().isoformat()
    }
    await redis_service.set_session(
        session_id=str(user.id),
        user_data=session_data,
        expire_seconds=604800  # 7 days
    )

    logger.info(f"User logged in: {user.email}")

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "subscription_tier": user.subscription_tier,
            "subscription_status": user.subscription_status
        }
    }


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Get current user profile
    """
    return current_user


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """
    Logout user (delete Redis session)
    """
    # Delete session from Redis
    await redis_service.delete_session(str(current_user.id))

    logger.info(f"User logged out: {current_user.email}")

    return {"message": "Logged out successfully"}
