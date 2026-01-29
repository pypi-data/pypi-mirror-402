"""Narrative Flow - Human-readable LLM conversation workflows.

Basic usage:

    from narrative_flow import parse_workflow, execute_workflow, save_log

    # Parse a workflow file
    workflow = parse_workflow("my_workflow.workflow.md")

    # Execute with inputs
    result = execute_workflow(workflow, {
        "short_transcript": "...",
        "episode_transcript": "...",
    })

    # Access outputs
    print(result.outputs["short_title"])

    # Save execution log
    save_log(result, output_dir="logs")
"""

from .executor import WorkflowExecutionError, execute_workflow
from .logger import generate_log, save_log
from .logging_config import configure_logging
from .models import (
    InputVariable,
    Message,
    ModelsConfig,
    OutputVariable,
    Step,
    StepResult,
    StepType,
    ValueType,
    WorkflowDefinition,
    WorkflowResult,
)
from .parser import WorkflowParseError, parse_workflow

__version__ = "1.1.0"  # x-release-please-version

__all__ = [
    # Main functions
    "parse_workflow",
    "execute_workflow",
    "generate_log",
    "save_log",
    "configure_logging",
    # Models
    "WorkflowDefinition",
    "WorkflowResult",
    "Step",
    "StepResult",
    "StepType",
    "Message",
    "InputVariable",
    "OutputVariable",
    "ModelsConfig",
    "ValueType",
    # Exceptions
    "WorkflowParseError",
    "WorkflowExecutionError",
]
