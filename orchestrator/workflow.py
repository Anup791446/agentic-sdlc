# orchestrator/workflow.py
import json
import os
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from config import Config
from models.schemas import (
    Task, TaskStatus, TaskType, 
    EngineeringSummary, Requirement, ArchitectureDesign, ValidationResult
)
from orchestrator.task_graph import TaskGraph
from agents.requirement_agent import RequirementAgent
from agents.architect_agent import ArchitectAgent
from agents.code_agent import CodeAgent
from agents.test_agent import TestAgent
from agents.validator_agent import ValidatorAgent

console = Console()

class WorkflowOrchestrator:
    """Orchestrates the end-to-end engineering workflow."""
    
    def __init__(self):
        self.task_graph = TaskGraph()
        self.context = {}  # Shared context between agents
        
        # Initialize agents
        self.agents = {
            TaskType.REQUIREMENT_ANALYSIS: RequirementAgent(),
            TaskType.ARCHITECTURE_DESIGN: ArchitectAgent(),
            TaskType.CODE_GENERATION: CodeAgent(),
            TaskType.TEST_GENERATION: TestAgent(),
            TaskType.VALIDATION: ValidatorAgent(),
        }
    
    def create_workflow(self, requirement: str):
        """Create the task graph for processing a requirement."""
        console.print(Panel(
            f"[bold]Processing Requirement[/bold]\n\n{requirement}",
            title="🚀 Agentic SDLC System",
            border_style="blue"
        ))
        
        # Store raw requirement
        self.context["raw_requirement"] = requirement
        
        # Define tasks with dependencies
        tasks = [
            Task(
                id="T1",
                name="Analyze Requirements",
                task_type=TaskType.REQUIREMENT_ANALYSIS,
                description="Parse and normalize the requirement",
                dependencies=[]
            ),
            Task(
                id="T2",
                name="Design Architecture",
                task_type=TaskType.ARCHITECTURE_DESIGN,
                description="Create system architecture based on requirements",
                dependencies=["T1"]
            ),
            Task(
                id="T3",
                name="Generate Code",
                task_type=TaskType.CODE_GENERATION,
                description="Generate production code based on architecture",
                dependencies=["T2"]
            ),
            Task(
                id="T4",
                name="Generate Tests",
                task_type=TaskType.TEST_GENERATION,
                description="Generate test cases for the code",
                dependencies=["T3"]
            ),
            Task(
                id="T5",
                name="Validate Output",
                task_type=TaskType.VALIDATION,
                description="Validate all outputs and identify risks",
                dependencies=["T3", "T4"]
            ),
        ]
        
        for task in tasks:
            self.task_graph.add_task(task)
        
        console.print("\n[bold]📋 Workflow Created[/bold]")
        self.task_graph.display()
    
    def execute_task(self, task: Task):
        """Execute a single task using the appropriate agent."""
        task.status = TaskStatus.IN_PROGRESS
        console.print(f"\n[bold yellow]▶ Executing:[/bold yellow] {task.name}")
        
        try:
            agent = self.agents.get(task.task_type)
            if not agent:
                raise ValueError(f"No agent for task type: {task.task_type}")
            
            # Prepare input based on task type
            input_data = self._prepare_input(task)
            
            # Execute agent
            result = agent.execute(input_data)
            
            # Store result in context
            self._store_result(task, result)
            
            self.task_graph.mark_completed(task.id, str(result))
            
        except Exception as e:
            console.print(f"[red]Error in {task.name}: {e}[/red]")
            if "OpenAI insufficient quota" in str(e) or "insufficient_quota" in str(e):
                self.task_graph.mark_failed(task.id, str(e))
                return
            task.retries += 1
            
            if task.retries < Config.MAX_RETRIES:
                console.print(f"[yellow]Retrying... ({task.retries}/{Config.MAX_RETRIES})[/yellow]")
                task.status = TaskStatus.PENDING
            else:
                self.task_graph.mark_failed(task.id, str(e))
    
    def _prepare_input(self, task: Task) -> dict:
        """Prepare input data for a task based on its type."""
        if task.task_type == TaskType.REQUIREMENT_ANALYSIS:
            return {"requirement": self.context["raw_requirement"]}
        
        elif task.task_type == TaskType.ARCHITECTURE_DESIGN:
            return {"requirement": self.context.get("requirement")}
        
        elif task.task_type == TaskType.CODE_GENERATION:
            return {"architecture": self.context.get("architecture")}
        
        elif task.task_type == TaskType.TEST_GENERATION:
            return {
                "architecture": self.context.get("architecture"),
                "code_artifacts": self.context.get("code_artifacts", [])
            }
        
        elif task.task_type == TaskType.VALIDATION:
            return {
                "architecture": self.context.get("architecture"),
                "code_artifacts": self.context.get("code_artifacts", []),
                "test_artifacts": self.context.get("test_artifacts", [])
            }
        
        return {}
    
    def _store_result(self, task: Task, result):
        """Store task result in the shared context."""
        if task.task_type == TaskType.REQUIREMENT_ANALYSIS:
            self.context["requirement"] = result
        elif task.task_type == TaskType.ARCHITECTURE_DESIGN:
            self.context["architecture"] = result
        elif task.task_type == TaskType.CODE_GENERATION:
            self.context["code_artifacts"] = result
        elif task.task_type == TaskType.TEST_GENERATION:
            self.context["test_artifacts"] = result
        elif task.task_type == TaskType.VALIDATION:
            self.context["validation"] = result
    
    def run(self) -> EngineeringSummary:
        """Execute the complete workflow."""
        console.print("\n[bold green]🏃 Starting Workflow Execution[/bold green]\n")
        
        iteration = 0
        max_iterations = 20  # Safety limit
        
        while not self.task_graph.is_complete() and iteration < max_iterations:
            ready_tasks = self.task_graph.get_ready_tasks()
            
            if not ready_tasks:
                console.print("[yellow]No tasks ready. Waiting...[/yellow]")
                break
            
            for task in ready_tasks:
                self.execute_task(task)
            
            iteration += 1
            console.print(f"\n[dim]--- Iteration {iteration} complete ---[/dim]")
            self.task_graph.display()
        
        # Build final summary
        return self._build_summary()
    
    def _build_summary(self) -> EngineeringSummary:
        """Build the final engineering summary."""
        requirement = self.context.get("requirement")
        architecture = self.context.get("architecture")
        validation = self.context.get("validation")

        if requirement is None:
            requirement = Requirement(
                raw_input=self.context.get("raw_requirement", ""),
                summary="",
                functional_requirements=[],
                non_functional_requirements=[],
                ambiguities=[],
                assumptions=[],
                scenario_type="greenfield"
            )

        if architecture is None:
            architecture = ArchitectureDesign(
                overview="No architecture available.",
                components=[],
                api_contracts=[],
                data_models=[],
                tech_stack={},
                diagrams=None
            )

        if validation is None:
            validation = ValidationResult(
                is_valid=False,
                issues=["Workflow did not complete successfully."],
                risks=[],
                trade_offs=[],
                recommendations=["Resolve workflow failures and rerun or enable mock mode."]
            )
        
        summary = EngineeringSummary(
            requirement=requirement,
            architecture=architecture,
            code_artifacts=self.context.get("code_artifacts", []),
            test_artifacts=self.context.get("test_artifacts", []),
            validation=validation,
            implementation_plan=self._generate_implementation_plan(),
            assumptions_and_limitations=requirement.assumptions if requirement else []
        )
        
        return summary
    
    def _generate_implementation_plan(self) -> str:
        """Generate a human-readable implementation plan."""
        arch = self.context.get("architecture")
        if not arch:
            return "No architecture available."
        
        plan = f"""## Implementation Plan

### Overview
{arch.overview}

### Components to Build
"""
        for comp in arch.components:
            plan += f"- **{comp.get('name')}**: {comp.get('responsibility')}\n"
        
        plan += "\n### API Endpoints\n"
        for api in arch.api_contracts:
            plan += f"- `{api.get('method')} {api.get('endpoint')}`: {api.get('description')}\n"
        
        plan += f"\n### Technology Stack\n"
        for key, value in arch.tech_stack.items():
            plan += f"- **{key.title()}**: {value}\n"
        
        return plan
    
    def save_outputs(self, summary: EngineeringSummary, output_dir: str = None):
        """Save all generated artifacts to disk."""
        output_dir = output_dir or Config.OUTPUT_DIR
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = os.path.join(output_dir, f"run_{timestamp}")
        os.makedirs(run_dir, exist_ok=True)
        
        # Save code artifacts
        code_dir = os.path.join(run_dir, "src")
        os.makedirs(code_dir, exist_ok=True)
        for artifact in summary.code_artifacts:
            filepath = os.path.join(code_dir, artifact.filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, "w") as f:
                f.write(artifact.content)
        
        # Save test artifacts
        test_dir = os.path.join(run_dir, "tests")
        os.makedirs(test_dir, exist_ok=True)
        for artifact in summary.test_artifacts:
            filename = os.path.basename(artifact.filename)
            filepath = os.path.join(test_dir, filename)
            with open(filepath, "w") as f:
                f.write(artifact.content)
        
        # Save architecture diagram
        if summary.architecture.diagrams:
            with open(os.path.join(run_dir, "architecture.md"), "w") as f:
                f.write(f"# Architecture\n\n```mermaid\n{summary.architecture.diagrams}\n```")
        
        # Save summary report
        report = self._generate_report(summary)
        with open(os.path.join(run_dir, "REPORT.md"), "w") as f:
            f.write(report)
        
        console.print(f"\n[bold green]✅ Outputs saved to: {run_dir}[/bold green]")
        return run_dir
    
    def _generate_report(self, summary: EngineeringSummary) -> str:
        """Generate the final markdown report."""
        validation = summary.validation
        
        report = f"""# Engineering Summary Report

Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Requirement

**Original Input:**
> {summary.requirement.raw_input}

**Summary:** {summary.requirement.summary}

### Functional Requirements
"""
        for fr in summary.requirement.functional_requirements:
            report += f"- {fr}\n"
        
        report += "\n### Non-Functional Requirements\n"
        for nfr in summary.requirement.non_functional_requirements:
            report += f"- {nfr}\n"
        
        report += f"""
## Architecture

{summary.architecture.overview}

### Components
"""
        for comp in summary.architecture.components:
            report += f"- **{comp.get('name')}**: {comp.get('responsibility')}\n"
        
        report += f"""
### Tech Stack
"""
        for key, value in summary.architecture.tech_stack.items():
            report += f"- {key}: {value}\n"
        
        if summary.architecture.diagrams:
            report += f"""
### Architecture Diagram

```mermaid
{summary.architecture.diagrams}
```
"""
        
        report += f"""
## Generated Artifacts
### Code Files ({len(summary.code_artifacts)} files)
"""
        for artifact in summary.code_artifacts:
            report += f"- `{artifact.filename}`: {artifact.description}\n"
        
        report += f"\n### Test Files ({len(summary.test_artifacts)} files)\n"
        for artifact in summary.test_artifacts:
            report += f"- `{artifact.filename}` ({artifact.test_type}): {artifact.description}\n"
        
        report += f"""
## Validation
**Status:** {"✅ Valid" if summary.validation.is_valid else "⚠️ Issues Found"}
### Issues
"""
        for issue in summary.validation.issues:
            report += f"- {issue}\n"
        
        report += "\n### Risks\n"
        for risk in summary.validation.risks:
            report += f"- {risk}\n"
        
        report += "\n### Trade-offs\n"
        for tradeoff in summary.validation.trade_offs:
            report += f"- {tradeoff}\n"
        
        report += "\n### Recommendations\n"
        for rec in summary.validation.recommendations:
            report += f"- {rec}\n"
        
        report += "\n## Assumptions & Limitations\n"
        for assumption in summary.assumptions_and_limitations:
            report += f"- {assumption}\n"
        
        return report            