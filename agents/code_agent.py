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
        requirement = input_data.get("requirement")
        impact_analysis = input_data.get("impact_analysis")
        repo_summary = input_data.get("repo_summary")

        existing_files_message = "" if not impact_analysis else \
            f"Use these impacted files from the brownfield impact analysis: {impact_analysis.impacted_files}.\n" \
            f"If an existing file is modified, provide a `patch` field containing a unified diff.\n"

        repo_summary_text = ""
        if repo_summary:
            repo_summary_text = f"Repository summary:\n- Total files: {len(repo_summary.files)}\n- Python files: {len(repo_summary.python_files)}\n- API candidates: {repo_summary.api_candidates}\n- Likely impacted modules: {repo_summary.impacted_modules}\n\n"

        prompt = f"""Generate the code for this architecture:

**Requirement Summary:** {requirement.summary if requirement else 'N/A'}

**Overview:** {architecture.overview}

**Repository Context:**
{repo_summary_text}

**Components:**
{self._format_components(architecture.components)}

**API Contracts:**
{self._format_apis(architecture.api_contracts)}

**Data Models:**
{self._format_models(architecture.data_models)}

**Tech Stack:** {architecture.tech_stack}

{existing_files_message}
Generate complete, production-ready code files. Include:
1. Main application entry point
2. API route handlers
3. Data models / schemas
4. Business logic / services
5. Database / persistence layer
6. Configuration

For brownfield changes, follow these rules:
- For existing files to modify, include `patch` with a unified diff.
- For new files, include `content` and set `change_type` to `create`.
- For modified files, set `change_type` to `modify`.
- Include full file content for any files generated or modified.

Respond in JSON format with artifacts that may include patch metadata."""

        response = self.call_llm(prompt, expect_json=True)
        parsed = self.parse_json(response)

        artifacts = []
        for a in parsed.get("artifacts", []):
            filename = a.get("filename", "unknown.py")
            change_type = a.get("change_type")
            if not change_type and repo_summary:
                if filename in repo_summary.files:
                    change_type = "modify"
                else:
                    change_type = "create"

            artifacts.append(CodeArtifact(
                filename=filename,
                language=a.get("language", "python"),
                content=a.get("content", ""),
                description=a.get("description", ""),
                patch=a.get("patch"),
                change_type=change_type
            ))

        return artifacts
    
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
