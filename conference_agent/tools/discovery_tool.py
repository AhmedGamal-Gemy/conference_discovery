"""
Discovery pipeline — search for conferences via Exa + LLM relevance filter.

Flow:
1. Generate time-bounded search queries (topic + upcoming months)
2. Search Exa for each query
3. Deduplicate results by URL
4. LLM relevance filter on each unique result
5. Return clean list of {url, title}
"""

import asyncio
import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta

from conference_agent.config import settings
from conference_agent.tools.exa_tool import search_conferences
from conference_agent.tools.query_generator import generate_queries
from conference_agent.tools.relevance_filter import is_relevant_conference

logger = logging.getLogger(__name__)


async def run_discovery(
    topic: str | None = None,
    months_ahead: int | None = None,
    num_results: int | None = None,
) -> list[dict]:
    """Run the full discovery pipeline and return accepted conference URLs.

    Args:
        topic: Conference topic/tag (defaults to settings.discovery.topic).
        months_ahead: How many months ahead to search (defaults to settings.discovery.months_ahead).
        num_results: Max results per Exa query (defaults to settings.exa.num_results).

    Returns:
        list of {"url": str, "title": str} for accepted conference pages.
    """
    topic = topic or settings.discovery.topic
    months_ahead = months_ahead or settings.discovery.months_ahead
    num_results = num_results or settings.exa.num_results

    logger.info(
        "Discovery start — topic=%s, months=%d, num_results=%d",
        topic, months_ahead, num_results,
    )

    # Step 1: generate time-bounded search queries
    queries = _gen_queries(topic, months_ahead)

    # Step 2: Exa search for each query
    raw_results: list[dict] = []
    for query in queries:
        try:
            results = search_conferences(query, num_results)
            raw_results.extend(results)
        except Exception as exc:
            logger.warning("Exa search failed for query %r: %s", query, exc)

    logger.info("Discovery raw results: %d", len(raw_results))

    # Step 3: deduplicate by URL
    seen: dict[str, dict] = {}
    for r in raw_results:
        url = r.get("url", "")
        if url and url not in seen:
            seen[url] = r
    deduped = list(seen.values())
    logger.info("Discovery after dedup: %d", len(deduped))

    # Step 4: LLM relevance filter (runs concurrently)
    semaphore = asyncio.Semaphore(5)  # limit concurrent LLM calls

    async def _filter(r: dict) -> dict | None:
        async with semaphore:
            try:
                relevant = await is_relevant_conference(
                    topic=topic,
                    title=r.get("title", ""),
                    snippet=r.get("snippet", ""),
                    url=r.get("url", ""),
                )
                if relevant:
                    return {"url": r["url"], "title": r.get("title", "")}
            except Exception as exc:
                logger.warning("Relevance filter error for %r: %s", r.get("url"), exc)
            return None

    filter_tasks = [_filter(r) for r in deduped]
    filter_results = await asyncio.gather(*filter_tasks)
    clean_results = [r for r in filter_results if r is not None]

    logger.info("Discovery accepted: %d / %d", len(clean_results), len(deduped))
    return clean_results




