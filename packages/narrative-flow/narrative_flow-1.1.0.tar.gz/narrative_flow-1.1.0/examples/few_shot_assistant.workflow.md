---
name: few_shot_assistant
description: Demonstrate explicit User/Assistant steps with a few-shot example

models:
  conversation: openai/gpt-4o
  extraction: openai/gpt-4o-mini

inputs:
  - name: product
    description: The product to write a tagline for

outputs:
  - name: tagline
    description: A short tagline for the product
    type: string
---

## User

Write a short, punchy tagline for a new note-taking app.

## Assistant

Capture every idea before it disappears.

## User

Now write a short, punchy tagline for {{ product }}.

## Extract: tagline

Extract the tagline only.
