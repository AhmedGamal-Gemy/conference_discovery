"""Scrape conference directory/aggregator websites for conference URLs.

Two strategies:
  A — CSS-selector-based extraction from HTML (known aggregators)
  B — Markdown + LLM extraction fallback (unknown aggregators)

Pattern follows path_probe.py: create MCP session from shared pool,
don't close it, log and skip on errors.
"""

import asyncio
import json
import logging
import time
from urllib.parse import urljoin

import litellm
from bs4 import BeautifulSoup

from conference_agent.config import settings
from conference_agent.tools.scrapling_tool import scrapling_toolset

logger = logging.getLogger(__name__)

_MAX_CONCURRENT = 3

# ── Strategy A: CSS-selector-based HTML parsing ─────────────────────────


async def _fetch_html(session, url: str, timeout: int = 30000) -> str | None:
    """Fetch a page as raw HTML via Scrapling MCP."""
    try:
        result = await session.call_tool("stealthy_fetch", arguments={
            "url": url,
            "timeout": timeout,
            "extraction_type": "html",
            "solve_cloudflare": False,
            "main_content_only": False,
            "headless": True,
        })
        raw = json.loads(result.content[0].text)
        return "".join(raw.get("content", []))
    except Exception as exc:
        logger.warning("DIRECTORY  Fetch HTML failed — %s: %s", url, exc)
        return None


def _extract_listing(html: str, config) -> list[dict]:
    """Parse listing-page HTML via CSS selectors → [(title, detail_url), …]."""
    soup = BeautifulSoup(html, "html.parser")
    entries = []

    cards = soup.select(config.listing_selector) if config.listing_selector else [soup]

    for card in cards:
        if len(entries) >= settings.directories.max_entries_per_source:
            break
        try:
            title_el = card.select_one(config.title_selector) if config.title_selector else None
            title = title_el.get_text(strip=True) if title_el else ""

            link_el = card.select_one(config.detail_link_selector) if config.detail_link_selector else None
            if not link_el or not link_el.get("href"):
                continue

            href = link_el["href"]
            detail_url = config.detail_url_pattern.replace("{path}", href) if config.detail_url_pattern else urljoin(config.url, href)

            entries.append({"title": title, "detail_url": detail_url})
        except Exception as exc:
            logger.debug("DIRECTORY  Skipping card entry: %s", exc)

    return entries


async def _fetch_visit_url(session, detail_url: str, selector: str) -> str | None:
    """Fetch detail-page HTML and extract the actual conference website URL."""
    html = await _fetch_html(session, detail_url, timeout=15000)
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")
    link = soup.select_one(selector) if selector else None
    return link["href"] if link and link.get("href") else None


async def _strategy_a(session, config) -> list[dict]:
    """Extract conference URLs via CSS selectors (Strategy A)."""
    html = await _fetch_html(session, config.url)
    if not html:
        return []

    entries = _extract_listing(html, config)
    logger.info("DIRECTORY  %s — %d entries from listing", config.name, len(entries))
    if not entries:
        return []

    if not config.visit_link_selector:
        # No way to find the real conference URL — return detail-page URLs as-is
        return [{"url": e["detail_url"], "title": e["title"], "snippet": ""} for e in entries]

    sem = asyncio.Semaphore(_MAX_CONCURRENT)

    async def _resolve(entry: dict) -> dict | None:
        async with sem:
            visit_url = await _fetch_visit_url(session, entry["detail_url"], config.visit_link_selector)
            if visit_url:
                return {"url": visit_url, "title": entry["title"], "snippet": ""}
            # ponytail: fallback to detail URL if selector fails
            return {"url": entry["detail_url"], "title": entry["title"], "snippet": ""}

    tasks = [_resolve(e) for e in entries]
    gathered = await asyncio.gather(*tasks, return_exceptions=True)

    results = [r for r in gathered if isinstance(r, dict)]
    logger.info("DIRECTORY  %s — %d resolved URLs", config.name, len(results))
    return results


# ── Strategy B: Markdown + LLM extraction ──────────────────────────────


async def _fetch_markdown(session, url: str) -> str | None:
    """Fetch a page as markdown via Scrapling MCP."""
    try:
        result = await session.call_tool("stealthy_fetch", arguments={
            "url": url,
            "timeout": 30000,
            "extraction_type": "markdown",
            "solve_cloudflare": False,
            "main_content_only": False,
        })
        raw = json.loads(result.content[0].text)
        return "".join(raw.get("content", []))
    except Exception as exc:
        logger.warning("DIRECTORY  Fetch markdown failed — %s: %s", url, exc)
        return None


_LLM_EXTRACTION_PROMPT = """You are a conference URL extractor.

Extract all conference entries from this directory page markdown.
For each entry find the official conference website URL if present,
otherwise use the entry's detail/page URL.

Return ONLY valid JSON array:
[{"url": "...", "title": "...", "date": "..."}]

If no conferences found return [].

Markdown content:
{markdown}"""


async def _extract_via_llm(markdown: str) -> list[dict]:
    """Send listing-page markdown to LLM and parse extracted URLs."""
    # ponytail: hard 8000-char truncation — real pages are rarely longer
    truncated = markdown[:8000]
    prompt = _LLM_EXTRACTION_PROMPT.format(markdown=truncated)

    try:
        response = await litellm.acompletion(
            model=settings.llm.relevance_filter.model,
            temperature=0.0,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        parsed = json.loads(content)
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, dict):
            for key in ("conferences", "results", "entries"):
                val = parsed.get(key)
                if isinstance(val, list):
                    return val
        return []
    except Exception as exc:
        logger.warning("DIRECTORY  LLM extraction failed: %s", exc)
        return []


async def _strategy_b(session, config) -> list[dict]:
    """Extract conference URLs via markdown + LLM (Strategy B)."""
    markdown = await _fetch_markdown(session, config.url)
    if not markdown:
        return []

    raw = await _extract_via_llm(markdown)
    # Normalize to Exa-style format (snippet not returned by LLM)
    results = [{"url": r.get("url", ""), "title": r.get("title", ""), "snippet": ""} for r in raw if r.get("url")]
    logger.info("DIRECTORY  %s — LLM found %d entries", config.name, len(results))
    return results


# ── Per-aggregator dispatch ────────────────────────────────────────────


async def _scrape_aggregator(session, config) -> list[dict]:
    """Scrape a single aggregator by dispatching to strategy A or B."""
    logger.info("DIRECTORY  Scraping %s — %s", config.name, config.url)
    try:
        if config.extract_by_markdown or not config.listing_selector:
            return await _strategy_b(session, config)
        return await _strategy_a(session, config)
    except Exception as exc:
        logger.warning("DIRECTORY  Aggregator %s failed: %s", config.name, exc)
        return []


# ── Entry points ───────────────────────────────────────────────────────


async def _run_all() -> list[dict]:
    """Scrape every configured aggregator — one shared MCP session."""
    if not settings.directories.enabled:
        return []
    if not settings.directories.aggregators:
        return []

    session = None
    try:
        session = await scrapling_toolset._mcp_session_manager.create_session()
        results: list[dict] = []
        for agg in settings.directories.aggregators:
            agg_results = await _scrape_aggregator(session, agg)
            results.extend(agg_results)
        return results
    except Exception as exc:
        logger.warning("DIRECTORY  MCP session error: %s", exc)
        return []
    finally:
        # Intentionally NOT closing the shared session manager.
        # See path_probe.py line 146–154 for rationale.
        if session is not None:
            logger.debug("DIRECTORY  Session left open for reuse")


def run_directory_discovery(topic: str = "") -> list[dict]:
    """Run directory discovery for all configured aggregators.

    Returns a list of ``{"url": str, "title": str}`` dicts — same format
    as Exa results so they can be merged before dedup/filter.
    """
    t0 = time.time()

    if not settings.directories.enabled:
        logger.debug("DIRECTORY  Disabled — skipping")
        return []
    if not settings.directories.aggregators:
        logger.debug("DIRECTORY  No aggregators configured — skipping")
        return []

    logger.info(
        "DIRECTORY  Starting — %d aggregator(s)", len(settings.directories.aggregators),
    )

    try:
        results = asyncio.run(_run_all())
        elapsed = time.time() - t0
        logger.info("DIRECTORY  Complete — %d result(s) in %.1fs", len(results), elapsed)
        return results
    except Exception as exc:
        elapsed = time.time() - t0
        logger.warning("DIRECTORY  Failed after %.1fs: %s", elapsed, exc)
        return []
