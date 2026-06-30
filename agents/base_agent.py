# agents/base_agent.py
from abc import ABC, abstractmethod
from openai import OpenAI
from config import Config
import json
from rich.console import Console

console = Console()

class BaseAgent(ABC):
    """Base class for all agents."""
    
    def __init__(self, name: str, system_prompt: str):
        self.name = name
        self.system_prompt = system_prompt
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
    
    def call_llm(self, user_prompt: str, expect_json: bool = False) -> str:
        """Call the LLM with the given prompt."""
        console.print(f"[bold blue]🤖 {self.name}[/bold blue] is working...")

        if Config.is_mock_mode():
            console.print(f"[yellow]⚠️ {self.name} running in mock mode[/yellow]")
            return self._mock_response(user_prompt, expect_json)
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response_format = {"type": "json_object"} if expect_json else None
        
        try:
            response = self.client.chat.completions.create(
                model=Config.MODEL_NAME,
                messages=messages,
                response_format=response_format,
                temperature=0.2  # Lower = more deterministic
            )
            result = response.choices[0].message.content
            console.print(f"[green]✓ {self.name} completed[/green]")
            return result
        except Exception as e:
            msg = str(e)
            if "insufficient_quota" in msg or "quota" in msg.lower():
                console.print("[red]✗ OpenAI quota error: please check your billing, plan, or API key.[/red]")
                raise RuntimeError("OpenAI insufficient quota") from e
            console.print(f"[red]✗ {self.name} failed: {e}[/red]")
            raise

    def _mock_response(self, user_prompt: str, expect_json: bool = False) -> str:
        if self.name == "Requirement Analyst":
            return json.dumps({
                "summary": "Build a scalable URL shortening service with analytics.",
                "functional_requirements": [
                    "Accept long URLs and return shortened URLs",
                    "Redirect short URLs to original URLs",
                    "Track click analytics"
                ],
                "non_functional_requirements": [
                    "Handle high traffic with low latency",
                    "Ensure reliability and monitoring"
                ],
                "ambiguities": ["Exact retention policy for analytics data"],
                "assumptions": ["Use a modern web framework and managed database"],
                "scenario_type": "greenfield"
            }, indent=2)
        if self.name == "Software Architect":
            return json.dumps({
                "overview": "A scalable URL shortener using microservices for API, storage, and analytics.",
                "components": [
                    {"name": "API Service", "responsibility": "Handle URL creation and redirect requests", "tech": "FastAPI"},
                    {"name": "Analytics Service", "responsibility": "Collect and report click metrics", "tech": "Python"}
                ],
                "api_contracts": [
                    {"endpoint": "/shorten", "method": "POST", "description": "Create shortened URL", "request_body": {"url": "string"}, "response": {"short_url": "string"}},
                    {"endpoint": "/{code}", "method": "GET", "description": "Redirect to original URL", "request_body": {}, "response": {"redirect": "url"}}
                ],
                "data_models": [
                    {"name": "UrlRecord", "fields": {"code": "string", "target_url": "string", "created_at": "datetime"}}
                ],
                "tech_stack": {
                    "language": "Python",
                    "framework": "FastAPI",
                    "database": "PostgreSQL",
                    "cache": "Redis",
                    "other": ["Prometheus", "Docker"]
                },
                "diagrams": "graph TD; A[API Service] --> B[Database]; A --> C[Analytics Service];"
            }, indent=2)
        if self.name == "Code Generator":
            return json.dumps({
                "artifacts": [
                    {
                        "filename": "app.py",
                        "language": "python",
                        "content": "from fastapi import FastAPI\napp = FastAPI()\n\n@app.post('/shorten')\ndef shorten_url():\n    return {'short_url': 'https://short.ly/abc123'}\n\n@app.get('/{code}')\ndef redirect(code: str):\n    return {'redirect': 'https://example.com'}\n",
                        "description": "Main FastAPI application for URL shortening and redirects"
                    }
                ]
            }, indent=2)
        if self.name == "Test Generator":
            return json.dumps({
                "artifacts": [
                    {
                        "filename": "tests/test_api.py",
                        "test_type": "integration",
                        "content": "def test_shorten_url():\n    assert True\n",
                        "description": "Basic integration test for URL shortening API"
                    }
                ]
            }, indent=2)
        if self.name == "Validator":
            return json.dumps({
                "is_valid": True,
                "issues": [],
                "risks": ["Simplified mock implementation may miss real edge cases"],
                "trade_offs": ["Mock mode skips actual OpenAI evaluation"],
                "recommendations": ["Use a real OpenAI key for production validation"]
            }, indent=2)
        return json.dumps({"message": "Mock mode active"})

    def parse_json(self, response: str) -> dict:
        """Parse JSON from LLM response."""
        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            console.print(f"[yellow]Warning: JSON parse error, attempting repair[/yellow]")
            # Try to extract JSON from markdown code blocks
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                return json.loads(response[start:end].strip())
            raise e
    
    @abstractmethod
    def execute(self, input_data: dict) -> dict:
        """Execute the agent's task. Must be implemented by subclasses."""
        pass
