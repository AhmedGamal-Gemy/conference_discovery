import json
import litellm

from conference_agent.config import settings

import os
from dotenv import load_dotenv

load_dotenv()

MODEL = settings.llm.relevance_filter.model
TEMP = settings.llm.relevance_filter.temperature


async def is_relevant_conference(
    topic: str,
    title: str,
    snippet: str,
    url: str
):
    prompt = f"""
You are a conference relevance classifier.

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

    response = await litellm.acompletion(
        model=MODEL,
        api_key = os.getenv("MISTRAL_API_KEY"),
        temperature=TEMP,
        messages=[
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )

    content = response.choices[0].message.content

    parsed = json.loads(content)

    return parsed["relevant"]