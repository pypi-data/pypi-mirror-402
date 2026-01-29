---
# Workflow with Input Variables
#
# This workflow demonstrates how to define and use input variables.
# - Required inputs must be provided when executing the workflow
# - Optional inputs have defaults that are used if not provided
# - Variables are substituted using Jinja2 syntax: {{ variable_name }}

name: personalized_greeting
description: A greeting workflow that uses input variables

models:
  conversation: openai/gpt-4o
  extraction: openai/gpt-4o-mini

inputs:
  - name: user_name
    description: The name of the user to greet
    required: true
  - name: greeting_style
    description: The style of greeting (formal, casual, enthusiastic)
    required: false
    default: casual
---

## Personalized Greeting

Please greet {{ user_name }} in a {{ greeting_style }} style.
