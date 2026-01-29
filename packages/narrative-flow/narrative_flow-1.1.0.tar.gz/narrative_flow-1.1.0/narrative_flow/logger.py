"""Logger for saving workflow execution results as Markdown."""

import json
from datetime import datetime
from pathlib import Path

from .models import StepType, WorkflowResult
from .utils import sanitize_filename_component


def generate_log(result: WorkflowResult, truncate_inputs: int | None = 500) -> str:
    """Generate a Markdown log of the workflow execution.

    Args:
        result: The workflow execution result.
        truncate_inputs: Max characters for input values (None for no truncation).

    Returns:
        Markdown string of the execution log.
    """
    lines = []

    # Header
    timestamp = datetime.now().isoformat(sep=" ", timespec="seconds")
    lines.append("# Workflow Execution Log")
    lines.append("")
    lines.append(f"**Workflow:** {result.workflow_name}")
    lines.append(f"**Timestamp:** {timestamp}")
    lines.append(f"**Status:** {'✅ Success' if result.success else '❌ Failed'}")
    if result.error:
        lines.append(f"**Error:** {result.error}")
    lines.append("")

    # Inputs
    lines.append("## Inputs")
    lines.append("")
    if result.inputs:
        for name, value in result.inputs.items():
            display_value = str(value)
            if truncate_inputs and len(display_value) > truncate_inputs:
                display_value = display_value[:truncate_inputs] + "... [truncated]"
            lines.append(f"### {name}")
            lines.append("")
            _append_code_block(lines, display_value)
            lines.append("")
    else:
        lines.append("*No inputs*")
        lines.append("")

    # Outputs
    lines.append("## Outputs")
    lines.append("")
    if result.outputs:
        for name, value in result.outputs.items():
            lines.append(f"### {name}")
            lines.append("")
            _append_code_block(lines, _format_value(value))
            lines.append("")
    else:
        lines.append("*No outputs*")
        lines.append("")

    # Conversation
    lines.append("## Conversation")
    lines.append("")

    for step_result in result.step_results:
        step = step_result.step
        lines.append(f"### {step.name}")
        lines.append("")

        if step.type in {StepType.MESSAGE, StepType.USER}:
            lines.append("**User:**")
            lines.append("")
            lines.append(step_result.user_message or "*No message*")
            lines.append("")
            lines.append("---")
            lines.append("")
            lines.append("**Assistant:**")
            lines.append("")
            lines.append(step_result.assistant_response or "*No response*")
            lines.append("")
        elif step.type == StepType.ASSISTANT:
            lines.append("**Assistant:**")
            lines.append("")
            lines.append(step_result.assistant_response or "*No response*")
            lines.append("")
        else:  # EXTRACT
            lines.append("**Extraction Instruction:**")
            lines.append("")
            lines.append(step.content)
            lines.append("")
            lines.append(f"**Extracted Value (`{step.variable_name}`):**")
            lines.append("")
            if step_result.extracted_value is None:
                _append_code_block(lines, "*No value*")
            else:
                _append_code_block(lines, _format_value(step_result.extracted_value))
            lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def save_log(
    result: WorkflowResult,
    output_dir: str | Path = ".",
    filename: str | None = None,
    truncate_inputs: int | None = 500,
) -> Path:
    """Save the execution log to a Markdown file.

    Args:
        result: The workflow execution result.
        output_dir: Directory to save the log file.
        filename: Optional filename (defaults to workflow_name + timestamp).
        truncate_inputs: Max characters for input values.

    Returns:
        Path to the saved log file.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = sanitize_filename_component(result.workflow_name)
        filename = f"{safe_name}_{timestamp}.log.md"
    else:
        filename_path = Path(filename)
        if filename_path.name != filename or filename_path.is_absolute() or ".." in filename_path.parts:
            raise ValueError("filename must be a simple file name without path separators")

    log_content = generate_log(result, truncate_inputs=truncate_inputs)

    log_path = output_dir / filename
    log_path.write_text(log_content)

    return log_path


def _sanitize_filename_component(value: str) -> str:
    """Backwards-compatible alias for sanitize_filename_component."""
    return sanitize_filename_component(value)


def _append_code_block(lines: list[str], value: str) -> None:
    """Append a Markdown code block, choosing a safe fence length."""
    fence = "```"
    while fence in value:
        fence += "`"
    lines.append(fence)
    lines.append(value)
    lines.append(fence)


def _format_value(value: object) -> str:
    """Format values for logging."""
    if isinstance(value, (list, dict)):
        return json.dumps(value, indent=2)
    return str(value)
