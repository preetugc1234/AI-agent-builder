Real-Time WebSocket Architecture for VibeAgent Forge
🏗️ WebSocket System Architecture
High-Level WebSocket Flow
text
┌─────────────────┐    WebSocket Connections    ┌─────────────────┐
│   Frontend      │◄───────────────────────────►│   Backend       │
│   Next.js 15    │                             │   FastAPI       │
└─────────────────┘                             └─────────────────┘
         │                                              │
         │                                              │
         ▼                                              ▼
┌─────────────────┐                            ┌─────────────────┐
│   UI Components │                            │ WebSocket Manager│
│   • Chat        │                            │   • Connection   │
│   • Agent Flow  │                            │     Pool         │
│   • Terminal    │                            │   • Room Mgmt    │
│   • Code Editor │                            │   • Broadcast    │
└─────────────────┘                            └─────────────────┘
                                                         │
                                                         ▼
                                            ┌─────────────────────────┐
                                            │   Real-time Services    │
                                            │   • AI Generation       │
                                            │   • Agent Execution     │
                                            │   • Docker Build        │
                                            │   • Deployment          │
                                            └─────────────────────────┘
🔌 WebSocket Event Types
1. AI Generation Events
typescript
interface AIGenerationEvents {
  'ai-generation-start': { agentId: string; prompt: string };
  'ai-generation-progress': { agentId: string; step: string; progress: number };
  'ai-generation-code-chunk': { agentId: string; code: string; file: string };
  'ai-generation-integration-detected': { agentId: string; integrations: string[] };
  'ai-generation-complete': { agentId: string; code: string; files: string[] };
  'ai-generation-error': { agentId: string; error: string; step: string };
}
2. Agent Visualization Events
typescript
interface AgentVisualizationEvents {
  'agent-flow-update': { 
    agentId: string; 
    nodes: FlowNode[];
    connections: Connection[];
    status: 'building' | 'ready' | 'error';
  };
  'agent-node-status': {
    agentId: string;
    nodeId: string;
    status: 'pending' | 'running' | 'success' | 'error';
    output?: any;
  };
  'agent-execution-start': { agentId: string; trigger: string };
  'agent-execution-progress': { agentId: string; currentNode: string; progress: number };
  'agent-execution-complete': { agentId: string; result: any; duration: number };
}
3. Terminal & Logs Events
typescript
interface TerminalEvents {
  'terminal-output': { agentId: string; output: string; type: 'stdout' | 'stderr' };
  'terminal-command': { agentId: string; command: string };
  'terminal-clear': { agentId: string };
  'terminal-status': { agentId: string; status: 'connected' | 'disconnected' | 'error' };
}
4. Deployment Events
typescript
interface DeploymentEvents {
  'deployment-start': { agentId: string; platform: 'ecs' | 'lambda' | 'local' };
  'deployment-building': { agentId: string; step: string; progress: number };
  'deployment-logs': { agentId: string; logs: string };
  'deployment-status': { agentId: string; status: DeploymentStatus; url?: string };
  'deployment-error': { agentId: string; error: string; step: string };
}
🔧 Backend WebSocket Implementation
1. WebSocket Manager
python
# websockets/websocket_manager.py
import asyncio
import json
import uuid
from typing import Dict, Set, Any
from fastapi import WebSocket, WebSocketDisconnect

class ConnectionManager:
    def __init__(self):
        # agent_id -> set of connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # connection_id -> agent_id
        self.connection_agents: Dict[str, str] = {}
    
    async def connect(self, websocket: WebSocket, agent_id: str):
        await websocket.accept()
        connection_id = str(uuid.uuid4())
        
        if agent_id not in self.active_connections:
            self.active_connections[agent_id] = set()
        
        self.active_connections[agent_id].add(websocket)
        self.connection_agents[connection_id] = agent_id
        
        # Send connection established event
        await self.send_personal_message({
            "type": "connection-established",
            "connection_id": connection_id,
            "agent_id": agent_id
        }, websocket)
        
        return connection_id
    
    async def disconnect(self, websocket: WebSocket, connection_id: str):
        agent_id = self.connection_agents.get(connection_id)
        if agent_id and agent_id in self.active_connections:
            self.active_connections[agent_id].discard(websocket)
            if not self.active_connections[agent_id]:
                del self.active_connections[agent_id]
        
        if connection_id in self.connection_agents:
            del self.connection_agents[connection_id]
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)
    
    async def broadcast_to_agent(self, agent_id: str, message: dict):
        if agent_id in self.active_connections:
            disconnected = set()
            for websocket in self.active_connections[agent_id]:
                try:
                    await websocket.send_json(message)
                except Exception:
                    disconnected.add(websocket)
            
            # Clean up disconnected sockets
            self.active_connections[agent_id] -= disconnected
    
    async def broadcast_to_all(self, message: dict):
        for agent_id in list(self.active_connections.keys()):
            await self.broadcast_to_agent(agent_id, message)

# Global WebSocket manager instance
manager = ConnectionManager()
2. FastAPI WebSocket Endpoints
python
# websockets/endpoints.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
import json

router = APIRouter()

@router.websocket("/ws/agent/{agent_id}")
async def websocket_agent_endpoint(websocket: WebSocket, agent_id: str):
    connection_id = await manager.connect(websocket, agent_id)
    
    try:
        while True:
            # Listen for incoming messages from frontend
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            await handle_websocket_message(agent_id, connection_id, message)
            
    except WebSocketDisconnect:
        await manager.disconnect(websocket, connection_id)
        print(f"Client {connection_id} disconnected from agent {agent_id}")

async def handle_websocket_message(agent_id: str, connection_id: str, message: dict):
    message_type = message.get("type")
    
    if message_type == "ai-generation-request":
        await handle_ai_generation_request(agent_id, message)
    
    elif message_type == "agent-execution-start":
        await handle_agent_execution_start(agent_id, message)
    
    elif message_type == "terminal-command":
        await handle_terminal_command(agent_id, message)
    
    elif message_type == "deployment-request":
        await handle_deployment_request(agent_id, message)
    
    elif message_type == "subscribe-logs":
        await handle_subscribe_logs(agent_id, connection_id, message)
3. AI Generation with Real-time Updates
python
# workflows/ai_generation_websocket.py
class AIGenerationWebSocketWorkflow:
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.nemotron = NemotronAI()
    
    async def generate_agent_with_websocket_updates(self, prompt: str):
        try:
            # Step 1: Notify generation start
            await manager.broadcast_to_agent(self.agent_id, {
                "type": "ai-generation-start",
                "agent_id": self.agent_id,
                "prompt": prompt,
                "timestamp": self._get_timestamp()
            })
            
            # Step 2: Parse prompt and detect integrations
            await manager.broadcast_to_agent(self.agent_id, {
                "type": "ai-generation-progress",
                "agent_id": self.agent_id,
                "step": "parsing_prompt",
                "progress": 10,
                "message": "Analyzing your agent requirements..."
            })
            
            integrations = await self._detect_integrations(prompt)
            
            await manager.broadcast_to_agent(self.agent_id, {
                "type": "ai-generation-integration-detected",
                "agent_id": self.agent_id,
                "integrations": integrations,
                "progress": 20
            })
            
            # Step 3: Generate agent structure
            await manager.broadcast_to_agent(self.agent_id, {
                "type": "ai-generation-progress",
                "agent_id": self.agent_id,
                "step": "generating_structure",
                "progress": 30,
                "message": "Creating agent architecture..."
            })
            
            # Update visualization with initial nodes
            await self._update_agent_visualization(integrations)
            
            # Step 4: Generate code files in chunks
            files = await self._generate_code_files(prompt, integrations)
            
            # Step 5: Complete generation
            await manager.broadcast_to_agent(self.agent_id, {
                "type": "ai-generation-complete",
                "agent_id": self.agent_id,
                "files": files,
                "integrations": integrations,
                "progress": 100,
                "message": "Agent generation complete!"
            })
            
        except Exception as e:
            await manager.broadcast_to_agent(self.agent_id, {
                "type": "ai-generation-error",
                "agent_id": self.agent_id,
                "error": str(e),
                "step": "generation",
                "timestamp": self._get_timestamp()
            })
            raise
    
    async def _generate_code_files(self, prompt: str, integrations: list):
        files = {}
        
        # Generate main agent file
        await manager.broadcast_to_agent(self.agent_id, {
            "type": "ai-generation-progress",
            "agent_id": self.agent_id,
            "step": "generating_main",
            "progress": 50,
            "message": "Writing main agent logic..."
        })
        
        main_code = await self.nemotron.generate_agent_code(prompt, integrations)
        files["main.py"] = main_code
        
        # Send code chunk by chunk for real-time editor updates
        await manager.broadcast_to_agent(self.agent_id, {
            "type": "ai-generation-code-chunk",
            "agent_id": self.agent_id,
            "file": "main.py",
            "code": main_code,
            "progress": 60
        })
        
        # Generate requirements.txt
        await manager.broadcast_to_agent(self.agent_id, {
            "type": "ai-generation-progress",
            "agent_id": self.agent_id,
            "step": "generating_dependencies",
            "progress": 70,
            "message": "Configuring dependencies..."
        })
        
        requirements = self._generate_requirements(integrations)
        files["requirements.txt"] = requirements
        
        await manager.broadcast_to_agent(self.agent_id, {
            "type": "ai-generation-code-chunk",
            "agent_id": self.agent_id,
            "file": "requirements.txt",
            "code": requirements,
            "progress": 80
        })
        
        # Generate Dockerfile
        dockerfile = self._generate_dockerfile(integrations)
        files["Dockerfile"] = dockerfile
        
        await manager.broadcast_to_agent(self.agent_id, {
            "type": "ai-generation-code-chunk",
            "agent_id": self.agent_id,
            "file": "Dockerfile",
            "code": dockerfile,
            "progress": 90
        })
        
        return files
    
    async def _update_agent_visualization(self, integrations: list):
        """Update the visual agent flow in real-time"""
        nodes = []
        connections = []
        
        # Create input node
        nodes.append({
            "id": "input",
            "type": "input",
            "data": { "label": "User Input" },
            "position": { "x": 100, "y": 100 }
        })
        
        # Create integration nodes
        for i, integration in enumerate(integrations):
            nodes.append({
                "id": f"integration_{integration}",
                "type": "integration",
                "data": { "label": integration, "status": "pending" },
                "position": { "x": 300, "y": 100 + (i * 100) }
            })
            
            connections.append({
                "id": f"conn_input_{integration}",
                "source": "input",
                "target": f"integration_{integration}",
                "type": "smoothstep"
            })
        
        # Create output node
        nodes.append({
            "id": "output",
            "type": "output", 
            "data": { "label": "Agent Output" },
            "position": { "x": 500, "y": 100 }
        })
        
        # Send visualization update
        await manager.broadcast_to_agent(self.agent_id, {
            "type": "agent-flow-update",
            "agent_id": self.agent_id,
            "nodes": nodes,
            "connections": connections,
            "status": "building"
        })
4. Real-time Agent Execution
python
# workflows/agent_execution_websocket.py
class AgentExecutionWebSocketWorkflow:
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
    
    async def execute_agent_with_websocket(self, input_data: dict):
        """Execute agent with real-time progress updates"""
        try:
            # Start execution
            await manager.broadcast_to_agent(self.agent_id, {
                "type": "agent-execution-start",
                "agent_id": self.agent_id,
                "trigger": "user",
                "input": input_data,
                "timestamp": self._get_timestamp()
            })
            
            # Update node statuses in visualization
            await self._update_node_status("input", "running")
            
            # Process through each integration/node
            integrations = await self._get_agent_integrations(self.agent_id)
            
            for integration in integrations:
                await self._execute_integration_node(integration, input_data)
            
            # Complete execution
            await manager.broadcast_to_agent(self.agent_id, {
                "type": "agent-execution-complete", 
                "agent_id": self.agent_id,
                "result": {"status": "success"},
                "duration": 0,  # Calculate actual duration
                "timestamp": self._get_timestamp()
            })
            
        except Exception as e:
            await manager.broadcast_to_agent(self.agent_id, {
                "type": "agent-execution-error",
                "agent_id": self.agent_id,
                "error": str(e),
                "timestamp": self._get_timestamp()
            })
    
    async def _execute_integration_node(self, integration: str, input_data: dict):
        """Execute a single integration node with real-time updates"""
        node_id = f"integration_{integration}"
        
        # Update node status
        await self._update_node_status(node_id, "running")
        
        # Send terminal output
        await manager.broadcast_to_agent(self.agent_id, {
            "type": "terminal-output",
            "agent_id": self.agent_id,
            "output": f"Executing {integration}...\n",
            "type": "stdout"
        })
        
        try:
            # Simulate processing (replace with actual integration execution)
            await asyncio.sleep(1)
            
            # Update progress
            await manager.broadcast_to_agent(self.agent_id, {
                "type": "agent-execution-progress",
                "agent_id": self.agent_id,
                "currentNode": integration,
                "progress": 50  # Calculate actual progress
            })
            
            # Complete node execution
            await self._update_node_status(node_id, "success")
            
            await manager.broadcast_to_agent(self.agent_id, {
                "type": "terminal-output", 
                "agent_id": self.agent_id,
                "output": f"✓ {integration} completed successfully\n",
                "type": "stdout"
            })
            
        except Exception as e:
            await self._update_node_status(node_id, "error")
            
            await manager.broadcast_to_agent(self.agent_id, {
                "type": "terminal-output",
                "agent_id": self.agent_id, 
                "output": f"✗ {integration} failed: {str(e)}\n",
                "type": "stderr"
            })
            raise
    
    async def _update_node_status(self, node_id: str, status: str):
        """Update specific node status in visualization"""
        await manager.broadcast_to_agent(self.agent_id, {
            "type": "agent-node-status",
            "agent_id": self.agent_id,
            "nodeId": node_id,
            "status": status
        })
5. Real-time Terminal/Logs
python
# websockets/terminal_manager.py
import asyncio
import subprocess
from typing import Optional

class TerminalManager:
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.process: Optional[subprocess.Popen] = None
    
    async def execute_command(self, command: str):
        """Execute terminal command with real-time output"""
        try:
            # Notify command execution start
            await manager.broadcast_to_agent(self.agent_id, {
                "type": "terminal-output",
                "agent_id": self.agent_id,
                "output": f"$ {command}\n",
                "type": "stdout"
            })
            
            # Start process
            self.process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Stream stdout
            asyncio.create_task(self._stream_output(self.process.stdout, "stdout"))
            # Stream stderr  
            asyncio.create_task(self._stream_output(self.process.stderr, "stderr"))
            
            # Wait for completion
            return_code = await asyncio.get_event_loop().run_in_executor(
                None, self.process.wait
            )
            
            await manager.broadcast_to_agent(self.agent_id, {
                "type": "terminal-output",
                "agent_id": self.agent_id,
                "output": f"\nProcess completed with exit code: {return_code}\n",
                "type": "stdout"
            })
            
        except Exception as e:
            await manager.broadcast_to_agent(self.agent_id, {
                "type": "terminal-output",
                "agent_id": self.agent_id,
                "output": f"Error executing command: {str(e)}\n",
                "type": "stderr"
            })
    
    async def _stream_output(self, stream, stream_type: str):
        """Stream process output in real-time"""
        while True:
            line = stream.readline()
            if not line:
                break
            
            await manager.broadcast_to_agent(self.agent_id, {
                "type": "terminal-output",
                "agent_id": self.agent_id,
                "output": line,
                "type": stream_type
            })
            
            # Small delay to prevent flooding
            await asyncio.sleep(0.01)
🎯 Frontend WebSocket Integration
React Hook for WebSockets
typescript
// hooks/useWebSocket.ts
import { useEffect, useRef, useState, useCallback } from 'react';

interface WebSocketMessage {
  type: string;
  agentId: string;
  [key: string]: any;
}

export const useWebSocket = (agentId: string) => {
  const [isConnected, setIsConnected] = useState(false);
  const [messages, setMessages] = useState<WebSocketMessage[]>([]);
  const ws = useRef<WebSocket | null>(null);

  const connect = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/agent/${agentId}`;
    
    ws.current = new WebSocket(wsUrl);
    
    ws.current.onopen = () => {
      setIsConnected(true);
      console.log('WebSocket connected');
    };
    
    ws.current.onmessage = (event) => {
      const message: WebSocketMessage = JSON.parse(event.data);
      setMessages(prev => [...prev, message]);
      
      // Handle specific message types
      handleIncomingMessage(message);
    };
    
    ws.current.onclose = () => {
      setIsConnected(false);
      console.log('WebSocket disconnected');
    };
    
    ws.current.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }, [agentId]);

  const sendMessage = useCallback((message: Omit<WebSocketMessage, 'agentId'>) => {
    if (ws.current && isConnected) {
      ws.current.send(JSON.stringify({
        ...message,
        agentId
      }));
    }
  }, [agentId, isConnected]);

  const handleIncomingMessage = (message: WebSocketMessage) => {
    switch (message.type) {
      case 'ai-generation-code-chunk':
        // Update code editor in real-time
        updateCodeEditor(message.file, message.code);
        break;
      
      case 'agent-flow-update':
        // Update visualization
        updateFlowDiagram(message.nodes, message.connections);
        break;
      
      case 'terminal-output':
        // Append to terminal
        appendTerminalOutput(message.output, message.type);
        break;
      
      case 'agent-node-status':
        // Update node status in visualization
        updateNodeStatus(message.nodeId, message.status);
        break;
      
      default:
        console.log('Unhandled message type:', message.type);
    }
  };

  useEffect(() => {
    connect();
    
    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [connect]);

  return {
    isConnected,
    messages,
    sendMessage
  };
};
Real-time Agent Builder Component
typescript
// components/AgentBuilder.tsx
import { useWebSocket } from '../hooks/useWebSocket';

export const AgentBuilder: React.FC<{ agentId: string }> = ({ agentId }) => {
  const { isConnected, sendMessage } = useWebSocket(agentId);
  
  const handleGenerateAgent = (prompt: string) => {
    sendMessage({
      type: 'ai-generation-request',
      prompt: prompt
    });
  };
  
  const handleExecuteAgent = () => {
    sendMessage({
      type: 'agent-execution-start',
      input: {} // Add actual input data
    });
  };
  
  const handleDeployAgent = () => {
    sendMessage({
      type: 'deployment-request',
      platform: 'ecs'
    });
  };
  
  return (
    <div className="flex h-screen">
      {/* Left Strip Menu */}
      <LeftStripMenu />
      
      {/* Main Content */}
      <div className="flex-1 flex">
        {/* Chat Panel */}
        <ChatPanel 
          onGenerateAgent={handleGenerateAgent}
          isConnected={isConnected}
        />
        
        {/* Code Editor with real-time updates */}
        <CodeEditorWithWebSocket agentId={agentId} />
        
        {/* Agent Visualizer with real-time flow */}
        <AgentVisualizerWithWebSocket agentId={agentId} />
      </div>
    </div>
  );
};
🔄 Complete Real-time Workflow
User Journey with WebSockets:
text
1. User types prompt in chat
   → WS: 'ai-generation-request'
   
2. Backend starts AI generation
   → WS: 'ai-generation-start'
   → WS: 'ai-generation-progress' (multiple)
   → WS: 'ai-generation-code-chunk' (real-time code)
   → WS: 'agent-flow-update' (visual nodes)
   → WS: 'ai-generation-complete'

3. User views real-time code & flow
   → Code editor updates live
   → Flow diagram builds progressively

4. User executes agent
   → WS: 'agent-execution-start'
   → WS: 'agent-node-status' (node by node)
   → WS: 'terminal-output' (real-time logs)
   → WS: 'agent-execution-complete'

5. User deploys agent
   → WS: 'deployment-start'
   → WS: 'deployment-logs' (build logs)
   → WS: 'deployment-status'
WebSocket Scaling with Redis Pub/Sub
python
# For horizontal scaling across multiple backend instances
# websockets/redis_pubsub.py
import redis.asyncio as redis
import json

class RedisPubSubManager:
    def __init__(self):
        self.redis = redis.Redis.from_url(os.getenv('REDIS_URL'))
        self.pubsub = self.redis.pubsub()
    
    async def subscribe(self, agent_id: str):
        await self.pubsub.subscribe(f"agent:{agent_id}")
    
    async def publish(self, agent_id: str, message: dict):
        await self.redis.publish(f"agent:{agent_id}", json.dumps(message))
    
    async def listen(self):
        async for message in self.pubsub.listen():
            if message['type'] == 'message':
                data = json.loads(message['data'])
                await manager.broadcast_to_agent(data['agent_id'], data)
This WebSocket architecture ensures:

Real-time AI Generation: Live code streaming as it's generated

Interactive Visualizations: Dynamic flow diagrams that build progressively

Live Terminal: Real-time command execution and logs

Smooth UX: Instant feedback for all operations

Scalable: Redis Pub/Sub for multiple backend instances

Reliable: Connection management with reconnection logic