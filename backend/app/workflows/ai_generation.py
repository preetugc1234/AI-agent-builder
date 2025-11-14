"""
AI Agent Generation Workflow with real-time WebSocket updates
"""

import logging
from typing import List, Dict, Any
from datetime import datetime
from app.websockets.manager import manager
from app.services.ai_service import NemotronAIService

logger = logging.getLogger(__name__)


class AIGenerationWorkflow:
    """Workflow for AI-powered agent code generation"""

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.ai_service = NemotronAIService()

    async def generate_agent_with_websocket_updates(
        self,
        prompt: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Generate agent code with real-time WebSocket progress updates

        Args:
            prompt: User's vibe prompt
            user_id: User ID

        Returns:
            Generated agent data
        """
        try:
            # Step 1: Notify generation start
            await self._send_update("ai-generation-start", {
                "agent_id": self.agent_id,
                "prompt": prompt,
                "status": "started"
            })

            # Step 2: Parse prompt and detect integrations
            await self._send_update("ai-generation-progress", {
                "agent_id": self.agent_id,
                "step": "parsing_prompt",
                "progress": 10,
                "message": "Analyzing your agent requirements..."
            })

            integrations = await self.ai_service.detect_integrations(prompt)

            await self._send_update("ai-generation-integration-detected", {
                "agent_id": self.agent_id,
                "integrations": integrations,
                "progress": 20
            })

            # Step 3: Generate flow visualization
            await self._send_update("ai-generation-progress", {
                "agent_id": self.agent_id,
                "step": "generating_visualization",
                "progress": 30,
                "message": "Creating visual flow diagram..."
            })

            flow_data = await self.ai_service.generate_flow_data(prompt, integrations)

            await self._send_update("agent-flow-update", {
                "agent_id": self.agent_id,
                "nodes": flow_data["nodes"],
                "edges": flow_data["edges"],
                "status": "building"
            })

            # Step 4: Generate agent code
            await self._send_update("ai-generation-progress", {
                "agent_id": self.agent_id,
                "step": "generating_code",
                "progress": 50,
                "message": "Generating agent code with AI..."
            })

            code_data = await self.ai_service.generate_agent_code(
                prompt,
                integrations,
                user_id
            )

            # Step 5: Send code files one by one
            files = code_data.copy()
            integrations_list = files.pop("integrations", [])

            progress = 60
            for filename, code in files.items():
                await self._send_update("ai-generation-code-chunk", {
                    "agent_id": self.agent_id,
                    "file": filename,
                    "code": code,
                    "progress": progress
                })
                progress += 10

            # Step 6: Complete generation
            await self._send_update("ai-generation-complete", {
                "agent_id": self.agent_id,
                "files": list(files.keys()),
                "integrations": integrations_list,
                "flow_data": flow_data,
                "progress": 100,
                "message": "Agent generated successfully!"
            })

            return {
                "code_files": files,
                "integrations": integrations_list,
                "flow_data": flow_data
            }

        except Exception as e:
            logger.error(f"Error in AI generation workflow: {str(e)}")

            await self._send_update("ai-generation-error", {
                "agent_id": self.agent_id,
                "error": str(e),
                "step": "generation"
            })

            raise

    async def _send_update(self, event_type: str, data: Dict[str, Any]):
        """
        Send WebSocket update

        Args:
            event_type: Type of event
            data: Event data
        """
        message = {
            "type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            **data
        }

        await manager.broadcast_to_agent(self.agent_id, message)

    async def cleanup(self):
        """Cleanup resources"""
        await self.ai_service.close()
