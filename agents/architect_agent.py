# agents/architect_agent.py
from agents.base_agent import BaseAgent
from models.schemas import Requirement, ArchitectureDesign

SYSTEM_PROMPT = """You are a senior software architect with expertise in distributed systems.

Your job is to:
1. Design a clean, scalable architecture based on the requirements
2. Define components, their responsibilities, and interactions
3. Specify API contracts and data models
4. Choose an appropriate tech stack
5. Create a Mermaid diagram showing the architecture

Respond in JSON format:
{
    "overview": "Architecture overview paragraph",
    "components": [
        {"name": "Component Name", "responsibility": "What it does", "tech": "Technology used"}
    ],
    "api_contracts": [
        {"endpoint": "/api/path", "method": "POST", "description": "What it does", "request_body": {}, "response": {}}
    ],
    "data_models": [
        {"name": "ModelName", "fields": {"field1": "type", "field2": "type"}}
    ],
    "tech_stack": {
        "language": "Python",
        "framework": "FastAPI",
        "database": "PostgreSQL",
        "cache": "Redis",
        "other": []
    },
    "diagrams": "Mermaid diagram code as a string"
}"""

class ArchitectAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Software Architect",
            system_prompt=SYSTEM_PROMPT
        )
    
    def execute(self, input_data: dict) -> ArchitectureDesign:
        requirement: Requirement = input_data.get("requirement")
        
        prompt = f"""Design the architecture for this system:

**Summary:** {requirement.summary}

**Functional Requirements:**
{chr(10).join(f'- {fr}' for fr in requirement.functional_requirements)}

**Non-Functional Requirements:**
{chr(10).join(f'- {nfr}' for nfr in requirement.non_functional_requirements)}

**Assumptions:**
{chr(10).join(f'- {a}' for a in requirement.assumptions)}

Design a production-ready architecture with clear component separation."""

        response = self.call_llm(prompt, expect_json=True)
        parsed = self.parse_json(response)
        
        return ArchitectureDesign(
            overview=parsed.get("overview", ""),
            components=parsed.get("components", []),
            api_contracts=parsed.get("api_contracts", []),
            data_models=parsed.get("data_models", []),
            tech_stack=parsed.get("tech_stack", {}),
            diagrams=parsed.get("diagrams")
        )
