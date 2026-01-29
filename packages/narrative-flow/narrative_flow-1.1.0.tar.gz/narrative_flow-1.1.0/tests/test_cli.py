"""Tests for the command-line interface.

These tests demonstrate how to use the narrative-flow CLI.
Reference these tests to understand:

- validate command usage
- run command with various input methods
- Error handling and exit codes
- Output formats (plain text vs JSON)
"""

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from narrative_flow.cli import cmd_run, cmd_validate, main

# =============================================================================
# Validate Command Tests
# =============================================================================


class TestValidateCommand:
    """Tests for the 'validate' subcommand."""

    def test_validates_valid_workflow(self, workflows_dir: Path, capsys):
        """
        validate command returns 0 for valid workflows.

        Output includes workflow metadata.
        """
        args = MagicMock()
        args.workflow = workflows_dir / "simple_greeting.workflow.md"

        exit_code = cmd_validate(args)

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Valid workflow" in captured.out
        assert "simple_greeting" in captured.out

    def test_validates_workflow_with_inputs(self, workflows_dir: Path, capsys):
        """validate command shows input information."""
        args = MagicMock()
        args.workflow = workflows_dir / "with_inputs.workflow.md"

        exit_code = cmd_validate(args)

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Inputs:" in captured.out
        assert "user_name" in captured.out

    def test_validates_workflow_with_outputs(self, workflows_dir: Path, capsys):
        """validate command shows output information."""
        args = MagicMock()
        args.workflow = workflows_dir / "with_extraction.workflow.md"

        exit_code = cmd_validate(args)

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Outputs:" in captured.out
        assert "best_fact" in captured.out

    def test_shows_model_configuration(self, workflows_dir: Path, capsys):
        """validate command shows model configuration."""
        args = MagicMock()
        args.workflow = workflows_dir / "simple_greeting.workflow.md"

        cmd_validate(args)

        captured = capsys.readouterr()
        assert "Conversation model:" in captured.out
        assert "Extraction model:" in captured.out

    def test_shows_step_count(self, workflows_dir: Path, capsys):
        """validate command shows number of steps."""
        args = MagicMock()
        args.workflow = workflows_dir / "multi_step_conversation.workflow.md"

        cmd_validate(args)

        captured = capsys.readouterr()
        assert "Steps:" in captured.out

    def test_returns_error_for_invalid_workflow(self, tmp_path: Path, capsys):
        """validate command returns 1 for invalid workflows."""
        invalid_workflow = tmp_path / "invalid.workflow.md"
        invalid_workflow.write_text("not valid frontmatter")

        args = MagicMock()
        args.workflow = invalid_workflow

        exit_code = cmd_validate(args)

        assert exit_code == 1
        captured = capsys.readouterr()
        assert "Invalid workflow" in captured.err

    def test_returns_error_for_missing_file(self, capsys):
        """validate command returns 1 for missing files."""
        args = MagicMock()
        args.workflow = Path("/nonexistent/workflow.md")

        exit_code = cmd_validate(args)

        assert exit_code == 1
        captured = capsys.readouterr()
        assert "Invalid workflow" in captured.err


# =============================================================================
# Run Command Tests
# =============================================================================


class TestRunCommand:
    """Tests for the 'run' subcommand."""

    @pytest.fixture
    def mock_execute(self):
        """Mock execute_workflow to avoid real API calls."""
        with patch("narrative_flow.cli.execute_workflow") as mock:
            from narrative_flow import WorkflowResult

            mock.return_value = WorkflowResult(
                workflow_name="test",
                inputs={"topic": "testing"},
                outputs={"summary": "Testing is great."},
                step_results=[],
                conversation_history=[],
                success=True,
            )
            yield mock

    def test_runs_workflow_with_cli_inputs(self, workflows_dir: Path, mock_execute, capsys):
        """
        run command accepts inputs via --input NAME=VALUE.

        Multiple inputs can be provided by repeating the flag.
        """
        args = MagicMock()
        args.workflow = workflows_dir / "with_inputs.workflow.md"
        args.inputs = ["user_name=Alice", "greeting_style=formal"]
        args.inputs_file = None
        args.log_dir = Path(".")
        args.no_log = True
        args.output_json = False

        exit_code = cmd_run(args)

        assert exit_code == 0
        # Check that inputs were passed correctly
        call_args = mock_execute.call_args
        inputs = call_args[0][1]  # Second positional arg
        assert inputs["user_name"] == "Alice"
        assert inputs["greeting_style"] == "formal"

    def test_runs_workflow_with_inputs_file(self, workflows_dir: Path, mock_execute, tmp_path: Path, capsys):
        """
        run command accepts inputs from a JSON file.

        The file should contain a JSON object with input names as keys.
        """
        inputs_file = tmp_path / "inputs.json"
        inputs_file.write_text(json.dumps({"user_name": "Bob", "greeting_style": "casual"}))

        args = MagicMock()
        args.workflow = workflows_dir / "with_inputs.workflow.md"
        args.inputs = None
        args.inputs_file = inputs_file
        args.log_dir = Path(".")
        args.no_log = True
        args.output_json = False

        exit_code = cmd_run(args)

        assert exit_code == 0
        inputs = mock_execute.call_args[0][1]
        assert inputs["user_name"] == "Bob"

    def test_cli_inputs_override_file_inputs(self, workflows_dir: Path, mock_execute, tmp_path: Path):
        """
        CLI --input flags override values from --inputs-file.

        This allows overriding specific values from a base configuration.
        """
        inputs_file = tmp_path / "inputs.json"
        inputs_file.write_text(json.dumps({"user_name": "FileUser", "greeting_style": "formal"}))

        args = MagicMock()
        args.workflow = workflows_dir / "with_inputs.workflow.md"
        args.inputs = ["user_name=CliUser"]  # Override
        args.inputs_file = inputs_file
        args.log_dir = Path(".")
        args.no_log = True
        args.output_json = False

        cmd_run(args)

        inputs = mock_execute.call_args[0][1]
        assert inputs["user_name"] == "CliUser"  # CLI wins
        assert inputs["greeting_style"] == "formal"  # From file

    def test_outputs_json_when_requested(self, workflows_dir: Path, mock_execute, capsys):
        """--output-json flag produces JSON output."""
        args = MagicMock()
        args.workflow = workflows_dir / "simple_greeting.workflow.md"
        args.inputs = None
        args.inputs_file = None
        args.log_dir = Path(".")
        args.no_log = True
        args.output_json = True

        cmd_run(args)

        captured = capsys.readouterr()
        # Find the JSON object in the output (skip the "Running workflow" line)
        lines = [line for line in captured.out.strip().split("\n") if line.strip()]
        # The JSON output spans multiple lines, so join all lines after the first
        json_lines = []
        in_json = False
        for line in lines:
            if line.strip().startswith("{"):
                in_json = True
            if in_json:
                json_lines.append(line)
        json_str = "\n".join(json_lines)
        output = json.loads(json_str)
        assert "success" in output
        assert "outputs" in output

    def test_saves_log_by_default(self, workflows_dir: Path, mock_execute, tmp_path: Path):
        """Execution log is saved by default."""
        args = MagicMock()
        args.workflow = workflows_dir / "simple_greeting.workflow.md"
        args.inputs = None
        args.inputs_file = None
        args.log_dir = tmp_path
        args.no_log = False  # Save log
        args.output_json = False

        cmd_run(args)

        log_files = list(tmp_path.glob("*.log.md"))
        assert len(log_files) == 1

    def test_no_log_skips_saving(self, workflows_dir: Path, mock_execute, tmp_path: Path):
        """--no-log flag skips saving the execution log."""
        args = MagicMock()
        args.workflow = workflows_dir / "simple_greeting.workflow.md"
        args.inputs = None
        args.inputs_file = None
        args.log_dir = tmp_path
        args.no_log = True  # Skip log
        args.output_json = False

        cmd_run(args)

        log_files = list(tmp_path.glob("*.log.md"))
        assert len(log_files) == 0

    def test_returns_error_for_invalid_input_format(self, workflows_dir: Path, capsys):
        """Returns error for malformed --input values."""
        args = MagicMock()
        args.workflow = workflows_dir / "with_inputs.workflow.md"
        args.inputs = ["invalid_no_equals_sign"]
        args.inputs_file = None

        exit_code = cmd_run(args)

        assert exit_code == 1
        captured = capsys.readouterr()
        assert "Invalid input format" in captured.err

    def test_returns_error_for_invalid_inputs_file(self, workflows_dir: Path, tmp_path: Path, capsys):
        """Returns error for malformed JSON inputs file."""
        bad_json = tmp_path / "bad.json"
        bad_json.write_text("not valid json")

        args = MagicMock()
        args.workflow = workflows_dir / "with_inputs.workflow.md"
        args.inputs = None
        args.inputs_file = bad_json

        exit_code = cmd_run(args)

        assert exit_code == 1
        captured = capsys.readouterr()
        assert "Failed to read inputs file" in captured.err

    def test_returns_error_for_failed_workflow(self, workflows_dir: Path, capsys):
        """Returns error when workflow execution fails."""
        with patch("narrative_flow.cli.execute_workflow") as mock:
            from narrative_flow import WorkflowResult

            mock.return_value = WorkflowResult(
                workflow_name="test",
                inputs={},
                outputs={},
                step_results=[],
                conversation_history=[],
                success=False,
                error="API error",
            )

            args = MagicMock()
            args.workflow = workflows_dir / "simple_greeting.workflow.md"
            args.inputs = None
            args.inputs_file = None
            args.log_dir = Path(".")
            args.no_log = True
            args.output_json = False

            exit_code = cmd_run(args)

            assert exit_code == 1
            captured = capsys.readouterr()
            assert "failed" in captured.err.lower()

    def test_shows_outputs_on_success(self, workflows_dir: Path, mock_execute, capsys):
        """Shows output values on successful execution."""
        args = MagicMock()
        args.workflow = workflows_dir / "simple_greeting.workflow.md"
        args.inputs = None
        args.inputs_file = None
        args.log_dir = Path(".")
        args.no_log = True
        args.output_json = False

        cmd_run(args)

        captured = capsys.readouterr()
        assert "Outputs:" in captured.out
        assert "summary" in captured.out

    def test_returns_error_for_missing_required_inputs(self, tmp_path: Path, capsys):
        """Missing required inputs produce a clean CLI error."""
        workflow_path = tmp_path / "required_input.workflow.md"
        workflow_path.write_text(
            """\
---
name: required_input
models:
  conversation: openai/gpt-4o
  extraction: openai/gpt-4o-mini
inputs:
  - name: topic
    required: true
---

## Step

Tell me about {{ topic }}.
"""
        )

        args = MagicMock()
        args.workflow = workflow_path
        args.inputs = None
        args.inputs_file = None
        args.log_dir = Path(".")
        args.no_log = True
        args.output_json = False

        exit_code = cmd_run(args)

        assert exit_code == 1
        captured = capsys.readouterr()
        assert "Missing required inputs" in captured.err


# =============================================================================
# Main Entry Point Tests
# =============================================================================


class TestMainEntryPoint:
    """Tests for the main() entry point."""

    def test_validates_with_validate_command(self, workflows_dir: Path, monkeypatch):
        """main() dispatches to validate command."""
        workflow_path = str(workflows_dir / "simple_greeting.workflow.md")
        monkeypatch.setattr(sys, "argv", ["narrative-flow", "validate", workflow_path])

        # main() should complete without error
        exit_code = main()
        assert exit_code == 0

    def test_requires_subcommand(self, monkeypatch, capsys):
        """main() requires a subcommand."""
        monkeypatch.setattr(sys, "argv", ["narrative-flow"])

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code != 0


# =============================================================================
# End-to-End CLI Tests
# =============================================================================


class TestCLIEndToEnd:
    """End-to-end tests running the CLI as a subprocess."""

    def test_validate_via_subprocess(self, workflows_dir: Path):
        """validate command works when run as subprocess."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "narrative_flow.cli",
                "validate",
                str(workflows_dir / "simple_greeting.workflow.md"),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "Valid workflow" in result.stdout

    def test_validate_invalid_via_subprocess(self, tmp_path: Path):
        """validate command returns error for invalid workflow."""
        invalid = tmp_path / "invalid.workflow.md"
        invalid.write_text("invalid content")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "narrative_flow.cli",
                "validate",
                str(invalid),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 1
        assert "Invalid" in result.stderr

    def test_help_shows_usage(self):
        """--help shows usage information."""
        result = subprocess.run(
            [sys.executable, "-m", "narrative_flow.cli", "--help"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "narrative-flow" in result.stdout.lower() or "workflow" in result.stdout.lower()

    def test_run_help_shows_options(self):
        """run --help shows available options."""
        result = subprocess.run(
            [sys.executable, "-m", "narrative_flow.cli", "run", "--help"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "--input" in result.stdout
        assert "--inputs-file" in result.stdout
        assert "--log-dir" in result.stdout
