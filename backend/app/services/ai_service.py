"""
AI Service using NVIDIA Nemotron via OpenRouter
"""

import logging
from typing import List, Dict, Any
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)


class NemotronAIService:
    """NVIDIA Nemotron AI service for agent code generation"""

    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.base_url = settings.OPENROUTER_BASE_URL
        self.model = settings.AI_MODEL
        self.client = httpx.AsyncClient(timeout=120.0)

    async def generate_agent_code(
        self,
        vibe_prompt: str,
        integrations: List[str],
        user_id: str
    ) -> Dict[str, Any]:
        """
        Generate agent code from vibe prompt

        Args:
            vibe_prompt: User's natural language description
            integrations: List of required integrations
            user_id: User ID for personalization

        Returns:
            Dictionary containing generated code and metadata
        """
        try:
            system_prompt = self._build_system_prompt()
            user_message = self._build_user_message(vibe_prompt, integrations)

            response = await self._call_nemotron(system_prompt, user_message)

            # Parse and structure the response
            return self._parse_ai_response(response, integrations)

        except Exception as e:
            logger.error(f"Error generating agent code: {str(e)}")
            raise

    async def detect_integrations(self, vibe_prompt: str) -> List[str]:
        """
        Detect required integrations from vibe prompt

        Args:
            vibe_prompt: User's natural language description

        Returns:
            List of detected integration names
        """
        try:
            system_prompt = """You are an expert at analyzing requirements and identifying which services/integrations are needed.

Available integrations:
- gmail (email automation)
- slack (team communication)
- twilio (SMS/calls)
- supabase (database)
- google_sheets (spreadsheets)
- airtable (database)
- notion (knowledge base)
- openai (AI)
- langchain (AI orchestration)
- render (deployment)
- vercel (frontend deployment)
- docker (containers)
- github (code repository)
- razorpay (payments)
- stripe (payments)
- sentry (error tracking)

Analyze the user's request and return ONLY a JSON array of required integration names.
Example: ["gmail", "slack", "supabase"]"""

            user_message = f"What integrations are needed for this agent?\n\n{vibe_prompt}"

            response = await self._call_nemotron(system_prompt, user_message)

            # Extract integration list from response
            return self._parse_integrations_response(response)

        except Exception as e:
            logger.error(f"Error detecting integrations: {str(e)}")
            return []

    async def generate_flow_data(
        self,
        vibe_prompt: str,
        integrations: List[str]
    ) -> Dict[str, Any]:
        """
        Generate flow diagram data for visualization

        Args:
            vibe_prompt: User's description
            integrations: List of integrations

        Returns:
            Flow data with nodes and connections
        """
        nodes = []
        edges = []

        # Input node
        nodes.append({
            "id": "input",
            "type": "input",
            "data": {"label": "User Input"},
            "position": {"x": 100, "y": 200}
        })

        # Integration nodes
        y_offset = 100
        for i, integration in enumerate(integrations):
            node_id = f"integration_{integration}"
            nodes.append({
                "id": node_id,
                "type": "integration",
                "data": {
                    "label": integration.replace("_", " ").title(),
                    "integration": integration,
                    "status": "pending"
                },
                "position": {"x": 400, "y": y_offset + (i * 120)}
            })

            # Connection from input
            edges.append({
                "id": f"edge_input_{integration}",
                "source": "input",
                "target": node_id,
                "type": "smoothstep"
            })

        # Output node
        nodes.append({
            "id": "output",
            "type": "output",
            "data": {"label": "Agent Output"},
            "position": {"x": 700, "y": 200}
        })

        # Connect integrations to output
        for integration in integrations:
            node_id = f"integration_{integration}"
            edges.append({
                "id": f"edge_{integration}_output",
                "source": node_id,
                "target": "output",
                "type": "smoothstep"
            })

        return {"nodes": nodes, "edges": edges}

    def _build_system_prompt(self) -> str:
        """Build system prompt for code generation"""
        return """You are an expert AI agent developer specializing in creating production-ready Python agents.

Your task is to generate complete, working Python code based on the user's requirements.

Requirements:
1. Generate clean, well-documented Python code
2. Use async/await for I/O operations
3. Include proper error handling
4. Add type hints
5. Follow PEP 8 style guidelines
6. Include comments explaining complex logic
7. Make code modular and maintainable

Return ONLY valid Python code without markdown formatting or explanations."""

    def _build_user_message(self, vibe_prompt: str, integrations: List[str]) -> str:
        """Build user message with context"""
        integrations_str = ", ".join(integrations) if integrations else "none"

        return f"""Create a Python agent with the following requirements:

User Request: {vibe_prompt}

Required Integrations: {integrations_str}

Generate a complete Python script (main.py) that:
1. Implements the user's requirements
2. Uses the specified integrations
3. Has proper error handling and logging
4. Is production-ready

Return ONLY the Python code."""

    async def _call_nemotron(self, system_prompt: str, user_message: str) -> str:
        """
        Call NVIDIA Nemotron via OpenRouter

        Args:
            system_prompt: System instructions
            user_message: User's message

        Returns:
            AI response text
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://vibeagent-forge.com",
                "X-Title": "VibeAgent Forge"
            }

            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                "temperature": 0.7,
                "max_tokens": 4000
            }

            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            )

            response.raise_for_status()
            data = response.json()

            return data["choices"][0]["message"]["content"]

        except httpx.HTTPError as e:
            logger.error(f"HTTP error calling Nemotron: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error calling Nemotron: {str(e)}")
            raise

    def _parse_ai_response(self, response: str, integrations: List[str]) -> Dict[str, Any]:
        """
        Parse AI response into structured format

        Args:
            response: Raw AI response
            integrations: List of integrations

        Returns:
            Structured code data
        """
        # Extract code (remove markdown if present)
        code = response.strip()
        if code.startswith("```python"):
            code = code[9:]
        if code.startswith("```"):
            code = code[3:]
        if code.endswith("```"):
            code = code[:-3]

        code = code.strip()

        # Generate requirements.txt
        requirements = self._generate_requirements(integrations)

        # Generate Dockerfile
        dockerfile = self._generate_dockerfile()

        return {
            "main.py": code,
            "requirements.txt": requirements,
            "Dockerfile": dockerfile,
            "integrations": integrations
        }

    def _parse_integrations_response(self, response: str) -> List[str]:
        """Parse integrations from AI response"""
        import json
        try:
            # Try to parse as JSON array
            integrations = json.loads(response.strip())
            if isinstance(integrations, list):
                return integrations
        except:
            pass

        # Fallback: extract words that match known integrations
        known_integrations = [
            "gmail", "slack", "twilio", "supabase", "google_sheets",
            "airtable", "notion", "openai", "langchain", "render",
            "vercel", "docker", "github", "razorpay", "stripe",
            "sentry", "aws", "cloudflare"
        ]

        detected = []
        response_lower = response.lower()
        for integration in known_integrations:
            if integration in response_lower:
                detected.append(integration)

        return detected

    def _generate_requirements(self, integrations: List[str]) -> str:
        """Generate requirements.txt based on integrations"""
        base_requirements = [
            "asyncio",
            "aiohttp",
            "python-dotenv"
        ]

        integration_packages = {
            "gmail": ["google-api-python-client", "google-auth"],
            "slack": ["slack-sdk"],
            "twilio": ["twilio"],
            "supabase": ["supabase"],
            "google_sheets": ["gspread", "google-auth"],
            "airtable": ["pyairtable"],
            "notion": ["notion-client"],
            "openai": ["openai"],
            "langchain": ["langchain"],
            "docker": ["docker"],
            "aws": ["boto3"],
        }

        requirements = set(base_requirements)
        for integration in integrations:
            if integration in integration_packages:
                requirements.update(integration_packages[integration])

        return "\n".join(sorted(requirements))

    def _generate_dockerfile(self) -> str:
        """Generate Dockerfile for agent"""
        return """FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
"""

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
