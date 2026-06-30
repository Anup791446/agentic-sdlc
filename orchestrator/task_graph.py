# orchestrator/task_graph.py
from models.schemas import Task, TaskStatus, TaskType
from collections import deque
from rich.console import Console
from rich.table import Table

console = Console()

class TaskGraph:
    """Manages task dependencies and execution order."""
    
    def __init__(self):
        self.tasks: dict[str, Task] = {}
    
    def add_task(self, task: Task):
        """Add a task to the graph."""
        self.tasks[task.id] = task
    
    def get_ready_tasks(self) -> list[Task]:
        """Return tasks whose dependencies are all completed."""
        ready = []
        for task in self.tasks.values():
            if task.status != TaskStatus.PENDING:
                continue
            
            # Check if all dependencies are completed
            deps_met = all(
                self.tasks[dep_id].status == TaskStatus.COMPLETED
                for dep_id in task.dependencies
                if dep_id in self.tasks
            )
            
            if deps_met:
                ready.append(task)
        
        return ready
    
    def mark_completed(self, task_id: str, output: str):
        """Mark a task as completed."""
        if task_id in self.tasks:
            self.tasks[task_id].status = TaskStatus.COMPLETED
            self.tasks[task_id].output = output
    
    def mark_failed(self, task_id: str, error: str):
        """Mark a task as failed."""
        if task_id in self.tasks:
            self.tasks[task_id].status = TaskStatus.FAILED
            self.tasks[task_id].error = error
    
    def is_complete(self) -> bool:
        """Check if all tasks are done (completed or failed)."""
        return all(
            t.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]
            for t in self.tasks.values()
        )
    
    def display(self):
        """Print the task graph status."""
        table = Table(title="Task Execution Status")
        table.add_column("ID", style="cyan")
        table.add_column("Task", style="white")
        table.add_column("Type", style="blue")
        table.add_column("Status", style="green")
        table.add_column("Dependencies", style="yellow")
        
        for task in self.tasks.values():
            status_style = {
                TaskStatus.PENDING: "white",
                TaskStatus.IN_PROGRESS: "yellow",
                TaskStatus.COMPLETED: "green",
                TaskStatus.FAILED: "red",
                TaskStatus.BLOCKED: "magenta"
            }.get(task.status, "white")
            
            table.add_row(
                task.id,
                task.name,
                task.task_type.value,
                f"[{status_style}]{task.status.value}[/{status_style}]",
                ", ".join(task.dependencies) or "-"
            )
        
        console.print(table)
