"""Tests for the workflow parser.

These tests demonstrate how narrative-flow parses .workflow.md files into
structured WorkflowDefinition objects. Reference these tests to understand:

- Valid workflow file structure
- How inputs and outputs are parsed
- Message vs Extract step parsing
- Error handling for invalid workflows
"""

from pathlib import Path

import pytest

from narrative_flow import StepType, ValueType, parse_workflow
from narrative_flow.parser import WorkflowParseError

# =============================================================================
# Parsing Valid Workflows
# =============================================================================


class TestParseValidWorkflows:
    """Tests for successfully parsing valid workflow files."""

    def test_parses_minimal_workflow(self, minimal_workflow_content: str):
        """
        A workflow with just a name, models, and one step is valid.

        This is the simplest possible workflow structure.
        """
        workflow = parse_workflow(minimal_workflow_content)

        assert workflow.name == "minimal_workflow"
        assert workflow.description == "A minimal workflow for testing"
        assert workflow.models.conversation == "openai/gpt-4o"
        assert workflow.models.extraction == "openai/gpt-4o-mini"
        assert len(workflow.steps) == 1
        assert workflow.steps[0].name == "Say Hello"
        assert workflow.steps[0].content == "Hello, world!"

    def test_parses_workflow_from_file(self, workflows_dir: Path):
        """
        Workflows can be parsed from file paths.

        The parser accepts either a Path object or a string path.
        """
        workflow = parse_workflow(workflows_dir / "simple_greeting.workflow.md")

        assert workflow.name == "simple_greeting"
        assert len(workflow.steps) == 1

    def test_parses_workflow_with_inputs(self, workflow_with_inputs_and_outputs_content: str):
        """
        Inputs are parsed with name, description, required flag, and default.

        Required defaults to True if not specified.
        """
        workflow = parse_workflow(workflow_with_inputs_and_outputs_content)

        assert len(workflow.inputs) == 2

        # Required input
        topic_input = workflow.inputs[0]
        assert topic_input.name == "topic"
        assert topic_input.description == "The topic to explain"
        assert topic_input.required is True
        assert topic_input.default is None

        # Optional input with default
        style_input = workflow.inputs[1]
        assert style_input.name == "style"
        assert style_input.required is False
        assert style_input.default == "casual"

    def test_parses_workflow_with_outputs(self, workflow_with_inputs_and_outputs_content: str):
        """
        Outputs are parsed with name and description.

        Each output must have a corresponding Extract step.
        """
        workflow = parse_workflow(workflow_with_inputs_and_outputs_content)

        assert len(workflow.outputs) == 1
        assert workflow.outputs[0].name == "summary"
        assert workflow.outputs[0].description == "A brief summary of the topic"
        assert workflow.outputs[0].type == ValueType.STRING

    def test_parses_message_steps(self, minimal_workflow_content: str):
        """
        Message steps use regular headings (## Step Name).

        They contain the user message content to send to the LLM.
        """
        workflow = parse_workflow(minimal_workflow_content)

        step = workflow.steps[0]
        assert step.type == StepType.MESSAGE
        assert step.name == "Say Hello"
        assert step.variable_name is None

    def test_parses_extract_steps(self, workflow_with_inputs_and_outputs_content: str):
        """
        Extract steps use the format: ## Extract: variable_name

        They extract a value from the previous LLM response.
        """
        workflow = parse_workflow(workflow_with_inputs_and_outputs_content)

        extract_step = workflow.steps[1]
        assert extract_step.type == StepType.EXTRACT
        assert extract_step.name == "Extract: summary"
        assert extract_step.variable_name == "summary"
        assert "one-sentence summary" in extract_step.content

    def test_parses_user_and_assistant_steps(self):
        """User and assistant headings are parsed as explicit roles."""
        content = """\
---
name: roles_workflow
models:
  conversation: openai/gpt-4o
  extraction: openai/gpt-4o-mini
---

## User

Hello!

## Assistant

Hi there.

## Follow Up

What is next?
"""
        workflow = parse_workflow(content)

        assert workflow.steps[0].type == StepType.USER
        assert workflow.steps[1].type == StepType.ASSISTANT
        assert workflow.steps[2].type == StepType.MESSAGE

    def test_parses_multi_step_workflow(self, multi_step_workflow_content: str):
        """
        Workflows can have multiple message and extract steps.

        Steps are parsed in the order they appear in the file.
        """
        workflow = parse_workflow(multi_step_workflow_content)

        assert len(workflow.steps) == 5

        # Check step types in order
        expected_types = [
            StepType.MESSAGE,  # Introduction
            StepType.MESSAGE,  # Strength Question
            StepType.EXTRACT,  # Extract: strength
            StepType.MESSAGE,  # Improvement Question
            StepType.EXTRACT,  # Extract: improvement
        ]
        for step, expected_type in zip(workflow.steps, expected_types, strict=True):
            assert step.type == expected_type

    def test_parses_default_retries(self, minimal_workflow_content: str):
        """Retries defaults to 3 if not specified in frontmatter."""
        workflow = parse_workflow(minimal_workflow_content)
        assert workflow.retries == 3

    def test_parses_custom_retries(self):
        """Custom retry count can be specified in frontmatter."""
        content = """\
---
name: custom_retries
models:
  conversation: openai/gpt-4o
  extraction: openai/gpt-4o-mini
retries: 5
---

## Step

Hello
"""
        workflow = parse_workflow(content)
        assert workflow.retries == 5

    def test_parses_workflow_without_description(self):
        """Description is optional in frontmatter."""
        content = """\
---
name: no_description
models:
  conversation: openai/gpt-4o
  extraction: openai/gpt-4o-mini
---

## Step

Hello
"""
        workflow = parse_workflow(content)
        assert workflow.name == "no_description"
        assert workflow.description is None

    def test_parses_extract_step_case_insensitive(self):
        """The 'Extract:' prefix is case-insensitive."""
        content = """\
---
name: case_insensitive
models:
  conversation: openai/gpt-4o
  extraction: openai/gpt-4o-mini
---

## Message

Hello

## EXTRACT: result

Get the result.
"""
        workflow = parse_workflow(content)

        assert workflow.steps[1].type == StepType.EXTRACT
        assert workflow.steps[1].variable_name == "result"

    def test_parses_workflow_with_empty_inputs_list(self):
        """Workflow with no inputs defined is valid."""
        content = """\
---
name: no_inputs
models:
  conversation: openai/gpt-4o
  extraction: openai/gpt-4o-mini
inputs: []
---

## Step

Hello
"""
        workflow = parse_workflow(content)
        assert workflow.inputs == []

    def test_preserves_step_content_whitespace(self):
        """Multi-line step content preserves formatting."""
        content = """\
---
name: multiline
models:
  conversation: openai/gpt-4o
  extraction: openai/gpt-4o-mini
---

## Multi-line Step

This is line one.

This is line two with a blank line above.
"""
        workflow = parse_workflow(content)

        assert "line one" in workflow.steps[0].content
        assert "line two" in workflow.steps[0].content


# =============================================================================
# Parsing From Different Sources
# =============================================================================


class TestParseFromDifferentSources:
    """Tests for parsing workflows from various source types."""

    def test_parses_from_string_content(self, minimal_workflow_content: str):
        """
        Workflow content can be passed directly as a string.

        The parser detects string content by the presence of '---' at the start.
        """
        workflow = parse_workflow(minimal_workflow_content)
        assert workflow.name == "minimal_workflow"

    def test_parses_from_path_object(self, workflows_dir: Path):
        """Workflow can be parsed from a pathlib.Path object."""
        path = workflows_dir / "simple_greeting.workflow.md"
        workflow = parse_workflow(path)
        assert workflow.name == "simple_greeting"

    def test_parses_from_string_path(self, workflows_dir: Path):
        """Workflow can be parsed from a string file path."""
        path = str(workflows_dir / "simple_greeting.workflow.md")
        workflow = parse_workflow(path)
        assert workflow.name == "simple_greeting"

    def test_parses_example_workflows(self, examples_dir: Path):
        """All example workflows in the examples directory are valid."""
        for workflow_file in examples_dir.glob("*.workflow.md"):
            workflow = parse_workflow(workflow_file)
            assert workflow.name  # Has a name
            assert workflow.models.conversation  # Has conversation model
            assert workflow.models.extraction  # Has extraction model


# =============================================================================
# Helper Methods
# =============================================================================


class TestWorkflowHelperMethods:
    """Tests for WorkflowDefinition helper methods."""

    def test_get_required_inputs(self, workflow_with_inputs_and_outputs_content: str):
        """
        get_required_inputs() returns only the names of required inputs.

        Optional inputs (required=False) are excluded.
        """
        workflow = parse_workflow(workflow_with_inputs_and_outputs_content)

        required = workflow.get_required_inputs()

        assert required == ["topic"]
        assert "style" not in required  # Optional input excluded

    def test_get_output_names(self, workflow_with_inputs_and_outputs_content: str):
        """get_output_names() returns the names of all declared outputs."""
        workflow = parse_workflow(workflow_with_inputs_and_outputs_content)

        output_names = workflow.get_output_names()

        assert output_names == ["summary"]

    def test_get_required_inputs_when_all_optional(self):
        """get_required_inputs() returns empty list when all inputs are optional."""
        content = """\
---
name: all_optional
models:
  conversation: openai/gpt-4o
  extraction: openai/gpt-4o-mini
inputs:
  - name: optional_one
    required: false
    default: default1
  - name: optional_two
    required: false
    default: default2
---

## Step

Hello {{ optional_one }} and {{ optional_two }}
"""
        workflow = parse_workflow(content)
        assert workflow.get_required_inputs() == []


# =============================================================================
# Error Handling
# =============================================================================


class TestParseErrors:
    """Tests for error handling when parsing invalid workflows."""

    def test_raises_for_nonexistent_file(self):
        """
        WorkflowParseError is raised when the file doesn't exist.

        The error message includes the file path for debugging.
        """
        with pytest.raises(WorkflowParseError, match="not found"):
            parse_workflow("/nonexistent/path/workflow.md")

    def test_raises_for_missing_name(self, workflow_missing_name: str):
        """WorkflowParseError is raised when 'name' field is missing."""
        with pytest.raises(WorkflowParseError, match="Missing required field 'name'"):
            parse_workflow(workflow_missing_name)

    def test_raises_for_missing_models(self, workflow_missing_models: str):
        """WorkflowParseError is raised when 'models' field is missing."""
        with pytest.raises(WorkflowParseError, match="Missing required field 'models'"):
            parse_workflow(workflow_missing_models)

    def test_raises_for_missing_conversation_model(self, workflow_missing_conversation_model: str):
        """WorkflowParseError is raised when 'conversation' model is missing."""
        with pytest.raises(WorkflowParseError, match="Missing 'conversation'"):
            parse_workflow(workflow_missing_conversation_model)

    def test_raises_for_missing_extraction_model(self, workflow_missing_extraction_model: str):
        """WorkflowParseError is raised when 'extraction' model is missing."""
        with pytest.raises(WorkflowParseError, match="Missing 'extraction'"):
            parse_workflow(workflow_missing_extraction_model)

    def test_raises_for_invalid_variable_name(self, workflow_invalid_extract_varname: str):
        """
        WorkflowParseError is raised for invalid variable names.

        Variable names must be valid Python identifiers (alphanumeric + underscore,
        starting with letter or underscore).
        """
        with pytest.raises(WorkflowParseError, match="Invalid variable name"):
            parse_workflow(workflow_invalid_extract_varname)

    def test_raises_for_empty_extract_variable_name(self, workflow_empty_extract_varname: str):
        """WorkflowParseError is raised when Extract step has no variable name."""
        with pytest.raises(WorkflowParseError, match="missing variable name"):
            parse_workflow(workflow_empty_extract_varname)

    def test_raises_for_output_without_extract(self, workflow_missing_extract_for_output: str):
        """
        WorkflowParseError is raised when an output has no corresponding Extract step.

        Every declared output must have an Extract step that populates it.
        """
        with pytest.raises(WorkflowParseError, match="no Extract step found"):
            parse_workflow(workflow_missing_extract_for_output)

    def test_raises_for_invalid_frontmatter(self):
        """WorkflowParseError is raised for malformed YAML frontmatter."""
        content = """\
---
name: bad yaml
  invalid: indentation
---

## Step

Hello
"""
        with pytest.raises(WorkflowParseError, match="Failed to parse frontmatter"):
            parse_workflow(content)

    def test_raises_for_non_mapping_models(self):
        """WorkflowParseError is raised when models is not a mapping."""
        content = """\
---
name: bad_models
models: not_a_mapping
---

## Step

Hello
"""
        with pytest.raises(WorkflowParseError, match="models"):
            parse_workflow(content)

    def test_raises_for_non_list_inputs(self):
        """WorkflowParseError is raised when inputs is not a list."""
        content = """\
---
name: bad_inputs
models:
  conversation: openai/gpt-4o
  extraction: openai/gpt-4o-mini
inputs: not_a_list
---

## Step

Hello
"""
        with pytest.raises(WorkflowParseError, match="inputs"):
            parse_workflow(content)

    def test_raises_for_input_missing_name(self):
        """WorkflowParseError is raised when an input is missing a name."""
        content = """\
---
name: input_missing_name
models:
  conversation: openai/gpt-4o
  extraction: openai/gpt-4o-mini
inputs:
  - description: Missing name
---

## Step

Hello
"""
        with pytest.raises(WorkflowParseError, match=r"input.*name"):
            parse_workflow(content)

    def test_raises_for_non_list_outputs(self):
        """WorkflowParseError is raised when outputs is not a list."""
        content = """\
---
name: bad_outputs
models:
  conversation: openai/gpt-4o
  extraction: openai/gpt-4o-mini
outputs: not_a_list
---

## Step

Hello
"""
        with pytest.raises(WorkflowParseError, match="outputs"):
            parse_workflow(content)

    def test_raises_for_output_missing_name(self):
        """WorkflowParseError is raised when an output is missing a name."""
        content = """\
---
name: output_missing_name
models:
  conversation: openai/gpt-4o
  extraction: openai/gpt-4o-mini
outputs:
  - description: Missing name
    type: string
---

## Step

Hello
"""
        with pytest.raises(WorkflowParseError, match=r"output.*name"):
            parse_workflow(content)

    def test_defaults_output_type_to_string(self):
        """Outputs default to string type when type is omitted."""
        content = """\
---
name: output_default_type
models:
  conversation: openai/gpt-4o
  extraction: openai/gpt-4o-mini
outputs:
  - name: summary
    description: No explicit type
---

## Step

Hello

## Extract: summary

Extract a summary.
"""
        workflow = parse_workflow(content)
        assert workflow.outputs[0].type == ValueType.STRING

    def test_raises_for_invalid_output_type(self):
        """WorkflowParseError is raised when an output type is invalid."""
        content = """\
---
name: output_invalid_type
models:
  conversation: openai/gpt-4o
  extraction: openai/gpt-4o-mini
outputs:
  - name: summary
    type: stringish
---

## Step

Hello
"""
        with pytest.raises(WorkflowParseError, match="Invalid output type"):
            parse_workflow(content)


# =============================================================================
# Edge Cases
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_parses_workflow_with_no_steps(self):
        """A workflow with no steps (just frontmatter) is technically valid."""
        content = """\
---
name: no_steps
models:
  conversation: openai/gpt-4o
  extraction: openai/gpt-4o-mini
---

Just some text without any ## headings.
"""
        workflow = parse_workflow(content)
        assert workflow.steps == []

    def test_handles_unicode_in_content(self):
        """Unicode characters in workflow content are preserved."""
        content = """\
---
name: unicode_test
models:
  conversation: openai/gpt-4o
  extraction: openai/gpt-4o-mini
---

## Greeting

Hello! Please say "Bonjour" and "Hola" and "Ni Hao"
"""
        workflow = parse_workflow(content)
        assert "Bonjour" in workflow.steps[0].content
        assert "Hola" in workflow.steps[0].content

    def test_handles_special_characters_in_step_names(self):
        """Step names can contain special characters."""
        content = """\
---
name: special_chars
models:
  conversation: openai/gpt-4o
  extraction: openai/gpt-4o-mini
---

## Step #1: The Beginning!

Hello

## What's Next?

World
"""
        workflow = parse_workflow(content)
        assert workflow.steps[0].name == "Step #1: The Beginning!"
        assert workflow.steps[1].name == "What's Next?"

    def test_handles_template_syntax_in_content(self):
        """Jinja2 template syntax is preserved in step content."""
        content = """\
---
name: template_test
models:
  conversation: openai/gpt-4o
  extraction: openai/gpt-4o-mini
inputs:
  - name: user
  - name: topic
---

## Greeting

Hello {{ user }}, let's talk about {{ topic }}.
"""
        workflow = parse_workflow(content)
        assert "{{ user }}" in workflow.steps[0].content
        assert "{{ topic }}" in workflow.steps[0].content

    def test_variable_name_with_underscore(self):
        """Variable names can contain underscores."""
        content = """\
---
name: underscore_var
models:
  conversation: openai/gpt-4o
  extraction: openai/gpt-4o-mini
---

## Message

Hello

## Extract: my_variable_name

Extract something.
"""
        workflow = parse_workflow(content)
        assert workflow.steps[1].variable_name == "my_variable_name"

    def test_variable_name_starting_with_underscore(self):
        """Variable names can start with underscore."""
        content = """\
---
name: underscore_start
models:
  conversation: openai/gpt-4o
  extraction: openai/gpt-4o-mini
---

## Message

Hello

## Extract: _private

Extract something.
"""
        workflow = parse_workflow(content)
        assert workflow.steps[1].variable_name == "_private"

    def test_variable_name_with_numbers(self):
        """Variable names can contain numbers (but not start with them)."""
        content = """\
---
name: number_var
models:
  conversation: openai/gpt-4o
  extraction: openai/gpt-4o-mini
---

## Message

Hello

## Extract: var123

Extract something.
"""
        workflow = parse_workflow(content)
        assert workflow.steps[1].variable_name == "var123"

    def test_rejects_variable_name_starting_with_number(self):
        """Variable names cannot start with a number."""
        content = """\
---
name: bad_var
models:
  conversation: openai/gpt-4o
  extraction: openai/gpt-4o-mini
---

## Extract: 123var

Extract something.
"""
        with pytest.raises(WorkflowParseError, match="Invalid variable name"):
            parse_workflow(content)
