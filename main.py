
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

import argparse
import os
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
    parser = argparse.ArgumentParser(description="Run the Agentic SDLC application")
    parser.add_argument("requirement", nargs="*", help="Requirement text to process")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive requirement mode")
    parser.add_argument("--mock", action="store_true", help="Run in mock mode without OpenAI calls")
    parser.add_argument("--repo-path", help="Path to an existing repository for brownfield analysis")
    parser.add_argument("--yes", action="store_true", help="Automatically confirm the requirement prompt")
    args = parser.parse_args()

    if args.mock:
        os.environ["MOCK_MODE"] = "true"

    display_banner()
    
    if args.mock:
        console.print("[yellow]⚠️ Running in MOCK mode. No OpenAI API calls will be made.[/yellow]\n")

    # Validate configuration
    try:
        Config.validate()
    except ValueError as e:
        console.print(f"[red]Configuration Error: {e}[/red]")
        if not Config.is_mock_mode():
            console.print("\nPlease create a .env file with your OPENAI_API_KEY")
        sys.exit(1)

    # Determine the requirement to process
    if args.interactive:
        requirement = run_interactive()
    elif args.requirement:
        requirement = " ".join(args.requirement)
    else:
        console.print("[yellow]No requirement provided. Using default URL shortener example.[/yellow]\n")
        requirement = DEFAULT_REQUIREMENT

    # Confirm before proceeding
    console.print(Panel(requirement.strip(), title="Requirement to Process", border_style="blue"))
    if not args.yes:
        if not Confirm.ask("\nProceed with this requirement?"):
            console.print("[yellow]Cancelled.[/yellow]")
            sys.exit(0)

    if args.repo_path and not os.path.isdir(args.repo_path):
        console.print(f"[red]Repository path not found: {args.repo_path}[/red]")
        sys.exit(1)

    # Create and run the workflow
    orchestrator = WorkflowOrchestrator()
    orchestrator.create_workflow(requirement, repo_path=args.repo_path)

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
