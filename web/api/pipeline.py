"""Pipeline SSE streaming endpoint.

POST /api/pipeline/run — accepts PipelineRequest JSON body, returns
EventSourceResponse (SSE stream) with step_start/step_complete/step_error/
pipeline_complete/done events.
"""

import asyncio
import json
import logging
from pathlib import Path
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

from dotenv import load_dotenv
from fastapi import APIRouter, Request
from sse_starlette import EventSourceResponse

# Load conference_agent/.env BEFORE importing conference_agent modules
# (sets EXA_API_KEY etc. before exa_tool.py creates its client at module load)
_ROOT = Path(__file__).parent.parent.parent
load_dotenv(_ROOT / "conference_agent" / ".env")

from conference_agent.schemas.output_keys import output_keys
from web.schemas import (
    STEP_START,
    STEP_COMPLETE,
    STEP_ERROR,
    PIPELINE_COMPLETE,
    DONE,
    ConferenceResponse,
    PipelineRequest,
)
from web.services.pipeline_runner import (
    PipelineRunner,
    StepProgress as RunnerStep,
    PipelineResult,
)

router = APIRouter(prefix="/api/pipeline")


@router.post("/run")
async def run_pipeline(request: Request, body: PipelineRequest):
    """Run the conference discovery pipeline and stream progress via SSE.

    Returns an EventSourceResponse that emits these event types:
      - step_start:       {step, label, index, total, elapsed}
      - step_complete:    {step, label, index, total, elapsed}
      - step_error:       {step, label, index, total, error, elapsed}
      - pipeline_complete:{conference, total_elapsed, steps_completed}
      - done:             {}
    """

    async def event_generator():
        runner = PipelineRunner()
        step_names = runner.STEP_NAMES
        # Precompute 1-based index for each step name
        step_index_map = {name: i + 1 for i, name in enumerate(step_names)}
        total_steps = len(step_names)

        logger.info(
            "SSE pipeline request — url=%s, user_id=%s",
            body.url, body.user_id or "anonymous",
        )

        try:
            async for evt in runner.run(url=body.url, user_id=body.user_id):
                # ── Check client disconnect proactively ────────────────
                if await request.is_disconnected():
                    logger.warning("Client disconnected during SSE stream (url=%s)", body.url)
                    return

                # ── StepProgress events (start / complete / error) ────
                if isinstance(evt, RunnerStep):
                    idx = step_index_map.get(evt.step_name, 0)
                    data = {
                        "step": evt.step_name,
                        "label": evt.step_label,
                        "index": idx,
                        "total": total_steps,
                        "elapsed": round(evt.elapsed, 1),
                    }

                    if evt.status == "start":
                        logger.debug("SSE emit: %s → %s (idx=%d/%d)", STEP_START, evt.step_name, idx, total_steps)
                        yield {"event": STEP_START, "data": json.dumps(data)}
                    elif evt.status == "complete":
                        logger.debug("SSE emit: %s → %s (idx=%d/%d)", STEP_COMPLETE, evt.step_name, idx, total_steps)
                        yield {"event": STEP_COMPLETE, "data": json.dumps(data)}
                    elif evt.status == "error":
                        logger.error("SSE emit: %s → %s — %s", STEP_ERROR, evt.step_name, evt.error)
                        yield {
                            "event": STEP_ERROR,
                            "data": json.dumps({**data, "error": evt.error}),
                        }

                # ── PipelineResult — apply url resolution, then emit ──
                elif isinstance(evt, PipelineResult):
                    state = evt.state or {}
                    base_url = state.get(output_keys.URL, "")

                    # URL resolution post-processing (same as run_pipeline.py:80-104)
                    if base_url:
                        # Fix sub_pages URLs in homepage_data
                        homepage_data = state.get(output_keys.HOMEPAGE_DATA, {})
                        if isinstance(homepage_data, dict):
                            sub_pages = homepage_data.get("sub_pages", {})
                            for key in ("speakers", "venue", "registration"):
                                if sub_pages.get(key):
                                    sub_pages[key] = urljoin(base_url, sub_pages[key])

                        # Fix discovered_links URLs
                        discovered_links = state.get(output_keys.DISCOVERED_LINKS, {})
                        if isinstance(discovered_links, dict):
                            for link in discovered_links.get("links", []):
                                if link.get("url"):
                                    link["url"] = urljoin(base_url, link["url"])

                        # Fix sub_pages_urls
                        sub_pages_urls = state.get(output_keys.SUB_PAGES_URLS, {})
                        if isinstance(sub_pages_urls, dict):
                            for key in ("speakers", "venue", "registration"):
                                if sub_pages_urls.get(key):
                                    sub_pages_urls[key] = urljoin(base_url, sub_pages_urls[key])

                    # Serialise Conference model → flattened dict for SSE
                    # (ConferenceResponse flattens nested homepage/venue/registration)
                    conference_dict = (
                        ConferenceResponse.from_pipeline_state(state).model_dump()
                        if state.get(output_keys.CONFERENCE_DATA)
                        else None
                    )

                    conf_name = conference_dict.get("conference_name") if conference_dict else None
                    logger.info(
                        "Pipeline complete — url=%s, conference=%s, steps=%d, %.1fs",
                        body.url, conf_name or "N/A", evt.steps_completed, evt.total_elapsed,
                    )

                    yield {
                        "event": PIPELINE_COMPLETE,
                        "data": json.dumps({
                            "conference": conference_dict,
                            "total_elapsed": round(evt.total_elapsed, 1),
                            "steps_completed": evt.steps_completed,
                        }),
                    }

                    yield {"event": DONE, "data": json.dumps({})}
                    return

        except asyncio.CancelledError:
            logger.warning("SSE generator cancelled (client disconnect)")
            yield {"event": DONE, "data": json.dumps({})}
            return

        except Exception as exc:
            logger.exception("SSE generator exception: %s", exc)
            yield {
                "event": STEP_ERROR,
                "data": json.dumps({
                    "step": "unknown",
                    "label": "Unknown",
                    "error": str(exc),
                }),
            }
            yield {"event": DONE, "data": json.dumps({})}
            return

    return EventSourceResponse(event_generator(), ping=15)
