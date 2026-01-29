"""Tests for the execution logger.

These tests demonstrate how narrative-flow generates execution logs.
Reference these tests to understand:

- Log format and structure
- Input truncation behavior
- File saving functionality
- How different step types are logged
"""

import re
from pathlib import Path

import pytest

from narrative_flow import (
    Step,
    StepResult,
    StepType,
    WorkflowResult,
    generate_log,
    save_log,
)

# =============================================================================
# Log Generation Tests
# =============================================================================


class TestGenerateLog:
    """Tests for the generate_log function."""

    def test_generates_markdown_header(self, successful_workflow_result: WorkflowResult):
        """
        Logs include a header with workflow name, timestamp, and status.

        The header provides quick context for the execution.
        """
        log = generate_log(successful_workflow_result)

        assert "# Workflow Execution Log" in log
        assert "**Workflow:** test_workflow" in log
        assert "**Timestamp:**" in log
        assert "Success" in log

    def test_generates_inputs_section(self, successful_workflow_result: WorkflowResult):
        """
        Logs include an Inputs section listing all provided inputs.

        Input values are displayed in code blocks.
        """
        log = generate_log(successful_workflow_result)

        assert "## Inputs" in log
        assert "### topic" in log
        assert "Python testing" in log

    def test_generates_outputs_section(self, successful_workflow_result: WorkflowResult):
        """
        Logs include an Outputs section listing all extracted outputs.

        Output values are displayed in code blocks.
        """
        log = generate_log(successful_workflow_result)

        assert "## Outputs" in log
        assert "### summary" in log
        assert "Testing ensures code quality." in log

    def test_logs_list_outputs_as_json(self):
        """List outputs are rendered as JSON arrays."""
        result = WorkflowResult(
            workflow_name="list_output",
            inputs={},
            outputs={"items": ["alpha", "beta"]},
            step_results=[],
            conversation_history=[],
            success=True,
        )

        log = generate_log(result)

        assert "### items" in log
        assert '"alpha"' in log
        assert '"beta"' in log

    def test_generates_conversation_section(self, successful_workflow_result: WorkflowResult):
        """
        Logs include a Conversation section with each step's details.

        Message steps show user/assistant exchanges.
        """
        log = generate_log(successful_workflow_result)

        assert "## Conversation" in log
        assert "**User:**" in log
        assert "**Assistant:**" in log
        assert "Explain Python testing" in log

    def test_shows_extract_steps(self, successful_workflow_result: WorkflowResult):
        """
        Extract steps show the extraction instruction and extracted value.

        This helps debug extraction issues.
        """
        log = generate_log(successful_workflow_result)

        assert "Extract: summary" in log
        assert "**Extraction Instruction:**" in log
        assert "**Extracted Value" in log

    def test_shows_failed_status(self, failed_workflow_result: WorkflowResult):
        """Failed workflows show failure status and error message."""
        log = generate_log(failed_workflow_result)

        assert "Failed" in log
        assert "**Error:**" in log
        assert "API connection failed" in log

    def test_shows_no_inputs_message(self):
        """When there are no inputs, shows 'No inputs' message."""
        result = WorkflowResult(
            workflow_name="no_inputs",
            inputs={},
            outputs={},
            step_results=[],
            conversation_history=[],
            success=True,
        )

        log = generate_log(result)

        assert "*No inputs*" in log

    def test_shows_no_outputs_message(self):
        """When there are no outputs, shows 'No outputs' message."""
        result = WorkflowResult(
            workflow_name="no_outputs",
            inputs={"some": "input"},
            outputs={},
            step_results=[],
            conversation_history=[],
            success=True,
        )

        log = generate_log(result)

        assert "*No outputs*" in log


# =============================================================================
# Input Truncation Tests
# =============================================================================


class TestInputTruncation:
    """Tests for input value truncation in logs."""

    def test_truncates_long_inputs(self):
        """
        Long input values are truncated to prevent huge logs.

        The default truncation is 500 characters.
        """
        long_input = "x" * 600  # Longer than default 500
        result = WorkflowResult(
            workflow_name="test",
            inputs={"long_value": long_input},
            outputs={},
            step_results=[],
            conversation_history=[],
            success=True,
        )

        log = generate_log(result)

        assert "... [truncated]" in log
        assert "x" * 500 in log  # First 500 chars present
        assert "x" * 600 not in log  # Full value not present

    def test_custom_truncation_limit(self):
        """Truncation limit can be customized."""
        input_value = "x" * 100
        result = WorkflowResult(
            workflow_name="test",
            inputs={"value": input_value},
            outputs={},
            step_results=[],
            conversation_history=[],
            success=True,
        )

        log = generate_log(result, truncate_inputs=50)

        assert "... [truncated]" in log
        assert "x" * 50 in log

    def test_no_truncation_when_none(self):
        """Truncation can be disabled by passing None."""
        input_value = "x" * 1000
        result = WorkflowResult(
            workflow_name="test",
            inputs={"value": input_value},
            outputs={},
            step_results=[],
            conversation_history=[],
            success=True,
        )

        log = generate_log(result, truncate_inputs=None)

        assert "[truncated]" not in log
        assert "x" * 1000 in log

    def test_no_truncation_for_short_inputs(self):
        """Short inputs are not truncated."""
        result = WorkflowResult(
            workflow_name="test",
            inputs={"short": "hello"},
            outputs={},
            step_results=[],
            conversation_history=[],
            success=True,
        )

        log = generate_log(result)

        assert "[truncated]" not in log
        assert "hello" in log


# =============================================================================
# Step Result Logging Tests
# =============================================================================


class TestStepResultLogging:
    """Tests for how step results are logged."""

    def test_logs_message_step_with_user_and_assistant(self):
        """Message steps show both user message and assistant response."""
        step = Step(type=StepType.MESSAGE, name="Test Step", content="Hello")
        step_result = StepResult(
            step=step,
            user_message="Hello there!",
            assistant_response="Hi, how can I help?",
        )
        result = WorkflowResult(
            workflow_name="test",
            inputs={},
            outputs={},
            step_results=[step_result],
            conversation_history=[],
            success=True,
        )

        log = generate_log(result)

        assert "### Test Step" in log
        assert "**User:**" in log
        assert "Hello there!" in log
        assert "**Assistant:**" in log
        assert "Hi, how can I help?" in log

    def test_logs_extract_step_with_instruction_and_value(self):
        """Extract steps show instruction and extracted value."""
        step = Step(
            type=StepType.EXTRACT,
            name="Extract: keyword",
            content="Extract the main keyword",
            variable_name="keyword",
        )
        step_result = StepResult(
            step=step,
            extracted_value="testing",
        )
        result = WorkflowResult(
            workflow_name="test",
            inputs={},
            outputs={},
            step_results=[step_result],
            conversation_history=[],
            success=True,
        )

        log = generate_log(result)

        assert "### Extract: keyword" in log
        assert "**Extraction Instruction:**" in log
        assert "Extract the main keyword" in log
        assert "**Extracted Value (`keyword`):**" in log
        assert "testing" in log

    def test_logs_extract_step_with_list_value(self):
        """Extract steps render list values as JSON arrays."""
        step = Step(
            type=StepType.EXTRACT,
            name="Extract: items",
            content="Extract items",
            variable_name="items",
        )
        step_result = StepResult(
            step=step,
            extracted_value=["alpha", "beta"],
        )
        result = WorkflowResult(
            workflow_name="test",
            inputs={},
            outputs={},
            step_results=[step_result],
            conversation_history=[],
            success=True,
        )

        log = generate_log(result)

        assert '"alpha"' in log
        assert '"beta"' in log

    def test_logs_assistant_step_only(self):
        """Assistant steps show only the assistant content."""
        step = Step(type=StepType.ASSISTANT, name="Assistant", content="Preset response")
        step_result = StepResult(
            step=step,
            assistant_response="Preset response",
        )
        result = WorkflowResult(
            workflow_name="test",
            inputs={},
            outputs={},
            step_results=[step_result],
            conversation_history=[],
            success=True,
        )

        log = generate_log(result)

        assert "### Assistant" in log
        assert "**Assistant:**" in log
        assert "Preset response" in log

    def test_handles_missing_user_message(self):
        """Handles case where user_message is None."""
        step = Step(type=StepType.MESSAGE, name="Test", content="Hello")
        step_result = StepResult(
            step=step,
            user_message=None,
            assistant_response="Response",
        )
        result = WorkflowResult(
            workflow_name="test",
            inputs={},
            outputs={},
            step_results=[step_result],
            conversation_history=[],
            success=True,
        )

        log = generate_log(result)

        assert "*No message*" in log

    def test_handles_missing_assistant_response(self):
        """Handles case where assistant_response is None."""
        step = Step(type=StepType.MESSAGE, name="Test", content="Hello")
        step_result = StepResult(
            step=step,
            user_message="Hello",
            assistant_response=None,
        )
        result = WorkflowResult(
            workflow_name="test",
            inputs={},
            outputs={},
            step_results=[step_result],
            conversation_history=[],
            success=True,
        )

        log = generate_log(result)

        assert "*No response*" in log

    def test_handles_missing_extracted_value(self):
        """Handles case where extracted_value is None."""
        step = Step(
            type=StepType.EXTRACT,
            name="Extract: val",
            content="Extract",
            variable_name="val",
        )
        step_result = StepResult(
            step=step,
            extracted_value=None,
        )
        result = WorkflowResult(
            workflow_name="test",
            inputs={},
            outputs={},
            step_results=[step_result],
            conversation_history=[],
            success=True,
        )

        log = generate_log(result)

        assert "*No value*" in log


# =============================================================================
# Log Saving Tests
# =============================================================================


class TestSaveLog:
    """Tests for the save_log function."""

    def test_saves_to_specified_directory(self, successful_workflow_result: WorkflowResult, tmp_path: Path):
        """Logs are saved to the specified output directory."""
        log_path = save_log(
            successful_workflow_result,
            output_dir=tmp_path,
            filename="test.log.md",
        )

        assert log_path.exists()
        assert log_path.parent == tmp_path
        assert log_path.name == "test.log.md"

    def test_creates_directory_if_not_exists(self, successful_workflow_result: WorkflowResult, tmp_path: Path):
        """Output directory is created if it doesn't exist."""
        nested_dir = tmp_path / "nested" / "logs"

        log_path = save_log(
            successful_workflow_result,
            output_dir=nested_dir,
            filename="test.log.md",
        )

        assert nested_dir.exists()
        assert log_path.exists()

    def test_auto_generates_filename(self, successful_workflow_result: WorkflowResult, tmp_path: Path):
        """
        Filename is auto-generated if not provided.

        Format: {workflow_name}_{timestamp}.log.md
        """
        log_path = save_log(
            successful_workflow_result,
            output_dir=tmp_path,
        )

        assert log_path.exists()
        assert log_path.name.startswith("test_workflow_")
        assert log_path.name.endswith(".log.md")
        # Check timestamp format (YYYYMMDD_HHMMSS)
        assert re.search(r"\d{8}_\d{6}", log_path.name)

    def test_writes_correct_content(self, successful_workflow_result: WorkflowResult, tmp_path: Path):
        """Saved file contains the generated log content."""
        log_path = save_log(
            successful_workflow_result,
            output_dir=tmp_path,
            filename="test.log.md",
        )

        content = log_path.read_text()

        assert "# Workflow Execution Log" in content
        assert "test_workflow" in content
        assert "Python testing" in content

    def test_respects_truncate_inputs(self, tmp_path: Path):
        """save_log passes truncate_inputs to generate_log."""
        long_input = "x" * 100
        result = WorkflowResult(
            workflow_name="test",
            inputs={"value": long_input},
            outputs={},
            step_results=[],
            conversation_history=[],
            success=True,
        )

        log_path = save_log(
            result,
            output_dir=tmp_path,
            filename="test.log.md",
            truncate_inputs=50,
        )

        content = log_path.read_text()
        assert "[truncated]" in content

    def test_returns_path_object(self, successful_workflow_result: WorkflowResult, tmp_path: Path):
        """save_log returns a Path object for the saved file."""
        result = save_log(
            successful_workflow_result,
            output_dir=tmp_path,
        )

        assert isinstance(result, Path)

    def test_sanitizes_workflow_name_in_auto_filename(self, tmp_path: Path):
        """Auto-generated filenames are sanitized to prevent path traversal."""
        result = WorkflowResult(
            workflow_name="../unsafe/../../name",
            inputs={},
            outputs={},
            step_results=[],
            conversation_history=[],
            success=True,
        )

        log_path = save_log(result, output_dir=tmp_path)

        assert log_path.parent == tmp_path
        assert ".." not in log_path.name
        assert "/" not in log_path.name

    def test_rejects_filename_with_path_separators(self, successful_workflow_result: WorkflowResult, tmp_path: Path):
        """save_log rejects filenames that include path separators."""
        with pytest.raises(ValueError, match="filename must be a simple file name"):
            save_log(
                successful_workflow_result,
                output_dir=tmp_path,
                filename="../bad.log.md",
            )


# =============================================================================
# Log Format Tests
# =============================================================================


class TestLogFormat:
    """Tests for the log format structure."""

    def test_log_is_valid_markdown(self, successful_workflow_result: WorkflowResult):
        """Generated log is valid Markdown structure."""
        log = generate_log(successful_workflow_result)

        # Check for proper heading hierarchy
        assert log.count("# Workflow Execution Log") == 1  # H1
        assert "## Inputs" in log  # H2
        assert "## Outputs" in log
        assert "## Conversation" in log
        assert "### " in log  # H3 for individual items

    def test_uses_code_blocks_for_values(self, successful_workflow_result: WorkflowResult):
        """Values are wrapped in code blocks for formatting."""
        log = generate_log(successful_workflow_result)

        # Count code block markers
        code_block_count = log.count("```")

        # Should have pairs of ``` for each value block
        assert code_block_count >= 4  # At least 2 complete blocks

    def test_uses_horizontal_rules_between_steps(self, successful_workflow_result: WorkflowResult):
        """Horizontal rules separate conversation steps."""
        log = generate_log(successful_workflow_result)

        assert "---" in log

    def test_sections_appear_in_order(self, successful_workflow_result: WorkflowResult):
        """Log sections appear in expected order."""
        log = generate_log(successful_workflow_result)

        header_pos = log.find("# Workflow Execution Log")
        inputs_pos = log.find("## Inputs")
        outputs_pos = log.find("## Outputs")
        conversation_pos = log.find("## Conversation")

        assert header_pos < inputs_pos
        assert inputs_pos < outputs_pos
        assert outputs_pos < conversation_pos
