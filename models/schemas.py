# models/schemas.py
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"

class TaskType(str, Enum):
    REQUIREMENT_ANALYSIS = "requirement_analysis"
    ARCHITECTURE_DESIGN = "architecture_design"
    CODE_GENERATION = "code_generation"
    TEST_GENERATION = "test_generation"
    DOCUMENTATION = "documentation"
    VALIDATION = "validation"

class Task(BaseModel):
    """Represents a single task in the workflow."""
    id: str
    name: str
    task_type: TaskType
    description: str
    dependencies: list[str] = Field(default_factory=list)  # IDs of tasks this depends on
    status: TaskStatus = TaskStatus.PENDING
    output: Optional[str] = None
    error: Optional[str] = None
    retries: int = 0

class Requirement(BaseModel):
    """Parsed and normalized requirement."""
    raw_input: str
    summary: str
    functional_requirements: list[str]
    non_functional_requirements: list[str]
    ambiguities: list[str]
    assumptions: list[str]
    scenario_type: str  # "greenfield" or "brownfield"

class ArchitectureDesign(BaseModel):
    """System architecture output."""
    overview: str
    components: list[dict]
    api_contracts: list[dict]
    data_models: list[dict]
    tech_stack: dict
    diagrams: Optional[str] = None  # Mermaid diagram code

class CodeArtifact(BaseModel):
    """Generated code artifact."""
    filename: str
    language: str
    content: str
    description: str

class TestArtifact(BaseModel):
    """Generated test artifact."""
    filename: str
    test_type: str  # "unit", "integration", "e2e"
    content: str
    description: str

class ValidationResult(BaseModel):
    """Validation output."""
    is_valid: bool
    issues: list[str]
    risks: list[str]
    trade_offs: list[str]
    recommendations: list[str]

class EngineeringSummary(BaseModel):
    """Final output delivered to the user."""
    requirement: Requirement
    architecture: ArchitectureDesign
    code_artifacts: list[CodeArtifact]
    test_artifacts: list[TestArtifact]
    validation: ValidationResult
    implementation_plan: str
    assumptions_and_limitations: list[str]
