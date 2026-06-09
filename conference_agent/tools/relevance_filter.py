"""Relevance filter for Exa search results.

Routes LLM calls through the LiteLLM proxy (project convention).
Uses sync litellm.completion() because this is called from sync FunctionTool context.
"""

import json

import litellm

from conference_agent.config import settings

MODEL = settings.llm.relevance_filter.model
TEMP = settings.llm.relevance_filter.temperature


def is_relevant_conference(
    topic: str,
    title: str,
    snippet: str,
    url: str,
) -> bool:
    """Return True if the page looks like a real conference for the given topic."""

    prompt = f"""You are a conference relevance classifier.

Determine if this is a REAL conference page relevant to the topic "{topic}".

Reject:
- blogs
- news articles
- directories
- ads
- unrelated pages

Return ONLY valid JSON:

{{
  "relevant": true
}}

Title: {title}

URL: {url}

Snippet:
{snippet}
"""

    response = litellm.completion(
        model=MODEL,
        temperature=TEMP,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content
    parsed = json.loads(content)
    return parsed["relevant"]