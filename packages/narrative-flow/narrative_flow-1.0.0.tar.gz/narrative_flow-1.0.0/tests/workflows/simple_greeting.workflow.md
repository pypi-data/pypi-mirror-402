---
# Simple Greeting Workflow
#
# This is the simplest possible workflow: a single message step with no inputs or outputs.
# Use this as a reference for understanding the minimal workflow structure.

name: simple_greeting
description: A simple greeting workflow with one message step

models:
  conversation: openai/gpt-4o
  extraction: openai/gpt-4o-mini
---

## Greet the User

Hello! Please give me a friendly greeting.
