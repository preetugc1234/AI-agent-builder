"""
Token Manager
Manages token limits for the 3-agent workflow (Architect, Coder, Reviewer)
Enforces daily limits and per-agent allocations
"""

import logging
from typing import Dict, Optional
from uuid import UUID

from app.services.token_counter_service import token_counter
from app.services.redis_service import redis_service
from app.core.exceptions import QuotaExceededError

logger = logging.getLogger(__name__)


class TokenManager:
    """
    Manages token allocation for the 3-agent workflow

    **Per-Prompt Limits**:
    - Max Input: 1,500 tokens
    - Max Output: 5,000 tokens

    **Agent Allocation** (of 5,000 output tokens):
    - Agent 1 (Architect): 15% = 750 tokens
    - Agent 2 (Coder): 70% = 3,500 tokens
    - Agent 3 (Reviewer): 15% = 750 tokens

    **Daily Limits**:
    - Free tier: 26,000 tokens/day/user
    - Pro tier: 260,000 tokens/day/user
    - Enterprise: Unlimited
    """

    # Per-prompt limits
    MAX_INPUT_TOKENS = 1500
    MAX_OUTPUT_TOKENS = 5000

    # Agent allocation percentages
    ARCHITECT_PERCENTAGE = 0.15  # 15%
    CODER_PERCENTAGE = 0.70      # 70%
    REVIEWER_PERCENTAGE = 0.15   # 15%

    # Daily limits by tier
    DAILY_LIMITS = {
        "free": 26000,
        "pro": 260000,
        "enterprise": float('inf')
    }

    def __init__(self):
        """Initialize TokenManager"""
        # Calculate agent-specific limits
        self.agent_limits = {
            "architect": int(self.MAX_OUTPUT_TOKENS * self.ARCHITECT_PERCENTAGE),  # 750
            "coder": int(self.MAX_OUTPUT_TOKENS * self.CODER_PERCENTAGE),          # 3500
            "reviewer": int(self.MAX_OUTPUT_TOKENS * self.REVIEWER_PERCENTAGE)     # 750
        }

    async def check_daily_limit(
        self,
        user_id: str,
        required_tokens: int,
        tier: str = "free"
    ) -> Dict[str, any]:
        """
        Check if user is within daily token limit

        Args:
            user_id: User UUID
            required_tokens: Tokens needed for request
            tier: Subscription tier

        Returns:
            {
                "allowed": bool,
                "used_today": int,
                "limit": int,
                "remaining": int,
                "percentage_used": float
            }

        Raises:
            QuotaExceededError: If daily limit exceeded
        """
        try:
            limit = self.DAILY_LIMITS.get(tier, self.DAILY_LIMITS["free"])

            # Get today's usage from Redis
            usage = await redis_service.get_token_usage(user_id, period="today")
            used_today = usage.get("total", 0)

            remaining = max(0, limit - used_today)
            percentage_used = (used_today / limit * 100) if limit != float('inf') else 0
            allowed = (used_today + required_tokens) <= limit

            result = {
                "allowed": allowed,
                "used_today": used_today,
                "limit": limit,
                "remaining": remaining,
                "required": required_tokens,
                "percentage_used": percentage_used
            }

            if not allowed:
                raise QuotaExceededError(
                    quota_type="Daily AI tokens",
                    limit=limit,
                    current=used_today,
                    details={
                        "tier": tier,
                        "required": required_tokens,
                        "remaining": remaining
                    }
                )

            # Warn if approaching limit (90%)
            if percentage_used >= 90 and tier == "free":
                logger.warning(
                    f"User {user_id} approaching daily limit: "
                    f"{used_today}/{limit} ({percentage_used:.1f}%)"
                )

            return result

        except QuotaExceededError:
            raise
        except Exception as e:
            logger.error(f"Failed to check daily limit: {e}")
            # Fail open - allow request if check fails
            return {
                "allowed": True,
                "used_today": 0,
                "limit": limit,
                "remaining": limit,
                "required": required_tokens,
                "percentage_used": 0
            }

    def validate_input_tokens(self, input_tokens: int) -> bool:
        """
        Validate input tokens are within limit

        Args:
            input_tokens: Number of input tokens

        Returns:
            True if within limit

        Raises:
            QuotaExceededError: If input exceeds MAX_INPUT_TOKENS (1500)
        """
        if input_tokens > self.MAX_INPUT_TOKENS:
            raise QuotaExceededError(
                quota_type="Input tokens per prompt",
                limit=self.MAX_INPUT_TOKENS,
                current=input_tokens,
                details={
                    "message": f"Prompt too long. Please shorten to {self.MAX_INPUT_TOKENS} tokens or less."
                }
            )
        return True

    def get_agent_limit(self, agent_name: str) -> int:
        """
        Get token limit for a specific agent

        Args:
            agent_name: "architect", "coder", or "reviewer"

        Returns:
            Max tokens allowed for that agent
        """
        return self.agent_limits.get(agent_name, 0)

    def validate_agent_output(self, agent_name: str, output_tokens: int) -> bool:
        """
        Validate agent output is within its allocated limit

        Args:
            agent_name: "architect", "coder", or "reviewer"
            output_tokens: Number of tokens in agent's output

        Returns:
            True if within limit (logs warning if exceeded)
        """
        limit = self.get_agent_limit(agent_name)

        if output_tokens > limit:
            logger.warning(
                f"Agent '{agent_name}' exceeded token limit: "
                f"{output_tokens}/{limit} tokens ({output_tokens/limit*100:.1f}%)"
            )
            # Don't raise error - just log warning
            # Agent already completed, we'll still accept it
            return False

        return True

    async def track_agent_usage(
        self,
        user_id: str,
        agent_id: str,
        agent_name: str,
        input_tokens: int,
        output_tokens: int,
        model: str = "nvidia/nemotron-nano-12b-v2-vl"
    ):
        """
        Track token usage for a specific agent execution

        Args:
            user_id: User UUID
            agent_id: Agent UUID
            agent_name: "architect", "coder", or "reviewer"
            input_tokens: Tokens in input/prompt
            output_tokens: Tokens in output/completion
            model: AI model name
        """
        try:
            total_tokens = input_tokens + output_tokens

            # Track in Redis via token counter
            await token_counter.track_usage(
                user_id=user_id,
                agent_id=agent_id,
                prompt_tokens=input_tokens,
                completion_tokens=output_tokens,
                model=model
            )

            # Log detailed agent usage
            logger.info(
                f"Agent usage tracked: user={user_id}, agent={agent_id}, "
                f"agent_name={agent_name}, input={input_tokens}, "
                f"output={output_tokens}, total={total_tokens}, "
                f"limit={self.get_agent_limit(agent_name)}"
            )

            # Validate agent stayed within limit
            self.validate_agent_output(agent_name, output_tokens)

        except Exception as e:
            logger.error(f"Failed to track agent usage: {e}")

    async def estimate_workflow_cost(self, input_text: str) -> Dict[str, int]:
        """
        Estimate total token cost for 3-agent workflow

        Args:
            input_text: User's vibe prompt

        Returns:
            {
                "input_tokens": int,
                "architect_tokens": int,
                "coder_tokens": int,
                "reviewer_tokens": int,
                "total_tokens": int
            }
        """
        # Count input tokens
        input_tokens = token_counter.count_tokens(input_text)

        # Estimate output tokens (use allocated limits)
        estimate = {
            "input_tokens": input_tokens,
            "architect_tokens": self.agent_limits["architect"],
            "coder_tokens": self.agent_limits["coder"],
            "reviewer_tokens": self.agent_limits["reviewer"],
            "total_tokens": (
                input_tokens +
                self.agent_limits["architect"] +
                self.agent_limits["coder"] +
                self.agent_limits["reviewer"]
            )
        }

        return estimate

    async def check_workflow_quota(
        self,
        user_id: str,
        input_text: str,
        tier: str = "free"
    ) -> Dict[str, any]:
        """
        Check if user has enough quota for entire 3-agent workflow

        Args:
            user_id: User UUID
            input_text: User's vibe prompt
            tier: Subscription tier

        Returns:
            {
                "allowed": bool,
                "estimate": {...},
                "quota": {...}
            }

        Raises:
            QuotaExceededError: If quota exceeded
        """
        # 1. Validate input length
        input_tokens = token_counter.count_tokens(input_text)
        self.validate_input_tokens(input_tokens)

        # 2. Estimate workflow cost
        estimate = await self.estimate_workflow_cost(input_text)

        # 3. Check daily quota
        quota = await self.check_daily_limit(
            user_id=user_id,
            required_tokens=estimate["total_tokens"],
            tier=tier
        )

        return {
            "allowed": quota["allowed"],
            "estimate": estimate,
            "quota": quota
        }

    def get_limits_info(self) -> Dict[str, any]:
        """
        Get information about all token limits

        Returns:
            Complete limits configuration
        """
        return {
            "per_prompt": {
                "max_input": self.MAX_INPUT_TOKENS,
                "max_output": self.MAX_OUTPUT_TOKENS
            },
            "agent_allocation": {
                "architect": {
                    "percentage": self.ARCHITECT_PERCENTAGE * 100,
                    "tokens": self.agent_limits["architect"]
                },
                "coder": {
                    "percentage": self.CODER_PERCENTAGE * 100,
                    "tokens": self.agent_limits["coder"]
                },
                "reviewer": {
                    "percentage": self.REVIEWER_PERCENTAGE * 100,
                    "tokens": self.agent_limits["reviewer"]
                }
            },
            "daily_limits": self.DAILY_LIMITS,
            "total_workflow_estimate": (
                self.MAX_INPUT_TOKENS +
                self.agent_limits["architect"] +
                self.agent_limits["coder"] +
                self.agent_limits["reviewer"]
            )
        }


# Global instance
token_manager = TokenManager()
