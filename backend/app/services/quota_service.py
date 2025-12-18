"""
Per-User Quota Service

Comprehensive quota management for NodeRush platform.
Enforces tier-based limits on all resources.

Features:
- Tier-based limits (free, pro, enterprise)
- Multiple quota types (agents, executions, tokens, storage)
- Redis-backed real-time tracking
- Database-backed permanent quotas
- Automatic quota reset (daily/monthly)
"""

import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime, date, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class QuotaTier(Enum):
    """User subscription tiers"""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class QuotaType(Enum):
    """Types of quotas"""
    AGENTS_TOTAL = "agents:total"
    AGENTS_CREATE_HOUR = "agents:create_hour"
    AGENTS_CREATE_DAY = "agents:create_day"
    EXECUTIONS_HOUR = "executions:hour"
    EXECUTIONS_DAY = "executions:day"
    AI_TOKENS_REQUEST = "ai_tokens:request"
    AI_TOKENS_DAY = "ai_tokens:day"
    STORAGE_MB = "storage:mb"
    STORAGE_FILES = "storage:files"
    WEBSOCKET_CONCURRENT = "websocket:concurrent"


@dataclass
class QuotaResult:
    """Result of a quota check"""
    allowed: bool
    current: int
    limit: int
    remaining: int
    quota_type: str
    tier: str
    reset_at: Optional[int] = None  # Unix timestamp
    message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "allowed": self.allowed,
            "current": self.current,
            "limit": self.limit,
            "remaining": self.remaining,
            "quota_type": self.quota_type,
            "tier": self.tier,
            "reset_at": self.reset_at,
            "message": self.message
        }


# Quota limits per tier (aligned with ARCHITECTURE.md)
TIER_QUOTAS = {
    QuotaTier.FREE.value: {
        # Agent quotas
        QuotaType.AGENTS_TOTAL.value: 10,           # Max 10 agents total
        QuotaType.AGENTS_CREATE_HOUR.value: 5,      # Max 5 new agents per hour
        QuotaType.AGENTS_CREATE_DAY.value: 20,      # Max 20 new agents per day

        # Execution quotas
        QuotaType.EXECUTIONS_HOUR.value: 10,        # Max 10 executions per hour
        QuotaType.EXECUTIONS_DAY.value: 50,         # Max 50 executions per day

        # AI token quotas
        QuotaType.AI_TOKENS_REQUEST.value: 3000,    # Max 3000 tokens per request
        QuotaType.AI_TOKENS_DAY.value: 26000,       # Max 26k tokens per day (from Day 5)

        # Storage quotas
        QuotaType.STORAGE_MB.value: 100,            # Max 100 MB in R2
        QuotaType.STORAGE_FILES.value: 1000,        # Max 1000 files

        # WebSocket quotas
        QuotaType.WEBSOCKET_CONCURRENT.value: 3,    # Max 3 concurrent WS connections
    },
    QuotaTier.PRO.value: {
        # Agent quotas (5x free)
        QuotaType.AGENTS_TOTAL.value: 50,
        QuotaType.AGENTS_CREATE_HOUR.value: 25,
        QuotaType.AGENTS_CREATE_DAY.value: 100,

        # Execution quotas (5x free)
        QuotaType.EXECUTIONS_HOUR.value: 50,
        QuotaType.EXECUTIONS_DAY.value: 250,

        # AI token quotas
        QuotaType.AI_TOKENS_REQUEST.value: 10000,
        QuotaType.AI_TOKENS_DAY.value: 260000,      # 260k tokens per day

        # Storage quotas (5x free)
        QuotaType.STORAGE_MB.value: 500,
        QuotaType.STORAGE_FILES.value: 5000,

        # WebSocket quotas
        QuotaType.WEBSOCKET_CONCURRENT.value: 10,
    },
    QuotaTier.ENTERPRISE.value: {
        # Agent quotas (unlimited = very high)
        QuotaType.AGENTS_TOTAL.value: 1000,
        QuotaType.AGENTS_CREATE_HOUR.value: 100,
        QuotaType.AGENTS_CREATE_DAY.value: 500,

        # Execution quotas
        QuotaType.EXECUTIONS_HOUR.value: 500,
        QuotaType.EXECUTIONS_DAY.value: 5000,

        # AI token quotas (unlimited)
        QuotaType.AI_TOKENS_REQUEST.value: 50000,
        QuotaType.AI_TOKENS_DAY.value: float('inf'),

        # Storage quotas
        QuotaType.STORAGE_MB.value: 10000,
        QuotaType.STORAGE_FILES.value: 100000,

        # WebSocket quotas
        QuotaType.WEBSOCKET_CONCURRENT.value: 100,
    }
}


# TTL for different quota types (seconds)
QUOTA_TTL = {
    QuotaType.AGENTS_CREATE_HOUR.value: 3600,      # 1 hour
    QuotaType.AGENTS_CREATE_DAY.value: 86400,      # 1 day
    QuotaType.EXECUTIONS_HOUR.value: 3600,         # 1 hour
    QuotaType.EXECUTIONS_DAY.value: 86400,         # 1 day
    QuotaType.AI_TOKENS_DAY.value: 86400,          # 1 day
}


class QuotaService:
    """
    Per-user quota service

    Manages all resource quotas across different tiers.
    Uses Redis for real-time tracking and supports
    tier-based multipliers.
    """

    def __init__(self, redis_service):
        """
        Initialize quota service

        Args:
            redis_service: RedisService instance for storage
        """
        self.redis = redis_service
        self.tier_quotas = TIER_QUOTAS
        self.quota_ttl = QUOTA_TTL

    def get_limit(self, quota_type: str, tier: str = "free") -> int:
        """
        Get quota limit for a specific type and tier

        Args:
            quota_type: Type of quota (e.g., 'agents:total')
            tier: User tier ('free', 'pro', 'enterprise')

        Returns:
            Limit value for the quota
        """
        tier_limits = self.tier_quotas.get(tier, self.tier_quotas["free"])
        return tier_limits.get(quota_type, 0)

    async def check_quota(
        self,
        user_id: str,
        quota_type: str,
        tier: str = "free",
        required: int = 1
    ) -> QuotaResult:
        """
        Check if user is within quota

        Args:
            user_id: User ID
            quota_type: Type of quota to check
            tier: User's subscription tier
            required: Amount needed for this operation

        Returns:
            QuotaResult with allowed status and details
        """
        try:
            limit = self.get_limit(quota_type, tier)

            # Handle unlimited (infinity) limits
            if limit == float('inf'):
                return QuotaResult(
                    allowed=True,
                    current=0,
                    limit=999999999,  # Large number for display
                    remaining=999999999,
                    quota_type=quota_type,
                    tier=tier,
                    message="Unlimited quota"
                )

            # Get current usage from Redis
            key = self._get_quota_key(user_id, quota_type)
            current = await self.redis.redis_client.get(key)
            current = int(current) if current else 0

            remaining = max(0, limit - current)
            allowed = (current + required) <= limit

            # Calculate reset time if applicable
            reset_at = None
            if quota_type in self.quota_ttl:
                ttl = await self.redis.redis_client.ttl(key)
                if ttl > 0:
                    reset_at = int(datetime.utcnow().timestamp()) + ttl

            message = None
            if not allowed:
                message = f"Quota exceeded for {quota_type}. Current: {current}/{limit}"

            return QuotaResult(
                allowed=allowed,
                current=current,
                limit=limit,
                remaining=remaining,
                quota_type=quota_type,
                tier=tier,
                reset_at=reset_at,
                message=message
            )

        except Exception as e:
            logger.error(f"Failed to check quota: {e}")
            # Fail open - allow if Redis fails
            return QuotaResult(
                allowed=True,
                current=0,
                limit=self.get_limit(quota_type, tier),
                remaining=self.get_limit(quota_type, tier),
                quota_type=quota_type,
                tier=tier,
                message=f"Quota check failed: {e}"
            )

    async def increment_quota(
        self,
        user_id: str,
        quota_type: str,
        amount: int = 1
    ) -> int:
        """
        Increment quota usage

        Args:
            user_id: User ID
            quota_type: Type of quota
            amount: Amount to increment

        Returns:
            New usage value
        """
        try:
            key = self._get_quota_key(user_id, quota_type)
            new_value = await self.redis.redis_client.incrby(key, amount)

            # Set TTL if this is a time-based quota
            if quota_type in self.quota_ttl:
                ttl = await self.redis.redis_client.ttl(key)
                if ttl == -1:  # No expiry set
                    await self.redis.redis_client.expire(
                        key,
                        self.quota_ttl[quota_type]
                    )
            else:
                # Permanent quotas - 31 day expiry for cleanup
                ttl = await self.redis.redis_client.ttl(key)
                if ttl == -1:
                    await self.redis.redis_client.expire(key, 86400 * 31)

            return new_value

        except Exception as e:
            logger.error(f"Failed to increment quota: {e}")
            return 0

    async def decrement_quota(
        self,
        user_id: str,
        quota_type: str,
        amount: int = 1
    ) -> int:
        """
        Decrement quota usage (e.g., when agent is deleted)

        Args:
            user_id: User ID
            quota_type: Type of quota
            amount: Amount to decrement

        Returns:
            New usage value
        """
        try:
            key = self._get_quota_key(user_id, quota_type)
            current = await self.redis.redis_client.get(key)
            current = int(current) if current else 0

            new_value = max(0, current - amount)
            await self.redis.redis_client.set(key, new_value)

            return new_value

        except Exception as e:
            logger.error(f"Failed to decrement quota: {e}")
            return 0

    async def set_quota(
        self,
        user_id: str,
        quota_type: str,
        value: int
    ) -> bool:
        """
        Set quota to specific value (admin function)

        Args:
            user_id: User ID
            quota_type: Type of quota
            value: Value to set

        Returns:
            Success status
        """
        try:
            key = self._get_quota_key(user_id, quota_type)
            await self.redis.redis_client.set(key, value)
            return True
        except Exception as e:
            logger.error(f"Failed to set quota: {e}")
            return False

    async def reset_quota(
        self,
        user_id: str,
        quota_type: str
    ) -> bool:
        """
        Reset quota to zero

        Args:
            user_id: User ID
            quota_type: Type of quota

        Returns:
            Success status
        """
        try:
            key = self._get_quota_key(user_id, quota_type)
            await self.redis.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Failed to reset quota: {e}")
            return False

    async def get_all_quotas(
        self,
        user_id: str,
        tier: str = "free"
    ) -> Dict[str, QuotaResult]:
        """
        Get all quota statuses for a user

        Args:
            user_id: User ID
            tier: User's subscription tier

        Returns:
            Dictionary of quota type -> QuotaResult
        """
        results = {}

        for quota_type in QuotaType:
            result = await self.check_quota(
                user_id=user_id,
                quota_type=quota_type.value,
                tier=tier
            )
            results[quota_type.value] = result

        return results

    async def get_usage_summary(
        self,
        user_id: str,
        tier: str = "free"
    ) -> Dict[str, Any]:
        """
        Get a summary of user's quota usage

        Args:
            user_id: User ID
            tier: User's subscription tier

        Returns:
            Summary with usage percentages
        """
        quotas = await self.get_all_quotas(user_id, tier)

        summary = {
            "tier": tier,
            "quotas": {},
            "warnings": [],
            "blocked": []
        }

        for quota_type, result in quotas.items():
            if result.limit == 999999999:  # Unlimited
                percentage = 0
            else:
                percentage = (result.current / result.limit * 100) if result.limit > 0 else 0

            summary["quotas"][quota_type] = {
                "current": result.current,
                "limit": result.limit,
                "remaining": result.remaining,
                "percentage": round(percentage, 1),
                "reset_at": result.reset_at
            }

            # Track warnings (>80% usage)
            if percentage >= 80 and percentage < 100:
                summary["warnings"].append(quota_type)

            # Track blocked (100% usage)
            if percentage >= 100:
                summary["blocked"].append(quota_type)

        return summary

    async def check_and_increment(
        self,
        user_id: str,
        quota_type: str,
        tier: str = "free",
        required: int = 1
    ) -> QuotaResult:
        """
        Atomically check quota and increment if allowed

        Args:
            user_id: User ID
            quota_type: Type of quota
            tier: User's subscription tier
            required: Amount needed

        Returns:
            QuotaResult with allowed status
        """
        # First check
        result = await self.check_quota(user_id, quota_type, tier, required)

        if result.allowed:
            # Increment usage
            new_value = await self.increment_quota(user_id, quota_type, required)
            result.current = new_value
            result.remaining = max(0, result.limit - new_value)

        return result

    def _get_quota_key(self, user_id: str, quota_type: str) -> str:
        """
        Generate Redis key for quota

        For time-based quotas, includes date/hour component.
        For permanent quotas, just user_id.
        """
        now = datetime.utcnow()

        if "hour" in quota_type:
            # Hourly quota - include hour in key
            hour = now.strftime("%Y-%m-%d-%H")
            return f"quota:{quota_type}:{user_id}:{hour}"
        elif "day" in quota_type:
            # Daily quota - include date in key
            day = now.strftime("%Y-%m-%d")
            return f"quota:{quota_type}:{user_id}:{day}"
        else:
            # Permanent quota (like total agents)
            return f"quota:{quota_type}:{user_id}"


# Singleton instance - initialized in main.py
quota_service: Optional[QuotaService] = None


def init_quota_service(redis_service) -> QuotaService:
    """Initialize the quota service singleton"""
    global quota_service
    quota_service = QuotaService(redis_service)
    return quota_service


def get_quota_service() -> Optional[QuotaService]:
    """Get the quota service singleton"""
    return quota_service
