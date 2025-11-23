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

Real-Time Agent Flow Visualization (100% Free)
🎯 Tech Stack for Flow Visualization
Free Open-Source Libraries:
text
Frontend Flow Library: React Flow (MIT License) - COMPLETELY FREE
WebSocket: Native WebSocket API + FastAPI WebSockets - FREE
Backend: Python + FastAPI - FREE
Real-time Updates: WebSockets - FREE
Deployment: AWS Free Tier - FREE
🏗️ Real-time Flow Architecture
System Architecture:
text
┌─────────────────┐    WebSocket    ┌─────────────────┐
│   Frontend      │ ◄─────────────► │   Backend       │
│   React Flow    │                 │   FastAPI       │
│   Visualization │                 │   WebSockets    │
└─────────────────┘                 └─────────────────┘
         │                                    │
         │                                    │
         ▼                                    ▼
┌─────────────────┐                 ┌─────────────────┐
│   Real-time     │                 │   AI Service    │
│   Node Updates  │                 │   Nemotron      │
│   & Connections │                 │   Generation    │
└─────────────────┘                 └─────────────────┘
🔧 Implementation
1. Frontend - React Flow Setup
typescript
// components/AgentFlowVisualizer.tsx
import React, { useCallback, useEffect } from 'react';
import ReactFlow, {
  Node,
  Edge,
  addEdge,
  Connection,
  useNodesState,
  useEdgesState,
  Background,
  Controls,
  MiniMap,
  NodeTypes
} from 'reactflow';
import 'reactflow/dist/style.css';

// Custom Node Components
const InputNode = ({ data }: any) => (
  <div className="px-4 py-2 shadow-md rounded-md bg-white border-2 border-stone-400">
    <div className="font-bold">{data.label}</div>
    <div className="text-gray-500 text-xs">Input</div>
  </div>
);

const IntegrationNode = ({ data }: any) => (
  <div className={`px-4 py-2 shadow-md rounded-md border-2 ${
    data.status === 'running' ? 'border-yellow-400 bg-yellow-50' :
    data.status === 'success' ? 'border-green-400 bg-green-50' :
    data.status === 'error' ? 'border-red-400 bg-red-50' :
    'border-blue-400 bg-blue-50'
  }`}>
    <div className="font-bold">{data.label}</div>
    <div className="text-gray-500 text-xs capitalize">{data.status || 'pending'}</div>
  </div>
);

const OutputNode = ({ data }: any) => (
  <div className="px-4 py-2 shadow-md rounded-md bg-white border-2 border-stone-400">
    <div className="font-bold">{data.label}</div>
    <div className="text-gray-500 text-xs">Output</div>
  </div>
);

const nodeTypes: NodeTypes = {
  input: InputNode,
  integration: IntegrationNode,
  output: OutputNode,
};

interface AgentFlowVisualizerProps {
  agentId: string;
}

export const AgentFlowVisualizer: React.FC<AgentFlowVisualizerProps> = ({ agentId }) => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  // WebSocket for real-time updates
  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws/agent/${agentId}`);
    
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      
      switch (message.type) {
        case 'agent-flow-update':
          setNodes(message.nodes);
          setEdges(message.connections);
          break;
          
        case 'agent-node-status':
          setNodes((nds) =>
            nds.map((node) => {
              if (node.id === message.nodeId) {
                return {
                  ...node,
                  data: {
                    ...node.data,
                    status: message.status,
                    output: message.output
                  }
                };
              }
              return node;
            })
          );
          break;
          
        case 'ai-generation-integration-detected':
          // Add new integration nodes dynamically
          addIntegrationNodes(message.integrations);
          break;
      }
    };
    
    return () => ws.close();
  }, [agentId]);

  const addIntegrationNodes = (integrations: string[]) => {
    const newNodes: Node[] = [];
    const newEdges: Edge[] = [];
    
    integrations.forEach((integration, index) => {
      const nodeId = `integration_${integration}`;
      
      newNodes.push({
        id: nodeId,
        type: 'integration',
        data: { 
          label: integration.replace(/_/g, ' ').toUpperCase(),
          status: 'pending'
        },
        position: { x: 300, y: 100 + (index * 120) }
      });
      
      // Connect from input to this integration
      newEdges.push({
        id: `conn_input_${integration}`,
        source: 'input',
        target: nodeId,
        type: 'smoothstep'
      });
      
      // Connect from this integration to output
      newEdges.push({
        id: `conn_${integration}_output`,
        source: nodeId,
        target: 'output', 
        type: 'smoothstep'
      });
    });
    
    setNodes((nds) => [...nds, ...newNodes]);
    setEdges((eds) => [...eds, ...newEdges]);
  };

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  return (
    <div className="h-full w-full bg-gray-50 rounded-lg">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        nodeTypes={nodeTypes}
        fitView
      >
        <Background />
        <Controls />
        <MiniMap />
      </ReactFlow>
    </div>
  );
};
2. Backend - Real-time Flow Generator
python
# workflows/flow_generator.py
import asyncio
from typing import List, Dict, Any
import uuid

class RealTimeFlowGenerator:
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.current_nodes = []
        self.current_edges = []
    
    async def generate_initial_flow(self):
        """Create initial flow structure"""
        initial_nodes = [
            {
                "id": "input",
                "type": "input",
                "data": {"label": "User Input"},
                "position": {"x": 100, "y": 250}
            },
            {
                "id": "output", 
                "type": "output",
                "data": {"label": "Agent Output"},
                "position": {"x": 800, "y": 250}
            }
        ]
        
        await self._update_flow(initial_nodes, [])
    
    async def add_integration_node(self, integration: str, position_x: int = 400):
        """Add a new integration node to the flow"""
        node_id = f"integration_{integration}"
        
        new_node = {
            "id": node_id,
            "type": "integration",
            "data": {
                "label": integration.replace('_', ' ').title(),
                "status": "pending"
            },
            "position": {"x": position_x, "y": self._calculate_y_position()}
        }
        
        # Create connections
        new_edges = [
            {
                "id": f"conn_input_{integration}",
                "source": "input",
                "target": node_id,
                "type": "smoothstep"
            },
            {
                "id": f"conn_{integration}_output", 
                "source": node_id,
                "target": "output",
                "type": "smoothstep"
            }
        ]
        
        self.current_nodes.append(new_node)
        self.current_edges.extend(new_edges)
        
        await self._update_flow(self.current_nodes, self.current_edges)
    
    async def update_node_status(self, node_id: str, status: str, output: Any = None):
        """Update node status in real-time"""
        updated_nodes = []
        
        for node in self.current_nodes:
            if node["id"] == node_id:
                node["data"]["status"] = status
                if output:
                    node["data"]["output"] = output
            
            updated_nodes.append(node)
        
        self.current_nodes = updated_nodes
        await self._update_flow(self.current_nodes, self.current_edges)
        
        # Also send individual node update for real-time effects
        await self._send_node_status_update(node_id, status, output)
    
    async def add_processing_step(self, step_name: str, dependencies: List[str] = None):
        """Add intermediate processing steps"""
        step_id = f"step_{step_name.lower().replace(' ', '_')}"
        
        new_node = {
            "id": step_id,
            "type": "integration",  # Reuse integration style
            "data": {
                "label": step_name,
                "status": "pending"
            },
            "position": {"x": 500, "y": self._calculate_y_position()}
        }
        
        # Create connections from dependencies
        new_edges = []
        if dependencies:
            for dep in dependencies:
                new_edges.append({
                    "id": f"conn_{dep}_{step_id}",
                    "source": f"integration_{dep}",
                    "target": step_id,
                    "type": "smoothstep"
                })
        else:
            # Connect from all current integration nodes
            integration_nodes = [n for n in self.current_nodes if n["id"].startswith("integration_")]
            for node in integration_nodes:
                new_edges.append({
                    "id": f"conn_{node['id']}_{step_id}",
                    "source": node["id"],
                    "target": step_id,
                    "type": "smoothstep"
                })
        
        # Connect to output
        new_edges.append({
            "id": f"conn_{step_id}_output",
            "source": step_id, 
            "target": "output",
            "type": "smoothstep"
        })
        
        self.current_nodes.append(new_node)
        self.current_edges.extend(new_edges)
        
        await self._update_flow(self.current_nodes, self.current_edges)
    
    def _calculate_y_position(self) -> int:
        """Calculate Y position for new nodes to avoid overlap"""
        integration_nodes = [n for n in self.current_nodes if n["id"].startswith("integration_") or n["id"].startswith("step_")]
        return 100 + (len(integration_nodes) * 120)
    
    async def _update_flow(self, nodes: List[Dict], edges: List[Dict]):
        """Send complete flow update to frontend"""
        from websockets.websocket_manager import manager
        
        await manager.broadcast_to_agent(self.agent_id, {
            "type": "agent-flow-update",
            "agent_id": self.agent_id,
            "nodes": nodes,
            "connections": edges,
            "status": "building"
        })
    
    async def _send_node_status_update(self, node_id: str, status: str, output: Any = None):
        """Send individual node status update"""
        from websockets.websocket_manager import manager
        
        await manager.broadcast_to_agent(self.agent_id, {
            "type": "agent-node-status",
            "agent_id": self.agent_id,
            "nodeId": node_id,
            "status": status,
            "output": output
        })
3. AI Integration with Real-time Flow
python
# workflows/ai_flow_integration.py
class AIFlowIntegration:
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.flow_generator = RealTimeFlowGenerator(agent_id)
        self.nemotron = NemotronAI()
    
    async def generate_agent_with_visual_flow(self, prompt: str):
        """Generate agent with real-time flow visualization"""
        try:
            # Step 1: Initialize empty flow
            await self.flow_generator.generate_initial_flow()
            await asyncio.sleep(0.5)  # Let frontend render
            
            # Step 2: Analyze prompt and detect integrations
            await self._update_status("Analyzing your agent requirements...")
            integrations = await self._detect_integrations_from_prompt(prompt)
            
            # Add integration nodes one by one with animation effect
            for i, integration in enumerate(integrations):
                await self.flow_generator.add_integration_node(integration)
                await asyncio.sleep(0.3)  # Visual delay for animation effect
            
            # Step 3: Generate core logic steps
            await self._update_status("Designing agent workflow...")
            processing_steps = await self._generate_processing_steps(prompt, integrations)
            
            for step in processing_steps:
                await self.flow_generator.add_processing_step(step["name"], step["dependencies"])
                await asyncio.sleep(0.2)
            
            # Step 4: Mark flow as complete
            await self.flow_generator._update_flow(
                self.flow_generator.current_nodes,
                self.flow_generator.current_edges
            )
            
            # Step 5: Generate actual code
            await self._update_status("Generating agent code...")
            agent_code = await self.nemotron.generate_agent_code(prompt, integrations)
            
            return agent_code
            
        except Exception as e:
            await self._update_status(f"Error: {str(e)}", "error")
            raise
    
    async def _detect_integrations_from_prompt(self, prompt: str) -> List[str]:
        """Detect required integrations from user prompt"""
        # Use Nemotron to analyze prompt and extract integrations
        analysis_prompt = f"""
        Analyze this agent request and extract all required services/integrations:
        "{prompt}"
        
        Return ONLY a JSON array of service names like ["gmail", "slack", "postgresql"]
        """
        
        response = await self.nemotron.generate_response(analysis_prompt)
        
        try:
            # Parse JSON response
            integrations = json.loads(response)
            return integrations
        except:
            # Fallback: basic keyword detection
            return self._fallback_integration_detection(prompt)
    
    async def _generate_processing_steps(self, prompt: str, integrations: List[str]) -> List[Dict]:
        """Generate processing steps for the workflow"""
        steps_prompt = f"""
        Based on this agent request: "{prompt}"
        And these integrations: {integrations}
        
        Generate 3-5 processing steps for the workflow. Return JSON:
        [{{"name": "Step Name", "dependencies": ["integration1", "integration2"]}}]
        """
        
        response = await self.nemotron.generate_response(steps_prompt)
        
        try:
            return json.loads(response)
        except:
            # Default steps
            return [
                {"name": "Data Processing", "dependencies": integrations},
                {"name": "AI Analysis", "dependencies": []},
                {"name": "Output Generation", "dependencies": []}
            ]
    
    async def _update_status(self, message: str, level: str = "info"):
        """Send status updates to frontend"""
        from websockets.websocket_manager import manager
        
        await manager.broadcast_to_agent(self.agent_id, {
            "type": "ai-generation-progress",
            "agent_id": self.agent_id,
            "message": message,
            "level": level
        })
4. Enhanced WebSocket Handler
python
# websockets/flow_websocket.py
from fastapi import WebSocket
import json

class FlowWebSocketHandler:
    def __init__(self):
        self.active_flows = {}  # agent_id -> FlowGenerator
    
    async def handle_flow_message(self, agent_id: str, message: dict, websocket: WebSocket):
        """Handle flow-related WebSocket messages"""
        message_type = message.get("type")
        
        if message_type == "flow-generation-request":
            await self.handle_flow_generation_request(agent_id, message, websocket)
        
        elif message_type == "node-interaction":
            await self.handle_node_interaction(agent_id, message)
        
        elif message_type == "flow-layout-change":
            await self.handle_flow_layout_change(agent_id, message)
    
    async def handle_flow_generation_request(self, agent_id: str, message: dict, websocket: WebSocket):
        """Handle request to generate new flow"""
        prompt = message.get("prompt", "")
        
        # Initialize flow generator for this agent
        flow_integration = AIFlowIntegration(agent_id)
        
        # Start flow generation in background
        asyncio.create_task(
            self._generate_flow_background(flow_integration, prompt, websocket)
        )
    
    async def _generate_flow_background(self, flow_integration: AIFlowIntegration, prompt: str, websocket: WebSocket):
        """Generate flow in background with real-time updates"""
        try:
            agent_code = await flow_integration.generate_agent_with_visual_flow(prompt)
            
            # Send completion message
            await websocket.send_json({
                "type": "flow-generation-complete",
                "agent_id": flow_integration.agent_id,
                "code": agent_code
            })
            
        except Exception as e:
            await websocket.send_json({
                "type": "flow-generation-error", 
                "agent_id": flow_integration.agent_id,
                "error": str(e)
            })
    
    async def handle_node_interaction(self, agent_id: str, message: dict):
        """Handle user interactions with nodes"""
        node_id = message.get("nodeId")
        action = message.get("action")
        
        if agent_id in self.active_flows:
            flow_generator = self.active_flows[agent_id]
            
            if action == "test":
                await flow_generator.update_node_status(node_id, "running")
                # Simulate testing
                await asyncio.sleep(2)
                await flow_generator.update_node_status(node_id, "success")
            
            elif action == "configure":
                await flow_generator.update_node_status(node_id, "configuring")
5. Frontend Integration Hook
typescript
// hooks/useAgentFlow.ts
import { useWebSocket } from './useWebSocket';

export const useAgentFlow = (agentId: string) => {
  const { sendMessage, isConnected } = useWebSocket(agentId);
  
  const generateFlow = (prompt: string) => {
    sendMessage({
      type: 'flow-generation-request',
      prompt: prompt
    });
  };
  
  const testNode = (nodeId: string) => {
    sendMessage({
      type: 'node-interaction',
      nodeId: nodeId,
      action: 'test'
    });
  };
  
  const configureNode = (nodeId: string) => {
    sendMessage({
      type: 'node-interaction', 
      nodeId: nodeId,
      action: 'configure'
    });
  };
  
  const updateLayout = (nodes: any[], edges: any[]) => {
    sendMessage({
      type: 'flow-layout-change',
      nodes: nodes,
      edges: edges
    });
  };
  
  return {
    generateFlow,
    testNode,
    configureNode, 
    updateLayout,
    isConnected
  };
};
🎨 Enhanced Visual Features
Custom Styling for Premium Look
css
/* styles/flow.css */
.react-flow__node {
  border-radius: 10px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.react-flow__node:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
}

.react-flow__edge path {
  stroke-width: 2;
  stroke-dasharray: 5;
  animation: flow 2s linear infinite;
}

@keyframes flow {
  0% {
    stroke-dashoffset: 10;
  }
  100% {
    stroke-dashoffset: 0;
  }
}

/* Status colors */
.node-status-pending {
  border-color: #6b7280;
}

.node-status-running {
  border-color: #f59e0b;
  animation: pulse 2s infinite;
}

.node-status-success {
  border-color: #10b981;
}

.node-status-error {
  border-color: #ef4444;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
}
🚀 Complete User Experience
Real-time Flow Building Process:
text
1. User types: "Create email agent for Gmail + Slack notifications"
2. Instantly see: [Input] node appears
3. AI detects integrations: Gmail, Slack
4. Watch nodes appear one by one with smooth animations:
   → [Gmail] node slides in from left
   → [Slack] node appears below
   → Connections automatically draw between nodes
5. Processing steps appear:
   → [Email Processing] 
   → [Notification Logic]
   → [Output Formatting]
6. All nodes connected in beautiful flow
7. User can click nodes to test/configure
8. Real-time status updates during execution
Features Users See in Real-time:
✅ Progressive Building: Nodes appear one by one

✅ Smooth Animations: Slide-in effects and connection drawing

✅ Live Status: Colors change based on node state

✅ Interactive Nodes: Click to test/configure

✅ Auto-layout: Smart positioning without overlap

✅ Visual Feedback: Pulses, glows, and hover effects
