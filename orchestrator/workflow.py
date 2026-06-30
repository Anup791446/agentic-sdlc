# orchestrator/workflow.py
import difflib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import py_compile
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from config import Config
from models.schemas import (
    Task, TaskStatus, TaskType,
    EngineeringSummary, Requirement, ArchitectureDesign,
    ValidationResult, RepoSummary, ImpactAnalysisResult
)
from orchestrator.task_graph import TaskGraph
from agents.requirement_agent import RequirementAgent
from agents.architect_agent import ArchitectAgent
from agents.code_agent import CodeAgent
from agents.test_agent import TestAgent
from agents.validator_agent import ValidatorAgent
from agents.repo_analysis_agent import RepoAnalysisAgent
from agents.impact_analysis_agent import ImpactAnalysisAgent
from agents.documentation_agent import DocumentationAgent

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
            TaskType.REPO_ANALYSIS: RepoAnalysisAgent(),
            TaskType.IMPACT_ANALYSIS: ImpactAnalysisAgent(),
            TaskType.DOCUMENTATION: DocumentationAgent(),
        }
    
    def create_workflow(self, requirement: str, repo_path: str | None = None):
        """Create the task graph for processing a requirement."""
        console.print(Panel(
            f"[bold]Processing Requirement[/bold]\n\n{requirement}",
            title="🚀 Agentic SDLC System",
            border_style="blue"
        ))
        
        # Store raw requirement and repo path
        self.context["raw_requirement"] = requirement
        self.context["repo_path"] = repo_path
        
        # Always run requirement analysis first
        self.task_graph.add_task(Task(
            id="T1",
            name="Analyze Requirements",
            task_type=TaskType.REQUIREMENT_ANALYSIS,
            description="Parse and normalize the requirement",
            dependencies=[]
        ))
        self.context["workflow_expanded"] = False
        
        console.print("\n[bold]📋 Initial workflow created. Requirements analysis will determine the full task graph.[/bold]")
        self.task_graph.display()
    
    def execute_task(self, task: Task):
        """Execute a single task using the appropriate agent or local validation step."""
        task.status = TaskStatus.IN_PROGRESS
        console.print(f"\n[bold yellow]▶ Executing:[/bold yellow] {task.name}")
        
        try:
            if task.task_type in {TaskType.COMPILATION_VALIDATION, TaskType.TEST_EXECUTION, TaskType.BROWNFIELD_CODE_MODIFICATION}:
                result = self._execute_local_validation(task)
            else:
                agent = self.agents.get(task.task_type)
                if not agent:
                    raise ValueError(f"No agent for task type: {task.task_type}")
                input_data = self._prepare_input(task)
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
        
        elif task.task_type == TaskType.REPO_ANALYSIS:
            return {"repo_path": self.context.get("repo_path")}

        elif task.task_type == TaskType.IMPACT_ANALYSIS:
            return {
                "requirement": self.context.get("requirement"),
                "repo_summary": self.context.get("repo_summary")
            }
        
        elif task.task_type == TaskType.ARCHITECTURE_DESIGN:
            return {
                "requirement": self.context.get("requirement"),
                "repo_summary": self.context.get("repo_summary"),
                "impact_analysis": self.context.get("impact_analysis")
            }
        
        elif task.task_type == TaskType.CODE_GENERATION:
            return {
                "architecture": self.context.get("architecture"),
                "requirement": self.context.get("requirement"),
                "repo_summary": self.context.get("repo_summary"),
                "impact_analysis": self.context.get("impact_analysis")
            }
        elif task.task_type == TaskType.DOCUMENTATION:
            return {
                "requirement": self.context.get("requirement"),
                "recommended_steps": self.context.get("requirement").recommended_steps if self.context.get("requirement") else []
            }
        elif task.task_type == TaskType.TEST_GENERATION:
            return {
                "architecture": self.context.get("architecture"),
                "code_artifacts": self.context.get("code_artifacts", [])
            }
        
        elif task.task_type == TaskType.COMPILATION_VALIDATION:
            return {"code_artifacts": self.context.get("code_artifacts", [])}
        
        elif task.task_type == TaskType.TEST_EXECUTION:
            return {
                "code_artifacts": self.context.get("code_artifacts", []),
                "test_artifacts": self.context.get("test_artifacts", [])
            }
        
        elif task.task_type == TaskType.BROWNFIELD_CODE_MODIFICATION:
            return {
                "repo_path": self.context.get("repo_path"),
                "code_artifacts": self.context.get("code_artifacts", []),
                "impact_analysis": self.context.get("impact_analysis")
            }
        elif task.task_type == TaskType.VALIDATION:
            return {
                "architecture": self.context.get("architecture"),
                "code_artifacts": self.context.get("code_artifacts", []),
                "test_artifacts": self.context.get("test_artifacts", []),
                "compilation_result": self.context.get("compilation_result"),
                "test_execution_result": self.context.get("test_execution_result"),
                "impact_analysis": self.context.get("impact_analysis"),
                "brownfield_patch_result": self.context.get("brownfield_patch_result")
            }
        
        return {}

    def _expand_workflow(self):
        """Expand the workflow dynamically based on requirement analysis results."""
        requirement = self.context.get("requirement")
        repo_path = self.context.get("repo_path")
        if not requirement or self.context.get("workflow_expanded"):
            return

        is_brownfield = bool(repo_path) or requirement.scenario_type == "brownfield"
        recommended = requirement.recommended_steps or []
        self.context["workflow_expanded"] = True

        if is_brownfield and repo_path:
            self.task_graph.add_task(Task(
                id="T2",
                name="Analyze Repository",
                task_type=TaskType.REPO_ANALYSIS,
                description="Summarize existing repository structure",
                dependencies=["T1"]
            ))
            self.task_graph.add_task(Task(
                id="T3",
                name="Impact Analysis",
                task_type=TaskType.IMPACT_ANALYSIS,
                description="Determine which existing modules and files are affected",
                dependencies=["T2"]
            ))
            self.task_graph.add_task(Task(
                id="T4",
                name="Design Architecture",
                task_type=TaskType.ARCHITECTURE_DESIGN,
                description="Create architecture considering existing codebase",
                dependencies=["T1", "T3"]
            ))
            self.task_graph.add_task(Task(
                id="T5",
                name="Generate Code",
                task_type=TaskType.CODE_GENERATION,
                description="Generate production code based on architecture",
                dependencies=["T4"]
            ))
            self.task_graph.add_task(Task(
                id="T6",
                name="Modify Existing Codebase",
                task_type=TaskType.BROWNFIELD_CODE_MODIFICATION,
                description="Apply or simulate patch updates to the existing repository",
                dependencies=["T5"]
            ))
            self.task_graph.add_task(Task(
                id="T7",
                name="Generate Tests",
                task_type=TaskType.TEST_GENERATION,
                description="Generate test cases for the code",
                dependencies=["T6"]
            ))
            self.task_graph.add_task(Task(
                id="T8",
                name="Compile Generated Code",
                task_type=TaskType.COMPILATION_VALIDATION,
                description="Compile generated Python code to detect syntax issues",
                dependencies=["T6"]
            ))
            self.task_graph.add_task(Task(
                id="T9",
                name="Execute Generated Tests",
                task_type=TaskType.TEST_EXECUTION,
                description="Run generated tests against the generated code",
                dependencies=["T7", "T8"]
            ))
            self.task_graph.add_task(Task(
                id="T10",
                name="Validate Output",
                task_type=TaskType.VALIDATION,
                description="Validate all outputs and identify risks",
                dependencies=["T8", "T9"]
            ))
        else:
            self.task_graph.add_task(Task(
                id="T2",
                name="Design Architecture",
                task_type=TaskType.ARCHITECTURE_DESIGN,
                description="Create system architecture based on requirements",
                dependencies=["T1"]
            ))
            self.task_graph.add_task(Task(
                id="T3",
                name="Generate Code",
                task_type=TaskType.CODE_GENERATION,
                description="Generate production code based on architecture",
                dependencies=["T2"]
            ))
            self.task_graph.add_task(Task(
                id="T4",
                name="Generate Tests",
                task_type=TaskType.TEST_GENERATION,
                description="Generate test cases for the code",
                dependencies=["T3"]
            ))
            self.task_graph.add_task(Task(
                id="T5",
                name="Compile Generated Code",
                task_type=TaskType.COMPILATION_VALIDATION,
                description="Compile generated Python code to detect syntax issues",
                dependencies=["T3"]
            ))
            self.task_graph.add_task(Task(
                id="T6",
                name="Execute Generated Tests",
                task_type=TaskType.TEST_EXECUTION,
                description="Run generated tests against the generated code",
                dependencies=["T4", "T5"]
            ))
            self.task_graph.add_task(Task(
                id="T7",
                name="Validate Output",
                task_type=TaskType.VALIDATION,
                description="Validate all outputs and identify risks",
                dependencies=["T5", "T6"]
            ))

        if recommended:
            self._add_documentation_task()
            self._add_recommended_step_tasks(recommended)

        console.print("\n[bold]📦 Workflow expanded dynamically based on requirement analysis[/bold]")
        self.task_graph.display()

    def _add_recommended_step_tasks(self, recommended_steps: list[str]):
        """Add dynamic tasks based on recommendation text from requirements analysis."""
        is_brownfield = bool(self.context.get("repo_path")) or self.context.get("requirement").scenario_type == "brownfield"
        previous_task_id = None

        for idx, step in enumerate(recommended_steps, start=1):
            task_id = f"RS{idx}"
            if task_id in self.task_graph.tasks:
                previous_task_id = task_id
                continue

            task_type = self._infer_task_type_for_recommended_step(step, is_brownfield)
            anchor_task_id = self._get_recommended_step_anchor(step, is_brownfield)
            dependencies = [anchor_task_id] if anchor_task_id else ["T1"]

            if previous_task_id and previous_task_id not in dependencies:
                dependencies.append(previous_task_id)

            name = f"Recommended Step {idx}"
            description = step
            if task_type == TaskType.DOCUMENTATION:
                name = f"Review recommended step {idx}"
                description = f"Review and align this recommended step with the existing workflow: {step}"

            self.task_graph.add_task(Task(
                id=task_id,
                name=name,
                task_type=task_type,
                description=description,
                dependencies=dependencies,
                metadata={
                    "anchor_task": anchor_task_id,
                    "original_step": step
                }
            ))
            previous_task_id = task_id

    def _add_documentation_task(self):
        """Add a workflow-level documentation/review task if any recommended steps exist."""
        if "T_DOC" in self.task_graph.tasks:
            return

        self.task_graph.add_task(Task(
            id="T_DOC",
            name="Review Recommended Steps",
            task_type=TaskType.DOCUMENTATION,
            description="Review and validate the implementation plan derived from recommended requirement steps.",
            dependencies=["T1"]
        ))

    def _get_recommended_step_anchor(self, step: str, is_brownfield: bool) -> str | None:
        text = step.lower()

        if any(keyword in text for keyword in ["repo", "repository", "existing code", "impact", "brownfield"]):
            return "T2" if is_brownfield and "T2" in self.task_graph.tasks else "T1"
        if "architecture" in text or "design" in text:
            return "T4" if is_brownfield and "T4" in self.task_graph.tasks else "T2" if "T2" in self.task_graph.tasks else "T1"
        if any(keyword in text for keyword in ["generate code", "code generation", "implement", "build code", "api", "endpoint"]):
            return "T5" if is_brownfield and "T5" in self.task_graph.tasks else "T3" if "T3" in self.task_graph.tasks else "T1"
        if any(keyword in text for keyword in ["modify", "patch", "update existing", "brownfield"]):
            return "T6" if is_brownfield and "T6" in self.task_graph.tasks else "T3" if "T3" in self.task_graph.tasks else "T1"
        if any(keyword in text for keyword in ["test", "unit", "integration", "e2e", "coverage"]):
            return "T7" if is_brownfield and "T7" in self.task_graph.tasks else "T4" if "T4" in self.task_graph.tasks else "T3" if "T3" in self.task_graph.tasks else "T1"
        if any(keyword in text for keyword in ["compile", "validate", "review", "risk", "quality"]):
            return "T10" if is_brownfield and "T10" in self.task_graph.tasks else "T7" if "T7" in self.task_graph.tasks else "T5" if "T5" in self.task_graph.tasks else "T1"
        if any(keyword in text for keyword in ["document", "documentation", "checklist"]):
            return "T_DOC" if "T_DOC" in self.task_graph.tasks else "T1"

        return "T_DOC" if "T_DOC" in self.task_graph.tasks else "T1"

    def _infer_task_type_for_recommended_step(self, step: str, is_brownfield: bool) -> TaskType:
        text = step.lower()
        if any(keyword in text for keyword in ["repo", "repository", "existing code", "brownfield", "impact"]):
            return TaskType.REPO_ANALYSIS if "repo" in text or "repository" in text else TaskType.IMPACT_ANALYSIS
        if "architecture" in text or "design" in text:
            return TaskType.ARCHITECTURE_DESIGN
        if any(keyword in text for keyword in ["generate code", "code generation", "implement", "build code", "api", "endpoint"]):
            return TaskType.CODE_GENERATION
        if any(keyword in text for keyword in ["modify", "patch", "update existing", "brownfield"]):
            return TaskType.BROWNFIELD_CODE_MODIFICATION
        if any(keyword in text for keyword in ["test", "unit", "integration", "e2e", "coverage"]):
            return TaskType.TEST_GENERATION
        if any(keyword in text for keyword in ["compile", "validate", "review", "risk", "quality"]):
            return TaskType.VALIDATION
        if any(keyword in text for keyword in ["document", "documentation", "checklist"]):
            return TaskType.DOCUMENTATION
        return TaskType.DOCUMENTATION

    def _find_task_id_for_type(self, task_type: TaskType) -> str | None:
        for task_id, task in self.task_graph.tasks.items():
            if task.task_type == task_type:
                return task_id
        return None
    
    def _store_result(self, task: Task, result):
        """Store task result in the shared context."""
        if task.task_type == TaskType.REQUIREMENT_ANALYSIS:
            self.context["requirement"] = result
        elif task.task_type == TaskType.REPO_ANALYSIS:
            self.context["repo_summary"] = result
        elif task.task_type == TaskType.IMPACT_ANALYSIS:
            self.context["impact_analysis"] = result
        elif task.task_type == TaskType.ARCHITECTURE_DESIGN:
            self.context["architecture"] = result
        elif task.task_type == TaskType.CODE_GENERATION:
            self.context["code_artifacts"] = result
        elif task.task_type == TaskType.TEST_GENERATION:
            self.context["test_artifacts"] = result
        elif task.task_type == TaskType.COMPILATION_VALIDATION:
            self.context["compilation_result"] = result
        elif task.task_type == TaskType.TEST_EXECUTION:
            self.context["test_execution_result"] = result
        elif task.task_type == TaskType.BROWNFIELD_CODE_MODIFICATION:
            self.context["brownfield_patch_result"] = result
        elif task.task_type == TaskType.VALIDATION:
            self.context["validation"] = result

    def _execute_local_validation(self, task: Task) -> dict:
        """Run local validation for compilation or tests."""
        code_artifacts = self.context.get("code_artifacts", [])
        test_artifacts = self.context.get("test_artifacts", [])

        with tempfile.TemporaryDirectory() as tempdir:
            src_dir = Path(tempdir) / "src"
            tests_dir = Path(tempdir) / "tests"
            src_dir.mkdir(parents=True, exist_ok=True)
            tests_dir.mkdir(parents=True, exist_ok=True)

            for artifact in code_artifacts:
                path = src_dir / artifact.filename
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(artifact.content, encoding="utf-8")

            for artifact in test_artifacts:
                path = tests_dir / Path(artifact.filename).name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(artifact.content, encoding="utf-8")

            if task.task_type == TaskType.COMPILATION_VALIDATION:
                compile_errors = []
                for py_file in src_dir.rglob("*.py"):
                    try:
                        py_compile.compile(str(py_file), doraise=True)
                    except py_compile.PyCompileError as exc:
                        compile_errors.append(str(exc))
                return {
                    "success": len(compile_errors) == 0,
                    "errors": compile_errors
                }

            if task.task_type == TaskType.BROWNFIELD_CODE_MODIFICATION:
                return self._execute_brownfield_modification(task, src_dir)

            if task.task_type == TaskType.TEST_EXECUTION:
                pytest_args = [
                    sys.executable,
                    "-m",
                    "pytest",
                    str(tests_dir),
                    "-q"
                ]
                result = subprocess.run(pytest_args, capture_output=True, text=True)
                return {
                    "success": result.returncode == 0,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode
                }

        return {"success": False, "message": "Unknown validation task."}

    def _execute_brownfield_modification(self, task: Task, src_dir: Path) -> dict:
        """Simulate applying brownfield patches and new files to a temp repo copy."""
        input_data = self._prepare_input(task)
        repo_path = input_data.get("repo_path")
        code_artifacts = input_data.get("code_artifacts", [])
        impact_analysis = input_data.get("impact_analysis")

        report = {
            "success": True,
            "applied_modifications": [],
            "created_files": [],
            "issues": [],
            "generated_patches": {},
            "impact_analysis": impact_analysis.dict() if impact_analysis else {},
            "repo_copy": None
        }

        if not repo_path:
            report["success"] = False
            report["issues"].append("No repository path provided for brownfield code modification.")
            return report

        if not code_artifacts:
            report["success"] = False
            report["issues"].append("No code artifacts available to apply to the repository.")
            return report

        with tempfile.TemporaryDirectory() as tempdir:
            temp_repo = Path(tempdir) / "repo"
            try:
                shutil.copytree(repo_path, temp_repo, dirs_exist_ok=True, ignore=shutil.ignore_patterns('.git'))
            except Exception as exc:
                report["success"] = False
                report["issues"].append(f"Failed to copy repository for patch simulation: {exc}")
                return report

            report["repo_copy"] = str(temp_repo)
            git_available = shutil.which("git") is not None

            for artifact in code_artifacts:
                if artifact.change_type == "modify":
                    target_file = temp_repo / artifact.filename
                    if not target_file.exists():
                        report["success"] = False
                        report["issues"].append(f"Target file not found for modification: {artifact.filename}")
                        continue

                    patch_text = artifact.patch
                    if not patch_text and artifact.content is not None:
                        original = target_file.read_text(encoding="utf-8")
                        diff_lines = difflib.unified_diff(
                            original.splitlines(keepends=True),
                            artifact.content.splitlines(keepends=True),
                            fromfile=str(target_file),
                            tofile=f"{str(target_file)}.modified",
                            lineterm=""
                        )
                        patch_text = "\n".join(diff_lines)
                        if patch_text:
                            report["generated_patches"][artifact.filename] = patch_text

                    if not patch_text:
                        report["success"] = False
                        report["issues"].append(
                            f"Artifact {artifact.filename} marked modify but missing patch and content."
                        )
                        continue

                    patch_file = Path(tempdir) / f"{Path(artifact.filename).name}.patch"
                    patch_file.write_text(patch_text, encoding="utf-8")

                    if git_available:
                        result = subprocess.run(
                            ["git", "apply", "--check", str(patch_file)],
                            cwd=temp_repo,
                            capture_output=True,
                            text=True
                        )
                        if result.returncode != 0:
                            report["success"] = False
                            report["issues"].append(
                                f"Patch check failed for {artifact.filename}: {result.stderr.strip() or result.stdout.strip()}"
                            )
                            continue

                        apply_result = subprocess.run(
                            ["git", "apply", str(patch_file)],
                            cwd=temp_repo,
                            capture_output=True,
                            text=True
                        )
                        if apply_result.returncode != 0:
                            report["success"] = False
                            report["issues"].append(
                                f"Patch apply failed for {artifact.filename}: {apply_result.stderr.strip() or apply_result.stdout.strip()}"
                            )
                            continue
                    else:
                        if artifact.content is not None:
                            target_file.write_text(artifact.content, encoding="utf-8")
                        report["issues"].append(
                            f"Git not available; wrote modified content for {artifact.filename} without patch verification."
                        )

                    report["applied_modifications"].append(artifact.filename)

                elif artifact.change_type == "create":
                    file_path = temp_repo / artifact.filename
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_text(artifact.content or "", encoding="utf-8")
                    report["created_files"].append(artifact.filename)
                else:
                    if artifact.patch:
                        report["applied_modifications"].append(artifact.filename)
                    else:
                        report["issues"].append(
                            f"Artifact {artifact.filename} lacks a recognized change_type and patch metadata."
                        )

            if not report["applied_modifications"] and not report["created_files"]:
                report["success"] = False
                report["issues"].append("No patches or created files were processed.")

            return report
    
    def run(self) -> EngineeringSummary:
        """Execute the complete workflow."""
        console.print("\n[bold green]🏃 Starting Workflow Execution[/bold green]\n")
        
        iteration = 0
        max_iterations = 20  # Safety limit
        
        while not self.task_graph.is_complete() and iteration < max_iterations:
            if not self.context.get("workflow_expanded") and self.task_graph.tasks["T1"].status == TaskStatus.COMPLETED:
                self._expand_workflow()

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
        patches_dir = os.path.join(run_dir, "patches")
        os.makedirs(patches_dir, exist_ok=True)

        for artifact in summary.code_artifacts:
            if artifact.patch:
                patch_path = os.path.join(patches_dir, f"{os.path.basename(artifact.filename)}.patch")
                with open(patch_path, "w", encoding="utf-8") as f:
                    f.write(artifact.patch)
            if artifact.content:
                filepath = os.path.join(code_dir, artifact.filename)
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(artifact.content)

        # Save test artifacts
        test_dir = os.path.join(run_dir, "tests")
        os.makedirs(test_dir, exist_ok=True)
        for artifact in summary.test_artifacts:
            filename = os.path.basename(artifact.filename)
            filepath = os.path.join(test_dir, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(artifact.content)

        if summary.architecture.diagrams:
            with open(os.path.join(run_dir, "architecture.md"), "w", encoding="utf-8") as f:
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

        report += "\n### Compilation Summary\n"
        report += f"```\n{summary.validation.compilation_summary or 'No compilation results available.'}\n```\n"

        report += "\n### Test Execution Summary\n"
        report += f"```\n{summary.validation.test_summary or 'No test execution results available.'}\n```\n"
        impact_analysis = getattr(summary, 'impact_analysis', None) or self.context.get('impact_analysis')
        if impact_analysis:
            report += "\n## Brownfield Impact Analysis\n"
            report += f"**Impacted Files:** {', '.join(impact_analysis.impacted_files or [])}\n"
            report += f"**Change Strategy:** {impact_analysis.change_strategy}\n"
            report += "### Compatibility Risks\n"
            for risk in impact_analysis.compatibility_risks:
                report += f"- {risk}\n"
            report += "### Recommended Actions\n"
            for action in impact_analysis.recommended_actions:
                report += f"- {action}\n"
        report += "\n### Recommendations\n"
        for rec in summary.validation.recommendations:
            report += f"- {rec}\n"
        
        report += "\n## Assumptions & Limitations\n"
        for assumption in summary.assumptions_and_limitations:
            report += f"- {assumption}\n"
        
        return report            