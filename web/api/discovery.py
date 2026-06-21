"""Discovery endpoint - searches for conferences via Exa + LLM filter.

POST /api/discovery/search - accepts topic/months_ahead, streams:
  - search_start:       discovery search has begun
  - result_found:       one conference passed the LLM relevance filter
  - search_complete:    all Exa queries done, filtering done, results finalised
  - done:               SSE stream ended
"""

import asyncio
import json
import logging
from pathlib import Path

from fastapi import APIRouter
from sse_starlette import EventSourceResponse

from dotenv import load_dotenv
from web.schemas import (
    STEP_COMPLETE,
    PIPELINE_COMPLETE,
    DONE,
    DiscoveryComplete,
    DiscoveryResultItem,
)
from conference_agent.tools.discovery_tool import run_discovery
from conference_agent.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# ── New event types ──────────────────────────────────────────────────────
SEARCH_START = "search_start"
RESULT_FOUND = "result_found"
SEARCH_COMPLETE = "search_complete"


@router.post("/search")
async def search_discovery(body: dict):
    """Run discovery search and stream results as they're found.

    Body (all optional, defaults from settings):
        topic: str = "medical"
        months_ahead: int = 3
        num_results: int = 5

    Streams one 'result_found' event per accepted conference,
    followed by a single 'search_complete' with the final summary.
    """
    topic = body.get("topic", settings.discovery.topic)
    months_ahead = body.get("months_ahead", settings.discovery.months_ahead)
    num_results = body.get("num_results", settings.exa.num_results)

    logger.info(
        "DISCOVERY  Request received — topic=%s, months_ahead=%d, num_results=%d",
        topic, months_ahead, num_results,
    )

    async def event_generator():
        t0 = asyncio.get_event_loop().time()

        # Check service health before starting
        try:
            from conference_agent.health import run_all_checks
            health = await run_all_checks(scrapling_url=settings.scrapling_mcp_url)
            health.log()
            required = {"scrapling-mcp", "litellm-proxy", "exa-api-key", "freetheai-api-key"}
            down = [s.name for s in health.services if not s.ok() and s.name in required]
            if down:
                logger.warning("DISCOVERY  Required services DOWN: %s", down)
        except Exception:
            logger.exception("DISCOVERY  Health check failed — continuing anyway")

        # Signal search has started
        yield {
            "event": SEARCH_START,
            "data": json.dumps({
                "topic": topic,
                "months_ahead": months_ahead,
                "elapsed": 0.0,
            }),
        }

        try:
            loop = asyncio.get_event_loop()
            queue: asyncio.Queue[tuple[str, dict | None]] = asyncio.Queue()

            # Producer: runs sync generator in thread, pushes results into queue
            def _produce() -> None:
                for result in run_discovery(topic, months_ahead, num_results):
                    loop.call_soon_threadsafe(
                        queue.put_nowait, ("result", result)
                    )
                loop.call_soon_threadsafe(queue.put_nowait, ("done", None))

            loop.run_in_executor(None, _produce)

            found_count = 0
            while True:
                msg_type, payload = await queue.get()
                if msg_type == "done":
                    break

                found_count += 1
                elapsed = asyncio.get_event_loop().time() - t0
                item = DiscoveryResultItem(
                    url=payload["url"],
                    title=payload.get("title", ""),
                )
                yield {
                    "event": RESULT_FOUND,
                    "data": json.dumps({
                        "item": item.model_dump(),
                        "count": found_count,
                        "elapsed": round(elapsed, 1),
                    }),
                }

            elapsed = asyncio.get_event_loop().time() - t0
            logger.info(
                "DISCOVERY  Search complete — %d results accepted (%.1fs)",
                found_count, elapsed,
            )
            yield {
                "event": SEARCH_COMPLETE,
                "data": json.dumps({
                    "total_found": found_count,
                    "elapsed": round(elapsed, 1),
                }),
            }

        except Exception as exc:
            logger.exception("DISCOVERY  Error: %s", exc)
            yield {
                "event": SEARCH_COMPLETE,
                "data": json.dumps({
                    "total_found": 0,
                    "error": str(exc),
                    "elapsed": asyncio.get_event_loop().time() - t0,
                }),
            }

        yield {"event": DONE, "data": json.dumps({})}

    return EventSourceResponse(event_generator(), ping=15)