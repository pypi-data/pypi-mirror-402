"""Tests for the data models.

These tests demonstrate the structure and behavior of narrative-flow's
Pydantic models. Reference these tests to understand:

- Model field types and defaults
- Validation behavior
- Helper methods on WorkflowDefinition
- StepType enum values
"""

import pytest
from pydantic import ValidationError

from narrative_flow import (
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

# =============================================================================
# StepType Enum Tests
# =============================================================================


class TestStepType:
    """Tests for the StepType enumeration."""

    def test_user_type_value(self):
        """USER step type has string value 'user'."""
        assert StepType.USER.value == "user"

    def test_assistant_type_value(self):
        """ASSISTANT step type has string value 'assistant'."""
        assert StepType.ASSISTANT.value == "assistant"

    def test_message_type_value(self):
        """MESSAGE step type has string value 'message'."""
        assert StepType.MESSAGE.value == "message"

    def test_extract_type_value(self):
        """EXTRACT step type has string value 'extract'."""
        assert StepType.EXTRACT.value == "extract"

    def test_step_type_is_string_enum(self):
        """StepType values are strings for JSON serialization."""
        assert StepType.USER == "user"
        assert StepType.ASSISTANT == "assistant"
        assert StepType.MESSAGE == "message"
        assert StepType.EXTRACT == "extract"


# =============================================================================
# InputVariable Tests
# =============================================================================


class TestInputVariable:
    """Tests for the InputVariable model."""

    def test_creates_with_name_only(self):
        """InputVariable can be created with just a name."""
        var = InputVariable(name="my_input")

        assert var.name == "my_input"
        assert var.description is None
        assert var.required is True  # Default
        assert var.default is None

    def test_creates_with_all_fields(self):
        """InputVariable can specify all fields."""
        var = InputVariable(
            name="topic",
            description="The topic to discuss",
            required=False,
            default="Python",
        )

        assert var.name == "topic"
        assert var.description == "The topic to discuss"
        assert var.required is False
        assert var.default == "Python"

    def test_required_defaults_to_true(self):
        """Inputs are required by default."""
        var = InputVariable(name="test")
        assert var.required is True

    def test_serializes_to_dict(self):
        """InputVariable can be serialized to dictionary."""
        var = InputVariable(name="test", description="Test input")
        data = var.model_dump()

        assert data["name"] == "test"
        assert data["description"] == "Test input"


# =============================================================================
# OutputVariable Tests
# =============================================================================


class TestOutputVariable:
    """Tests for the OutputVariable model."""

    def test_creates_with_name_only(self):
        """OutputVariable can be created with a name and type."""
        var = OutputVariable(name="result", type=ValueType.STRING)

        assert var.name == "result"
        assert var.description is None
        assert var.type == ValueType.STRING

    def test_creates_with_description(self):
        """OutputVariable can have a description."""
        var = OutputVariable(name="summary", description="A brief summary", type=ValueType.STRING)

        assert var.name == "summary"
        assert var.description == "A brief summary"
        assert var.type == ValueType.STRING


# =============================================================================
# ValueType Enum Tests
# =============================================================================


class TestValueType:
    """Tests for the ValueType enumeration."""

    def test_string_value(self):
        """STRING value type uses 'string'."""
        assert ValueType.STRING.value == "string"

    def test_string_list_value(self):
        """STRING_LIST value type uses 'string_list'."""
        assert ValueType.STRING_LIST.value == "string_list"


# =============================================================================
# ModelsConfig Tests
# =============================================================================


class TestModelsConfig:
    """Tests for the ModelsConfig model."""

    def test_requires_both_models(self):
        """ModelsConfig requires both conversation and extraction models."""
        config = ModelsConfig(
            conversation="openai/gpt-4o",
            extraction="openai/gpt-4o-mini",
        )

        assert config.conversation == "openai/gpt-4o"
        assert config.extraction == "openai/gpt-4o-mini"

    def test_raises_for_missing_conversation(self):
        """ValidationError is raised when conversation model is missing."""
        with pytest.raises(ValidationError):
            ModelsConfig(extraction="openai/gpt-4o-mini")

    def test_raises_for_missing_extraction(self):
        """ValidationError is raised when extraction model is missing."""
        with pytest.raises(ValidationError):
            ModelsConfig(conversation="openai/gpt-4o")


# =============================================================================
# Step Tests
# =============================================================================


class TestStep:
    """Tests for the Step model."""

    def test_creates_message_step(self):
        """MESSAGE step has type, name, and content."""
        step = Step(
            type=StepType.MESSAGE,
            name="Greeting",
            content="Hello, please respond.",
        )

        assert step.type == StepType.MESSAGE
        assert step.name == "Greeting"
        assert step.content == "Hello, please respond."
        assert step.variable_name is None  # Not used for MESSAGE

    def test_creates_extract_step(self):
        """EXTRACT step includes variable_name for storing the result."""
        step = Step(
            type=StepType.EXTRACT,
            name="Extract: summary",
            content="Extract a summary.",
            variable_name="summary",
        )

        assert step.type == StepType.EXTRACT
        assert step.name == "Extract: summary"
        assert step.content == "Extract a summary."
        assert step.variable_name == "summary"

    def test_variable_name_optional_for_message(self):
        """variable_name is optional (typically used only for EXTRACT)."""
        step = Step(
            type=StepType.MESSAGE,
            name="Test",
            content="Test content",
        )
        assert step.variable_name is None


# =============================================================================
# WorkflowDefinition Tests
# =============================================================================


class TestWorkflowDefinition:
    """Tests for the WorkflowDefinition model."""

    def test_creates_minimal_workflow(self):
        """Workflow can be created with minimal required fields."""
        workflow = WorkflowDefinition(
            name="test_workflow",
            models=ModelsConfig(
                conversation="openai/gpt-4o",
                extraction="openai/gpt-4o-mini",
            ),
        )

        assert workflow.name == "test_workflow"
        assert workflow.description is None
        assert workflow.retries == 3  # Default
        assert workflow.inputs == []
        assert workflow.outputs == []
        assert workflow.steps == []

    def test_creates_full_workflow(self):
        """Workflow can specify all fields."""
        workflow = WorkflowDefinition(
            name="full_workflow",
            description="A complete workflow",
            models=ModelsConfig(
                conversation="openai/gpt-4o",
                extraction="openai/gpt-4o-mini",
            ),
            retries=5,
            inputs=[InputVariable(name="input1")],
            outputs=[OutputVariable(name="output1", type=ValueType.STRING)],
            steps=[
                Step(type=StepType.MESSAGE, name="Step 1", content="Hello"),
            ],
        )

        assert workflow.name == "full_workflow"
        assert workflow.description == "A complete workflow"
        assert workflow.retries == 5
        assert len(workflow.inputs) == 1
        assert len(workflow.outputs) == 1
        assert len(workflow.steps) == 1

    def test_retries_must_be_non_negative(self):
        """retries field must be >= 0."""
        with pytest.raises(ValidationError):
            WorkflowDefinition(
                name="test",
                models=ModelsConfig(
                    conversation="openai/gpt-4o",
                    extraction="openai/gpt-4o-mini",
                ),
                retries=-1,
            )

    def test_get_required_inputs_returns_required_only(self):
        """
        get_required_inputs() returns names of required inputs only.

        Useful for validating that all required inputs are provided.
        """
        workflow = WorkflowDefinition(
            name="test",
            models=ModelsConfig(
                conversation="openai/gpt-4o",
                extraction="openai/gpt-4o-mini",
            ),
            inputs=[
                InputVariable(name="required1", required=True),
                InputVariable(name="optional1", required=False),
                InputVariable(name="required2", required=True),
            ],
        )

        required = workflow.get_required_inputs()

        assert required == ["required1", "required2"]
        assert "optional1" not in required

    def test_get_required_inputs_empty_when_all_optional(self):
        """get_required_inputs() returns empty list when all inputs are optional."""
        workflow = WorkflowDefinition(
            name="test",
            models=ModelsConfig(
                conversation="openai/gpt-4o",
                extraction="openai/gpt-4o-mini",
            ),
            inputs=[
                InputVariable(name="opt1", required=False, default="a"),
                InputVariable(name="opt2", required=False, default="b"),
            ],
        )

        assert workflow.get_required_inputs() == []

    def test_get_output_names(self):
        """get_output_names() returns all output variable names."""
        workflow = WorkflowDefinition(
            name="test",
            models=ModelsConfig(
                conversation="openai/gpt-4o",
                extraction="openai/gpt-4o-mini",
            ),
            outputs=[
                OutputVariable(name="summary", type=ValueType.STRING),
                OutputVariable(name="keywords", type=ValueType.STRING_LIST),
            ],
        )

        output_names = workflow.get_output_names()

        assert output_names == ["summary", "keywords"]

    def test_get_output_names_empty_when_no_outputs(self):
        """get_output_names() returns empty list when no outputs defined."""
        workflow = WorkflowDefinition(
            name="test",
            models=ModelsConfig(
                conversation="openai/gpt-4o",
                extraction="openai/gpt-4o-mini",
            ),
        )

        assert workflow.get_output_names() == []


# =============================================================================
# Message Tests
# =============================================================================


class TestMessage:
    """Tests for the Message model."""

    def test_creates_user_message(self):
        """Message can represent a user message."""
        msg = Message(role="user", content="Hello, assistant!")

        assert msg.role == "user"
        assert msg.content == "Hello, assistant!"

    def test_creates_assistant_message(self):
        """Message can represent an assistant message."""
        msg = Message(role="assistant", content="Hello, user!")

        assert msg.role == "assistant"
        assert msg.content == "Hello, user!"


# =============================================================================
# StepResult Tests
# =============================================================================


class TestStepResult:
    """Tests for the StepResult model."""

    def test_creates_message_step_result(self):
        """StepResult captures message step execution."""
        step = Step(type=StepType.MESSAGE, name="Test", content="Hello")
        result = StepResult(
            step=step,
            user_message="Hello (rendered)",
            assistant_response="Hi there!",
        )

        assert result.step == step
        assert result.user_message == "Hello (rendered)"
        assert result.assistant_response == "Hi there!"
        assert result.extracted_value is None

    def test_creates_extract_step_result(self):
        """StepResult captures extraction step execution."""
        step = Step(
            type=StepType.EXTRACT,
            name="Extract: key",
            content="Extract the key",
            variable_name="key",
        )
        result = StepResult(
            step=step,
            extracted_value="the extracted value",
        )

        assert result.step == step
        assert result.extracted_value == "the extracted value"
        assert result.user_message is None
        assert result.assistant_response is None


# =============================================================================
# WorkflowResult Tests
# =============================================================================


class TestWorkflowResult:
    """Tests for the WorkflowResult model."""

    def test_creates_successful_result(self):
        """WorkflowResult captures successful execution."""
        result = WorkflowResult(
            workflow_name="test_workflow",
            inputs={"topic": "Python"},
            outputs={"summary": "Python is great"},
            step_results=[],
            conversation_history=[],
            success=True,
            error=None,
        )

        assert result.workflow_name == "test_workflow"
        assert result.inputs == {"topic": "Python"}
        assert result.outputs == {"summary": "Python is great"}
        assert result.success is True
        assert result.error is None

    def test_creates_failed_result(self):
        """WorkflowResult captures failed execution with error message."""
        result = WorkflowResult(
            workflow_name="failed_workflow",
            inputs={},
            outputs={},
            step_results=[],
            conversation_history=[],
            success=False,
            error="API connection failed",
        )

        assert result.success is False
        assert result.error == "API connection failed"

    def test_includes_conversation_history(self):
        """WorkflowResult includes full conversation history."""
        result = WorkflowResult(
            workflow_name="test",
            inputs={},
            outputs={},
            step_results=[],
            conversation_history=[
                Message(role="user", content="Hello"),
                Message(role="assistant", content="Hi!"),
            ],
            success=True,
        )

        assert len(result.conversation_history) == 2
        assert result.conversation_history[0].role == "user"
        assert result.conversation_history[1].role == "assistant"

    def test_includes_step_results(self):
        """WorkflowResult includes results for each executed step."""
        step = Step(type=StepType.MESSAGE, name="Test", content="Hello")
        step_result = StepResult(
            step=step,
            user_message="Hello",
            assistant_response="Hi!",
        )

        result = WorkflowResult(
            workflow_name="test",
            inputs={},
            outputs={},
            step_results=[step_result],
            conversation_history=[],
            success=True,
        )

        assert len(result.step_results) == 1
        assert result.step_results[0].step.name == "Test"
