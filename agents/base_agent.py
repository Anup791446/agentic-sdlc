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

        if Config.is_mock_mode():
            console.print(f"[yellow]⚠️ {self.name} running in mock mode[/yellow]")
            return self._mock_response(user_prompt, expect_json)
        
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
            msg = str(e)
            if "insufficient_quota" in msg or "quota" in msg.lower():
                console.print("[red]✗ OpenAI quota error: please check your billing, plan, or API key.[/red]")
                raise RuntimeError("OpenAI insufficient quota") from e
            console.print(f"[red]✗ {self.name} failed: {e}[/red]")
            raise

    def _mock_response(self, user_prompt: str, expect_json: bool = False) -> str:
        requirement_text = user_prompt.lower()
        is_todo_app = any(keyword in requirement_text for keyword in ["todo", "task", "login", "persistence"])

        if self.name == "Requirement Analyst":
            if is_todo_app:
                return json.dumps({
                    "summary": "Build a simple todo application with user authentication, task management, and persistence.",
                    "functional_requirements": [
                        "Allow users to register and log in",
                        "Allow users to create, update, and delete tasks",
                        "Persist tasks and user data",
                        "Display task status and ownership"
                    ],
                    "non_functional_requirements": [
                        "Ensure secure authentication",
                        "Provide a responsive and simple user experience",
                        "Support reliable data persistence"
                    ],
                    "ambiguities": ["Whether to support role-based access or single-user mode"],
                    "assumptions": ["Use a simple web app with a backend API and persistent storage"],
                    "scenario_type": "greenfield",
                    "recommended_steps": [
                        "Design a simple authentication and task management architecture",
                        "Generate API and business logic code for todos",
                        "Create unit and integration tests",
                        "Validate persistence and user flow"
                    ]
                }, indent=2)

            return json.dumps({
                "summary": "Build a scalable URL shortening service with analytics.",
                "functional_requirements": [
                    "Accept long URLs and return shortened URLs",
                    "Redirect short URLs to original URLs",
                    "Track click analytics"
                ],
                "non_functional_requirements": [
                    "Handle high traffic with low latency",
                    "Ensure reliability and monitoring"
                ],
                "ambiguities": ["Exact retention policy for analytics data"],
                "assumptions": ["Use a modern web framework and managed database"],
                "scenario_type": "greenfield",
                "recommended_steps": [
                    "Design a scalable microservice architecture",
                    "Generate API and business logic code",
                    "Create unit and integration tests",
                    "Validate code quality and architecture"
                ]
            }, indent=2)

        if self.name == "Software Architect":
            if is_todo_app:
                return json.dumps({
                    "overview": "A simple todo application with authentication, task CRUD operations, and persistence.",
                    "components": [
                        {"name": "Auth Service", "responsibility": "Handle user registration and login", "tech": "FastAPI"},
                        {"name": "Todo Service", "responsibility": "Manage task creation, updates, deletion, and status", "tech": "FastAPI"},
                        {"name": "Persistence Layer", "responsibility": "Store users and tasks", "tech": "SQLite"}
                    ],
                    "api_contracts": [
                        {"endpoint": "/auth/register", "method": "POST", "description": "Register a user", "request_body": {"username": "string", "password": "string"}, "response": {"message": "string"}},
                        {"endpoint": "/auth/login", "method": "POST", "description": "Authenticate a user", "request_body": {"username": "string", "password": "string"}, "response": {"token": "string"}},
                        {"endpoint": "/todos", "method": "GET", "description": "List tasks for the authenticated user", "request_body": {}, "response": {"todos": ["array"]}},
                        {"endpoint": "/todos", "method": "POST", "description": "Create a task", "request_body": {"title": "string", "completed": "boolean"}, "response": {"todo": "object"}}
                    ],
                    "data_models": [
                        {"name": "User", "fields": {"id": "int", "username": "string", "password_hash": "string"}},
                        {"name": "Todo", "fields": {"id": "int", "title": "string", "completed": "bool", "owner_id": "int"}}
                    ],
                    "tech_stack": {
                        "language": "Python",
                        "framework": "FastAPI",
                        "database": "SQLite",
                        "cache": "None",
                        "other": ["pytest", "uvicorn"]
                    },
                    "diagrams": "graph TD; A[Client] --> B[Auth Service]; A --> C[Todo Service]; C --> D[SQLite Database];"
                }, indent=2)

            return json.dumps({
                "overview": "A scalable URL shortener using microservices for API, storage, and analytics.",
                "components": [
                    {"name": "API Service", "responsibility": "Handle URL creation and redirect requests", "tech": "FastAPI"},
                    {"name": "Analytics Service", "responsibility": "Collect and report click metrics", "tech": "Python"}
                ],
                "api_contracts": [
                    {"endpoint": "/shorten", "method": "POST", "description": "Create shortened URL", "request_body": {"url": "string"}, "response": {"short_url": "string"}},
                    {"endpoint": "/{code}", "method": "GET", "description": "Redirect to original URL", "request_body": {}, "response": {"redirect": "url"}}
                ],
                "data_models": [
                    {"name": "UrlRecord", "fields": {"code": "string", "target_url": "string", "created_at": "datetime"}}
                ],
                "tech_stack": {
                    "language": "Python",
                    "framework": "FastAPI",
                    "database": "PostgreSQL",
                    "cache": "Redis",
                    "other": ["Prometheus", "Docker"]
                },
                "diagrams": "graph TD; A[API Service] --> B[Database]; A --> C[Analytics Service];"
            }, indent=2)

        if self.name == "Code Generator":
            if is_todo_app:
                return json.dumps({
                    "artifacts": [
                        {
                            "filename": "app.py",
                            "language": "python",
                            "content": "from fastapi import FastAPI, HTTPException\nfrom pydantic import BaseModel\n\napp = FastAPI()\n\nclass UserCreate(BaseModel):\n    username: str\n    password: str\n\nclass TodoCreate(BaseModel):\n    title: str\n    completed: bool = False\n\n# In-memory persistence for mock demo\nusers = {}\ntodos = {}\n\n@app.post('/auth/register')\ndef register_user(payload: UserCreate):\n    if payload.username in users:\n        raise HTTPException(status_code=400, detail='user exists')\n    users[payload.username] = payload.password\n    return {'message': 'registered'}\n\n@app.post('/auth/login')\ndef login_user(payload: UserCreate):\n    if users.get(payload.username) != payload.password:\n        raise HTTPException(status_code=401, detail='invalid credentials')\n    return {'token': f\"token-{payload.username}\"}\n\n@app.get('/todos')\ndef list_todos():\n    return {'todos': list(todos.values())}\n\n@app.post('/todos')\ndef create_todo(payload: TodoCreate):\n    todo_id = str(len(todos) + 1)\n    todo = {'id': todo_id, 'title': payload.title, 'completed': payload.completed}\n    todos[todo_id] = todo\n    return {'todo': todo}\n\n@app.put('/todos/{todo_id}')\ndef update_todo(todo_id: str, payload: TodoCreate):\n    if todo_id not in todos:\n        raise HTTPException(status_code=404, detail='not found')\n    todos[todo_id]['title'] = payload.title\n    todos[todo_id]['completed'] = payload.completed\n    return {'todo': todos[todo_id]}\n\n@app.delete('/todos/{todo_id}')\ndef delete_todo(todo_id: str):\n    if todo_id not in todos:\n        raise HTTPException(status_code=404, detail='not found')\n    removed = todos.pop(todo_id)\n    return {'deleted': removed}\n",
                            "description": "FastAPI app with authentication and todo CRUD endpoints"
                        }
                    ]
                }, indent=2)

            return json.dumps({
                "artifacts": [
                    {
                        "filename": "app.py",
                        "language": "python",
                        "content": "from fastapi import FastAPI\napp = FastAPI()\n\n@app.post('/shorten')\ndef shorten_url():\n    return {'short_url': 'https://short.ly/abc123'}\n\n@app.get('/{code}')\ndef redirect(code: str):\n    return {'redirect': 'https://example.com'}\n",
                        "description": "Main FastAPI application for URL shortening and redirects"
                    }
                ]
            }, indent=2)

        if self.name == "Test Generator":
            if is_todo_app:
                return json.dumps({
                    "artifacts": [
                        {
                            "filename": "tests/test_api.py",
                            "test_type": "integration",
                            "content": "from fastapi.testclient import TestClient\nfrom app import app\n\nclient = TestClient(app)\n\ndef test_register_and_login():\n    register_response = client.post('/auth/register', json={'username': 'alice', 'password': 'secret'})\n    assert register_response.status_code == 200\n\n    login_response = client.post('/auth/login', json={'username': 'alice', 'password': 'secret'})\n    assert login_response.status_code == 200\n\n\ndef test_todo_crud_flow():\n    create_response = client.post('/todos', json={'title': 'Write report', 'completed': False})\n    assert create_response.status_code == 200\n\n    todos_response = client.get('/todos')\n    assert todos_response.status_code == 200\n",
                            "description": "Integration tests for auth and todo CRUD flow"
                        }
                    ]
                }, indent=2)

            return json.dumps({
                "artifacts": [
                    {
                        "filename": "tests/test_api.py",
                        "test_type": "integration",
                        "content": "def test_shorten_url():\n    assert True\n",
                        "description": "Basic integration test for URL shortening API"
                    }
                ]
            }, indent=2)

        if self.name == "Validator":
            return json.dumps({
                "is_valid": True,
                "issues": [],
                "risks": ["Simplified mock implementation may miss real edge cases"],
                "trade_offs": ["Mock mode skips actual OpenAI evaluation"],
                "recommendations": ["Use a real OpenAI key for production validation"]
            }, indent=2)
        return json.dumps({"message": "Mock mode active"})

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
