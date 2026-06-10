"""Discovery pipeline - search for conferences via Exa + LLM relevance filter.

Fully synchronous: designed to be called from ADK FunctionTool (sync context).

Flow:
1. Generate time-bounded search queries (topic + upcoming months)
2. Search Exa for each query
3. Deduplicate results by URL
4. LLM relevance filter on each unique result (sync litellm.completion)
5. Yield {url, title} per accepted conference (incremental)
"""

import logging

from conference_agent.config import settings
from conference_agent.tools.exa_tool import search_conferences
from conference_agent.tools.query_generator import generate_queries
from conference_agent.tools.relevance_filter import is_relevant_conference

logger = logging.getLogger(__name__)


def run_discovery(
    topic: str | None = None,
    months_ahead: int | None = None,
    num_results: int | None = None,
):
    """Run the full discovery pipeline, yielding accepted conferences incrementally.

    Yields dicts of {url, title, raw} per accepted conference.
    Fully synchronous - safe to call from ADK FunctionTool or thread pool.
    """
    topic = topic or settings.discovery.topic
    months_ahead = months_ahead or settings.discovery.months_ahead
    num_results = num_results or settings.exa.num_results

    logger.info(
        "Discovery start - topic=%s, months=%d, num_results=%d",
        topic, months_ahead, num_results,
    )

    queries = generate_queries(topic, months_ahead)

    raw_results: list[dict] = []
    for query in queries:
        try:
            results = search_conferences(query, num_results)
            raw_results.extend(results)
        except Exception as exc:
            logger.warning("Exa search failed for query %r: %s", query, exc)

    logger.info("Discovery raw results: %d", len(raw_results))

    seen: dict[str, dict] = {}
    for r in raw_results:
        url = r.get("url", "")
        if url and url not in seen:
            seen[url] = r
    deduped = list(seen.values())
    logger.info("Discovery after dedup: %d", len(deduped))

    for r in deduped:
        try:
            relevant = is_relevant_conference(
                topic=topic,
                title=r.get("title", ""),
                snippet=r.get("snippet", ""),
                url=r.get("url", ""),
            )
            if relevant:
                logger.debug("Discovery accepted: %s", r.get("url"))
                yield {"url": r["url"], "title": r.get("title", ""), "raw": r}
        except Exception as exc:
            logger.warning("Relevance filter error for %r: %s", r.get("url"), exc)

    logger.info("Discovery complete")