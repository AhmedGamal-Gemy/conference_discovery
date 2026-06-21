import logging
import time

from conference_agent.config import settings
from conference_agent.tools.query_generator import generate_queries
from conference_agent.tools.exa_tool import search_conferences
from conference_agent.tools.relevance_filter import is_relevant_conference

logger = logging.getLogger(__name__)

# ponytail: these domains are press-release/aggregator — never a conference homepage
_REJECTED_DOMAINS = frozenset({
    "prnewswire.com", "chainwire.org", "morningstar.com", "linkedin.com",
    "finance.yahoo.com", "businesswire.com", "globenewswire.com",
})


def _url_is_rejected(url: str) -> bool:
    """Check if URL is a known press-release / aggregator domain."""
    try:
        from urllib.parse import urlparse
        domain = urlparse(url).netloc.lower()
        # Strip optional www. prefix for matching
        domain = domain.removeprefix("www.")
        return any(rejected in domain for rejected in _REJECTED_DOMAINS)
    except Exception:
        return False


def run_discovery(topic: str = "", months_ahead: int = 0, num_results: int = 0):
    t0 = time.time()
    topic = topic or settings.discovery.topic
    months_ahead = months_ahead or settings.discovery.months_ahead
    num_results = num_results or settings.exa.num_results

    logger.info(
        "DISCOVERY  Pipeline starting — topic=%r, months_ahead=%d, num_results=%d",
        topic, months_ahead, num_results,
    )

    queries = generate_queries(topic)
    raw_results = []

    for query in queries:
        try:
            results = search_conferences(query, num_results)
            logger.info("DISCOVERY  Query %r — %d results", query, len(results))
            raw_results.extend(results)
        except Exception as exc:
            logger.warning("DISCOVERY  Query %r failed: %s — continuing", query, exc)
            continue  # Don't let one bad query kill the whole run

    # Deduplicate by URL
    dedup = {}
    for r in raw_results:
        dedup[r["url"]] = r

    deduped_results = list(dedup.values())
    logger.info(
        "DISCOVERY  Dedup — %d raw → %d unique URLs",
        len(raw_results), len(deduped_results),
    )

    accepted = 0
    rejected = 0
    for r in deduped_results:
        try:
            # ponytail: skip press-release/aggregator URLs before LLM filter — saves tokens
            if _url_is_rejected(r["url"]):
                rejected += 1
                logger.debug("DISCOVERY  ✗ DOMAIN REJECTED: %s — %s", r["title"][:60], r["url"])
                continue

            relevant = is_relevant_conference(
                topic=topic,
                title=r["title"],
                snippet=r["snippet"],
                url=r["url"],
            )

            if relevant:
                accepted += 1
                logger.info("DISCOVERY  ✓ ACCEPTED: %s — %s", r["title"][:60], r["url"])
                yield {"url": r["url"], "title": r["title"]}
            else:
                rejected += 1
                logger.debug("DISCOVERY  ✗ REJECTED: %s — %s", r["title"][:60], r["url"])
        except Exception as exc:
            rejected += 1
            logger.warning("DISCOVERY  ✗ ERROR filtering %s: %s", r["url"], exc)

    elapsed = time.time() - t0
    logger.info(
        "DISCOVERY  Pipeline complete — accepted=%d, rejected=%d (%.1fs)",
        accepted, rejected, elapsed,
    )
