from agents.base_agent import BaseAgent

SYSTEM_PROMPT = """You are a documentation specialist.

Your job is to:
1. Review recommended implementation steps from requirements analysis.
2. Summarize the steps into a concise checklist.
3. Highlight any missing concerns or additional validation tasks.

Respond in JSON format:
{
    "review": "A brief summary of the recommended steps.",
    "recommended_steps": ["Step 1", "Step 2", ...]
}
"""

class DocumentationAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="Documentation Specialist", system_prompt=SYSTEM_PROMPT)

    def execute(self, input_data: dict) -> dict:
        requirement = input_data.get("requirement")
        recommended_steps = input_data.get("recommended_steps", [])

        prompt = f"""Review the following recommended implementation steps derived from the requirements analysis:\n\n"""
        if recommended_steps:
            prompt += "\n".join(f"- {step}" for step in recommended_steps)
        else:
            prompt += "No recommended steps provided."

        prompt += f"\n\nProvide a short checklist and note any missing concerns or extra validation needed."

        response = self.call_llm(prompt, expect_json=True)
        parsed = self.parse_json(response)

        return {
            "review": parsed.get("review", ""),
            "recommended_steps": parsed.get("recommended_steps", [])
        }
