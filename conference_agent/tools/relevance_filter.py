import json
import logging
import time

import litellm

from conference_agent.config import settings

logger = logging.getLogger(__name__)

# LiteLLM proxy routes via LITELLM_PROXY_API_BASE / LITELLM_PROXY_API_KEY env vars
# No direct api_key — proxy handles auth.

MODEL = settings.llm.relevance_filter.model
TEMP = settings.llm.relevance_filter.temperature
logger.info("TOOL  Relevance filter loaded — model=%s, temp=%.1f", MODEL, TEMP)


def is_relevant_conference(
    topic: str,
    title: str,
    snippet: str,
    url: str,
) -> bool:
    t0 = time.time()
    logger.debug("RELEVANCE  Checking — url=%s, title=%s", url, title[:60])

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

    try:
        response = litellm.completion(
            model=MODEL,
            temperature=TEMP,
            messages=[
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        parsed = json.loads(content)
        result = parsed.get("relevant", False)

        elapsed = time.time() - t0
        if result:
            logger.info("RELEVANCE  ✓ ACCEPTED — %s (%.1fs)", title[:60], elapsed)
        else:
            logger.debug("RELEVANCE  ✗ REJECTED — %s (%.1fs)", title[:60], elapsed)

        return result

    except json.JSONDecodeError:
        elapsed = time.time() - t0
        logger.error("RELEVANCE  JSON decode failed for %s (%.1fs): content=%r", url, elapsed, content[:200])
        return False
    except Exception as exc:
        elapsed = time.time() - t0
        logger.error("RELEVANCE  Check failed for %s (%.1fs): %s", url, elapsed, exc)
        return False