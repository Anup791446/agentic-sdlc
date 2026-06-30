# agents/validator_agent.py
from agents.base_agent import BaseAgent
from models.schemas import ValidationResult, EngineeringSummary

SYSTEM_PROMPT = """You are a senior tech lead responsible for code review and risk assessment.

Your job is to:
1. Review the generated architecture and code for issues
2. Identify security vulnerabilities, performance concerns, and design flaws
3. Highlight trade-offs made in the design
4. Assess risks and provide mitigation recommendations
5. Determine if the output is production-ready

Respond in JSON format:
{
    "is_valid": true or false,
    "issues": ["List of problems found"],
    "risks": ["List of risks"],
    "trade_offs": ["List of trade-offs"],
    "recommendations": ["Suggestions for improvement"]
}"""

class ValidatorAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Validator",
            system_prompt=SYSTEM_PROMPT
        )
    
    def execute(self, input_data: dict) -> ValidationResult:
        architecture = input_data.get("architecture")
        code_artifacts = input_data.get("code_artifacts", [])
        test_artifacts = input_data.get("test_artifacts", [])
        
        prompt = f"""Review this engineering output:

**Architecture:**
{architecture.overview}

**Components:** {len(architecture.components)} components defined
**APIs:** {len(architecture.api_contracts)} endpoints defined
**Tech Stack:** {architecture.tech_stack}

**Code Artifacts:** {len(code_artifacts)} files generated
**Test Artifacts:** {len(test_artifacts)} test files generated

**Sample Code (first file):**
