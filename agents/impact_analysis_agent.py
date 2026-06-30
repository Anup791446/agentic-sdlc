from agents.base_agent import BaseAgent
from models.schemas import Requirement, RepoSummary, ImpactAnalysisResult
import json

SYSTEM_PROMPT = """You are an impact analyst for brownfield software changes.

Your job is to:
1. Take the normalized requirement and the existing repository summary.
2. Identify the exact files and modules that are likely affected.
3. Define a safe change strategy that minimizes disruption to existing code.
4. Call out compatibility risks, integration risks, and migration steps.
5. Recommend concrete actions for modifying the current codebase.

Respond in JSON format exactly as shown:
{
    "impacted_files": ["relative/path/to/file1.py", "relative/path/to/file2.py"],
    "change_strategy": "Describe the approach to update the repo safely.",
    "compatibility_risks": ["Risk 1", "Risk 2"],
    "recommended_actions": ["Action 1", "Action 2"]
}
"""

class ImpactAnalysisAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="Impact Analyst", system_prompt=SYSTEM_PROMPT)

    def execute(self, input_data: dict) -> ImpactAnalysisResult:
        requirement: Requirement = input_data.get("requirement")
        repo_summary: RepoSummary = input_data.get("repo_summary")

        prompt = f"""Perform impact analysis for this brownfield requirement.

Requirement summary:
{requirement.summary}

Functional requirements:
{chr(10).join(f'- {fr}' for fr in requirement.functional_requirements)}

Non-functional requirements:
{chr(10).join(f'- {nfr}' for nfr in requirement.non_functional_requirements)}

Repository summary:
{json.dumps(repo_summary.dict(), indent=2)}

Use the detailed Python file analysis to identify the exact files and symbols that must change.
For each impacted file, describe whether it should be modified or if a new file is preferred.

Identify impacted files and modules, and recommend a concrete change strategy."""

        response = self.call_llm(prompt, expect_json=True)
        parsed = self.parse_json(response)

        return ImpactAnalysisResult(
            impacted_files=parsed.get("impacted_files", []),
            change_strategy=parsed.get("change_strategy", ""),
            compatibility_risks=parsed.get("compatibility_risks", []),
            recommended_actions=parsed.get("recommended_actions", [])
        )
