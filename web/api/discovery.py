"""Discovery endpoint - searches for conferences via Exa + LLM filter.

POST /api/discovery/search - accepts topic/months_ahead, returns
SSE stream of discovery progress + final result list.
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


@router.post("/search")
async def search_discovery(body: dict):
    """Run discovery search and stream results via SSE.

    Body (all optional, defaults from settings):
        topic: str = "medical"
        months_ahead: int = 3
        num_results: int = 5
    """
    topic = body.get("topic", settings.discovery.topic)
    months_ahead = body.get("months_ahead", settings.discovery.months_ahead)
    num_results = body.get("num_results", settings.exa.num_results)

    async def event_generator():
        t0 = asyncio.get_event_loop().time()
        yield {
            "event": STEP_COMPLETE,
            "data": json.dumps({
                "step": "search_exa",
                "label": "Searching Exa...",
                "elapsed": 0.0,
            }),
        }
        try:
            # Run sync discovery in thread pool to avoid blocking event loop
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                lambda: run_discovery(topic, months_ahead, num_results)
            )
            elapsed = asyncio.get_event_loop().time() - t0
            items = [
                DiscoveryResultItem(url=r["url"], title=r.get("title", ""))
                for r in results
            ]
            yield {
                "event": PIPELINE_COMPLETE,
                "data": json.dumps({
                    **DiscoveryComplete(
                        results=items,
                        total_elapsed=round(elapsed, 1),
                        steps_completed=1,
                        total_found=len(results),
                        accepted=len(results),
                    ).model_dump(),
                }),
            }
        except Exception as exc:
            logger.exception("Discovery error: %s", exc)
            yield {
                "event": STEP_COMPLETE,
                "data": json.dumps({
                    "step": "error",
                    "label": "Discovery failed",
                    "error": str(exc),
                    "elapsed": asyncio.get_event_loop().time() - t0,
                }),
            }
        yield {"event": DONE, "data": json.dumps({})}

    return EventSourceResponse(event_generator(), ping=15)