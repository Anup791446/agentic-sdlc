import ast
from pathlib import Path
from agents.base_agent import BaseAgent
from models.schemas import RepoSummary

SYSTEM_PROMPT = """You are a repository analyst.

Your job is to summarize the existing codebase structure and identify likely areas of impact for a new requirement.

The output should be a structured summary of the repository, including Python files, function and class signatures, imports, and likely API or service candidates.
"""

class RepoAnalysisAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="Repository Analyst", system_prompt=SYSTEM_PROMPT)

    def execute(self, input_data: dict) -> RepoSummary:
        repo_path = input_data.get("repo_path")
        if not repo_path:
            raise ValueError("repo_path is required for repository analysis")

        repo_root = Path(repo_path)
        files = [
            str(path.relative_to(repo_root)).replace("\\", "/")
            for path in repo_root.rglob("*")
            if path.is_file() and not path.name.startswith(".")
        ]
        python_files = [path for path in files if path.endswith(".py")]
        api_candidates = [
            path for path in python_files
            if any(keyword in path.lower() for keyword in ["api", "route", "service", "app.py", "controller"])
        ]

        entry_points = [path for path in python_files if path.lower().endswith(("main.py", "app.py", "server.py", "wsgi.py", "asgi.py"))]
        impacted_modules = list(dict.fromkeys(api_candidates + entry_points))

        python_file_details = {}
        for rel_path in python_files:
            full_path = repo_root / rel_path
            try:
                source = full_path.read_text(encoding="utf-8")
                tree = ast.parse(source)
            except Exception:
                python_file_details[rel_path] = {
                    "functions": [],
                    "classes": [],
                    "imports": [],
                    "parse_error": True
                }
                continue

            functions = []
            classes = []
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append(node.name)
                elif isinstance(node, ast.AsyncFunctionDef):
                    functions.append(node.name)
                elif isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.append(node.module)

            python_file_details[rel_path] = {
                "functions": sorted(set(functions)),
                "classes": sorted(set(classes)),
                "imports": sorted(set(imports))
            }

        return RepoSummary(
            repo_path=repo_path,
            files=files,
            python_files=python_files,
            api_candidates=api_candidates,
            impacted_modules=impacted_modules,
            python_file_details=python_file_details
        )
