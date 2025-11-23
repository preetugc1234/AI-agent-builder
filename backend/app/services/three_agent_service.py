"""
3-Agent AI Service using NVIDIA Nemotron via OpenRouter
Agent 1: Architect - Designs system and file structure
Agent 2: Coder - Writes the actual code
Agent 3: Reviewer - Checks and fixes bugs
"""

import httpx
import json
import logging
from typing import Dict, Any, List, AsyncGenerator
from app.core.config import settings

logger = logging.getLogger(__name__)


class ThreeAgentService:
    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = "nvidia/nemotron-nano-12b-v2-vl:free"

    async def generate_agent(
        self,
        prompt: str,
        on_progress: callable = None
    ) -> Dict[str, Any]:
        """
        Run the full 3-agent pipeline
        Returns architecture, code, review, and final code
        """
        result = {
            "architecture": "",
            "generated_code": "",
            "review_notes": "",
            "final_code": "",
            "file_structure": [],
            "integrations": []
        }

        try:
            # Agent 1: Architect
            if on_progress:
                await on_progress("agent1_start", "Starting Architect Agent...")

            architecture = await self._run_architect_agent(prompt)
            result["architecture"] = architecture
            result["file_structure"] = self._extract_file_structure(architecture)
            result["integrations"] = self._extract_integrations(architecture)

            if on_progress:
                await on_progress("agent1_complete", "Architect completed!")

            # Agent 2: Coder
            if on_progress:
                await on_progress("agent2_start", "Starting Coder Agent...")

            generated_code = await self._run_coder_agent(prompt, architecture)
            result["generated_code"] = generated_code

            if on_progress:
                await on_progress("agent2_complete", "Coder completed!")

            # Agent 3: Reviewer
            if on_progress:
                await on_progress("agent3_start", "Starting Reviewer Agent...")

            review_result = await self._run_reviewer_agent(prompt, architecture, generated_code)
            result["review_notes"] = review_result["review"]
            result["final_code"] = review_result["final_code"]

            if on_progress:
                await on_progress("agent3_complete", "Reviewer completed!")

            return result

        except Exception as e:
            logger.error(f"3-Agent generation failed: {e}")
            raise

    async def _run_architect_agent(self, user_prompt: str) -> str:
        """
        Agent 1: Architect
        Designs system architecture, file structure, and workflow
        """
        system_prompt = """You are an expert Software Architect AI Agent.

Your task is to analyze the user's requirements and create a comprehensive technical design.

You MUST provide:
1. **System Overview**: Brief description of what the agent will do
2. **Architecture Design**: Technical architecture with components
3. **File Structure**: Complete list of files needed (as JSON array)
4. **Data Flow**: How data moves through the system
5. **Integrations**: List of external services/APIs needed
6. **Technical Decisions**: Key technical choices and why

Format your response clearly with headers and bullet points.
For file structure, use this exact format:
```json
["main.py", "requirements.txt", "config.py", "utils/helper.py"]
```

Be thorough but concise. This design will be used by a Coder Agent to implement."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Design an AI agent for this request:\n\n{user_prompt}"}
        ]

        return await self._call_nemotron(messages)

    async def _run_coder_agent(self, user_prompt: str, architecture: str) -> str:
        """
        Agent 2: Coder
        Writes the actual implementation code
        """
        system_prompt = """You are an expert Python Developer AI Agent.

Your task is to implement the complete code based on the architecture design provided.

You MUST:
1. Write COMPLETE, WORKING code - no placeholders or TODOs
2. Include ALL necessary imports
3. Add proper error handling
4. Include docstrings and comments
5. Follow best practices and clean code principles
6. Create ALL files mentioned in the architecture

Format each file like this:
```python
# filename: main.py
<complete code here>
```

```python
# filename: requirements.txt
<dependencies here>
```

Make sure the code is production-ready and fully functional."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"""Original Request:
{user_prompt}

Architecture Design:
{architecture}

Now write the complete implementation code for all files."""}
        ]

        return await self._call_nemotron(messages)

    async def _run_reviewer_agent(self, user_prompt: str, architecture: str, code: str) -> Dict[str, str]:
        """
        Agent 3: Reviewer
        Reviews code, finds bugs, fixes them, and provides summary
        """
        system_prompt = """You are an expert Code Reviewer AI Agent.

Your task is to review the code, find any bugs or issues, fix them, and provide the final version.

You MUST:
1. **Review**: Check for bugs, errors, security issues, and improvements
2. **Fix**: Correct ALL issues you find
3. **Summary**: Provide a brief summary of what was built and any fixes made

Format your response EXACTLY like this:

## REVIEW NOTES
<list all issues found and fixes applied>

## SUMMARY
<brief summary of what was built, key features, and how to use it>

## FINAL CODE
<the complete, fixed code with all files>

Use the same file format as before:
```python
# filename: main.py
<fixed code>
```

The final code must be bug-free and production-ready."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"""Original Request:
{user_prompt}

Architecture:
{architecture}

Generated Code:
{code}

Please review this code, fix any issues, and provide the final version."""}
        ]

        response = await self._call_nemotron(messages)

        # Parse the response
        review = ""
        final_code = ""

        if "## REVIEW NOTES" in response:
            parts = response.split("## FINAL CODE")
            review = parts[0].replace("## REVIEW NOTES", "").strip()
            if len(parts) > 1:
                final_code = parts[1].strip()
            else:
                final_code = code  # Use original if no final code section
        else:
            review = "Review completed"
            final_code = response

        return {
            "review": review,
            "final_code": final_code
        }

    async def _call_nemotron(self, messages: List[Dict[str, str]]) -> str:
        """
        Call NVIDIA Nemotron via OpenRouter with reasoning enabled
        """
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://noderush.vercel.app",
                    "X-Title": "NodeRush AI Agent Builder"
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "extra_body": {
                        "reasoning": {"enabled": True}
                    }
                }
            )

            if response.status_code != 200:
                error_text = response.text
                logger.error(f"OpenRouter API error: {response.status_code} - {error_text}")
                raise Exception(f"AI API error: {response.status_code}")

            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def stream_generation(
        self,
        prompt: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream the 3-agent generation process
        Yields progress updates for real-time UI
        """
        # Agent 1: Architect
        yield {"type": "agent_start", "agent": 1, "name": "Architect", "message": "Analyzing requirements and designing architecture..."}

        architecture = await self._run_architect_agent(prompt)
        file_structure = self._extract_file_structure(architecture)
        integrations = self._extract_integrations(architecture)

        yield {
            "type": "agent_complete",
            "agent": 1,
            "name": "Architect",
            "output": architecture,
            "file_structure": file_structure,
            "integrations": integrations
        }

        # Agent 2: Coder
        yield {"type": "agent_start", "agent": 2, "name": "Coder", "message": "Writing implementation code..."}

        generated_code = await self._run_coder_agent(prompt, architecture)

        yield {
            "type": "agent_complete",
            "agent": 2,
            "name": "Coder",
            "output": generated_code
        }

        # Agent 3: Reviewer
        yield {"type": "agent_start", "agent": 3, "name": "Reviewer", "message": "Reviewing code and fixing issues..."}

        review_result = await self._run_reviewer_agent(prompt, architecture, generated_code)

        yield {
            "type": "agent_complete",
            "agent": 3,
            "name": "Reviewer",
            "review": review_result["review"],
            "final_code": review_result["final_code"]
        }

        # Final result
        yield {
            "type": "generation_complete",
            "message": "Agent generation complete!",
            "summary": f"Created {len(file_structure)} files with {len(integrations)} integrations"
        }

    def _extract_file_structure(self, architecture: str) -> List[str]:
        """Extract file structure from architecture text"""
        files = []

        # Try to find JSON array
        try:
            import re
            json_match = re.search(r'\[[\s\S]*?\]', architecture)
            if json_match:
                potential_json = json_match.group()
                parsed = json.loads(potential_json)
                if isinstance(parsed, list):
                    files = [f for f in parsed if isinstance(f, str)]
        except:
            pass

        # Fallback: look for common file patterns
        if not files:
            import re
            file_patterns = re.findall(r'[\w/]+\.(py|txt|json|yaml|yml|md|js|ts)', architecture)
            files = list(set(file_patterns))

        return files or ["main.py", "requirements.txt"]

    def _extract_integrations(self, architecture: str) -> List[str]:
        """Extract integrations/services from architecture text"""
        integrations = []

        # Common integrations to look for
        known_integrations = [
            "gmail", "slack", "github", "vercel", "docker",
            "postgresql", "redis", "mongodb", "supabase",
            "openai", "langchain", "twilio", "stripe", "razorpay",
            "aws", "cloudflare", "notion", "airtable", "google_sheets"
        ]

        arch_lower = architecture.lower()
        for integration in known_integrations:
            if integration in arch_lower:
                integrations.append(integration)

        return integrations


# Create singleton instance
three_agent_service = ThreeAgentService()
