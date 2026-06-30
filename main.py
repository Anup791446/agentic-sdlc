
# main.py
"""
Agentic SDLC System
===================
An AI-powered system that transforms software requirements into engineering outputs.

Usage:
    python main.py                          # Run with default URL shortener requirement
    python main.py "Your custom requirement"  # Run with custom requirement
    python main.py --interactive            # Interactive mode
"""

import sys
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

from config import Config
from orchestrator.workflow import WorkflowOrchestrator

console = Console()

# Default requirement (mandatory use case)
DEFAULT_REQUIREMENT = """
Build a scalable URL shortener service with APIs, persistence, and analytics.

The service should:
- Accept long URLs and return shortened versions
- Redirect short URLs to original URLs
- Track click analytics (timestamp, referrer, location)
- Handle high traffic with low latency
- Provide API endpoints for URL management
"""

def display_banner():
    """Display the application banner."""
    banner = """
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║        🤖 AGENTIC SOFTWARE ENGINEERING SYSTEM 🤖          ║
    ║                                                           ║
    ║   Transform requirements into production-ready code       ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """
    console.print(banner, style="bold cyan")

def run_interactive():
    """Run in interactive mode."""
    console.print("\n[bold]Interactive Mode[/bold]")
    console.print("Enter your software requirement (press Enter twice to submit):\n")
    
    lines = []
    while True:
        line = input()
        if line == "":
            if lines:
                break
        else:
            lines.append(line)
    
    requirement = "\n".join(lines)
    return requirement

def main():
    """Main entry point."""
    display_banner()
    
    # Validate configuration
    try:
        Config.validate()
    except ValueError as e:
        console.print(f"[red]Configuration Error: {e}[/red]")
        console.print("\nPlease create a .env file with your OPENAI_API_KEY")
        sys.exit(1)
    
    # Determine the requirement to process
    if len(sys.argv) > 1:
        if sys.argv[1] == "--interactive":
            requirement = run_interactive()
        else:
            requirement = " ".join(sys.argv[1:])
    else:
        console.print("[yellow]No requirement provided. Using default URL shortener example.[/yellow]\n")
        requirement = DEFAULT_REQUIREMENT
    
    # Confirm before proceeding
    console.print(Panel(requirement.strip(), title="Requirement to Process", border_style="blue"))
    
    if not Confirm.ask("\nProceed with this requirement?"):
        console.print("[yellow]Cancelled.[/yellow]")
        sys.exit(0)
    
    # Create and run the workflow
    orchestrator = WorkflowOrchestrator()
    orchestrator.create_workflow(requirement)
    
    console.print("\n" + "="*60)
    summary = orchestrator.run()
    console.print("="*60 + "\n")
    
    # Save outputs
    output_dir = orchestrator.save_outputs(summary)
    
    # Display final summary
    console.print(Panel(
        f"""[bold green]✅ Workflow Complete![/bold green]

📁 Output Directory: {output_dir}

📄 Files Generated:
   - Code: {len(summary.code_artifacts)} files
   - Tests: {len(summary.test_artifacts)} files
   - Report: REPORT.md
   - Architecture: architecture.md

⚠️  Validation Status: {"Passed" if summary.validation.is_valid else "Issues Found"}
   - {len(summary.validation.issues)} issues
   - {len(summary.validation.risks)} risks identified

📋 Next Steps:
   1. Review the generated code in {output_dir}/src/
   2. Review tests in {output_dir}/tests/
   3. Read the full report in {output_dir}/REPORT.md
""",
        title="Execution Summary",
        border_style="green"
    ))

if __name__ == "__main__":
    main()
