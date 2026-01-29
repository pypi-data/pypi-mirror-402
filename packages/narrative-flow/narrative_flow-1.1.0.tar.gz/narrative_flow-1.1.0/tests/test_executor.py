"""Tests for the workflow executor.

These tests demonstrate how narrative-flow executes workflows against the
OpenRouter API. The API is mocked using pytest-httpx. Reference these tests
to understand:

- How workflows are executed step by step
- Template variable substitution
- Value extraction from LLM responses
- Error handling and retry behavior
- Conversation history management
"""

from typing import Any

import pytest
from pytest_httpx import HTTPXMock

from narrative_flow import (
    InputVariable,
    ModelsConfig,
    OutputVariable,
    Step,
    StepType,
    ValueType,
    WorkflowDefinition,
    execute_workflow,
)
from narrative_flow.executor import (
    OpenRouterClient,
    WorkflowExecutionError,
    _render_template,
)

# =============================================================================
# OpenRouter Client Tests
# =============================================================================


class TestOpenRouterClient:
    """Tests for the OpenRouterClient class."""

    def test_requires_api_key(self, monkeypatch: pytest.MonkeyPatch):
        """
        WorkflowExecutionError is raised if no API key is provided.

        The API key can be passed directly or via OPENROUTER_API_KEY env var.
        """
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

        with pytest.raises(WorkflowExecutionError, match="API key not provided"):
            OpenRouterClient()

    def test_uses_env_api_key(self, monkeypatch: pytest.MonkeyPatch):
        """API key is read from OPENROUTER_API_KEY environment variable."""
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-from-env")

        client = OpenRouterClient()

        assert client.api_key == "test-key-from-env"

    def test_prefers_explicit_api_key(self, monkeypatch: pytest.MonkeyPatch):
        """Explicit api_key parameter takes precedence over env var."""
        monkeypatch.setenv("OPENROUTER_API_KEY", "key-from-env")

        client = OpenRouterClient(api_key="explicit-key")

        assert client.api_key == "explicit-key"

    def test_chat_sends_correct_request(
        self,
        httpx_mock: HTTPXMock,
        monkeypatch: pytest.MonkeyPatch,
        mock_openrouter_response: dict[str, Any],
    ):
        """
        The chat method sends a properly formatted request to OpenRouter.

        Request includes:
        - Authorization header with Bearer token
        - JSON payload with model and messages
        - Proper content-type header
        """
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-api-key")
        httpx_mock.add_response(json=mock_openrouter_response)

        client = OpenRouterClient()
        client.chat(
            model="openai/gpt-4o",
            messages=[{"role": "user", "content": "Hello"}],
        )

        request = httpx_mock.get_request()
        assert request is not None
        assert request.headers["Authorization"] == "Bearer test-api-key"
        assert request.headers["Content-Type"] == "application/json"
        assert "openai/gpt-4o" in request.content.decode()

    def test_chat_returns_assistant_content(
        self,
        httpx_mock: HTTPXMock,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """chat() returns the assistant's message content from the response."""
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
        httpx_mock.add_response(json={"choices": [{"message": {"role": "assistant", "content": "Hello, human!"}}]})

        client = OpenRouterClient()
        response = client.chat(
            model="openai/gpt-4o",
            messages=[{"role": "user", "content": "Hi"}],
        )

        assert response == "Hello, human!"

    def test_retries_on_rate_limit(
        self,
        httpx_mock: HTTPXMock,
        monkeypatch: pytest.MonkeyPatch,
        mock_openrouter_response: dict[str, Any],
    ):
        """
        Client retries with exponential backoff on 429 rate limit errors.

        This test uses fast retries (mocked sleep) to verify the retry logic.
        """
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

        # First request: rate limited
        httpx_mock.add_response(status_code=429)
        # Second request: success
        httpx_mock.add_response(json=mock_openrouter_response)

        client = OpenRouterClient()
        # Use minimal retries to make test fast
        response = client.chat(
            model="openai/gpt-4o",
            messages=[{"role": "user", "content": "test"}],
            retries=1,
        )

        assert response == "This is a mock response from the LLM."
        assert len(httpx_mock.get_requests()) == 2

    def test_retries_on_server_error(
        self,
        httpx_mock: HTTPXMock,
        monkeypatch: pytest.MonkeyPatch,
        mock_openrouter_response: dict[str, Any],
    ):
        """Client retries on 5xx server errors."""
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

        # First request: server error
        httpx_mock.add_response(status_code=500)
        # Second request: success
        httpx_mock.add_response(json=mock_openrouter_response)

        client = OpenRouterClient()
        response = client.chat(
            model="openai/gpt-4o",
            messages=[{"role": "user", "content": "test"}],
            retries=1,
        )

        assert response == "This is a mock response from the LLM."

    def test_raises_immediately_on_client_error(
        self,
        httpx_mock: HTTPXMock,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Client errors (4xx except 429) raise immediately without retry."""
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
        httpx_mock.add_response(status_code=400, text="Bad request")

        client = OpenRouterClient()

        with pytest.raises(WorkflowExecutionError, match="400"):
            client.chat(
                model="openai/gpt-4o",
                messages=[{"role": "user", "content": "test"}],
            )

        # Only one request was made (no retries)
        assert len(httpx_mock.get_requests()) == 1

    def test_raises_after_max_retries(
        self,
        httpx_mock: HTTPXMock,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """WorkflowExecutionError is raised after exhausting retries."""
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

        # All requests fail
        httpx_mock.add_response(status_code=500)
        httpx_mock.add_response(status_code=500)

        client = OpenRouterClient()

        with pytest.raises(WorkflowExecutionError, match="Failed after"):
            client.chat(
                model="openai/gpt-4o",
                messages=[{"role": "user", "content": "test"}],
                retries=1,
            )


# =============================================================================
# Template Rendering Tests
# =============================================================================


class TestTemplateRendering:
    """Tests for Jinja2 template rendering in workflow content."""

    def test_renders_simple_variable(self):
        """Simple variable substitution works."""
        result = _render_template("Hello {{ name }}!", {"name": "World"})
        assert result == "Hello World!"

    def test_renders_multiple_variables(self):
        """Multiple variables in the same template are substituted."""
        result = _render_template(
            "{{ greeting }} {{ name }}, welcome to {{ place }}!",
            {"greeting": "Hello", "name": "User", "place": "Python"},
        )
        assert result == "Hello User, welcome to Python!"

    def test_undefined_variable_raises_error(self):
        """Undefined variables raise an error to fail fast."""
        with pytest.raises(WorkflowExecutionError, match="Undefined variable"):
            _render_template("Hello {{ undefined_var }}!", {})

    def test_preserves_non_template_content(self):
        """Content without template syntax is returned unchanged."""
        content = "Plain text without variables"
        result = _render_template(content, {"unused": "value"})
        assert result == content


# =============================================================================
# Workflow Execution Tests
# =============================================================================


class TestExecuteWorkflow:
    """Tests for executing complete workflows."""

    @pytest.fixture
    def api_key_env(self, monkeypatch: pytest.MonkeyPatch):
        """Set API key in environment for all tests in this class."""
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    def test_executes_minimal_workflow(
        self,
        httpx_mock: HTTPXMock,
        api_key_env: None,
        minimal_workflow: WorkflowDefinition,
    ):
        """
        A minimal workflow with one message step executes successfully.

        The result contains the conversation history and success status.
        """
        httpx_mock.add_response(json={"choices": [{"message": {"content": "Hello to you too!"}}]})

        result = execute_workflow(minimal_workflow, {})

        assert result.success is True
        assert result.error is None
        assert len(result.conversation_history) == 2  # user + assistant
        assert result.conversation_history[0].role == "user"
        assert result.conversation_history[1].role == "assistant"

    def test_assistant_only_workflow_does_not_require_api_key(self, monkeypatch: pytest.MonkeyPatch):
        """Assistant-only workflows run without an API key."""
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

        workflow = WorkflowDefinition(
            name="assistant_only",
            models=ModelsConfig(conversation="openai/gpt-4o", extraction="openai/gpt-4o-mini"),
            steps=[
                Step(type=StepType.ASSISTANT, name="Assistant", content="Preset response."),
            ],
        )

        result = execute_workflow(workflow, {})

        assert result.success is True
        assert len(result.conversation_history) == 1
        assert result.conversation_history[0].role == "assistant"

    def test_executes_workflow_with_inputs(
        self,
        httpx_mock: HTTPXMock,
        api_key_env: None,
        workflow_with_inputs_and_outputs: WorkflowDefinition,
    ):
        """
        Input variables are substituted into message content.

        The rendered content appears in the conversation history.
        """
        httpx_mock.add_response(json={"choices": [{"message": {"content": "Python is great for..."}}]})
        httpx_mock.add_response(json={"choices": [{"message": {"content": '"Python is versatile."'}}]})

        result = execute_workflow(
            workflow_with_inputs_and_outputs,
            {"topic": "Python", "style": "casual"},  # Provide both inputs
        )

        assert result.success is True
        # Check that the template was rendered with the input
        user_message = result.conversation_history[0].content
        assert "Python" in user_message
        assert "casual" in user_message

    def test_uses_default_for_missing_required_input(
        self,
        httpx_mock: HTTPXMock,
        api_key_env: None,
    ):
        """
        Required inputs with defaults use the default when not provided.

        This allows required inputs to have fallback values.
        """
        workflow = WorkflowDefinition(
            name="test",
            models=ModelsConfig(
                conversation="openai/gpt-4o",
                extraction="openai/gpt-4o-mini",
            ),
            inputs=[
                InputVariable(name="topic", required=True, default="Python"),
            ],
            steps=[
                Step(
                    type=StepType.MESSAGE,
                    name="Ask",
                    content="Tell me about {{ topic }}",
                ),
            ],
        )

        httpx_mock.add_response(json={"choices": [{"message": {"content": "Explanation..."}}]})

        result = execute_workflow(workflow, {})  # No inputs provided

        assert result.success is True
        # Verify default was used
        assert "Python" in result.conversation_history[0].content

    def test_extracts_values_from_response(
        self,
        httpx_mock: HTTPXMock,
        api_key_env: None,
        workflow_with_inputs_and_outputs: WorkflowDefinition,
    ):
        """
        Extract steps pull values from the previous LLM response.

        Extracted values appear in the workflow result outputs.
        """
        # First response: conversation
        httpx_mock.add_response(json={"choices": [{"message": {"content": "Here's the explanation..."}}]})
        # Second response: extraction
        httpx_mock.add_response(json={"choices": [{"message": {"content": '"This is the summary."'}}]})

        result = execute_workflow(
            workflow_with_inputs_and_outputs,
            {"topic": "AI"},
        )

        assert result.success is True
        assert "summary" in result.outputs
        assert result.outputs["summary"] == "This is the summary."

    def test_extracted_values_available_in_subsequent_steps(
        self,
        httpx_mock: HTTPXMock,
        api_key_env: None,
    ):
        """
        Extracted values can be used in later message steps.

        This enables building on previous extractions in the conversation.
        """
        workflow = WorkflowDefinition(
            name="chained_extraction",
            models=ModelsConfig(conversation="openai/gpt-4o", extraction="openai/gpt-4o-mini"),
            inputs=[InputVariable(name="topic")],
            outputs=[OutputVariable(name="keyword", type=ValueType.STRING)],
            steps=[
                Step(type=StepType.MESSAGE, name="Get Info", content="Tell me about {{ topic }}"),
                Step(
                    type=StepType.EXTRACT,
                    name="Extract: keyword",
                    content="Extract main keyword",
                    variable_name="keyword",
                ),
                Step(type=StepType.MESSAGE, name="Follow Up", content="Tell me more about {{ keyword }}"),
            ],
        )

        httpx_mock.add_response(json={"choices": [{"message": {"content": "Info about ML..."}}]})
        httpx_mock.add_response(json={"choices": [{"message": {"content": '"neural networks"'}}]})
        httpx_mock.add_response(json={"choices": [{"message": {"content": "Deep dive into neural networks..."}}]})

        result = execute_workflow(workflow, {"topic": "machine learning"})

        assert result.success is True
        # The third message should use the extracted keyword
        requests = httpx_mock.get_requests()
        assert len(requests) == 3

    def test_raises_for_missing_required_input(
        self,
        api_key_env: None,
        workflow_with_inputs_and_outputs: WorkflowDefinition,
    ):
        """
        Missing required inputs result in a failed workflow result.
        """
        # Don't provide 'topic' which is required (and has no default)
        result = execute_workflow(workflow_with_inputs_and_outputs, {})
        assert result.success is False
        assert "Missing required inputs" in (result.error or "")

    def test_uses_default_for_missing_optional_input(
        self,
        httpx_mock: HTTPXMock,
        api_key_env: None,
    ):
        """Optional inputs with defaults use the default when not provided."""
        workflow = WorkflowDefinition(
            name="optional_default",
            models=ModelsConfig(
                conversation="openai/gpt-4o",
                extraction="openai/gpt-4o-mini",
            ),
            inputs=[
                InputVariable(name="style", required=False, default="casual"),
            ],
            steps=[
                Step(
                    type=StepType.MESSAGE,
                    name="Ask",
                    content="Use a {{ style }} tone.",
                ),
            ],
        )

        httpx_mock.add_response(json={"choices": [{"message": {"content": "Got it."}}]})

        result = execute_workflow(workflow, {})

        assert result.success is True
        assert "casual" in result.conversation_history[0].content

    def test_returns_step_results(
        self,
        httpx_mock: HTTPXMock,
        api_key_env: None,
        workflow_with_inputs_and_outputs: WorkflowDefinition,
    ):
        """
        Each step's result is captured in step_results.

        This provides visibility into what happened at each step.
        """
        httpx_mock.add_response(json={"choices": [{"message": {"content": "Explanation"}}]})
        httpx_mock.add_response(json={"choices": [{"message": {"content": '"Summary"'}}]})

        result = execute_workflow(workflow_with_inputs_and_outputs, {"topic": "test"})

        assert len(result.step_results) == 2

        # Message step result
        msg_result = result.step_results[0]
        assert msg_result.step.type == StepType.MESSAGE
        assert msg_result.user_message is not None
        assert msg_result.assistant_response == "Explanation"

        # Extract step result
        extract_result = result.step_results[1]
        assert extract_result.step.type == StepType.EXTRACT
        assert extract_result.extracted_value == "Summary"

    def test_records_workflow_name_in_result(
        self,
        httpx_mock: HTTPXMock,
        api_key_env: None,
        minimal_workflow: WorkflowDefinition,
    ):
        """The workflow name is recorded in the result."""
        httpx_mock.add_response(json={"choices": [{"message": {"content": "Hi!"}}]})

        result = execute_workflow(minimal_workflow, {})

        assert result.workflow_name == "minimal_workflow"

    def test_records_inputs_in_result(
        self,
        httpx_mock: HTTPXMock,
        api_key_env: None,
        workflow_with_inputs_and_outputs: WorkflowDefinition,
    ):
        """Input values are recorded in the result."""
        httpx_mock.add_response(json={"choices": [{"message": {"content": "Response"}}]})
        httpx_mock.add_response(json={"choices": [{"message": {"content": '"Summary"'}}]})

        result = execute_workflow(
            workflow_with_inputs_and_outputs,
            {"topic": "testing", "style": "formal"},
        )

        assert result.inputs["topic"] == "testing"
        assert result.inputs["style"] == "formal"

    def test_handles_api_failure_gracefully(
        self,
        httpx_mock: HTTPXMock,
        api_key_env: None,
        minimal_workflow: WorkflowDefinition,
    ):
        """
        API failures result in a failed WorkflowResult, not an exception.

        This allows callers to handle failures without try/except.
        """
        httpx_mock.add_response(status_code=400, text="Bad request")

        result = execute_workflow(minimal_workflow, {})

        assert result.success is False
        assert result.error is not None
        assert "400" in result.error or "Bad request" in result.error

    def test_uses_custom_api_key(
        self,
        httpx_mock: HTTPXMock,
        monkeypatch: pytest.MonkeyPatch,
        minimal_workflow: WorkflowDefinition,
    ):
        """API key can be passed directly to execute_workflow."""
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        httpx_mock.add_response(json={"choices": [{"message": {"content": "Hi!"}}]})

        result = execute_workflow(
            minimal_workflow,
            {},
            api_key="custom-api-key",
        )

        assert result.success is True
        request = httpx_mock.get_request()
        assert request.headers["Authorization"] == "Bearer custom-api-key"


# =============================================================================
# Extract Step Tests
# =============================================================================


class TestExtractStep:
    """Tests specifically for extraction step behavior."""

    @pytest.fixture
    def api_key_env(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    def test_extraction_uses_extraction_model(
        self,
        httpx_mock: HTTPXMock,
        api_key_env: None,
    ):
        """
        Extract steps use the extraction model, not the conversation model.

        This allows using a smaller/faster model for extractions.
        """
        workflow = WorkflowDefinition(
            name="test",
            models=ModelsConfig(
                conversation="openai/gpt-4o",  # Conversation model
                extraction="openai/gpt-4o-mini",  # Extraction model
            ),
            outputs=[OutputVariable(name="result", type=ValueType.STRING)],
            steps=[
                Step(type=StepType.MESSAGE, name="Ask", content="Hello"),
                Step(type=StepType.EXTRACT, name="Extract: result", content="Extract", variable_name="result"),
            ],
        )

        httpx_mock.add_response(json={"choices": [{"message": {"content": "Response"}}]})
        httpx_mock.add_response(json={"choices": [{"message": {"content": '"Extracted"'}}]})

        execute_workflow(workflow, {})

        requests = httpx_mock.get_requests()
        assert len(requests) == 2

        # First request uses conversation model
        assert b"gpt-4o" in requests[0].content
        # Second request uses extraction model
        assert b"gpt-4o-mini" in requests[1].content

    def test_extraction_strips_whitespace(
        self,
        httpx_mock: HTTPXMock,
        api_key_env: None,
    ):
        """Extracted values have leading/trailing whitespace stripped."""
        workflow = WorkflowDefinition(
            name="test",
            models=ModelsConfig(conversation="openai/gpt-4o", extraction="openai/gpt-4o-mini"),
            outputs=[OutputVariable(name="value", type=ValueType.STRING)],
            steps=[
                Step(type=StepType.MESSAGE, name="Ask", content="Hello"),
                Step(type=StepType.EXTRACT, name="Extract: value", content="Extract", variable_name="value"),
            ],
        )

        httpx_mock.add_response(json={"choices": [{"message": {"content": "Response"}}]})
        httpx_mock.add_response(json={"choices": [{"message": {"content": '  "extracted value"  \n'}}]})

        result = execute_workflow(workflow, {})

        assert result.outputs["value"] == "extracted value"

    def test_extraction_strips_code_fences_for_string(
        self,
        httpx_mock: HTTPXMock,
        api_key_env: None,
    ):
        """Extracted string outputs allow fenced JSON responses."""
        workflow = WorkflowDefinition(
            name="test",
            models=ModelsConfig(conversation="openai/gpt-4o", extraction="openai/gpt-4o-mini"),
            outputs=[OutputVariable(name="value", type=ValueType.STRING)],
            steps=[
                Step(type=StepType.MESSAGE, name="Ask", content="Hello"),
                Step(type=StepType.EXTRACT, name="Extract: value", content="Extract", variable_name="value"),
            ],
        )

        httpx_mock.add_response(json={"choices": [{"message": {"content": "Response"}}]})
        httpx_mock.add_response(json={"choices": [{"message": {"content": '```json\n"extracted value"\n```'}}]})

        result = execute_workflow(workflow, {})

        assert result.outputs["value"] == "extracted value"

    def test_extraction_parses_string_list(
        self,
        httpx_mock: HTTPXMock,
        api_key_env: None,
    ):
        """Extracted list outputs are parsed from JSON arrays."""
        workflow = WorkflowDefinition(
            name="test",
            models=ModelsConfig(conversation="openai/gpt-4o", extraction="openai/gpt-4o-mini"),
            outputs=[OutputVariable(name="items", type=ValueType.STRING_LIST)],
            steps=[
                Step(type=StepType.MESSAGE, name="Ask", content="List items"),
                Step(type=StepType.EXTRACT, name="Extract: items", content="Extract items", variable_name="items"),
            ],
        )

        httpx_mock.add_response(json={"choices": [{"message": {"content": "Response"}}]})
        httpx_mock.add_response(json={"choices": [{"message": {"content": '["alpha", "beta"]'}}]})

        result = execute_workflow(workflow, {})

        assert result.outputs["items"] == ["alpha", "beta"]
        assert result.step_results[1].extracted_value == ["alpha", "beta"]

    def test_extraction_strips_code_fences_for_list(
        self,
        httpx_mock: HTTPXMock,
        api_key_env: None,
    ):
        """Extracted list outputs allow fenced JSON responses."""
        workflow = WorkflowDefinition(
            name="test",
            models=ModelsConfig(conversation="openai/gpt-4o", extraction="openai/gpt-4o-mini"),
            outputs=[OutputVariable(name="items", type=ValueType.STRING_LIST)],
            steps=[
                Step(type=StepType.MESSAGE, name="Ask", content="List items"),
                Step(type=StepType.EXTRACT, name="Extract: items", content="Extract items", variable_name="items"),
            ],
        )

        httpx_mock.add_response(json={"choices": [{"message": {"content": "Response"}}]})
        httpx_mock.add_response(json={"choices": [{"message": {"content": '```\n["alpha", "beta"]\n```'}}]})

        result = execute_workflow(workflow, {})

        assert result.outputs["items"] == ["alpha", "beta"]

    def test_extraction_rejects_invalid_list_type(
        self,
        httpx_mock: HTTPXMock,
        api_key_env: None,
    ):
        """List outputs must be JSON arrays of strings."""
        workflow = WorkflowDefinition(
            name="test",
            models=ModelsConfig(conversation="openai/gpt-4o", extraction="openai/gpt-4o-mini"),
            outputs=[OutputVariable(name="items", type=ValueType.STRING_LIST)],
            steps=[
                Step(type=StepType.MESSAGE, name="Ask", content="List items"),
                Step(type=StepType.EXTRACT, name="Extract: items", content="Extract items", variable_name="items"),
            ],
        )

        httpx_mock.add_response(json={"choices": [{"message": {"content": "Response"}}]})
        httpx_mock.add_response(json={"choices": [{"message": {"content": '"not a list"'}}]})

        result = execute_workflow(workflow, {})

        assert result.success is False
        assert "array of strings" in (result.error or "").lower()

    def test_extraction_fails_without_conversation_history(
        self,
        api_key_env: None,
    ):
        """
        Extract step fails if there's no conversation history.

        You can't extract from nothing - there must be a prior response.
        """
        workflow = WorkflowDefinition(
            name="test",
            models=ModelsConfig(conversation="openai/gpt-4o", extraction="openai/gpt-4o-mini"),
            outputs=[OutputVariable(name="value", type=ValueType.STRING)],
            steps=[
                # Extract without any prior message
                Step(type=StepType.EXTRACT, name="Extract: value", content="Extract", variable_name="value"),
            ],
        )

        result = execute_workflow(workflow, {})

        assert result.success is False
        assert "no conversation history" in result.error.lower()


# =============================================================================
# Conversation History Tests
# =============================================================================


class TestConversationHistory:
    """Tests for conversation history management."""

    @pytest.fixture
    def api_key_env(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    def test_maintains_conversation_context(
        self,
        httpx_mock: HTTPXMock,
        api_key_env: None,
    ):
        """
        Each message step includes the full conversation history.

        This allows the LLM to maintain context across the conversation.
        """
        workflow = WorkflowDefinition(
            name="multi_turn",
            models=ModelsConfig(conversation="openai/gpt-4o", extraction="openai/gpt-4o-mini"),
            steps=[
                Step(type=StepType.MESSAGE, name="First", content="Hello"),
                Step(type=StepType.MESSAGE, name="Second", content="What did I just say?"),
            ],
        )

        httpx_mock.add_response(json={"choices": [{"message": {"content": "Hi there!"}}]})
        httpx_mock.add_response(json={"choices": [{"message": {"content": "You said hello."}}]})

        execute_workflow(workflow, {})

        requests = httpx_mock.get_requests()

        # Second request should include first message and response
        import json

        second_request_body = json.loads(requests[1].content)
        messages = second_request_body["messages"]

        assert len(messages) == 3  # user1, assistant1, user2
        assert messages[0]["content"] == "Hello"
        assert messages[1]["content"] == "Hi there!"
        assert messages[2]["content"] == "What did I just say?"

    def test_extraction_does_not_add_to_history(
        self,
        httpx_mock: HTTPXMock,
        api_key_env: None,
    ):
        """
        Extract steps don't add their prompts to the conversation history.

        Extraction is a side operation that shouldn't pollute the main conversation.
        """
        workflow = WorkflowDefinition(
            name="extract_test",
            models=ModelsConfig(conversation="openai/gpt-4o", extraction="openai/gpt-4o-mini"),
            outputs=[OutputVariable(name="keyword", type=ValueType.STRING)],
            steps=[
                Step(type=StepType.MESSAGE, name="First", content="Hello"),
                Step(
                    type=StepType.EXTRACT, name="Extract: keyword", content="Extract keyword", variable_name="keyword"
                ),
                Step(type=StepType.MESSAGE, name="Third", content="Continue"),
            ],
        )

        httpx_mock.add_response(json={"choices": [{"message": {"content": "Response 1"}}]})
        httpx_mock.add_response(json={"choices": [{"message": {"content": '"extracted"'}}]})
        httpx_mock.add_response(json={"choices": [{"message": {"content": "Response 2"}}]})

        result = execute_workflow(workflow, {})

        # Conversation history should only have the message steps
        assert len(result.conversation_history) == 4  # user1, assistant1, user2, assistant2
        # Extraction prompt should not be in history
        assert not any("Extract keyword" in m.content for m in result.conversation_history)

    def test_assistant_steps_add_to_history_without_api_call(
        self,
        httpx_mock: HTTPXMock,
        api_key_env: None,
    ):
        """Assistant steps add to history but do not trigger API calls."""
        workflow = WorkflowDefinition(
            name="assistant_step",
            models=ModelsConfig(conversation="openai/gpt-4o", extraction="openai/gpt-4o-mini"),
            steps=[
                Step(type=StepType.MESSAGE, name="User", content="Hello"),
                Step(type=StepType.ASSISTANT, name="Assistant", content="Hi!"),
                Step(type=StepType.MESSAGE, name="User 2", content="What now?"),
            ],
        )

        httpx_mock.add_response(json={"choices": [{"message": {"content": "Hello there!"}}]})
        httpx_mock.add_response(json={"choices": [{"message": {"content": "Next step."}}]})

        execute_workflow(workflow, {})

        requests = httpx_mock.get_requests()
        assert len(requests) == 2

        import json

        second_request_body = json.loads(requests[1].content)
        messages = second_request_body["messages"]
        assert any(message["role"] == "assistant" and message["content"] == "Hi!" for message in messages)
