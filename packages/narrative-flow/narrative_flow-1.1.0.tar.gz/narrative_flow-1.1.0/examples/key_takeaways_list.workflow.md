---
name: key_takeaways_list
description: Generate and extract a list of key takeaways

models:
  conversation: openai/gpt-4o
  extraction: openai/gpt-4o-mini

inputs:
  - name: topic
    description: Topic to summarize

outputs:
  - name: takeaways
    description: Key takeaways as a list of short phrases
    type: string_list
---

## Ask for Takeaways

Give me 5 concise takeaways about {{ topic }}. Keep each takeaway under 10 words.

## Extract: takeaways

Extract the 5 takeaways.
