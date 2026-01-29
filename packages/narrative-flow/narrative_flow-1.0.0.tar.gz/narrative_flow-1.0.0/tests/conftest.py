"""Shared fixtures for narrative-flow tests.

This module provides reusable test fixtures that demonstrate common usage patterns.
Developers can reference these fixtures to understand how to construct workflows
and mock API responses in their own applications.
"""

from pathlib import Path
from typing import Any

import pytest

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
# Path Fixtures
# =============================================================================


@pytest.fixture
def workflows_dir() -> Path:
    """Path to the test workflows directory."""
    return Path(__file__).parent / "workflows"


@pytest.fixture
def examples_dir() -> Path:
    """Path to the examples directory in the project root."""
    return Path(__file__).parent.parent / "examples"


# =============================================================================
# Minimal Workflow Fixtures
# =============================================================================


@pytest.fixture
def minimal_workflow_content() -> str:
    """The simplest valid workflow: no inputs, no outputs, one message step."""
    return """\
---
name: minimal_workflow
description: A minimal workflow for testing

models:
  conversation: openai/gpt-4o
  extraction: openai/gpt-4o-mini
---

## Say Hello

Hello, world!
"""


@pytest.fixture
def minimal_workflow() -> WorkflowDefinition:
    """A minimal workflow definition for testing."""
    return WorkflowDefinition(
        name="minimal_workflow",
        description="A minimal workflow for testing",
        models=ModelsConfig(
            conversation="openai/gpt-4o",
            extraction="openai/gpt-4o-mini",
        ),
        steps=[
            Step(
                type=StepType.MESSAGE,
                name="Say Hello",
                content="Hello, world!",
            )
        ],
    )


# =============================================================================
# Full-Featured Workflow Fixtures
# =============================================================================


@pytest.fixture
def workflow_with_inputs_and_outputs_content() -> str:
    """A workflow with inputs, outputs, message steps, and extract steps."""
    return """\
---
name: topic_explainer
description: Explain a topic and extract insights

models:
  conversation: openai/gpt-4o
  extraction: openai/gpt-4o-mini

inputs:
  - name: topic
    description: The topic to explain
    required: true
  - name: style
    description: The explanation style
    required: false
    default: casual

outputs:
  - name: summary
    description: A brief summary of the topic
    type: string
---

## Explain the Topic

Please explain {{ topic }} in a {{ style }} tone.

## Extract: summary

Extract a one-sentence summary of the explanation.
"""


@pytest.fixture
def workflow_with_inputs_and_outputs() -> WorkflowDefinition:
    """A workflow definition with inputs, outputs, and extraction."""
    return WorkflowDefinition(
        name="topic_explainer",
        description="Explain a topic and extract insights",
        models=ModelsConfig(
            conversation="openai/gpt-4o",
            extraction="openai/gpt-4o-mini",
        ),
        inputs=[
            InputVariable(
                name="topic",
                description="The topic to explain",
                required=True,
            ),
            InputVariable(
                name="style",
                description="The explanation style",
                required=False,
                default="casual",
            ),
        ],
        outputs=[
            OutputVariable(
                name="summary",
                description="A brief summary of the topic",
                type=ValueType.STRING,
            ),
        ],
        steps=[
            Step(
                type=StepType.MESSAGE,
                name="Explain the Topic",
                content="Please explain {{ topic }} in a {{ style }} tone.",
            ),
            Step(
                type=StepType.EXTRACT,
                name="Extract: summary",
                content="Extract a one-sentence summary of the explanation.",
                variable_name="summary",
            ),
        ],
    )


@pytest.fixture
def multi_step_workflow_content() -> str:
    """A workflow with multiple message steps and extractions."""
    return """\
---
name: interview_simulator
description: Simulate an interview and extract responses

models:
  conversation: openai/gpt-4o
  extraction: openai/gpt-4o-mini

inputs:
  - name: candidate_name
    description: Name of the candidate

outputs:
  - name: strength
    description: The candidate's main strength
    type: string
  - name: improvement
    description: Area for improvement
    type: string
---

## Introduction

You are interviewing {{ candidate_name }}. Start by asking about their background.

## Strength Question

What would you say is your greatest professional strength?

## Extract: strength

Extract the main strength mentioned in one phrase.

## Improvement Question

What area are you currently working to improve?

## Extract: improvement

Extract the improvement area in one phrase.
"""


# =============================================================================
# Workflow Result Fixtures
# =============================================================================


@pytest.fixture
def successful_workflow_result() -> WorkflowResult:
    """A successful workflow result for testing log generation."""
    return WorkflowResult(
        workflow_name="test_workflow",
        inputs={"topic": "Python testing"},
        outputs={"summary": "Testing ensures code quality."},
        step_results=[
            StepResult(
                step=Step(
                    type=StepType.MESSAGE,
                    name="Explain",
                    content="Explain {{ topic }}",
                ),
                user_message="Explain Python testing",
                assistant_response="Python testing involves writing test cases to verify code behavior.",
            ),
            StepResult(
                step=Step(
                    type=StepType.EXTRACT,
                    name="Extract: summary",
                    content="Extract summary",
                    variable_name="summary",
                ),
                extracted_value="Testing ensures code quality.",
            ),
        ],
        conversation_history=[
            Message(role="user", content="Explain Python testing"),
            Message(
                role="assistant",
                content="Python testing involves writing test cases to verify code behavior.",
            ),
        ],
        success=True,
        error=None,
    )


@pytest.fixture
def failed_workflow_result() -> WorkflowResult:
    """A failed workflow result for testing error handling."""
    return WorkflowResult(
        workflow_name="failed_workflow",
        inputs={"topic": "test"},
        outputs={},
        step_results=[],
        conversation_history=[],
        success=False,
        error="API connection failed",
    )


# =============================================================================
# Mock API Response Fixtures
# =============================================================================


@pytest.fixture
def mock_openrouter_response() -> dict[str, Any]:
    """A typical OpenRouter API response structure."""
    return {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "This is a mock response from the LLM.",
                }
            }
        ]
    }


@pytest.fixture
def mock_api_responses() -> list[str]:
    """A sequence of mock responses for multi-step workflow testing."""
    return [
        "Here's an explanation of the topic you asked about.",
        "The key insight is simplicity.",
        "Here's another detailed response.",
        "Focus on fundamentals.",
    ]


# =============================================================================
# Invalid Workflow Content Fixtures
# =============================================================================


@pytest.fixture
def workflow_missing_name() -> str:
    """Workflow content missing the required 'name' field."""
    return """\
---
description: No name field

models:
  conversation: openai/gpt-4o
  extraction: openai/gpt-4o-mini
---

## Step One

Hello
"""


@pytest.fixture
def workflow_missing_models() -> str:
    """Workflow content missing the required 'models' field."""
    return """\
---
name: missing_models
description: No models field
---

## Step One

Hello
"""


@pytest.fixture
def workflow_missing_conversation_model() -> str:
    """Workflow content missing the 'conversation' model."""
    return """\
---
name: missing_conversation
models:
  extraction: openai/gpt-4o-mini
---

## Step One

Hello
"""


@pytest.fixture
def workflow_missing_extraction_model() -> str:
    """Workflow content missing the 'extraction' model."""
    return """\
---
name: missing_extraction
models:
  conversation: openai/gpt-4o
---

## Step One

Hello
"""


@pytest.fixture
def workflow_invalid_extract_varname() -> str:
    """Workflow with an invalid variable name in Extract step."""
    return """\
---
name: invalid_varname
models:
  conversation: openai/gpt-4o
  extraction: openai/gpt-4o-mini
---

## Extract: invalid-name

This variable name has a hyphen.
"""


@pytest.fixture
def workflow_missing_extract_for_output() -> str:
    """Workflow declaring an output but missing the corresponding Extract step."""
    return """\
---
name: missing_extract
models:
  conversation: openai/gpt-4o
  extraction: openai/gpt-4o-mini

outputs:
  - name: summary
    description: A summary that has no extract step
    type: string
---

## Just a Message

This workflow declares an output but has no Extract step for it.
"""


@pytest.fixture
def workflow_empty_extract_varname() -> str:
    """Workflow with empty variable name after 'Extract:'."""
    return """\
---
name: empty_varname
models:
  conversation: openai/gpt-4o
  extraction: openai/gpt-4o-mini
---

## Extract:

Missing variable name.
"""
