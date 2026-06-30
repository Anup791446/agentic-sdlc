# agents/test_agent.py
from agents.base_agent import BaseAgent
from models.schemas import CodeArtifact, TestArtifact

SYSTEM_PROMPT = """You are a senior QA engineer who writes comprehensive tests.

Your job is to:
1. Generate unit tests for individual functions/methods
2. Generate integration tests for API endpoints
3. Cover happy paths, edge cases, and error scenarios
4. Use pytest as the testing framework
5. Include mocks/fixtures where appropriate

Respond in JSON format:
{
    "artifacts": [
        {
            "filename": "tests/test_something.py",
            "test_type": "unit" or "integration",
            "content": "Full test file content",
            "description": "What these tests cover"
        }
    ]
}"""

class TestAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Test Generator",
            system_prompt=SYSTEM_PROMPT
        )
    
    def execute(self, input_data: dict) -> list[TestArtifact]:
        code_artifacts: list[CodeArtifact] = input_data.get("code_artifacts", [])
        architecture = input_data.get("architecture")
        
        code_summary = "\n\n".join(
            f"**{a.filename}**:\n```{a.language}\n{a.content[:1500]}...\n```"
            for a in code_artifacts[:5]  # Limit to avoid token overflow
        )
        
        prompt = f"""Generate comprehensive tests for this codebase:

**Architecture Overview:** {architecture.overview}

**API Endpoints:**
{self._format_apis(architecture.api_contracts)}

**Code Files (truncated):**
{code_summary}

Generate:
1. Unit tests for core business logic
2. Integration tests for API endpoints
3. Test fixtures and mocks
4. Edge case coverage"""

        response = self.call_llm(prompt, expect_json=True)
        parsed = self.parse_json(response)
        
        return [
            TestArtifact(
                filename=a.get("filename", "tests/test_unknown.py"),
                test_type=a.get("test_type", "unit"),
                content=a.get("content", ""),
                description=a.get("description", "")
            )
            for a in parsed.get("artifacts", [])
        ]
    
    def _format_apis(self, apis: list) -> str:
        return "\n".join(
            f"- {a.get('method')} {a.get('endpoint')}"
            for a in apis
        )
