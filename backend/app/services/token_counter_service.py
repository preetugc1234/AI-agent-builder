"""
Token Counter Service
Uses tiktoken to accurately count AI tokens for different models
Tracks usage in Redis and database for billing/quotas
"""

import tiktoken
import logging
from typing import Optional, Dict, List
from uuid import UUID

from app.services.redis_service import redis_service
from app.core.config import settings

logger = logging.getLogger(__name__)


class TokenCounterService:
    """
    Service for counting AI tokens using tiktoken

    Features:
    - Accurate token counting for different models
    - Track usage in Redis (real-time)
    - Daily, monthly, per-agent tracking
    - Quota enforcement
    """

    # Model encodings (OpenAI models)
    # NVIDIA Nemotron uses similar tokenization to GPT models
    MODEL_ENCODINGS = {
        "gpt-4": "cl100k_base",
        "gpt-4-turbo": "cl100k_base",
        "gpt-3.5-turbo": "cl100k_base",
        "nvidia/nemotron-nano-12b-v2-vl": "cl100k_base",  # Uses same encoding
        "default": "cl100k_base"
    }

    def __init__(self):
        self.encoders: Dict[str, tiktoken.Encoding] = {}

    def _get_encoder(self, model: str) -> tiktoken.Encoding:
        """
        Get tiktoken encoder for a specific model

        Args:
            model: Model name (e.g., "gpt-4", "nvidia/nemotron...")

        Returns:
            tiktoken.Encoding instance
        """
        encoding_name = self.MODEL_ENCODINGS.get(model, self.MODEL_ENCODINGS["default"])

        # Cache encoder
        if encoding_name not in self.encoders:
            try:
                self.encoders[encoding_name] = tiktoken.get_encoding(encoding_name)
                logger.debug(f"Loaded tiktoken encoding: {encoding_name}")
            except Exception as e:
                logger.error(f"Failed to load tiktoken encoding {encoding_name}: {e}")
                # Fallback to default
                self.encoders[encoding_name] = tiktoken.get_encoding("cl100k_base")

        return self.encoders[encoding_name]

    def count_tokens(self, text: str, model: str = "default") -> int:
        """
        Count tokens in a text string

        Args:
            text: Text to count tokens for
            model: Model name for appropriate tokenizer

        Returns:
            Number of tokens
        """
        try:
            if not text:
                return 0

            encoder = self._get_encoder(model)
            tokens = encoder.encode(text)
            return len(tokens)

        except Exception as e:
            logger.error(f"Error counting tokens: {e}")
            # Fallback: rough estimate (1 token ≈ 4 characters)
            return len(text) // 4

    def count_messages_tokens(
        self,
        messages: List[Dict[str, str]],
        model: str = "default"
    ) -> int:
        """
        Count tokens for a list of messages (chat format)

        ChatGPT format:
        [
            {"role": "system", "content": "You are..."},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi!"}
        ]

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model name

        Returns:
            Total token count including overhead
        """
        try:
            encoder = self._get_encoder(model)

            # Token counting follows OpenAI's format:
            # - 3 tokens per message (metadata)
            # - 1 token per message delimiter
            tokens_per_message = 3
            tokens_per_name = 1

            num_tokens = 0

            for message in messages:
                num_tokens += tokens_per_message
                for key, value in message.items():
                    num_tokens += len(encoder.encode(str(value)))
                    if key == "name":
                        num_tokens += tokens_per_name

            # Add 3 tokens for reply priming
            num_tokens += 3

            return num_tokens

        except Exception as e:
            logger.error(f"Error counting message tokens: {e}")
            # Fallback estimate
            total_chars = sum(len(str(m.get("content", ""))) for m in messages)
            return total_chars // 4

    async def track_usage(
        self,
        user_id: str,
        agent_id: Optional[str],
        prompt_tokens: int,
        completion_tokens: int,
        model: str = "unknown"
    ) -> bool:
        """
        Track token usage in Redis

        Args:
            user_id: User UUID
            agent_id: Agent UUID (optional)
            prompt_tokens: Tokens in prompt
            completion_tokens: Tokens in completion
            model: Model name

        Returns:
            True if tracking successful
        """
        try:
            total_tokens = prompt_tokens + completion_tokens

            # Track in Redis (for real-time quotas)
            await redis_service.track_token_usage(
                user_id=user_id,
                agent_id=agent_id,
                tokens=total_tokens,
                model=model
            )

            logger.info(
                f"Tracked token usage: user={user_id}, agent={agent_id}, "
                f"prompt={prompt_tokens}, completion={completion_tokens}, "
                f"total={total_tokens}, model={model}"
            )

            return True

        except Exception as e:
            logger.error(f"Failed to track token usage: {e}")
            return False

    async def check_quota(
        self,
        user_id: str,
        required_tokens: int,
        tier: str = "free"
    ) -> Dict[str, any]:
        """
        Check if user has enough tokens remaining in quota

        Free tier: 50,000 tokens/day
        Pro tier: 500,000 tokens/day
        Enterprise: Unlimited

        Args:
            user_id: User UUID
            required_tokens: Tokens needed for request
            tier: Subscription tier

        Returns:
            {
                "allowed": bool,
                "used_today": int,
                "limit": int,
                "remaining": int
            }
        """
        try:
            # Define limits by tier
            limits = {
                "free": 50000,
                "pro": 500000,
                "enterprise": float('inf')
            }

            limit = limits.get(tier, limits["free"])

            # Get today's usage from Redis
            usage = await redis_service.get_token_usage(user_id, period="today")
            used_today = usage.get("total", 0)

            remaining = max(0, limit - used_today)
            allowed = (used_today + required_tokens) <= limit

            return {
                "allowed": allowed,
                "used_today": used_today,
                "limit": limit,
                "remaining": remaining,
                "required": required_tokens
            }

        except Exception as e:
            logger.error(f"Failed to check token quota: {e}")
            # Fail open - allow request if check fails
            return {
                "allowed": True,
                "used_today": 0,
                "limit": 50000,
                "remaining": 50000,
                "required": required_tokens
            }

    async def get_user_usage_stats(self, user_id: str) -> Dict[str, any]:
        """
        Get comprehensive usage statistics for a user

        Returns:
            {
                "today": {"total": int, "gpt-4": int, ...},
                "month": {"total": int, ...},
                "breakdown": {...}
            }
        """
        try:
            today = await redis_service.get_token_usage(user_id, period="today")
            month = await redis_service.get_token_usage(user_id, period="month")

            return {
                "today": today,
                "month": month,
                "breakdown": {
                    "total_today": today.get("total", 0),
                    "total_month": month.get("total", 0),
                    "models": {
                        k: v for k, v in today.items() if k != "total"
                    }
                }
            }

        except Exception as e:
            logger.error(f"Failed to get usage stats: {e}")
            return {
                "today": {"total": 0},
                "month": {"total": 0},
                "breakdown": {}
            }

    async def get_agent_usage_stats(self, agent_id: str) -> Dict[str, int]:
        """
        Get token usage statistics for a specific agent

        Returns:
            {"total": int, "model_name": int, ...}
        """
        try:
            return await redis_service.get_agent_token_usage(agent_id)
        except Exception as e:
            logger.error(f"Failed to get agent usage stats: {e}")
            return {"total": 0}

    def estimate_tokens(self, text: str) -> int:
        """
        Quick estimation of tokens without tiktoken (fallback)

        Rule of thumb: 1 token ≈ 4 characters for English text

        Args:
            text: Text to estimate

        Returns:
            Estimated token count
        """
        return max(1, len(text) // 4)

    def format_token_count(self, tokens: int) -> str:
        """
        Format token count for display

        Args:
            tokens: Number of tokens

        Returns:
            Formatted string (e.g., "1.2K", "15.3K", "1.2M")
        """
        if tokens < 1000:
            return str(tokens)
        elif tokens < 1000000:
            return f"{tokens/1000:.1f}K"
        else:
            return f"{tokens/1000000:.1f}M"


# Global instance
token_counter = TokenCounterService()
