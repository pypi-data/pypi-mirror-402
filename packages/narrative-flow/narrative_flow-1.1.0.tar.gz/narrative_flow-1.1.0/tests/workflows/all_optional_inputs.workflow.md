---
# Workflow with All Optional Inputs
#
# This workflow has only optional inputs with defaults.
# It can be executed without providing any inputs.

name: default_greeter
description: A workflow where all inputs have defaults

models:
  conversation: openai/gpt-4o
  extraction: openai/gpt-4o-mini

inputs:
  - name: language
    description: The language for the greeting
    required: false
    default: English
  - name: formality
    description: Level of formality
    required: false
    default: neutral
---

## Generate Greeting

Please create a {{ formality }} greeting in {{ language }}.
