"""
Token Bucket Rate Limiter

A sophisticated rate limiting implementation using the Token Bucket Algorithm.
Supports multiple time windows, user tiers, and resource-specific limits.

Features:
- True Token Bucket Algorithm with refill over time
- Multiple windows (per minute, per hour, per day)
- Per-user and per-IP rate limiting
- Resource-specific rate limits
- Tier-based limits (free, pro, enterprise)
- FastAPI decorator and middleware support
- Rate limit headers in responses
- Fail-open on Redis errors
"""

import time
import logging
from typing import Optional, Dict, Any, Callable, List
from functools import wraps
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class RateLimitWindow(Enum):
    """Rate limit time windows"""
    SECOND = 1
    MINUTE = 60
    HOUR = 3600
    DAY = 86400


@dataclass
class RateLimitResult:
    """Result of a rate limit check"""
    allowed: bool
    current_tokens: float
    max_tokens: int
    remaining: int
    reset_at: int
    retry_after: int
    resource: str

    def to_headers(self) -> Dict[str, str]:
        """Convert to HTTP response headers"""
        return {
            "X-RateLimit-Limit": str(self.max_tokens),
            "X-RateLimit-Remaining": str(self.remaining),
            "X-RateLimit-Reset": str(self.reset_at),
            "X-RateLimit-Resource": self.resource,
        }


# Production rate limits aligned with ARCHITECTURE.md
RATE_LIMIT_PRESETS = {
    # Authentication
    "auth:signup": {
        "per_hour": 5,
        "per_day": 10,
        "bucket_size": 5,
        "refill_rate": 5 / 3600,  # 5 per hour
    },
    "auth:login": {
        "per_minute": 10,
        "per_hour": 100,
        "bucket_size": 10,
        "refill_rate": 10 / 60,  # 10 per minute
    },

    # Agent operations
    "agent:create": {
        "per_hour": 5,
        "per_day": 20,
        "bucket_size": 5,
        "refill_rate": 5 / 3600,  # 5 per hour
    },
    "agent:execute": {
        "per_hour": 10,
        "per_day": 50,
        "bucket_size": 10,
        "refill_rate": 10 / 3600,  # 10 per hour
    },
    "agent:read": {
        "per_minute": 60,
        "per_hour": 500,
        "bucket_size": 60,
        "refill_rate": 1,  # 1 per second
    },

    # General API
    "api:general": {
        "per_minute": 60,
        "per_hour": 1000,
        "bucket_size": 60,
        "refill_rate": 1,  # 1 per second
    },

    # WebSocket
    "websocket:connect": {
        "per_minute": 10,
        "concurrent": 3,
        "bucket_size": 10,
        "refill_rate": 10 / 60,
    },

    # AI tokens
    "ai:generate": {
        "per_minute": 5,
        "per_hour": 30,
        "per_day": 100,
        "bucket_size": 5,
        "refill_rate": 5 / 60,
    },
}

# Tier multipliers for rate limits
TIER_MULTIPLIERS = {
    "free": 1.0,
    "pro": 5.0,
    "enterprise": 20.0,
}


class TokenBucketRateLimiter:
    """
    Token Bucket Rate Limiter using Redis

    The token bucket algorithm works as follows:
    1. Each user has a "bucket" that can hold up to `bucket_size` tokens
    2. Tokens are added to the bucket at `refill_rate` per second
    3. Each request consumes 1 token
    4. If the bucket is empty, the request is denied
    5. The bucket can never exceed `bucket_size` tokens

    Benefits over simple counting:
    - Allows bursts up to bucket_size
    - Smooths out request rate over time
    - More fair for irregular usage patterns
    """

    def __init__(self, redis_service):
        """
        Initialize rate limiter with Redis connection

        Args:
            redis_service: RedisService instance for storage
        """
        self.redis = redis_service
        self.presets = RATE_LIMIT_PRESETS
        self.tier_multipliers = TIER_MULTIPLIERS

    async def check_limit(
        self,
        identifier: str,
        resource: str,
        max_tokens: Optional[int] = None,
        refill_rate: Optional[float] = None,
        bucket_size: Optional[int] = None,
        tier: str = "free",
        cost: int = 1
    ) -> RateLimitResult:
        """
        Check if request is within rate limit using token bucket algorithm

        Args:
            identifier: User ID or IP address
            resource: Resource name (e.g., 'agent:create', 'api:general')
            max_tokens: Maximum tokens (uses preset if not provided)
            refill_rate: Tokens per second to refill
            bucket_size: Maximum bucket capacity
            tier: User tier for multiplier ('free', 'pro', 'enterprise')
            cost: Number of tokens this request consumes (default 1)

        Returns:
            RateLimitResult with allowed status and metadata
        """
        try:
            # Get preset if not provided
            preset = self.presets.get(resource, self.presets.get("api:general", {}))

            if max_tokens is None:
                max_tokens = preset.get("bucket_size", 60)
            if refill_rate is None:
                refill_rate = preset.get("refill_rate", 1.0)
            if bucket_size is None:
                bucket_size = preset.get("bucket_size", max_tokens)

            # Apply tier multiplier
            multiplier = self.tier_multipliers.get(tier, 1.0)
            max_tokens = int(max_tokens * multiplier)
            bucket_size = int(bucket_size * multiplier)
            refill_rate = refill_rate * multiplier

            # Redis key for this bucket
            key = f"ratelimit:bucket:{resource}:{identifier}"

            # Get current bucket state
            state = await self.redis.redis_client.hgetall(key)

            now = time.time()

            if not state:
                # First request - initialize full bucket
                current_tokens = float(bucket_size)
                last_refill = now
            else:
                current_tokens = float(state.get("tokens", bucket_size))
                last_refill = float(state.get("last_refill", now))

            # Calculate tokens to add based on time passed
            time_passed = now - last_refill
            refill_amount = time_passed * refill_rate
            current_tokens = min(bucket_size, current_tokens + refill_amount)

            # Check if we have enough tokens
            if current_tokens >= cost:
                # Consume tokens
                current_tokens -= cost
                allowed = True
                remaining = int(current_tokens)
            else:
                # Not enough tokens
                allowed = False
                remaining = 0

            # Calculate when bucket will have tokens again
            if current_tokens < cost:
                tokens_needed = cost - current_tokens
                seconds_until_refill = int(tokens_needed / refill_rate) + 1
            else:
                seconds_until_refill = 0

            # Update bucket state
            await self.redis.redis_client.hset(key, mapping={
                "tokens": str(current_tokens),
                "last_refill": str(now)
            })
            await self.redis.redis_client.expire(key, 86400)  # 24h expiry

            reset_at = int(now) + seconds_until_refill

            result = RateLimitResult(
                allowed=allowed,
                current_tokens=current_tokens,
                max_tokens=bucket_size,
                remaining=remaining,
                reset_at=reset_at,
                retry_after=seconds_until_refill,
                resource=resource
            )

            if not allowed:
                logger.warning(
                    f"Rate limit exceeded for {identifier} on {resource}. "
                    f"Tokens: {current_tokens:.2f}/{bucket_size}, Retry in: {seconds_until_refill}s"
                )

            return result

        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            # Fail open - allow request if Redis fails
            return RateLimitResult(
                allowed=True,
                current_tokens=1,
                max_tokens=max_tokens or 60,
                remaining=1,
                reset_at=int(time.time()) + 60,
                retry_after=0,
                resource=resource
            )

    async def check_sliding_window(
        self,
        identifier: str,
        resource: str,
        limit: int,
        window: RateLimitWindow,
        tier: str = "free"
    ) -> RateLimitResult:
        """
        Check rate limit using sliding window counter

        This is simpler than token bucket and useful for strict limits
        like "max 5 signups per hour" where bursts are not desired.

        Args:
            identifier: User ID or IP address
            resource: Resource name
            limit: Maximum requests in window
            window: Time window (MINUTE, HOUR, DAY)
            tier: User tier for multiplier

        Returns:
            RateLimitResult with allowed status
        """
        try:
            # Apply tier multiplier
            multiplier = self.tier_multipliers.get(tier, 1.0)
            limit = int(limit * multiplier)

            key = f"ratelimit:window:{resource}:{identifier}:{window.name}"
            now = time.time()
            window_start = now - window.value

            # Use sorted set for sliding window
            # Remove old entries
            await self.redis.redis_client.zremrangebyscore(key, 0, window_start)

            # Count current entries
            current = await self.redis.redis_client.zcard(key)

            if current >= limit:
                # Get oldest entry to calculate reset time
                oldest = await self.redis.redis_client.zrange(key, 0, 0, withscores=True)
                if oldest:
                    reset_at = int(oldest[0][1]) + window.value
                else:
                    reset_at = int(now) + window.value

                return RateLimitResult(
                    allowed=False,
                    current_tokens=0,
                    max_tokens=limit,
                    remaining=0,
                    reset_at=reset_at,
                    retry_after=reset_at - int(now),
                    resource=resource
                )

            # Add current request
            await self.redis.redis_client.zadd(key, {str(now): now})
            await self.redis.redis_client.expire(key, window.value + 60)

            return RateLimitResult(
                allowed=True,
                current_tokens=limit - current - 1,
                max_tokens=limit,
                remaining=limit - current - 1,
                reset_at=int(now) + window.value,
                retry_after=0,
                resource=resource
            )

        except Exception as e:
            logger.error(f"Sliding window check failed: {e}")
            return RateLimitResult(
                allowed=True,
                current_tokens=1,
                max_tokens=limit,
                remaining=1,
                reset_at=int(time.time()) + window.value,
                retry_after=0,
                resource=resource
            )

    async def check_concurrent_limit(
        self,
        identifier: str,
        resource: str,
        max_concurrent: int,
        tier: str = "free"
    ) -> RateLimitResult:
        """
        Check concurrent connection/operation limit

        Used for things like WebSocket connections where we need
        to limit how many active connections a user can have.

        Args:
            identifier: User ID
            resource: Resource name
            max_concurrent: Maximum concurrent operations
            tier: User tier

        Returns:
            RateLimitResult with allowed status
        """
        try:
            multiplier = self.tier_multipliers.get(tier, 1.0)
            max_concurrent = int(max_concurrent * multiplier)

            key = f"ratelimit:concurrent:{resource}:{identifier}"

            current = await self.redis.redis_client.scard(key)

            return RateLimitResult(
                allowed=current < max_concurrent,
                current_tokens=max_concurrent - current,
                max_tokens=max_concurrent,
                remaining=max(0, max_concurrent - current),
                reset_at=0,  # No reset for concurrent limits
                retry_after=0 if current < max_concurrent else 30,
                resource=resource
            )

        except Exception as e:
            logger.error(f"Concurrent limit check failed: {e}")
            return RateLimitResult(
                allowed=True,
                current_tokens=1,
                max_tokens=max_concurrent,
                remaining=1,
                reset_at=0,
                retry_after=0,
                resource=resource
            )

    async def add_concurrent_connection(
        self,
        identifier: str,
        resource: str,
        connection_id: str,
        ttl: int = 3600
    ) -> bool:
        """Add a connection to the concurrent set"""
        try:
            key = f"ratelimit:concurrent:{resource}:{identifier}"
            await self.redis.redis_client.sadd(key, connection_id)
            await self.redis.redis_client.expire(key, ttl)
            return True
        except Exception as e:
            logger.error(f"Failed to add concurrent connection: {e}")
            return False

    async def remove_concurrent_connection(
        self,
        identifier: str,
        resource: str,
        connection_id: str
    ) -> bool:
        """Remove a connection from the concurrent set"""
        try:
            key = f"ratelimit:concurrent:{resource}:{identifier}"
            await self.redis.redis_client.srem(key, connection_id)
            return True
        except Exception as e:
            logger.error(f"Failed to remove concurrent connection: {e}")
            return False

    async def reset_limit(self, identifier: str, resource: str) -> bool:
        """Reset rate limit for a user/resource"""
        try:
            patterns = [
                f"ratelimit:bucket:{resource}:{identifier}",
                f"ratelimit:window:{resource}:{identifier}:*",
                f"ratelimit:concurrent:{resource}:{identifier}",
            ]

            for pattern in patterns:
                if "*" in pattern:
                    keys = await self.redis.redis_client.keys(pattern)
                    if keys:
                        await self.redis.redis_client.delete(*keys)
                else:
                    await self.redis.redis_client.delete(pattern)

            return True
        except Exception as e:
            logger.error(f"Failed to reset rate limit: {e}")
            return False

    async def get_limit_status(
        self,
        identifier: str,
        resource: str
    ) -> Dict[str, Any]:
        """Get current rate limit status for a user/resource"""
        try:
            key = f"ratelimit:bucket:{resource}:{identifier}"
            state = await self.redis.redis_client.hgetall(key)

            if not state:
                preset = self.presets.get(resource, {})
                return {
                    "resource": resource,
                    "tokens": preset.get("bucket_size", 60),
                    "max_tokens": preset.get("bucket_size", 60),
                    "last_activity": None,
                    "status": "fresh"
                }

            return {
                "resource": resource,
                "tokens": float(state.get("tokens", 0)),
                "max_tokens": self.presets.get(resource, {}).get("bucket_size", 60),
                "last_activity": float(state.get("last_refill", 0)),
                "status": "active"
            }

        except Exception as e:
            logger.error(f"Failed to get limit status: {e}")
            return {"resource": resource, "error": str(e)}


def rate_limit(
    resource: str = "api:general",
    limit: Optional[int] = None,
    window: RateLimitWindow = RateLimitWindow.MINUTE,
    use_token_bucket: bool = True,
    cost: int = 1,
    use_ip: bool = False
):
    """
    Rate limit decorator for FastAPI endpoints

    Usage:
        @app.get("/api/agents")
        @rate_limit(resource="agent:read", limit=60, window=RateLimitWindow.MINUTE)
        async def get_agents(request: Request):
            ...

    Args:
        resource: Resource identifier for rate limit lookup
        limit: Maximum requests (uses preset if not provided)
        window: Time window for sliding window (ignored if use_token_bucket=True)
        use_token_bucket: Use token bucket (True) or sliding window (False)
        cost: Number of tokens/requests this endpoint costs
        use_ip: Use IP address instead of user ID for identifier
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get request from args or kwargs
            request = kwargs.get("request")
            if request is None:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break

            if request is None:
                # No request object, can't rate limit
                return await func(*args, **kwargs)

            # Get rate limiter from app state
            rate_limiter = getattr(request.app.state, "rate_limiter", None)
            if rate_limiter is None:
                # Rate limiter not configured, allow request
                return await func(*args, **kwargs)

            # Get identifier (user ID or IP)
            if use_ip:
                identifier = request.client.host if request.client else "unknown"
            else:
                # Try to get user ID from request state
                user = getattr(request.state, "user", None)
                if user:
                    identifier = str(getattr(user, "id", "unknown"))
                else:
                    # Fall back to IP
                    identifier = request.client.host if request.client else "unknown"

            # Get user tier
            user = getattr(request.state, "user", None)
            tier = getattr(user, "subscription_tier", "free") if user else "free"

            # Check rate limit
            if use_token_bucket:
                result = await rate_limiter.check_limit(
                    identifier=identifier,
                    resource=resource,
                    max_tokens=limit,
                    tier=tier,
                    cost=cost
                )
            else:
                result = await rate_limiter.check_sliding_window(
                    identifier=identifier,
                    resource=resource,
                    limit=limit or 60,
                    window=window,
                    tier=tier
                )

            if not result.allowed:
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": "RATE_LIMIT_EXCEEDED",
                        "message": f"Rate limit exceeded for {resource}. Retry in {result.retry_after} seconds.",
                        "retry_after": result.retry_after,
                        "limit": result.max_tokens,
                        "remaining": 0,
                        "resource": resource
                    },
                    headers=result.to_headers()
                )

            # Call the actual function
            response = await func(*args, **kwargs)

            # Add rate limit headers if response is a Response object
            if isinstance(response, Response):
                for key, value in result.to_headers().items():
                    response.headers[key] = value

            return response

        return wrapper
    return decorator


async def rate_limit_middleware(request: Request, call_next):
    """
    Global rate limiting middleware

    Applies basic rate limiting to all requests before they reach endpoints.
    Individual endpoints can have more specific limits via the decorator.

    Usage:
        app.middleware("http")(rate_limit_middleware)
    """
    # Skip rate limiting for health checks
    if request.url.path in ["/health", "/", "/docs", "/redoc", "/openapi.json"]:
        return await call_next(request)

    # Get rate limiter
    rate_limiter = getattr(request.app.state, "rate_limiter", None)
    if rate_limiter is None:
        return await call_next(request)

    # Use IP for global rate limit
    identifier = request.client.host if request.client else "unknown"

    # Check global rate limit (100 requests per minute per IP)
    result = await rate_limiter.check_limit(
        identifier=identifier,
        resource="api:global",
        max_tokens=100,
        refill_rate=100/60,  # 100 per minute
        bucket_size=100
    )

    if not result.allowed:
        return JSONResponse(
            status_code=429,
            content={
                "error": "RATE_LIMIT_EXCEEDED",
                "message": "Global rate limit exceeded. Please slow down.",
                "retry_after": result.retry_after
            },
            headers=result.to_headers()
        )

    # Proceed with request
    response = await call_next(request)

    # Add rate limit headers
    for key, value in result.to_headers().items():
        response.headers[key] = value

    return response


# Singleton instance - initialized in main.py
rate_limiter: Optional[TokenBucketRateLimiter] = None


def init_rate_limiter(redis_service) -> TokenBucketRateLimiter:
    """Initialize the rate limiter singleton"""
    global rate_limiter
    rate_limiter = TokenBucketRateLimiter(redis_service)
    return rate_limiter


def get_rate_limiter() -> Optional[TokenBucketRateLimiter]:
    """Get the rate limiter singleton"""
    return rate_limiter


def require_quota(
    quota_type: str,
    required: int = 1,
    increment_on_success: bool = True
):
    """
    Quota enforcement decorator for FastAPI endpoints

    Usage:
        @app.post("/api/agents")
        @require_quota(quota_type="agents:total", required=1)
        async def create_agent(request: Request):
            ...

    Args:
        quota_type: Type of quota to check (e.g., 'agents:total', 'executions:hour')
        required: Amount required for this operation (default 1)
        increment_on_success: Increment quota after successful operation (default True)
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get request from args or kwargs
            request = kwargs.get("request")
            if request is None:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break

            if request is None:
                # No request object, can't check quota
                return await func(*args, **kwargs)

            # Get quota service from app state
            quota_service = getattr(request.app.state, "quota_service", None)
            if quota_service is None:
                # Quota service not configured, allow request
                return await func(*args, **kwargs)

            # Get user from request state
            user = getattr(request.state, "user", None)
            if user is None:
                # No user, can't check per-user quota
                return await func(*args, **kwargs)

            user_id = str(getattr(user, "id", "unknown"))
            tier = getattr(user, "subscription_tier", "free")

            # Check quota
            result = await quota_service.check_quota(
                user_id=user_id,
                quota_type=quota_type,
                tier=tier,
                required=required
            )

            if not result.allowed:
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "QUOTA_EXCEEDED",
                        "message": result.message or f"Quota exceeded for {quota_type}",
                        "quota_type": quota_type,
                        "current": result.current,
                        "limit": result.limit,
                        "remaining": result.remaining,
                        "tier": tier,
                        "reset_at": result.reset_at
                    },
                    headers={
                        "X-Quota-Limit": str(result.limit),
                        "X-Quota-Remaining": str(result.remaining),
                        "X-Quota-Type": quota_type,
                    }
                )

            # Call the actual function
            response = await func(*args, **kwargs)

            # Increment quota on success
            if increment_on_success:
                await quota_service.increment_quota(
                    user_id=user_id,
                    quota_type=quota_type,
                    amount=required
                )

            # Add quota headers to response if possible
            if isinstance(response, Response):
                response.headers["X-Quota-Limit"] = str(result.limit)
                response.headers["X-Quota-Remaining"] = str(max(0, result.remaining - required))
                response.headers["X-Quota-Type"] = quota_type

            return response

        return wrapper
    return decorator


def rate_limit_and_quota(
    rate_resource: str = "api:general",
    quota_type: Optional[str] = None,
    rate_limit_value: Optional[int] = None,
    quota_required: int = 1,
    rate_cost: int = 1,
    increment_quota: bool = True
):
    """
    Combined rate limit and quota decorator

    Usage:
        @app.post("/api/agents")
        @rate_limit_and_quota(
            rate_resource="agent:create",
            quota_type="agents:total"
        )
        async def create_agent(request: Request):
            ...

    Args:
        rate_resource: Resource for rate limiting
        quota_type: Type of quota to check (optional)
        rate_limit_value: Override rate limit (uses preset if not provided)
        quota_required: Amount required for quota
        rate_cost: Token cost for rate limit
        increment_quota: Increment quota on success
    """
    def decorator(func: Callable):
        # Apply rate limit decorator
        rate_decorated = rate_limit(
            resource=rate_resource,
            limit=rate_limit_value,
            cost=rate_cost
        )(func)

        # Apply quota decorator if quota_type provided
        if quota_type:
            quota_decorated = require_quota(
                quota_type=quota_type,
                required=quota_required,
                increment_on_success=increment_quota
            )(rate_decorated)
            return quota_decorated

        return rate_decorated
    return decorator
