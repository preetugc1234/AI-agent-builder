"""
Authentication API Routes
JWT-based authentication with Redis sessions and audit logging
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, List

from app.db.database import get_db
from app.models.models import User
from app.schemas.schemas import UserCreate, UserLogin, UserResponse
from app.core.config import settings
from app.core.auth_middleware import AuthMiddleware, get_tier_permissions
from app.core.logging_config import get_logger
from app.core.exceptions import (
    AuthenticationError,
    ResourceAlreadyExistsError,
    ValidationError,
    SessionExpiredError
)
from app.services.redis_service import redis_service
from app.services.audit_service import audit_service

router = APIRouter()
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
logger = get_logger(__name__)


def hash_password(password: str) -> str:
    """
    Hash password with bcrypt

    Note: bcrypt has a 72-byte limit. For passwords >72 bytes,
    we hash them with SHA256 first to create a fixed-size input.
    """
    import hashlib

    # Check if password exceeds bcrypt's 72-byte limit
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        # Hash long passwords with SHA256 first (creates 64-byte hex string)
        password = hashlib.sha256(password_bytes).hexdigest()

    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against bcrypt hash

    Note: Applies same SHA256 hashing as hash_password()
    for passwords >72 bytes to ensure verification works.
    """
    import hashlib

    # Apply same transformation as hash_password()
    password_bytes = plain_password.encode('utf-8')
    if len(password_bytes) > 72:
        # Hash long passwords with SHA256 first (same as hash_password)
        plain_password = hashlib.sha256(password_bytes).hexdigest()

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


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    user_data: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user

    Creates a new user account with email and password.
    No email verification required in MVP.

    **Rate Limit**: 5 signups per hour per IP (handled by Cloudflare Worker)

    **Free Tier Limits**:
    - Max 10 agents
    - 5 agent creations per hour
    - 50k AI tokens per day
    """
    # Get client IP for logging
    client_ip = request.client.host if request.client else "unknown"

    # Create request logger with context
    request_logger = logger.bind(
        request_id=getattr(request.state, "request_id", "unknown"),
        ip_address=client_ip,
        email=user_data.email
    )

    request_logger.info("Signup request received")

    # Check if user exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        request_logger.warning("Signup failed: Email already registered")
        await audit_service.log_event(
            event_type="signup_failed",
            ip_address=client_ip,
            details={"email": user_data.email, "reason": "email_exists"},
            severity="warning"
        )
        raise ResourceAlreadyExistsError("User", user_data.email)

    # Validate password strength
    if len(user_data.password) < 8:
        request_logger.warning("Signup failed: Weak password")
        raise ValidationError(
            "Password must be at least 8 characters long",
            field="password"
        )

    # Validate email format (basic check)
    if "@" not in user_data.email or "." not in user_data.email:
        request_logger.warning("Signup failed: Invalid email format")
        raise ValidationError(
            "Invalid email format",
            field="email"
        )

    try:
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

        request_logger.info(
            "User registered successfully",
            user_id=str(new_user.id)
        )

        # Log successful signup audit event
        await audit_service.log_event(
            event_type="signup_success",
            user_id=str(new_user.id),
            ip_address=client_ip,
            details={"email": user_data.email},
            severity="info",
            db=db
        )

        return new_user

    except Exception as e:
        await db.rollback()
        request_logger.exception("Signup failed with database error")
        raise


@router.post("/login")
async def login(
    user_data: UserLogin,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Login user and return JWT access token

    Authenticates user and creates a Redis session.
    Token valid for 7 days with auto-refresh on activity.

    **Rate Limit**: 10 login attempts per minute per IP

    **Returns**:
    - access_token: JWT token for API requests
    - token_type: "bearer"
    - user: User profile information
    """
    # Get client IP for logging
    client_ip = request.client.host if request.client else "unknown"

    # Create request logger with context
    request_logger = logger.bind(
        request_id=getattr(request.state, "request_id", "unknown"),
        ip_address=client_ip,
        email=user_data.email
    )

    request_logger.info("Login request received")

    # Find user
    result = await db.execute(select(User).where(User.email == user_data.email))
    user = result.scalar_one_or_none()

    # Verify credentials
    if not user or not verify_password(user_data.password, user.password_hash):
        request_logger.warning("Login failed: Invalid credentials")

        # Log failed login audit event
        await audit_service.log_login_failed(
            email=user_data.email,
            ip_address=client_ip,
            reason="invalid_credentials",
            db=db
        )

        raise AuthenticationError(
            "Incorrect email or password",
            details={"email": user_data.email}
        )

    # Create access token with permissions (7 days expiry)
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
        "login_time": datetime.utcnow().isoformat(),
        "ip_address": client_ip
    }
    await redis_service.set_session(
        session_id=str(user.id),
        user_data=session_data,
        expire_seconds=604800  # 7 days (7 * 24 * 60 * 60)
    )

    request_logger.info(
        "User logged in successfully",
        user_id=str(user.id)
    )

    # Log successful login audit event
    await audit_service.log_login_success(
        user_id=str(user.id),
        ip_address=client_ip,
        db=db
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # seconds
        "user": {
            "id": str(user.id),
            "email": user.email,
            "subscription_tier": user.subscription_tier,
            "subscription_status": user.subscription_status,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }
    }


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Get current user profile
    """
    return current_user


@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Logout user

    Deletes the user's Redis session, invalidating the JWT token.
    The token will still be valid until it expires, but the session check will fail.
    """
    # Get client IP for logging
    client_ip = request.client.host if request.client else "unknown"

    # Create request logger with context
    request_logger = logger.bind(
        request_id=getattr(request.state, "request_id", "unknown"),
        user_id=str(current_user.id),
        ip_address=client_ip
    )

    request_logger.info("Logout request received")

    # Delete session from Redis
    deleted = await redis_service.delete_session(str(current_user.id))

    if deleted:
        request_logger.info("User logged out successfully")

        # Log logout audit event
        await audit_service.log_event(
            event_type="logout",
            user_id=str(current_user.id),
            ip_address=client_ip,
            severity="info"
        )

        return {
            "message": "Logged out successfully",
            "user_id": str(current_user.id)
        }
    else:
        request_logger.warning("Logout failed: Session not found")
        return {
            "message": "Already logged out",
            "user_id": str(current_user.id)
        }


@router.post("/refresh")
async def refresh_token(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh JWT access token

    Returns a new JWT token with extended expiration.
    Useful for keeping users logged in without re-authentication.

    **Note**: Requires valid JWT token in Authorization header
    """
    # Get client IP for logging
    client_ip = request.client.host if request.client else "unknown"

    # Create request logger with context
    request_logger = logger.bind(
        request_id=getattr(request.state, "request_id", "unknown"),
        user_id=str(current_user.id),
        ip_address=client_ip
    )

    request_logger.info("Token refresh request received")

    # Verify session still exists
    session_data = await redis_service.get_session(str(current_user.id))

    if not session_data:
        request_logger.warning("Token refresh failed: Session not found")
        raise SessionExpiredError()

    # Create new access token
    new_access_token = create_access_token(
        user_id=str(current_user.id),
        email=current_user.email,
        tier=current_user.subscription_tier
    )

    # Refresh session TTL in Redis
    session_data["last_refresh"] = datetime.utcnow().isoformat()
    await redis_service.set_session(
        session_id=str(current_user.id),
        user_data=session_data,
        expire_seconds=604800  # 7 days
    )

    request_logger.info("Token refreshed successfully")

    # Log token refresh audit event
    await audit_service.log_event(
        event_type="token_refreshed",
        user_id=str(current_user.id),
        ip_address=client_ip,
        severity="info"
    )

    return {
        "access_token": new_access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": {
            "id": str(current_user.id),
            "email": current_user.email,
            "subscription_tier": current_user.subscription_tier
        }
    }
