---
name: youtube_short_titler
description: Generate titles and descriptions for YouTube shorts using MrBeast's principles

models:
  conversation: google/gemini-2.5-pro
  extraction: google/gemini-2.5-flash

retries: 3

inputs:
  - name: short_transcript
  - name: episode_transcript

outputs:
  - name: short_title
  - name: short_description
---

## MrBeast Titling Principles

What does Mr Beast say about titling YouTube videos?

## Shorts vs Traditional Videos

How do you think MrBeast would approach creating a title for a YouTube short that is a clip from a podcast versus one of his traditional videos? Would he use the same approach or something different?

## Generate Title

Help me write the title for this YouTube short in accordance with Mr. Beast's best practices.

The YouTube short is a clip from a recent podcast episode which I co-host. The Podcast is called "They Might Be Self-Aware"

The podcast is described as:

> "They Might Be Self-Aware" is your weekly tech frenzy with Hunter Powers and Daniel Bishop. Every Monday and Thursday, these ex-co-workers, now tech savants, strip down the AI and technology revolution to its nuts and bolts. Forget the usual sermon. Hunter and Daniel are here to inject raw, unfiltered insight into AI's labyrinth – from its radiant promises to its shadowy puzzles. Whether you're AI-illiterate or a digital sage, their sharp banter will be your gateway to the heart of tech's biggest quandary. Jack into "They Might Be Self-Aware" for a no-holds-barred journey into technology's enigma. Is it our savior or a mother harbinger of doom? Get in the loop, subscribe today, and be part of the most gripping debate of our era.

Here is the transcript for the YouTube short:

```
{{ short_transcript }}
```

Here is the transcript for the entire podcast episode for additional context:

```
{{ episode_transcript }}
```

Help me write the title for this YouTube short in accordance with Mr. Beast's best practices.

## Extract: short_title

Extract the single best suggested title from the response.

## Generate Description

Great. I will go with `{{ short_title }}`. Now I need the perfect description to pair with the YouTube short. I'll note the primary goal of the short is to get people to subscribe and the secondary goal is to get people to watch the full podcast episodes. What would Mr. Beast write for the perfect YouTube short description?

## Extract: short_description

Extract the single best suggested description from the response.
