---
name: blog_post_generator
description: Generate a blog post with iterative refinement - demonstrates mid-conversation extraction

models:
  conversation: openai/gpt-4o
  extraction: openai/gpt-4o-mini

inputs:
  - name: subject
    description: What the blog post should be about
  - name: audience
    description: Who the target audience is
  - name: tone
    description: The desired tone (e.g., professional, casual, humorous)
    required: false
    default: conversational

outputs:
  - name: title
    description: The blog post title
    type: string
  - name: hook
    description: The opening hook paragraph
    type: string
  - name: outline
    description: The full post outline
    type: string
  - name: post
    description: The complete blog post
    type: string
---

## Brainstorm Angles

I'm writing a blog post about {{ subject }} for {{ audience }}.

What are 5 unique angles or hooks I could use to make this post stand out? For each angle, give me a one-sentence description of the approach.

## Pick the Best Angle

Which of those angles do you think would resonate most with {{ audience }}? Consider what would make them stop scrolling and actually read. Explain your reasoning.

## Generate Title Options

Great. Based on that angle, give me 5 title options for this blog post. The tone should be {{ tone }}. Make them compelling and specific.

## Extract: title

Extract the single best title from the options.

## Write the Hook

Perfect, I'll use "{{ title }}" as my title.

Now write me a killer opening paragraph (the hook) that:

- Grabs attention in the first sentence
- Creates curiosity or tension
- Makes the reader NEED to keep reading

Keep the {{ tone }} tone. This is for {{ audience }}.

## Extract: hook

Extract just the hook paragraph.

## Create the Outline

Now let's plan out the full post. Create a detailed outline for "{{ title }}" that includes:

- The hook we wrote
- 3-5 main sections with subpoints
- A compelling conclusion with a call to action

Target length: 1500-2000 words when fully written.

## Extract: outline

Extract the outline in a clean format. Use simple dashes for hierarchy.

## Write the Post

Now write the complete blog post following this outline:

{{ outline }}

Remember:

- Title: {{ title }}
- Audience: {{ audience }}
- Tone: {{ tone }}
- Start with this hook: {{ hook }}

Make it engaging, actionable, and valuable. Include specific examples where relevant.

## Extract: post

Extract the complete blog post. Return only the post content starting from the title.
