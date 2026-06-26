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


def _extract_listing(html: str, config, url: str) -> list[dict]:
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
            detail_url = config.detail_url_pattern.replace("{path}", href) if config.detail_url_pattern else urljoin(url, href)

            entries.append({"title": title, "detail_url": detail_url})
        except Exception as exc:
            logger.debug("DIRECTORY  Skipping card entry: %s", exc)

    return entries


async def _strategy_a(session, config, topic) -> list[dict]:
    """Extract conference URLs via CSS selectors (Strategy A).

    1. Fetch listing page → extract entries
    2. Bulk-fetch all detail pages using ``css_selector`` to extract visit links directly
    """
    url = config.url_for(topic)
    if url is None:
        logger.info("DIRECTORY  %s — no URL for topic %r, skipping", config.name, topic)
        return []
    html = await _fetch_html(session, url)
    if not html:
        return []

    entries = _extract_listing(html, config, url)
    logger.info("DIRECTORY  %s — %d entries from listing", config.name, len(entries))
    if not entries:
        return []

    if not config.visit_link_selector:
        return [{"url": e["detail_url"], "title": e["title"], "snippet": ""} for e in entries]

    detail_urls = [e["detail_url"] for e in entries]

    try:
        r = await session.call_tool("bulk_stealthy_fetch", arguments={
            "urls": detail_urls,
            "timeout": 20000,
            "extraction_type": "html",
            "css_selector": config.visit_link_selector,
            "solve_cloudflare": False,
            "main_content_only": False,
            "headless": True,
        })
    except Exception as exc:
        logger.warning("DIRECTORY  %s — bulk fetch failed: %s — falling back to detail URLs", config.name, exc)
        return [{"url": e["detail_url"], "title": e["title"], "snippet": ""} for e in entries]

    results = []
    for i, tc in enumerate(r.content):
        if i >= len(entries):
            break
        try:
            raw = json.loads(tc.text)
            htmls = raw.get("content", [])
            snippet = htmls[0] if htmls else ""
            if snippet:
                soup = BeautifulSoup(snippet, "html.parser")
                link = soup.select_one("a")
                if link and link.get("href"):
                    results.append({"url": link["href"], "title": entries[i]["title"], "snippet": ""})
                    continue
            results.append({"url": entries[i]["detail_url"], "title": entries[i]["title"], "snippet": ""})
        except Exception:
            results.append({"url": entries[i]["detail_url"], "title": entries[i]["title"], "snippet": ""})

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
            "solve_cloudflare": True,
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
[{{"url": "...", "title": "...", "date": "..."}}]

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
        logger.debug("DIRECTORY  LLM raw response: %s", content[:500])
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, dict):
            # Check named keys first, then fall back to any list value
            for key in ("conferences", "results", "entries", "events", "items", "data"):
                val = parsed.get(key)
                if isinstance(val, list):
                    return val
            for val in parsed.values():
                if isinstance(val, list):
                    return val
            logger.warning("DIRECTORY  LLM returned dict with no list value — keys: %s", list(parsed.keys()))
        return []
    except Exception as exc:
        logger.warning("DIRECTORY  LLM extraction failed: %s", exc)
        return []


async def _strategy_b(session, config, topic) -> list[dict]:
    """Extract conference URLs via markdown + LLM (Strategy B)."""
    url = config.url_for(topic)
    if url is None:
        logger.info("DIRECTORY  %s — no URL for topic %r, skipping", config.name, topic)
        return []
    markdown = await _fetch_markdown(session, url)
    if not markdown:
        return []

    raw = await _extract_via_llm(markdown)
    # Normalize to Exa-style format (snippet not returned by LLM)
    results = [{"url": r.get("url", ""), "title": r.get("title", ""), "snippet": ""} for r in raw if r.get("url")]
    logger.info("DIRECTORY  %s — LLM found %d entries", config.name, len(results))
    return results


# ── Per-aggregator dispatch ────────────────────────────────────────────


async def _scrape_aggregator(session, config, topic) -> list[dict]:
    """Scrape a single aggregator by dispatching to strategy A or B."""
    url = config.url_for(topic)
    if url is None:
        logger.info("DIRECTORY  %s — no URL for topic %r, skipping", config.name, topic)
        return []
    logger.info("DIRECTORY  Scraping %s — %s", config.name, url)
    try:
        if config.extract_by_markdown or not config.listing_selector:
            return await _strategy_b(session, config, topic)
        return await _strategy_a(session, config, topic)
    except Exception as exc:
        logger.warning("DIRECTORY  Aggregator %s failed: %s", config.name, exc)
        return []


# ── Entry points ───────────────────────────────────────────────────────


async def _run_all(topic: str) -> list[dict]:
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
            agg_results = await _scrape_aggregator(session, agg, topic)
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
        results = asyncio.run(_run_all(topic))
        elapsed = time.time() - t0
        logger.info("DIRECTORY  Complete — %d result(s) in %.1fs", len(results), elapsed)
        return results
    except Exception as exc:
        elapsed = time.time() - t0
        logger.warning("DIRECTORY  Failed after %.1fs: %s", elapsed, exc)
        return []
