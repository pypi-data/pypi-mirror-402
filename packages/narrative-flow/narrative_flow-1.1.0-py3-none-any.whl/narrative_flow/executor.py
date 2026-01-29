"""Executor for running workflows via OpenRouter."""

import json
import logging
import os
import re
import time
from typing import Any

import httpx
from jinja2 import StrictUndefined, Template, UndefinedError

from .logging_config import format_messages, format_payload, should_log_payloads
from .models import (
    Message,
    Step,
    StepResult,
    StepType,
    ValueType,
    WorkflowDefinition,
    WorkflowResult,
)

logger = logging.getLogger(__name__)
_CODE_FENCE_RE = re.compile(r"^```(?:[a-zA-Z0-9_-]+)?\s*(.*?)\s*```$", re.DOTALL)


class WorkflowExecutionError(Exception):
    """Raised when workflow execution fails."""

    pass


class OpenRouterClient:
    """Client for making OpenRouter API calls."""

    BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        if not self.api_key:
            raise WorkflowExecutionError(
                "OpenRouter API key not provided. Set OPENROUTER_API_KEY environment variable."
            )

    def chat(
        self,
        model: str,
        messages: list[dict[str, str]],
        retries: int = 3,
    ) -> str:
        """Send a chat completion request to OpenRouter.

        Args:
            model: OpenRouter model ID
            messages: List of message dicts with 'role' and 'content'
            retries: Number of retries on failure

        Returns:
            The assistant's response content.
        """
        message_count = len(messages)
        total_content_length = sum(len(message.get("content", "")) for message in messages)
        role_counts: dict[str, int] = {}
        for message in messages:
            role = message.get("role", "unknown")
            role_counts[role] = role_counts.get(role, 0) + 1
        logger.debug(
            "OpenRouter request prepared: model=%s messages=%s roles=%s content_chars=%s retries=%s",
            model,
            message_count,
            role_counts,
            total_content_length,
            retries,
        )
        if should_log_payloads():
            logger.debug("OpenRouter request payload: %s", format_messages(messages))

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/hpowers/narrative-flow",
            "X-Title": "Narrative Flow",
        }

        payload = {
            "model": model,
            "messages": messages,
        }

        last_error = None
        for attempt in range(retries + 1):
            try:
                logger.debug("OpenRouter request attempt %s/%s", attempt + 1, retries + 1)
                with httpx.Client(timeout=120.0) as client:
                    response = client.post(
                        self.BASE_URL,
                        headers=headers,
                        json=payload,
                    )
                    response.raise_for_status()
                    data = response.json()
                    logger.debug(
                        "OpenRouter response received: status=%s response_chars=%s",
                        response.status_code,
                        len(response.text),
                    )
                    content = data["choices"][0]["message"]["content"]
                    if should_log_payloads():
                        logger.debug("OpenRouter response content: %s", format_payload(content))
                    return content
            except httpx.HTTPStatusError as e:
                last_error = e
                logger.debug(
                    "OpenRouter HTTP status error: status=%s attempt=%s",
                    e.response.status_code,
                    attempt + 1,
                )
                if e.response.status_code == 429:
                    # Rate limited, wait and retry
                    wait_time = 2**attempt
                    logger.debug("OpenRouter rate limited: waiting %s seconds", wait_time)
                    time.sleep(wait_time)
                elif e.response.status_code >= 500:
                    # Server error, retry
                    logger.debug("OpenRouter server error: retrying after 1 second")
                    time.sleep(1)
                else:
                    # Client error, don't retry
                    raise WorkflowExecutionError(
                        f"OpenRouter API error: {e.response.status_code} - {e.response.text}"
                    ) from e
            except httpx.RequestError as e:
                last_error = e
                logger.debug("OpenRouter request error: %s", e)
                time.sleep(1)

        raise WorkflowExecutionError(f"Failed after {retries + 1} attempts: {last_error}")


def execute_workflow(
    workflow: WorkflowDefinition,
    inputs: dict[str, Any],
    api_key: str | None = None,
) -> WorkflowResult:
    """Execute a workflow with the given inputs.

    Args:
        workflow: The workflow definition to execute.
        inputs: Dictionary of input variable values.
        api_key: Optional OpenRouter API key (falls back to env var).

    Returns:
        WorkflowResult containing outputs and execution details. Failures are
        captured in the result with success=False and an error message.
    """
    inputs_copy = dict(inputs)
    variables: dict[str, Any] = {}
    conversation_history: list[Message] = []
    step_results: list[StepResult] = []

    try:
        _apply_input_defaults(workflow, inputs_copy)

        # State for execution
        variables = dict(inputs_copy)
        output_types = {output.name: output.type for output in workflow.outputs}
        client: OpenRouterClient | None = None
        logger.debug(
            "Executing workflow: name=%s steps=%s inputs=%s outputs=%s retries=%s",
            workflow.name,
            len(workflow.steps),
            list(inputs_copy.keys()),
            workflow.get_output_names(),
            workflow.retries,
        )

        def _get_client() -> OpenRouterClient:
            """Create an OpenRouter client only when needed."""
            nonlocal client
            if client is None:
                client = OpenRouterClient(api_key=api_key)
            return client

        for step in workflow.steps:
            logger.debug("Executing step: name=%s type=%s", step.name, step.type.value)
            if step.type in {StepType.MESSAGE, StepType.USER}:
                result = _execute_message_step(
                    step=step,
                    variables=variables,
                    conversation_history=conversation_history,
                    client=_get_client(),
                    model=workflow.models.conversation,
                    retries=workflow.retries,
                )
            elif step.type == StepType.ASSISTANT:
                result = _execute_assistant_step(
                    step=step,
                    variables=variables,
                    conversation_history=conversation_history,
                )
            else:  # EXTRACT
                result = _execute_extract_step(
                    step=step,
                    variables=variables,
                    conversation_history=conversation_history,
                    client=_get_client(),
                    model=workflow.models.extraction,
                    retries=workflow.retries,
                    expected_type=output_types.get(step.variable_name or "", ValueType.STRING),
                )

            step_results.append(result)

        # Collect outputs
        outputs = {name: variables[name] for name in workflow.get_output_names()}
        logger.debug("Workflow completed: name=%s outputs=%s", workflow.name, list(outputs.keys()))

        return WorkflowResult(
            workflow_name=workflow.name,
            inputs=inputs_copy,
            outputs=outputs,
            step_results=step_results,
            conversation_history=conversation_history,
            success=True,
            error=None,
        )

    except Exception as e:
        outputs: dict[str, str | list[str]] = {}
        for name in workflow.get_output_names():
            if name in variables:
                outputs[name] = variables[name]
        return WorkflowResult(
            workflow_name=workflow.name,
            inputs=inputs_copy,
            outputs=outputs,
            step_results=step_results,
            conversation_history=conversation_history,
            success=False,
            error=str(e),
        )


def _render_template(content: str, variables: dict[str, Any]) -> str:
    """Render Jinja2 template with variables."""
    try:
        logger.debug(
            "Rendering template: content_chars=%s variables=%s",
            len(content),
            list(variables.keys()),
        )
        template = Template(content, undefined=StrictUndefined)
        return template.render(**variables)
    except UndefinedError as e:
        logger.debug("Template rendering failed: %s", e)
        raise WorkflowExecutionError(f"Undefined variable in template: {e}") from e


def _apply_input_defaults(workflow: WorkflowDefinition, inputs: dict[str, Any]) -> None:
    """Apply default values and validate required inputs.

    Args:
        workflow: Workflow definition containing input specs.
        inputs: Input values provided by the caller (mutated in-place).

    Raises:
        WorkflowExecutionError: If required inputs are missing with no default.
    """
    missing_required = []
    for inp in workflow.inputs:
        if inp.name in inputs:
            continue
        if inp.default is not None:
            logger.debug("Applying default for input: name=%s", inp.name)
            inputs[inp.name] = inp.default
        elif inp.required:
            missing_required.append(inp.name)

    if missing_required:
        missing_list = ", ".join(missing_required)
        logger.debug("Missing required inputs: %s", missing_list)
        raise WorkflowExecutionError(f"Missing required inputs: {missing_list}")


def _execute_message_step(
    step: Step,
    variables: dict[str, Any],
    conversation_history: list[Message],
    client: OpenRouterClient,
    model: str,
    retries: int,
) -> StepResult:
    """Execute a message step."""
    # Render the message content with variables
    rendered_content = _render_template(step.content, variables)
    logger.debug(
        "Message step rendered: name=%s content_chars=%s history_before=%s",
        step.name,
        len(rendered_content),
        len(conversation_history),
    )

    # Add user message to history
    user_message = Message(role="user", content=rendered_content)
    conversation_history.append(user_message)

    # Build messages for API call
    api_messages = [{"role": m.role, "content": m.content} for m in conversation_history]

    # Call the API
    response_content = client.chat(model=model, messages=api_messages, retries=retries)
    logger.debug(
        "Message step response: name=%s response_chars=%s history_after=%s",
        step.name,
        len(response_content),
        len(conversation_history) + 1,
    )

    # Add assistant response to history
    assistant_message = Message(role="assistant", content=response_content)
    conversation_history.append(assistant_message)

    return StepResult(
        step=step,
        user_message=rendered_content,
        assistant_response=response_content,
    )


def _execute_assistant_step(
    step: Step,
    variables: dict[str, Any],
    conversation_history: list[Message],
) -> StepResult:
    """Insert a predefined assistant message into the conversation history."""
    rendered_content = _render_template(step.content, variables)
    logger.debug(
        "Assistant step inserted: name=%s content_chars=%s history_before=%s",
        step.name,
        len(rendered_content),
        len(conversation_history),
    )
    if should_log_payloads():
        logger.debug("Assistant step content: %s", format_payload(rendered_content))
    assistant_message = Message(role="assistant", content=rendered_content)
    conversation_history.append(assistant_message)

    return StepResult(
        step=step,
        assistant_response=rendered_content,
    )


def _execute_extract_step(
    step: Step,
    variables: dict[str, Any],
    conversation_history: list[Message],
    client: OpenRouterClient,
    model: str,
    retries: int,
    expected_type: ValueType,
) -> StepResult:
    """Execute an extraction step."""
    if not conversation_history:
        raise WorkflowExecutionError("Cannot extract: no conversation history")

    # Get the last assistant response
    last_assistant = None
    for msg in reversed(conversation_history):
        if msg.role == "assistant":
            last_assistant = msg.content
            break

    if last_assistant is None:
        raise WorkflowExecutionError("Cannot extract: no assistant response found")

    # Render extraction instruction
    rendered_instruction = _render_template(step.content, variables)

    # Build extraction prompt
    type_instruction = _render_extraction_type_instruction(expected_type)
    extraction_prompt = f"""Here is a response from an AI assistant:

<response>
{last_assistant}
</response>

Your task: {rendered_instruction}

Return ONLY valid JSON {type_instruction} with no additional text, explanation, or formatting."""

    # Call extraction model (single turn, no history)
    api_messages = [{"role": "user", "content": extraction_prompt}]
    logger.debug(
        "Extraction prompt prepared: name=%s expected_type=%s prompt_chars=%s",
        step.name,
        expected_type.value,
        len(extraction_prompt),
    )
    extracted_value = client.chat(model=model, messages=api_messages, retries=retries)
    logger.debug(
        "Extraction response received: name=%s response_chars=%s",
        step.name,
        len(extracted_value),
    )
    parsed_value = _parse_extracted_value(extracted_value, expected_type, step.variable_name or "unknown")

    # Store in variables
    variables[step.variable_name] = parsed_value
    logger.debug(
        "Extraction parsed: name=%s variable=%s type=%s",
        step.name,
        step.variable_name,
        expected_type.value,
    )

    return StepResult(
        step=step,
        extracted_value=parsed_value,
    )


def _render_extraction_type_instruction(expected_type: ValueType) -> str:
    """Render type-specific instruction for extraction output."""
    match expected_type:
        case ValueType.STRING:
            return 'as a JSON string (e.g., "value")'
        case ValueType.STRING_LIST:
            return 'as a JSON array of strings (e.g., ["first", "second"])'
        case _:
            return f"matching type {expected_type.value}"


def _parse_extracted_value(raw_value: str, expected_type: ValueType, variable_name: str) -> str | list[str]:
    """Parse and validate extracted JSON based on expected type."""
    cleaned_value, stripped_fences = _strip_code_fences(raw_value)
    if stripped_fences:
        logger.debug("Extraction response contained code fences: variable=%s", variable_name)
    try:
        parsed_value = json.loads(cleaned_value)
    except json.JSONDecodeError as e:
        logger.debug(
            "Extraction JSON parse failed: variable=%s error=%s",
            variable_name,
            e.msg,
        )
        raise WorkflowExecutionError(f"Extraction for '{variable_name}' returned invalid JSON: {e.msg}") from e

    if expected_type == ValueType.STRING:
        if isinstance(parsed_value, str):
            return parsed_value
        raise WorkflowExecutionError(
            f"Extraction for '{variable_name}' must be a JSON string, got {type(parsed_value).__name__}"
        )

    if expected_type == ValueType.STRING_LIST:
        if isinstance(parsed_value, list) and all(isinstance(item, str) for item in parsed_value):
            return parsed_value
        raise WorkflowExecutionError(
            f"Extraction for '{variable_name}' must be a JSON array of strings, got {type(parsed_value).__name__}"
        )

    raise WorkflowExecutionError(f"Unsupported output type for '{variable_name}': {expected_type.value}")


def _strip_code_fences(raw_value: str) -> tuple[str, bool]:
    """Strip Markdown code fences from an extraction response if present.

    Args:
        raw_value: Raw extraction model response.

    Returns:
        A tuple of (cleaned_value, stripped_fences).
    """
    cleaned_value = raw_value.strip()
    match = _CODE_FENCE_RE.match(cleaned_value)
    if not match:
        return cleaned_value, False
    return match.group(1).strip(), True
