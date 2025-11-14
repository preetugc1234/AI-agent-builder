"""
WebSocket message handlers for different event types
"""

import logging
from typing import Dict, Any
from app.websockets.manager import manager
from app.workflows.ai_generation import AIGenerationWorkflow
from app.workflows.agent_execution import AgentExecutionWorkflow
from app.workflows.deployment import DeploymentWorkflow

logger = logging.getLogger(__name__)


async def handle_websocket_message(agent_id: str, connection_id: str, message: Dict[str, Any]):
    """
    Route WebSocket messages to appropriate handlers

    Args:
        agent_id: The agent ID
        connection_id: The connection ID
        message: The message data from frontend
    """
    message_type = message.get("type")

    try:
        if message_type == "ai-generation-request":
            await handle_ai_generation_request(agent_id, message)

        elif message_type == "agent-execution-start":
            await handle_agent_execution_start(agent_id, message)

        elif message_type == "agent-execution-stop":
            await handle_agent_execution_stop(agent_id, message)

        elif message_type == "deployment-request":
            await handle_deployment_request(agent_id, message)

        elif message_type == "terminal-command":
            await handle_terminal_command(agent_id, message)

        elif message_type == "ping":
            await handle_ping(agent_id, connection_id)

        else:
            logger.warning(f"Unknown message type: {message_type}")
            await manager.broadcast_to_agent(agent_id, {
                "type": "error",
                "message": f"Unknown message type: {message_type}"
            })

    except Exception as e:
        logger.error(f"Error handling message {message_type}: {str(e)}")
        await manager.broadcast_to_agent(agent_id, {
            "type": "error",
            "message": str(e),
            "original_type": message_type
        })


async def handle_ai_generation_request(agent_id: str, message: Dict[str, Any]):
    """
    Handle AI code generation request

    Args:
        agent_id: The agent ID
        message: Message containing prompt and user_id
    """
    logger.info(f"AI generation request for agent: {agent_id}")

    workflow = AIGenerationWorkflow(agent_id)
    prompt = message.get("prompt", "")
    user_id = message.get("user_id", "")

    # Run generation workflow (it will send WebSocket updates internally)
    await workflow.generate_agent_with_websocket_updates(prompt, user_id)


async def handle_agent_execution_start(agent_id: str, message: Dict[str, Any]):
    """
    Handle agent execution start request

    Args:
        agent_id: The agent ID
        message: Message containing input data
    """
    logger.info(f"Agent execution start for agent: {agent_id}")

    workflow = AgentExecutionWorkflow(agent_id)
    input_data = message.get("input_data", {})

    # Run execution workflow
    await workflow.execute_agent_with_websocket(input_data)


async def handle_agent_execution_stop(agent_id: str, message: Dict[str, Any]):
    """
    Handle agent execution stop request

    Args:
        agent_id: The agent ID
        message: Stop request message
    """
    logger.info(f"Agent execution stop for agent: {agent_id}")

    # TODO: Implement execution stopping logic
    await manager.broadcast_to_agent(agent_id, {
        "type": "agent-execution-stopped",
        "agent_id": agent_id,
        "message": "Agent execution stopped by user"
    })


async def handle_deployment_request(agent_id: str, message: Dict[str, Any]):
    """
    Handle deployment request

    Args:
        agent_id: The agent ID
        message: Message containing platform info
    """
    logger.info(f"Deployment request for agent: {agent_id}")

    workflow = DeploymentWorkflow(agent_id)
    platform = message.get("platform", "ecs")

    # Run deployment workflow
    await workflow.deploy_agent_with_websocket(platform)


async def handle_terminal_command(agent_id: str, message: Dict[str, Any]):
    """
    Handle terminal command execution

    Args:
        agent_id: The agent ID
        message: Message containing command
    """
    logger.info(f"Terminal command for agent: {agent_id}")

    command = message.get("command", "")

    # TODO: Implement safe terminal command execution
    await manager.broadcast_to_agent(agent_id, {
        "type": "terminal-output",
        "agent_id": agent_id,
        "output": f"$ {command}\n",
        "stream": "stdout"
    })


async def handle_ping(agent_id: str, connection_id: str):
    """
    Handle ping/pong for connection health check

    Args:
        agent_id: The agent ID
        connection_id: The connection ID
    """
    await manager.broadcast_to_agent(agent_id, {
        "type": "pong",
        "connection_id": connection_id
    })
