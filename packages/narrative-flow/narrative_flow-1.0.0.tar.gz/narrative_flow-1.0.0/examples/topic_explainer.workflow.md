---
name: topic_explainer
description: Explore a topic through conversation and extract key insights

models:
  conversation: openai/gpt-4o
  extraction: openai/gpt-4o-mini

inputs:
  - name: topic
    description: The topic to explore

outputs:
  - name: surprising_fact
    description: The most surprising fact about the topic
    type: string
  - name: analogy
    description: A memorable analogy to explain the topic
    type: string
---

## Get the Facts

Tell me three interesting facts about {{ topic }} that most people don't know.

## Find the Surprise

Which of those facts do you think would be most surprising to the average person? Why does it challenge common assumptions?

## Extract: surprising_fact

Extract the single most surprising fact in one clear sentence.

## Create an Analogy

Now I want to help people remember this. Can you create a memorable analogy that explains {{ topic }} by comparing it to something from everyday life? The analogy should make the concept click for someone unfamiliar with it.

## Extract: analogy

Extract just the analogy itself in 1-2 sentences.
