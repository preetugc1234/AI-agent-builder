"""
AI Service - OpenRouter Integration with NVIDIA Nemotron
Handles API calls to NVIDIA Nemotron via OpenRouter
Includes reasoning support and token management
"""

import logging
from typing import List, Dict, Optional, Any
from openai import OpenAI

from app.core.config import settings
from app.services.token_manager import token_manager
from app.services.token_counter_service import token_counter
from app.core.exceptions import AIGenerationError, QuotaExceededError

logger = logging.getLogger(__name__)


class AIService:
    """
    Service for calling NVIDIA Nemotron via OpenRouter

    Features:
    - OpenRouter API integration
    - NVIDIA Nemotron model support
    - Reasoning mode enabled
    - Token tracking and limits
    - Error handling and retries
    """

    # Model configuration
    MODEL = "nvidia/nemotron-nano-12b-v2-vl:free"
    BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(self):
        """Initialize AI service with OpenRouter client"""
        try:
            self.client = OpenAI(
                base_url=self.BASE_URL,
                api_key=settings.OPENROUTER_API_KEY
            )
            logger.info(f"✅ AI Service initialized with model: {self.MODEL}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize AI Service: {e}")
            self.client = None

    async def generate(
        self,
        messages: List[Dict[str, str]],
        user_id: str,
        agent_id: Optional[str] = None,
        agent_name: str = "unknown",
        max_tokens: Optional[int] = None,
        enable_reasoning: bool = True,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Generate AI response using NVIDIA Nemotron

        Args:
            messages: List of chat messages [{"role": "user", "content": "..."}]
            user_id: User UUID for tracking
            agent_id: Agent UUID for tracking (optional)
            agent_name: "architect", "coder", or "reviewer"
            max_tokens: Max completion tokens (defaults to agent limit)
            enable_reasoning: Enable reasoning mode
            temperature: Sampling temperature (0-1)

        Returns:
            {
                "content": str,
                "reasoning_details": dict (if enabled),
                "usage": {"prompt_tokens": int, "completion_tokens": int, "total_tokens": int},
                "model": str
            }

        Raises:
            AIGenerationError: If generation fails
            QuotaExceededError: If quota exceeded
        """
        try:
            if not self.client:
                raise AIGenerationError(
                    "AI Service not initialized",
                    details={"reason": "OpenRouter client is None"}
                )

            # 1. Set max_tokens from agent limit if not specified
            if max_tokens is None:
                max_tokens = token_manager.get_agent_limit(agent_name)
                if max_tokens == 0:
                    max_tokens = 2000  # Fallback

            # 2. Count input tokens
            input_tokens = token_counter.count_messages_tokens(messages)

            # 3. Check daily quota before API call
            quota_check = await token_manager.check_daily_limit(
                user_id=user_id,
                required_tokens=input_tokens + max_tokens,
                tier="free"  # TODO: Get tier from user object
            )

            logger.info(
                f"Generating with {agent_name}: input={input_tokens}, "
                f"max_output={max_tokens}, quota={quota_check['remaining']}/{quota_check['limit']}"
            )

            # 4. Call OpenRouter API
            extra_body = {}
            if enable_reasoning:
                extra_body["reasoning"] = {"enabled": True}

            response = self.client.chat.completions.create(
                model=self.MODEL,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                extra_body=extra_body
            )

            # 5. Extract response
            assistant_message = response.choices[0].message
            content = assistant_message.content

            # Extract reasoning details if available
            reasoning_details = None
            if hasattr(assistant_message, 'reasoning_details'):
                reasoning_details = assistant_message.reasoning_details

            # 6. Get token usage from API response
            usage = response.usage
            prompt_tokens = usage.prompt_tokens if hasattr(usage, 'prompt_tokens') else input_tokens
            completion_tokens = usage.completion_tokens if hasattr(usage, 'completion_tokens') else 0
            total_tokens = usage.total_tokens if hasattr(usage, 'total_tokens') else (prompt_tokens + completion_tokens)

            # Fallback: count manually if API doesn't provide
            if completion_tokens == 0:
                completion_tokens = token_counter.count_tokens(content)
                total_tokens = prompt_tokens + completion_tokens

            # 7. Track usage
            await token_manager.track_agent_usage(
                user_id=user_id,
                agent_id=agent_id or "unknown",
                agent_name=agent_name,
                input_tokens=prompt_tokens,
                output_tokens=completion_tokens,
                model=self.MODEL
            )

            # 8. Validate agent output
            token_manager.validate_agent_output(agent_name, completion_tokens)

            logger.info(
                f"✅ {agent_name} completed: prompt={prompt_tokens}, "
                f"completion={completion_tokens}, total={total_tokens}"
            )

            return {
                "content": content,
                "reasoning_details": reasoning_details,
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens
                },
                "model": self.MODEL,
                "agent_name": agent_name
            }

        except QuotaExceededError:
            raise
        except Exception as e:
            logger.error(f"❌ AI generation failed: {e}")
            raise AIGenerationError(
                "Failed to generate AI response",
                details={"error": str(e), "agent": agent_name}
            )

    async def generate_with_context(
        self,
        messages: List[Dict[str, str]],
        user_id: str,
        agent_id: Optional[str] = None,
        agent_name: str = "unknown",
        preserve_reasoning: bool = True
    ) -> Dict[str, Any]:
        """
        Generate response while preserving reasoning from previous messages

        This is used for multi-turn conversations where reasoning should continue.

        Args:
            messages: Chat history including previous assistant messages with reasoning
            user_id: User UUID
            agent_id: Agent UUID
            agent_name: Agent name
            preserve_reasoning: Whether to preserve reasoning_details in context

        Returns:
            Same format as generate()
        """
        # Call generate with the full message history
        # The model will see previous reasoning and continue from there
        return await self.generate(
            messages=messages,
            user_id=user_id,
            agent_id=agent_id,
            agent_name=agent_name,
            enable_reasoning=True
        )

    async def architect_generate(
        self,
        vibe_prompt: str,
        user_id: str,
        agent_id: str
    ) -> Dict[str, Any]:
        """
        Agent 1: Architect - Design system architecture

        Allocation: 15% of output (750 tokens)

        Args:
            vibe_prompt: User's natural language description
            user_id: User UUID
            agent_id: Agent UUID

        Returns:
            Architecture design document
        """
        messages = [
            {
                "role": "system",
                "content": (
                    "You are the Architect Agent. Analyze the user's requirements and design "
                    "a complete system architecture. Output a structured architecture document "
                    "including: 1) System overview, 2) Component breakdown, 3) Data flow, "
                    "4) Technology stack, 5) File structure. Be concise and technical."
                )
            },
            {
                "role": "user",
                "content": f"Design the architecture for:\n\n{vibe_prompt}"
            }
        ]

        result = await self.generate(
            messages=messages,
            user_id=user_id,
            agent_id=agent_id,
            agent_name="architect",
            enable_reasoning=True
        )

        return {
            "architecture": result["content"],
            "reasoning": result.get("reasoning_details"),
            "usage": result["usage"]
        }

    async def coder_generate(
        self,
        architecture: str,
        vibe_prompt: str,
        user_id: str,
        agent_id: str
    ) -> Dict[str, Any]:
        """
        Agent 2: Coder - Write production-ready code

        Allocation: 70% of output (3,500 tokens)

        Args:
            architecture: Architecture from Agent 1
            vibe_prompt: Original user prompt
            user_id: User UUID
            agent_id: Agent UUID

        Returns:
            Generated code
        """
        messages = [
            {
                "role": "system",
                "content": (
                    "You are the Coder Agent. Implement the architecture with production-ready code. "
                    "Write clean, documented, modular code following best practices. "
                    "Include all necessary files, configurations, and dependencies."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Original Request:\n{vibe_prompt}\n\n"
                    f"Architecture:\n{architecture}\n\n"
                    f"Implement this architecture with complete, working code."
                )
            }
        ]

        result = await self.generate(
            messages=messages,
            user_id=user_id,
            agent_id=agent_id,
            agent_name="coder",
            enable_reasoning=True
        )

        return {
            "code": result["content"],
            "reasoning": result.get("reasoning_details"),
            "usage": result["usage"]
        }

    async def reviewer_generate(
        self,
        architecture: str,
        code: str,
        vibe_prompt: str,
        user_id: str,
        agent_id: str
    ) -> Dict[str, Any]:
        """
        Agent 3: Reviewer - Review and improve code

        Allocation: 15% of output (750 tokens)

        Args:
            architecture: Architecture from Agent 1
            code: Code from Agent 2
            vibe_prompt: Original user prompt
            user_id: User UUID
            agent_id: Agent UUID

        Returns:
            Review notes and final code
        """
        messages = [
            {
                "role": "system",
                "content": (
                    "You are the Reviewer Agent. Review the code for correctness, best practices, "
                    "security, and performance. Provide specific feedback and suggestions. "
                    "Output: 1) Review summary, 2) Issues found, 3) Recommendations, 4) Final approval status."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Original Request:\n{vibe_prompt}\n\n"
                    f"Architecture:\n{architecture}\n\n"
                    f"Code:\n{code}\n\n"
                    f"Review this implementation thoroughly."
                )
            }
        ]

        result = await self.generate(
            messages=messages,
            user_id=user_id,
            agent_id=agent_id,
            agent_name="reviewer",
            enable_reasoning=True
        )

        return {
            "review": result["content"],
            "reasoning": result.get("reasoning_details"),
            "usage": result["usage"]
        }

    def get_model_info(self) -> Dict[str, str]:
        """Get information about the AI model being used"""
        return {
            "model": self.MODEL,
            "provider": "OpenRouter",
            "base_model": "NVIDIA Nemotron Nano 12B",
            "features": ["reasoning", "free_tier", "vision"],
            "base_url": self.BASE_URL
        }


# Global instance
ai_service = AIService()
