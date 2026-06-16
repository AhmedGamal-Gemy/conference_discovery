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


def batch_filter_conferences(
    topic: str,
    results: list[dict],
) -> list[dict]:
    """Filter a list of Exa results in a single LLM call.

    Takes all deduped results, sends them in one prompt, and returns
    only the results the LLM classifies as relevant conferences.

    Args:
        topic: Search topic (e.g. "medical").
        results: List of dicts with keys "url", "title", "snippet".

    Returns:
        Filtered list of dicts (same structure) for relevant conferences only.
    """
    if not results:
        return []

    # Build a numbered list for the prompt
    items_text = "\n\n".join(
        f"[{i + 1}]\nTitle: {r.get('title', '')}\nURL: {r.get('url', '')}\nSnippet: {r.get('snippet', '')[:300]}"
        for i, r in enumerate(results)
    )

    prompt = f"""You are a conference relevance classifier.

Determine which of the following items are REAL conference pages relevant to the topic "{topic}".

Reject:
- blogs
- news articles
- directories
- ads
- unrelated pages

Return ONLY valid JSON — an object with a "relevant_indices" array containing the 1-based index numbers of items that ARE relevant conferences.

Example:
{{"relevant_indices": [1, 3, 5]}}

Items to classify:
{items_text}
"""

    response = litellm.completion(
        model=MODEL,
        temperature=TEMP,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content
    parsed = json.loads(content)
    indices = parsed.get("relevant_indices", [])

    # Convert 1-based indices to 0-based and filter
    return [results[i - 1] for i in indices if 1 <= i <= len(results)]