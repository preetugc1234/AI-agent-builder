"""
Authentication Middleware
Handles JWT validation, permission checking, and session management
"""

from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from typing import Optional, List, Callable
from functools import wraps
import logging

from app.core.config import settings
from app.services.redis_service import redis_service

logger = logging.getLogger(__name__)

security = HTTPBearer()


class AuthMiddleware:
    """
    Authentication middleware for FastAPI
    Validates JWT tokens and manages user sessions
    """

    @staticmethod
    async def decode_token(token: str) -> dict:
        """
        Decode and validate JWT token

        Returns:
            dict: Token payload containing user_id, email, tier, permissions

        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )

            user_id: str = payload.get("sub")
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token: missing user ID",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            return payload

        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except JWTError as e:
            logger.error(f"JWT validation error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    @staticmethod
    async def verify_session(user_id: str) -> Optional[dict]:
        """
        Verify user session exists in Redis

        Args:
            user_id: User UUID

        Returns:
            dict: Session data if valid, None if not found
        """
        try:
            session_data = await redis_service.get_session(user_id)

            # Refresh session TTL on activity (7 days)
            if session_data:
                await redis_service.set_session(
                    session_id=user_id,
                    user_data=session_data,
                    expire_seconds=604800  # 7 days
                )

            return session_data

        except Exception as e:
            logger.error(f"Session verification error: {str(e)}")
            return None

    @staticmethod
    def check_permissions(required_permissions: List[str], user_permissions: List[str]) -> bool:
        """
        Check if user has required permissions

        Args:
            required_permissions: List of required permissions
            user_permissions: List of user's permissions

        Returns:
            bool: True if user has all required permissions
        """
        return all(perm in user_permissions for perm in required_permissions)


# Permission decorators
def require_permissions(*permissions: str):
    """
    Decorator to require specific permissions for an endpoint

    Usage:
        @require_permissions("read:agents", "write:agents")
        async def create_agent(...):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request from kwargs or args
            request: Optional[Request] = kwargs.get('request') or next(
                (arg for arg in args if isinstance(arg, Request)), None
            )

            if not request:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Request object not found"
                )

            # Get token from request state (set by dependency injection)
            token_payload = getattr(request.state, 'user_payload', None)

            if not token_payload:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )

            user_permissions = token_payload.get("permissions", [])

            if not AuthMiddleware.check_permissions(list(permissions), user_permissions):
                logger.warning(
                    f"Permission denied for user {token_payload.get('sub')}: "
                    f"required {permissions}, has {user_permissions}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required permissions: {', '.join(permissions)}"
                )

            return await func(*args, **kwargs)

        return wrapper
    return decorator


def require_tier(min_tier: str):
    """
    Decorator to require minimum subscription tier

    Usage:
        @require_tier("pro")
        async def advanced_feature(...):
            ...

    Tier hierarchy: free < pro < enterprise
    """
    tier_levels = {
        "free": 0,
        "pro": 1,
        "enterprise": 2
    }

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request: Optional[Request] = kwargs.get('request') or next(
                (arg for arg in args if isinstance(arg, Request)), None
            )

            if not request:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Request object not found"
                )

            token_payload = getattr(request.state, 'user_payload', None)

            if not token_payload:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )

            user_tier = token_payload.get("tier", "free")
            user_tier_level = tier_levels.get(user_tier, 0)
            required_tier_level = tier_levels.get(min_tier, 0)

            if user_tier_level < required_tier_level:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"This feature requires '{min_tier}' tier or higher. Your tier: '{user_tier}'"
                )

            return await func(*args, **kwargs)

        return wrapper
    return decorator


# Helper function to get permission list based on tier
def get_tier_permissions(tier: str) -> List[str]:
    """
    Get default permissions for a subscription tier

    Args:
        tier: Subscription tier (free, pro, enterprise)

    Returns:
        List of permission strings
    """
    permissions = {
        "free": [
            "read:agents",
            "write:agents",
            "execute:agents",
            "read:integrations",
        ],
        "pro": [
            "read:agents",
            "write:agents",
            "execute:agents",
            "deploy:agents",
            "read:integrations",
            "write:integrations",
            "read:analytics",
        ],
        "enterprise": [
            "read:agents",
            "write:agents",
            "execute:agents",
            "deploy:agents",
            "delete:agents",
            "read:integrations",
            "write:integrations",
            "delete:integrations",
            "read:analytics",
            "write:analytics",
            "admin:users",
            "admin:billing",
        ]
    }

    return permissions.get(tier, permissions["free"])
