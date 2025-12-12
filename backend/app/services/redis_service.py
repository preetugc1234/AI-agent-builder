"""
Redis Service for Caching, Sessions, and Queues
Uses Upstash Redis

Features:
- Session management (user sessions with 7-day expiry)
- Caching (agent data, AI responses)
- Queue management (background job processing with BRPOP)
- Rate limiting (token bucket algorithm)
- Token usage tracking (daily and per-agent)
- Quota management (user limits)
- Pub/Sub (real-time events)
"""

import json
import logging
import hashlib
from typing import Optional, Any, List, Dict
from datetime import datetime, timedelta
import redis.asyncio as redis
from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisService:
    """Redis service for caching, sessions, and pub/sub"""

    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.pubsub = None

    async def connect(self):
        """Connect to Redis (Upstash)"""
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                max_connections=10
            )
            await self.redis_client.ping()
            logger.info("✅ Connected to Redis (Upstash)")
            return True
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            return False

    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis disconnected")

    # ============= SESSION MANAGEMENT =============

    async def set_session(self, session_id: str, user_data: dict, expire_seconds: int = 86400):
        """Store user session (24 hours default)"""
        try:
            key = f"session:{session_id}"
            await self.redis_client.setex(
                key,
                expire_seconds,
                json.dumps(user_data)
            )
            return True
        except Exception as e:
            logger.error(f"Failed to set session: {e}")
            return False

    async def get_session(self, session_id: str) -> Optional[dict]:
        """Get user session"""
        try:
            key = f"session:{session_id}"
            data = await self.redis_client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Failed to get session: {e}")
            return None

    async def delete_session(self, session_id: str):
        """Delete user session (logout)"""
        try:
            key = f"session:{session_id}"
            await self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Failed to delete session: {e}")
            return False

    # ============= CACHING =============

    async def cache_set(self, key: str, value: Any, expire_seconds: int = 3600):
        """Cache data (1 hour default)"""
        try:
            cache_key = f"cache:{key}"
            serialized = json.dumps(value)
            await self.redis_client.setex(cache_key, expire_seconds, serialized)
            return True
        except Exception as e:
            logger.error(f"Failed to cache: {e}")
            return False

    async def cache_get(self, key: str) -> Optional[Any]:
        """Get cached data"""
        try:
            cache_key = f"cache:{key}"
            data = await self.redis_client.get(cache_key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Failed to get cache: {e}")
            return None

    async def cache_delete(self, key: str):
        """Delete cached data"""
        try:
            cache_key = f"cache:{key}"
            await self.redis_client.delete(cache_key)
            return True
        except Exception as e:
            logger.error(f"Failed to delete cache: {e}")
            return False

    # ============= WEBSOCKET CONNECTION STATE =============

    async def add_websocket_connection(self, agent_id: str, connection_id: str):
        """Track WebSocket connection"""
        try:
            key = f"ws:agent:{agent_id}"
            await self.redis_client.sadd(key, connection_id)
            await self.redis_client.expire(key, 3600)  # 1 hour
            return True
        except Exception as e:
            logger.error(f"Failed to add WS connection: {e}")
            return False

    async def remove_websocket_connection(self, agent_id: str, connection_id: str):
        """Remove WebSocket connection"""
        try:
            key = f"ws:agent:{agent_id}"
            await self.redis_client.srem(key, connection_id)
            return True
        except Exception as e:
            logger.error(f"Failed to remove WS connection: {e}")
            return False

    async def get_websocket_connections(self, agent_id: str) -> List[str]:
        """Get all WebSocket connections for agent"""
        try:
            key = f"ws:agent:{agent_id}"
            connections = await self.redis_client.smembers(key)
            return list(connections)
        except Exception as e:
            logger.error(f"Failed to get WS connections: {e}")
            return []

    # ============= AGENT EXECUTION QUEUE =============

    async def enqueue_agent_execution(self, agent_id: str, execution_data: dict):
        """Add agent execution to queue"""
        try:
            queue_key = "queue:agent_execution"
            payload = json.dumps({
                "agent_id": agent_id,
                "data": execution_data
            })
            await self.redis_client.lpush(queue_key, payload)
            return True
        except Exception as e:
            logger.error(f"Failed to enqueue execution: {e}")
            return False

    async def dequeue_agent_execution(self, timeout: int = 10) -> Optional[dict]:
        """
        Get next agent execution from queue (blocking)

        Args:
            timeout: Seconds to wait for item (default 10)

        Returns:
            Execution data or None if timeout
        """
        try:
            queue_key = "queue:agent_execution"
            # BRPOP returns (key, value) tuple or None
            result = await self.redis_client.brpop(queue_key, timeout=timeout)
            if result:
                _, data = result
                return json.loads(data) if data else None
            return None
        except Exception as e:
            logger.error(f"Failed to dequeue execution: {e}")
            return None

    async def get_queue_length(self, queue_name: str = "agent_execution") -> int:
        """Get number of items in queue"""
        try:
            queue_key = f"queue:{queue_name}"
            length = await self.redis_client.llen(queue_key)
            return length
        except Exception as e:
            logger.error(f"Failed to get queue length: {e}")
            return 0

    # ============= AI GENERATION CACHE =============

    async def cache_ai_response(self, prompt_hash: str, response: dict, expire_seconds: int = 86400):
        """Cache AI generation response (24 hours)"""
        try:
            key = f"ai:response:{prompt_hash}"
            await self.redis_client.setex(
                key,
                expire_seconds,
                json.dumps(response)
            )
            return True
        except Exception as e:
            logger.error(f"Failed to cache AI response: {e}")
            return False

    async def get_cached_ai_response(self, prompt_hash: str) -> Optional[dict]:
        """Get cached AI response"""
        try:
            key = f"ai:response:{prompt_hash}"
            data = await self.redis_client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Failed to get cached AI response: {e}")
            return None

    # ============= AGENT STATUS TRACKING =============

    async def set_agent_status(self, agent_id: str, status: str, data: Optional[dict] = None):
        """Set agent execution status"""
        try:
            key = f"agent:status:{agent_id}"
            payload = {
                "status": status,
                "data": data or {}
            }
            await self.redis_client.setex(
                key,
                3600,  # 1 hour
                json.dumps(payload)
            )
            return True
        except Exception as e:
            logger.error(f"Failed to set agent status: {e}")
            return False

    async def get_agent_status(self, agent_id: str) -> Optional[dict]:
        """Get agent execution status"""
        try:
            key = f"agent:status:{agent_id}"
            data = await self.redis_client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Failed to get agent status: {e}")
            return None

    # ============= RATE LIMITING (Token Bucket Algorithm) =============

    async def check_rate_limit(
        self,
        user_id: str,
        resource: str,
        limit: int,
        window_seconds: int = 60
    ) -> Dict[str, Any]:
        """
        Check if user is within rate limit using token bucket algorithm

        Args:
            user_id: User ID
            resource: Resource name (e.g., 'agent_creation', 'api_calls')
            limit: Maximum requests allowed in window
            window_seconds: Time window in seconds

        Returns:
            {
                "allowed": bool,
                "current": int,
                "limit": int,
                "remaining": int,
                "reset_at": int (timestamp)
            }
        """
        try:
            key = f"ratelimit:{resource}:{user_id}"
            current = await self.redis_client.get(key)

            if current is None:
                # First request - initialize counter
                await self.redis_client.setex(key, window_seconds, 1)
                return {
                    "allowed": True,
                    "current": 1,
                    "limit": limit,
                    "remaining": limit - 1,
                    "reset_at": int(datetime.utcnow().timestamp()) + window_seconds
                }

            current = int(current)

            if current >= limit:
                # Rate limit exceeded
                ttl = await self.redis_client.ttl(key)
                return {
                    "allowed": False,
                    "current": current,
                    "limit": limit,
                    "remaining": 0,
                    "reset_at": int(datetime.utcnow().timestamp()) + ttl
                }

            # Increment counter
            new_count = await self.redis_client.incr(key)
            ttl = await self.redis_client.ttl(key)

            return {
                "allowed": True,
                "current": new_count,
                "limit": limit,
                "remaining": limit - new_count,
                "reset_at": int(datetime.utcnow().timestamp()) + ttl
            }

        except Exception as e:
            logger.error(f"Failed to check rate limit: {e}")
            # Fail open - allow request if Redis fails
            return {
                "allowed": True,
                "current": 0,
                "limit": limit,
                "remaining": limit,
                "reset_at": 0
            }

    async def reset_rate_limit(self, user_id: str, resource: str):
        """Reset rate limit for a user"""
        try:
            key = f"ratelimit:{resource}:{user_id}"
            await self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Failed to reset rate limit: {e}")
            return False

    # ============= TOKEN USAGE TRACKING =============

    async def track_token_usage(
        self,
        user_id: str,
        agent_id: Optional[str],
        tokens: int,
        model: str = "unknown"
    ):
        """
        Track AI token usage for billing and quotas

        Stores:
        - Daily user total
        - Per-agent total
        - Per-model breakdown
        """
        try:
            today = datetime.utcnow().strftime("%Y-%m-%d")

            # Daily user total
            daily_key = f"tokens:user:{user_id}:day:{today}"
            await self.redis_client.hincrby(daily_key, "total", tokens)
            await self.redis_client.hincrby(daily_key, model, tokens)
            await self.redis_client.expire(daily_key, 86400 * 31)  # Keep 31 days

            # Per-agent total (if agent specified)
            if agent_id:
                agent_key = f"tokens:agent:{agent_id}:total"
                await self.redis_client.hincrby(agent_key, "total", tokens)
                await self.redis_client.hincrby(agent_key, model, tokens)
                await self.redis_client.expire(agent_key, 86400 * 30)  # Keep 30 days

            # Monthly user total
            month = datetime.utcnow().strftime("%Y-%m")
            monthly_key = f"tokens:user:{user_id}:month:{month}"
            await self.redis_client.hincrby(monthly_key, "total", tokens)
            await self.redis_client.expire(monthly_key, 86400 * 365)  # Keep 1 year

            return True
        except Exception as e:
            logger.error(f"Failed to track token usage: {e}")
            return False

    async def get_token_usage(self, user_id: str, period: str = "today") -> Dict[str, int]:
        """
        Get token usage for a user

        Args:
            user_id: User ID
            period: 'today', 'month', or 'YYYY-MM-DD' for specific day

        Returns:
            {"total": int, "model_name": int, ...}
        """
        try:
            if period == "today":
                date = datetime.utcnow().strftime("%Y-%m-%d")
                key = f"tokens:user:{user_id}:day:{date}"
            elif period == "month":
                month = datetime.utcnow().strftime("%Y-%m")
                key = f"tokens:user:{user_id}:month:{month}"
            else:
                # Assume period is a date string
                key = f"tokens:user:{user_id}:day:{period}"

            data = await self.redis_client.hgetall(key)
            if not data:
                return {"total": 0}

            # Convert string values to int
            return {k: int(v) for k, v in data.items()}
        except Exception as e:
            logger.error(f"Failed to get token usage: {e}")
            return {"total": 0}

    async def get_agent_token_usage(self, agent_id: str) -> Dict[str, int]:
        """Get total token usage for an agent"""
        try:
            key = f"tokens:agent:{agent_id}:total"
            data = await self.redis_client.hgetall(key)
            if not data:
                return {"total": 0}
            return {k: int(v) for k, v in data.items()}
        except Exception as e:
            logger.error(f"Failed to get agent token usage: {e}")
            return {"total": 0}

    # ============= QUOTA MANAGEMENT =============

    async def check_quota(self, user_id: str, quota_type: str, limit: int) -> Dict[str, Any]:
        """
        Check if user is within quota

        Args:
            user_id: User ID
            quota_type: Type of quota (e.g., 'agents', 'executions')
            limit: Maximum allowed

        Returns:
            {"allowed": bool, "current": int, "limit": int, "remaining": int}
        """
        try:
            key = f"quota:{quota_type}:{user_id}"
            current = await self.redis_client.get(key)
            current = int(current) if current else 0

            return {
                "allowed": current < limit,
                "current": current,
                "limit": limit,
                "remaining": max(0, limit - current)
            }
        except Exception as e:
            logger.error(f"Failed to check quota: {e}")
            return {"allowed": True, "current": 0, "limit": limit, "remaining": limit}

    async def increment_quota(self, user_id: str, quota_type: str, amount: int = 1):
        """Increment quota usage"""
        try:
            key = f"quota:{quota_type}:{user_id}"
            new_value = await self.redis_client.incrby(key, amount)
            # Set expiry if first time (31 days)
            ttl = await self.redis_client.ttl(key)
            if ttl == -1:  # No expiry set
                await self.redis_client.expire(key, 86400 * 31)
            return new_value
        except Exception as e:
            logger.error(f"Failed to increment quota: {e}")
            return 0

    async def reset_quota(self, user_id: str, quota_type: str):
        """Reset quota for a user"""
        try:
            key = f"quota:{quota_type}:{user_id}"
            await self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Failed to reset quota: {e}")
            return False

    # ============= CSRF TOKEN MANAGEMENT =============

    async def store_csrf_token(self, token: str, user_id: str, expire_seconds: int = 3600):
        """Store CSRF token"""
        try:
            key = f"csrf:{token}"
            await self.redis_client.setex(key, expire_seconds, user_id)
            return True
        except Exception as e:
            logger.error(f"Failed to store CSRF token: {e}")
            return False

    async def verify_csrf_token(self, token: str) -> Optional[str]:
        """Verify CSRF token and return user_id"""
        try:
            key = f"csrf:{token}"
            user_id = await self.redis_client.get(key)
            if user_id:
                # Delete token after use (one-time use)
                await self.redis_client.delete(key)
            return user_id
        except Exception as e:
            logger.error(f"Failed to verify CSRF token: {e}")
            return None

    # ============= SYSTEM FLAGS (Cost Control) =============

    async def set_system_flag(self, flag_name: str, value: str, expire_seconds: int = 3600):
        """
        Set system-wide flag (e.g., for cost control)

        Examples:
        - system:pause_agent_creation
        - system:pause_file_upload
        - system:aggressive_caching
        """
        try:
            key = f"system:{flag_name}"
            await self.redis_client.setex(key, expire_seconds, value)
            return True
        except Exception as e:
            logger.error(f"Failed to set system flag: {e}")
            return False

    async def get_system_flag(self, flag_name: str) -> Optional[str]:
        """Get system flag value"""
        try:
            key = f"system:{flag_name}"
            return await self.redis_client.get(key)
        except Exception as e:
            logger.error(f"Failed to get system flag: {e}")
            return None

    async def delete_system_flag(self, flag_name: str):
        """Delete system flag"""
        try:
            key = f"system:{flag_name}"
            await self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Failed to delete system flag: {e}")
            return False

    # ============= REDIS COMMAND TRACKING (Cost Monitoring) =============

    async def track_redis_command(self):
        """Track Redis command count for cost monitoring"""
        try:
            today = datetime.utcnow().strftime("%Y-%m-%d")
            key = f"redis:commands:count:{today}"
            count = await self.redis_client.incr(key)
            # Expire at end of day
            if count == 1:  # First command of the day
                # Set expiry to end of day
                now = datetime.utcnow()
                end_of_day = datetime.combine(now.date() + timedelta(days=1), datetime.min.time())
                seconds_until_eod = int((end_of_day - now).total_seconds())
                await self.redis_client.expire(key, seconds_until_eod)
            return count
        except Exception as e:
            logger.error(f"Failed to track Redis command: {e}")
            return 0

    async def get_redis_command_count(self, date: Optional[str] = None) -> int:
        """Get Redis command count for a date"""
        try:
            if date is None:
                date = datetime.utcnow().strftime("%Y-%m-%d")
            key = f"redis:commands:count:{date}"
            count = await self.redis_client.get(key)
            return int(count) if count else 0
        except Exception as e:
            logger.error(f"Failed to get Redis command count: {e}")
            return 0

    # ============= PUB/SUB FOR REAL-TIME EVENTS =============

    async def publish_event(self, channel: str, message: dict):
        """Publish event to channel"""
        try:
            await self.redis_client.publish(
                channel,
                json.dumps(message)
            )
            return True
        except Exception as e:
            logger.error(f"Failed to publish event: {e}")
            return False

    async def subscribe_to_channel(self, channel: str):
        """Subscribe to channel"""
        try:
            if not self.pubsub:
                self.pubsub = self.redis_client.pubsub()
            await self.pubsub.subscribe(channel)
            return self.pubsub
        except Exception as e:
            logger.error(f"Failed to subscribe: {e}")
            return None


# Global Redis service instance
redis_service = RedisService()
