"""Parser for .workflow.md files."""

import logging
import re
from pathlib import Path

import frontmatter

from .models import (
    InputVariable,
    ModelsConfig,
    OutputVariable,
    Step,
    StepType,
    ValueType,
    WorkflowDefinition,
)

logger = logging.getLogger(__name__)


class WorkflowParseError(Exception):
    """Raised when a workflow file cannot be parsed."""

    pass


def parse_workflow(source: str | Path) -> WorkflowDefinition:
    """Parse a workflow from a file path or string content.

    Args:
        source: Either a path to a .workflow.md file or the content as a string.

    Returns:
        WorkflowDefinition object.

    Raises:
        WorkflowParseError: If the workflow cannot be parsed.
    """
    if isinstance(source, Path) or (isinstance(source, str) and not source.strip().startswith("---")):
        # Treat as file path
        path = Path(source)
        if not path.exists():
            raise WorkflowParseError(f"Workflow file not found: {path}")
        logger.debug("Parsing workflow from file: path=%s", path)
        content = path.read_text()
    else:
        logger.debug("Parsing workflow from string content")
        content = source

    try:
        post = frontmatter.loads(content)
    except Exception as e:
        raise WorkflowParseError(f"Failed to parse frontmatter: {e}") from e

    metadata = post.metadata
    body = post.content

    # Validate required frontmatter fields
    if not isinstance(metadata, dict):
        raise WorkflowParseError("Frontmatter must be a mapping of keys to values")
    if "name" not in metadata:
        raise WorkflowParseError("Missing required field 'name' in frontmatter")
    if "models" not in metadata:
        raise WorkflowParseError("Missing required field 'models' in frontmatter")

    # Parse models
    models_data = metadata["models"]
    if not isinstance(models_data, dict):
        raise WorkflowParseError("Field 'models' must be a mapping")
    if "conversation" not in models_data:
        raise WorkflowParseError("Missing 'conversation' in models config")
    if "extraction" not in models_data:
        raise WorkflowParseError("Missing 'extraction' in models config")

    models = ModelsConfig(
        conversation=models_data["conversation"],
        extraction=models_data["extraction"],
    )

    # Parse inputs
    inputs = []
    inputs_data = metadata.get("inputs", [])
    if inputs_data is None:
        inputs_data = []
    if not isinstance(inputs_data, list):
        raise WorkflowParseError("Field 'inputs' must be a list")
    for inp in inputs_data:
        if not isinstance(inp, dict):
            raise WorkflowParseError("Each input must be a mapping")
        if "name" not in inp:
            raise WorkflowParseError("Each input must include a 'name'")
        inputs.append(
            InputVariable(
                name=inp["name"],
                description=inp.get("description"),
                required=inp.get("required", True),
                default=inp.get("default"),
            )
        )

    # Parse outputs
    outputs = []
    outputs_data = metadata.get("outputs", [])
    if outputs_data is None:
        outputs_data = []
    if not isinstance(outputs_data, list):
        raise WorkflowParseError("Field 'outputs' must be a list")
    for out in outputs_data:
        if not isinstance(out, dict):
            raise WorkflowParseError("Each output must be a mapping")
        if "name" not in out:
            raise WorkflowParseError("Each output must include a 'name'")
        outputs.append(
            OutputVariable(
                name=out["name"],
                description=out.get("description"),
                type=_parse_value_type(out.get("type", ValueType.STRING.value)),
            )
        )

    # Parse steps from body
    steps = _parse_steps(body)
    logger.debug(
        "Parsed workflow metadata: name=%s inputs=%s outputs=%s steps=%s",
        metadata["name"],
        len(inputs),
        len(outputs),
        len(steps),
    )

    # Validate that all outputs have corresponding extract steps
    extract_vars = {s.variable_name for s in steps if s.type == StepType.EXTRACT}
    output_names = {o.name for o in outputs}
    missing = output_names - extract_vars
    if missing:
        raise WorkflowParseError(f"Outputs declared but no Extract step found: {missing}")

    return WorkflowDefinition(
        name=metadata["name"],
        description=metadata.get("description"),
        models=models,
        retries=metadata.get("retries", 3),
        inputs=inputs,
        outputs=outputs,
        steps=steps,
    )


def _parse_value_type(value: object) -> ValueType:
    """Parse and validate a ValueType from frontmatter."""
    if not isinstance(value, str):
        raise WorkflowParseError("Output type must be a string")

    normalized = value.strip().lower()
    try:
        return ValueType(normalized)
    except ValueError as e:
        allowed = ", ".join(value_type.value for value_type in ValueType)
        raise WorkflowParseError(f"Invalid output type '{value}'. Expected one of: {allowed}") from e


def _parse_steps(body: str) -> list[Step]:
    """Parse the markdown body into steps."""
    steps = []

    # Split by ## headings
    # Pattern matches ## at start of line, captures heading and content
    pattern = r"^## (.+?)$\n(.*?)(?=^## |\Z)"
    matches = re.findall(pattern, body, re.MULTILINE | re.DOTALL)

    for heading, content in matches:
        heading = heading.strip()
        content = content.strip()

        heading_lower = heading.lower()
        if heading_lower.startswith("extract:"):
            # Extract step
            var_name = heading[8:].strip()  # After "Extract:"
            if not var_name:
                raise WorkflowParseError(f"Extract step missing variable name: {heading}")
            if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", var_name):
                raise WorkflowParseError(f"Invalid variable name: {var_name}")

            steps.append(
                Step(
                    type=StepType.EXTRACT,
                    name=heading,
                    content=content,
                    variable_name=var_name,
                )
            )
        elif heading_lower == "user" or heading_lower.startswith("user:"):
            steps.append(
                Step(
                    type=StepType.USER,
                    name=heading,
                    content=content,
                )
            )
        elif heading_lower == "assistant" or heading_lower.startswith("assistant:"):
            steps.append(
                Step(
                    type=StepType.ASSISTANT,
                    name=heading,
                    content=content,
                )
            )
        else:
            # Message step
            steps.append(
                Step(
                    type=StepType.MESSAGE,
                    name=heading,
                    content=content,
                )
            )

    return steps
