# Agentic Software Engineering System

An AI-powered system that turns a natural-language software requirement into a structured engineering workflow with architecture suggestions, starter code, tests, and a validation report.

## What This Project Does

The system follows an agent-based software development pipeline:

1. Accepts a requirement from the user
2. Analyzes the requirement
3. Designs an architecture
4. Generates source code
5. Produces test cases
6. Validates the output and saves a report

## Project Structure

- main.py: command-line entry point and user interaction
- orchestrator/: workflow orchestration and task graph management
- agents/: specialized agents for requirement analysis, architecture, code, testing, and validation
- models/: Pydantic schemas for workflow data
- tests/: regression tests for workflow behavior

## Setup

```powershell
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

Create a `.env` file with your OpenAI key:

```env
OPENAI_API_KEY=your-openai-key
```

## Run the Project

### Real mode

```powershell
.\venv\Scripts\python.exe main.py "Build a simple todo app with login and persistence"
```

### Mock mode

```powershell
.\venv\Scripts\python.exe main.py "Build a simple todo app with login and persistence" --mock --yes
```

Mock mode is useful for local testing and demos when OpenAI access is unavailable.

## Output

Each successful run creates a timestamped folder under the outputs directory containing:

- REPORT.md
- architecture.md
- src/ for generated code
- tests/ for generated tests

## Testing

```powershell
.\venv\Scripts\python.exe -m pytest -q tests/test_workflow.py
```

## Notes

- Real execution requires a valid OpenAI API key.
- The generated output is intended as a starter scaffold and should be reviewed before real-world use.
