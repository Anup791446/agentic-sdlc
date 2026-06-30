# agents/requirement_agent.py
from agents.base_agent import BaseAgent
from models.schemas import Requirement

SYSTEM_PROMPT = """You are a senior software engineer specializing in requirements analysis.

Your job is to:
1. Understand the user's requirement, even if vague or ambiguous
2. Extract functional and non-functional requirements
3. Identify ambiguities and make reasonable assumptions
4. Determine if this is a greenfield (new) or brownfield (existing system) scenario

Always respond in JSON format with this structure:
{
    "summary": "One-paragraph summary of the requirement",
    "functional_requirements": ["FR1", "FR2", ...],
    "non_functional_requirements": ["NFR1", "NFR2", ...],
    "ambiguities": ["Questions that need clarification"],
    "assumptions": ["Assumptions made to proceed"],
    "scenario_type": "greenfield" or "brownfield",
    "recommended_steps": ["Short implementation steps or workflow milestones"]
}"""

class RequirementAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Requirement Analyst",
            system_prompt=SYSTEM_PROMPT
        )
    
    def execute(self, input_data: dict) -> Requirement:
        raw_requirement = input_data.get("requirement", "")
        
        prompt = f"""Analyze this software requirement:

---
{raw_requirement}
---

Extract structured requirements, identify gaps, and make assumptions where needed."""

        response = self.call_llm(prompt, expect_json=True)
        parsed = self.parse_json(response)
        
        return Requirement(
            raw_input=raw_requirement,
            summary=parsed.get("summary", ""),
            functional_requirements=parsed.get("functional_requirements", []),
            non_functional_requirements=parsed.get("non_functional_requirements", []),
            ambiguities=parsed.get("ambiguities", []),
            assumptions=parsed.get("assumptions", []),
            scenario_type=parsed.get("scenario_type", "greenfield"),
            recommended_steps=parsed.get("recommended_steps", [])
        )
