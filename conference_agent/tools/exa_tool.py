"""Exa search wrapper with advanced SDK parameters.

Uses Exa's neural search, date filtering, and content extraction
to find higher-quality conference URLs with richer text snippets.

NOTE: The Exa Python SDK does NOT expose `use_autoprompt` — neural search
(type="neural") handles query optimization internally. The `contents` dict
uses camelCase keys per the SDK convention (maxCharacters, not max_characters).
"""
import logging
import os
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta

from pathlib import Path
from dotenv import load_dotenv
from exa_py import Exa

from conference_agent.config import settings

_ROOT = Path(__file__).parent.parent.parent  # tools/ → conference_agent/ → project root
load_dotenv(_ROOT / "conference_agent" / ".env")

logger = logging.getLogger(__name__)

_exa_key = os.getenv("EXA_API_KEY")
if _exa_key:
    exa = Exa(api_key=_exa_key)
    logger.info("TOOL  Exa client created — API key present (%s...)", _exa_key[:6])
else:
    exa = None
    logger.error("TOOL  Exa client NOT created — EXA_API_KEY missing")


def search_speaker_info(
    name: str,
    affiliation_hint: str | None = None,
) -> list[dict]:
    """Search Exa for a speaker's professional info to infer country/affiliation.

    Uses ``type="auto"`` and ``num_results=3`` per design spec.
    Returns up to 3 results with title, URL, and text snippet for
    heuristic parsing (no LLM calls).

    The ``affiliation_hint`` is appended to the query to improve relevance
    when the speaker name alone is ambiguous.
    """
    query = name
    if affiliation_hint:
        query = f"{name} {affiliation_hint}"

    logger.info("EXA  Searching speaker info: %r", query)

    if exa is None:
        logger.error("EXA  Cannot search speaker — Exa client not initialized (missing EXA_API_KEY)")
        return []

    try:
        result = exa.search(
            query,
            num_results=3,
            type="auto",
            contents={"text": {"maxCharacters": 500}},
        )

        items = [
            {
                "url": r.url,
                "title": r.title or "",
                "snippet": r.text[:500] if r.text else "",
            }
            for r in result.results
        ]

        logger.info("EXA  Found %d results for speaker %r", len(items), name)
        return items
    except Exception as exc:
        logger.error("EXA  search_speaker_info failed for %r: %s", name, exc)
        return []


def search_conferences(
    query: str,
    num_results: int = 0,
    search_type: str = "",
    text_max_chars: int = 0,
    start_published_date: str | None = None,
    include_text: list[str] | None = None,
    exclude_text: list[str] | None = None,
    include_domains: list[str] | None = None,
    exclude_domains: list[str] | None = None,
) -> list[dict]:
    """Search Exa for conference pages with advanced parameters.

    All params default to 0/empty/None → fall back to settings singleton values.
    This ensures config is always driven by settings.yaml unless explicitly overridden.
    Domain filters default to None → fall back to settings.exa.include_domains/exclude_domains.
    """
    t0 = time.time()

    # Resolve parameters from settings if not explicitly provided
    num_results = num_results or settings.exa.num_results
    search_type = search_type or settings.exa.type
    text_max_chars = text_max_chars or settings.exa.text_max_chars
    include_domains = include_domains or settings.exa.include_domains or None
    exclude_domains = exclude_domains or settings.exa.exclude_domains or None

    # Default: 6 months before today — filter for recently published conference pages
    if start_published_date is None:
        cutoff = datetime.now() - relativedelta(months=6)
        start_published_date = cutoff.strftime("%Y-%m-%d")

    logger.info(
        "EXA  Searching: %r (num=%d, type=%s, start=%s)",
        query, num_results, search_type, start_published_date,
    )

    if exa is None:
        logger.error("EXA  Cannot search — Exa client not initialized (missing EXA_API_KEY)")
        return []

    try:
        result = exa.search(
            query,
            num_results=num_results,
            type=search_type,
            start_published_date=start_published_date,
            contents={"text": {"maxCharacters": text_max_chars}},
            include_text=include_text,
            exclude_text=exclude_text,
            include_domains=include_domains,
            exclude_domains=exclude_domains,
        )

        items = [
            {
                "url": r.url,
                "title": r.title or "",
                "snippet": r.text[:text_max_chars] if r.text else "",
            }
            for r in result.results
        ]

        elapsed = time.time() - t0
        logger.info("EXA  Found %d results for %r (%.1fs)", len(items), query, elapsed)
        for item in items:
            logger.debug("EXA  Result: %s — %s", item["title"][:60], item["url"])
        return items
    except Exception as exc:
        logger.error("EXA  search_conferences failed for %r: %s", query, exc)
        return []
