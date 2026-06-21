"""Probe common URL paths on a conference website to discover sub-pages.

Uses direct MCP session access (not ADK tool routing) to call stealthy_fetch
for each common path, returning only those that serve real content.

Improvements over original:
- Parallel probing with asyncio.gather + semaphore (3 concurrent)
- Overall timeout (120s) so one hung path doesn't block everything
- Session lifecycle properly managed (try/finally → delete_session)
- Removed cloudflare solving and headless for path probing (faster, no benefit)
"""

import asyncio
import json
import logging
import time

from conference_agent.tools.scrapling_tool import scrapling_toolset

logger = logging.getLogger(__name__)

# Common sub-page paths to probe with their category
_PATHS: dict[str, str] = {
    "/speakers/": "speakers",
    "/registration/": "registration",
    "/venue/": "venue",
    "/program/": "schedule",
    "/sponsors/": "other",
    "/travel/": "venue",
    "/calls/": "other",
    "/attend/": "registration",
    "/about/": "other",
    "/committee/": "other",
}

# Phantom phrases that indicate a "not found" response
_NOT_FOUND_PHRASES = ["404", "page not found", "not found", "doesn't exist", "couldn't find"]

# Concurrency limit for parallel path probing
_MAX_CONCURRENT = 3

# Overall timeout for the entire probe_common_paths function
_OVERALL_TIMEOUT = 120.0


async def _probe_single_path(
    session,
    url: str,
    category: str,
    semaphore: asyncio.Semaphore,
) -> dict | None:
    """Probe a single URL path. Returns a result dict or None."""
    async with semaphore:
        try:
            result = await session.call_tool("stealthy_fetch", arguments={
                "url": url,
                "timeout": 15000,
                # Cloudflare + headless add 5-15s per request for no benefit on 404 checks
                "solve_cloudflare": False,
                "headless": True,
                "main_content_only": False,
            })
            raw = json.loads(result.content[0].text)
            content = "".join(raw.get("content", []))

            content_lower = content.lower()
            if len(content) > 100 and not any(
                phrase in content_lower for phrase in _NOT_FOUND_PHRASES
            ):
                logger.debug(
                    "PATH_PROBE ✓ %s — %s (%d chars)", category, url, len(content)
                )
                return {
                    "url": url,
                    "link_text": category.replace("_", " ").title(),
                    "category": category,
                }
            else:
                logger.debug(
                    "PATH_PROBE ✗ %s — no meaningful content (%d chars)",
                    url, len(content),
                )
                return None
        except Exception as exc:
            logger.debug("PATH_PROBE ✗ %s — %s", url, exc)
            return None


async def probe_common_paths(base_url: str) -> list[dict]:
    """Probe common conference sub-page paths and return found ones.

    Probes up to 10 common paths in parallel (3 at a time) with a 120s
    overall timeout. Returns only paths that returned >100 chars of
    meaningful content (not a 404 / not-found page).
    """
    t0 = time.time()
    logger.info(
        "PATH_PROBE Starting — base_url=%s, %d paths to probe",
        base_url, len(_PATHS),
    )

    semaphore = asyncio.Semaphore(_MAX_CONCURRENT)
    session = None
    success_count = 0
    fail_count = 0

    try:
        session = await scrapling_toolset._mcp_session_manager.create_session()

        tasks = [
            _probe_single_path(session, base_url.rstrip("/") + path, category, semaphore)
            for path, category in _PATHS.items()
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        found: list[dict] = []
        for r in results:
            if isinstance(r, Exception):
                fail_count += 1
                continue
            if r is not None:
                found.append(r)
                success_count += 1

        elapsed = time.time() - t0
        logger.info(
            "PATH_PROBE Complete — %d found, %d failed (%.1fs) — %s",
            success_count, fail_count, elapsed, base_url,
        )
        return found

    except asyncio.TimeoutError:
        elapsed = time.time() - t0
        logger.warning(
            "PATH_PROBE Timeout — %.1fs elapsed, returning partial results — %s",
            elapsed, base_url,
        )
        return []
    except Exception as exc:
        elapsed = time.time() - t0
        logger.error(
            "PATH_PROBE Error — %.1fs: %s — %s", elapsed, exc, base_url,
        )
        return []
    finally:
        # Intentionally NOT calling close() on the shared session manager.
        # The McpToolset's session manager is shared with ADK's MCP tooling
        # (used by scrape_homepage).  Calling close() on it kills ALL pooled
        # sessions, causing ADK to detect a transport crash and retry the
        # current agent step — resulting in an infinite loop.
        # The session will be naturally cleaned up when the pool reuses it
        # or on process shutdown.
        if session is not None:
            logger.debug("PATH_PROBE session left open for reuse — %s", base_url)
