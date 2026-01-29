---
name: user_assistant_example
description: Test fixture with explicit user and assistant steps

models:
  conversation: openai/gpt-4o
  extraction: openai/gpt-4o-mini

inputs:
  - name: topic

outputs:
  - name: takeaway
    type: string
---

## User

Explain {{ topic }} briefly.

## Assistant

A clear, direct explanation goes here.

## User

Now give a one-sentence takeaway.

## Extract: takeaway

Extract the takeaway sentence only.
