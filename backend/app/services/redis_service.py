"""
Redis Service for Caching, Sessions, and Queues
Uses Upstash Redis
"""

import json
import logging
from typing import Optional, Any, List
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

    async def dequeue_agent_execution(self) -> Optional[dict]:
        """Get next agent execution from queue"""
        try:
            queue_key = "queue:agent_execution"
            data = await self.redis_client.rpop(queue_key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Failed to dequeue execution: {e}")
            return None

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
