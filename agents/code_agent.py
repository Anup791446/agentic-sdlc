# agents/code_agent.py
from agents.base_agent import BaseAgent
from models.schemas import ArchitectureDesign, CodeArtifact

SYSTEM_PROMPT = """You are a senior software engineer who writes clean, production-quality code.

Your job is to:
1. Generate complete, runnable code files based on the architecture
2. Follow best practices: type hints, error handling, logging, documentation
3. Ensure code is modular and maintainable
4. Include necessary imports and dependencies

Respond in JSON format:
{
    "artifacts": [
        {
            "filename": "path/to/file.py",
            "language": "python",
            "content": "Full file content as a string",
            "description": "What this file does"
        }
    ]
}

IMPORTANT: The "content" field must contain the COMPLETE file content, not snippets."""

class CodeAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Code Generator",
            system_prompt=SYSTEM_PROMPT
        )
    
    def execute(self, input_data: dict) -> list[CodeArtifact]:
        architecture: ArchitectureDesign = input_data.get("architecture")
        
        prompt = f"""Generate the code for this architecture:

**Overview:** {architecture.overview}

**Components:**
{self._format_components(architecture.components)}

**API Contracts:**
{self._format_apis(architecture.api_contracts)}

**Data Models:**
{self._format_models(architecture.data_models)}

**Tech Stack:** {architecture.tech_stack}

Generate complete, production-ready code files. Include:
1. Main application entry point
2. API route handlers
3. Data models / schemas
4. Business logic / services
5. Database / persistence layer
6. Configuration"""

        response = self.call_llm(prompt, expect_json=True)
        parsed = self.parse_json(response)
        
        return [
            CodeArtifact(
                filename=a.get("filename", "unknown.py"),
                language=a.get("language", "python"),
                content=a.get("content", ""),
                description=a.get("description", "")
            )
            for a in parsed.get("artifacts", [])
        ]
    
    def _format_components(self, components: list) -> str:
        return "\n".join(
            f"- **{c.get('name')}**: {c.get('responsibility')} (Tech: {c.get('tech')})"
            for c in components
        )
    
    def _format_apis(self, apis: list) -> str:
        return "\n".join(
            f"- {a.get('method')} {a.get('endpoint')}: {a.get('description')}"
            for a in apis
        )
    
    def _format_models(self, models: list) -> str:
        return "\n".join(
            f"- {m.get('name')}: {m.get('fields')}"
            for m in models
        )
