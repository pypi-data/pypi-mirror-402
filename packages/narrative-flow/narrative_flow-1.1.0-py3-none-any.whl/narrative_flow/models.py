"""Data models for workflow definitions."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class StepType(str, Enum):
    ASSISTANT = "assistant"
    MESSAGE = "message"
    USER = "user"
    EXTRACT = "extract"


class ValueType(str, Enum):
    """Supported variable types for inputs/outputs."""

    STRING = "string"
    STRING_LIST = "string_list"


class InputVariable(BaseModel):
    """An input variable for the workflow."""

    name: str
    description: str | None = None
    required: bool = True
    default: str | None = None


class OutputVariable(BaseModel):
    """An output variable for the workflow."""

    name: str
    description: str | None = None
    type: ValueType


class ModelsConfig(BaseModel):
    """Model configuration for the workflow."""

    conversation: str
    extraction: str


class Step(BaseModel):
    """A single step in the workflow."""

    type: StepType
    name: str
    content: str
    variable_name: str | None = None  # Only for extract steps


class WorkflowDefinition(BaseModel):
    """Complete workflow definition parsed from a .workflow.md file."""

    name: str
    description: str | None = None
    models: ModelsConfig
    retries: int = Field(default=3, ge=0)
    inputs: list[InputVariable] = Field(default_factory=list)
    outputs: list[OutputVariable] = Field(default_factory=list)
    steps: list[Step] = Field(default_factory=list)

    def get_required_inputs(self) -> list[str]:
        """Get list of required input variable names."""
        return [inp.name for inp in self.inputs if inp.required]

    def get_output_names(self) -> list[str]:
        """Get list of output variable names."""
        return [out.name for out in self.outputs]


class Message(BaseModel):
    """A message in the conversation history."""

    role: str  # "user" or "assistant"
    content: str


class StepResult(BaseModel):
    """Result of executing a single step."""

    step: Step
    user_message: str | None = None  # For message steps
    assistant_response: str | None = None  # For message steps
    extracted_value: str | list[str] | None = None  # For extract steps


class WorkflowResult(BaseModel):
    """Result of executing a complete workflow."""

    workflow_name: str
    inputs: dict[str, Any]
    outputs: dict[str, str | list[str]]
    step_results: list[StepResult]
    conversation_history: list[Message]
    success: bool
    error: str | None = None
