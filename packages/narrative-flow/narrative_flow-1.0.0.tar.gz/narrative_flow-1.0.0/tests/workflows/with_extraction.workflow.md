---
# Workflow with Extraction
#
# This workflow demonstrates how to extract values from LLM responses.
# - Extract steps use the format: ## Extract: variable_name
# - The extraction model pulls specific information from the previous response
# - Extracted values are stored and can be used in subsequent steps
# - All declared outputs must have corresponding Extract steps

name: fact_extractor
description: Ask for facts and extract the most interesting one

models:
  conversation: openai/gpt-4o
  extraction: openai/gpt-4o-mini

inputs:
  - name: topic
    description: The topic to get facts about

outputs:
  - name: best_fact
    description: The most interesting fact extracted
    type: string
---

## Get Facts

Tell me three interesting facts about {{ topic }}.

## Extract: best_fact

Extract the single most interesting fact as one sentence.
