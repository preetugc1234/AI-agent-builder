"""
WebSocket Connection Manager
Handles real-time connections for agent operations
"""

import asyncio
import json
import uuid
from typing import Dict, Set, Any
from fastapi import WebSocket
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time agent operations"""

    def __init__(self):
        # agent_id -> set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # connection_id -> agent_id mapping
        self.connection_agents: Dict[str, str] = {}
        # connection_id -> WebSocket mapping
        self.connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, agent_id: str) -> str:
        """
        Accept and register a new WebSocket connection

        Args:
            websocket: The WebSocket connection
            agent_id: The agent ID this connection is for

        Returns:
            connection_id: Unique identifier for this connection
        """
        await websocket.accept()

        connection_id = str(uuid.uuid4())

        # Initialize agent connections if not exists
        if agent_id not in self.active_connections:
            self.active_connections[agent_id] = set()

        # Register connection
        self.active_connections[agent_id].add(websocket)
        self.connection_agents[connection_id] = agent_id
        self.connections[connection_id] = websocket

        # Send connection established event
        await self.send_personal_message(
            {
                "type": "connection-established",
                "connection_id": connection_id,
                "agent_id": agent_id,
                "timestamp": datetime.utcnow().isoformat()
            },
            websocket
        )

        logger.info(f"WebSocket connected: {connection_id} for agent: {agent_id}")
        return connection_id

    async def disconnect(self, websocket: WebSocket, connection_id: str):
        """
        Disconnect and cleanup a WebSocket connection

        Args:
            websocket: The WebSocket connection to disconnect
            connection_id: The connection ID
        """
        agent_id = self.connection_agents.get(connection_id)

        if agent_id and agent_id in self.active_connections:
            self.active_connections[agent_id].discard(websocket)

            # Remove empty agent entries
            if not self.active_connections[agent_id]:
                del self.active_connections[agent_id]

        # Cleanup mappings
        if connection_id in self.connection_agents:
            del self.connection_agents[connection_id]

        if connection_id in self.connections:
            del self.connections[connection_id]

        logger.info(f"WebSocket disconnected: {connection_id}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """
        Send message to a specific WebSocket connection

        Args:
            message: The message dictionary to send
            websocket: The target WebSocket connection
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {str(e)}")

    async def broadcast_to_agent(self, agent_id: str, message: dict):
        """
        Broadcast message to all connections for a specific agent

        Args:
            agent_id: The agent ID
            message: The message dictionary to broadcast
        """
        if agent_id not in self.active_connections:
            logger.warning(f"No active connections for agent: {agent_id}")
            return

        disconnected = set()

        for websocket in self.active_connections[agent_id]:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to agent {agent_id}: {str(e)}")
                disconnected.add(websocket)

        # Clean up disconnected sockets
        if disconnected:
            self.active_connections[agent_id] -= disconnected

    async def broadcast_to_all(self, message: dict):
        """
        Broadcast message to all active connections

        Args:
            message: The message dictionary to broadcast
        """
        for agent_id in list(self.active_connections.keys()):
            await self.broadcast_to_agent(agent_id, message)

    def get_agent_connections_count(self, agent_id: str) -> int:
        """
        Get number of active connections for an agent

        Args:
            agent_id: The agent ID

        Returns:
            Number of active connections
        """
        return len(self.active_connections.get(agent_id, set()))

    def get_total_connections_count(self) -> int:
        """
        Get total number of active connections

        Returns:
            Total number of active connections
        """
        return sum(len(connections) for connections in self.active_connections.values())


# Global WebSocket manager instance
manager = ConnectionManager()
