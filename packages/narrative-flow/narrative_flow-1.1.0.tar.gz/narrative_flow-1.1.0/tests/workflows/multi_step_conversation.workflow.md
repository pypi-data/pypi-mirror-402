---
# Multi-Step Conversation Workflow
#
# This workflow demonstrates a multi-turn conversation with multiple extractions.
# - Each message step adds to the conversation history
# - The LLM sees the full conversation context when responding
# - Multiple extractions can pull different pieces of information
# - Extracted values can be used in later steps via {{ variable_name }}

name: idea_generator
description: Generate and refine ideas through conversation

models:
  conversation: openai/gpt-4o
  extraction: openai/gpt-4o-mini

inputs:
  - name: domain
    description: The domain for idea generation

outputs:
  - name: initial_idea
    description: The first idea generated
    type: string
  - name: refined_idea
    description: The refined version of the idea
    type: string
---

## Generate Initial Ideas

I'm looking for innovative ideas in the {{ domain }} space.
Can you suggest one creative concept?

## Extract: initial_idea

Extract the main idea in one sentence.

## Refine the Idea

That's interesting! Now let's make it more practical.
How could we implement "{{ initial_idea }}" with limited resources?

## Extract: refined_idea

Extract the refined, practical version of the idea in one sentence.
