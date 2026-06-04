"""Probe common URL paths on a conference website to discover sub-pages.

Uses direct MCP session access (not ADK tool routing) to call stealthy_fetch
for each common path, returning only those that serve real content.
"""

import json
from conference_agent.tools.scrapling_tool import scrapling_toolset


async def probe_common_paths(base_url: str) -> list[dict]:
    """Probe common conference sub-page paths and return found ones.

    Args:
        base_url: The root URL of the conference website.

    Returns:
        A list of dicts with keys: url, link_text, category — one for each
        path that returned meaningful content (not a 404 / not-found page).
    """
    paths = {
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

    found = []
    session = await scrapling_toolset._mcp_session_manager.create_session()

    for path, category in paths.items():
        url = base_url.rstrip("/") + path
        try:
            result = await session.call_tool("stealthy_fetch", arguments={
                "url": url,
                "timeout": 15000,
                "solve_cloudflare": True,
                "headless": True,
                "main_content_only": True,
            })
            raw = json.loads(result.content[0].text)
            content = "".join(raw.get("content", []))

            # Skip 404s and pages that only say "Not Found"
            not_found_phrases = ["404", "page not found", "not found", "doesn't exist", "couldn't find"]
            content_lower = content.lower()
            if len(content) > 100 and not any(phrase in content_lower for phrase in not_found_phrases):
                found.append({
                    "url": url,
                    "link_text": path.strip("/").replace("/", " ").title(),
                    "category": category,
                })
        except Exception:
            # Silently skip failed probes (timeout, connection error, etc.)
            pass

    return found
