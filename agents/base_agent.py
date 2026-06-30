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
            console.print(f"[red]✗ {self.name} failed: {e}[/red]")
            raise
    
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
