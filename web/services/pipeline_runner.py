"""
PipelineRunner — wraps the ADK pipeline into an async generator.

Both the CLI (run_pipeline.py) and the web SSE endpoint use this class.
Yields StepProgress events for each step, then a final PipelineResult.
"""

import asyncio
import logging
import os
import time
from collections.abc import AsyncGenerator
from pathlib import Path
from urllib.parse import urljoin

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load conference_agent/.env before importing conference_agent (sets EXA_API_KEY etc.)
_ROOT = Path(__file__).parent.parent.parent
load_dotenv(_ROOT / "conference_agent" / ".env")

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part

from conference_agent.orchestrator import pipeline_orchestrator
from conference_agent.schemas.output_keys import output_keys
from conference_agent.schemas.conference import Conference


class StepProgress:
    """Progress event for a single pipeline step."""

    def __init__(
        self,
        step_name: str,
        step_label: str,
        status: str,  # "start", "complete", "error"
        error: str | None = None,
        elapsed: float = 0.0,
    ):
        self.step_name = step_name
        self.step_label = step_label
        self.status = status
        self.error = error
        self.elapsed = elapsed

    def __repr__(self):
        return (
            f"StepProgress(step={self.step_label!r}, status={self.status!r}, "
            f"elapsed={self.elapsed:.1f}s)"
        )


class PipelineResult:
    """Final result after all pipeline steps complete."""

    def __init__(
        self,
        conference: Conference | None,
        total_elapsed: float,
        steps_completed: int,
        state: dict | None = None,
    ):
        self.conference = conference
        self.total_elapsed = total_elapsed
        self.steps_completed = steps_completed
        self.state = state or {}

    def __repr__(self):
        conf_id = self.conference.conference_id if self.conference else None
        return (
            f"PipelineResult(conference={conf_id!r}, "
            f"steps={self.steps_completed}, elapsed={self.total_elapsed:.1f}s)"
        )


class PipelineRunner:
    """Runs the ADK conference pipeline and yields progress events."""

    STEP_NAMES = {
        "scrape_homepage": "1. Scrape homepage",
        "extract_homepage": "2. Extract homepage",
        "discover_links": "3. Discover links",
        "probe_paths": "4. Probe paths",
        "merge_links": "5. Merge links",
        "scrape_sub_pages": "6. Scrape sub-pages",
        "extract_sub_pages": "7. Extract sub-pages",
        "assemble_conference": "8. Assemble Conference",
    }

    async def run(
        self,
        url: str,
        user_id: str = "web_user",
        session_id: str | None = None,
    ) -> AsyncGenerator[StepProgress | PipelineResult, None]:
        """Run the full pipeline against *url*.

        Yields:
            StepProgress for each step transition (start/complete/error).
            PipelineResult when the pipeline finishes (or fails).
        """
        t0 = time.time()
        session_id = session_id or "web_session"

        logger.info(
            "Pipeline started — url=%s, user_id=%s, session_id=%s",
            url, user_id, session_id,
        )

        session_service = InMemorySessionService()
        await session_service.create_session(
            app_name="conference_discovery",
            user_id=user_id,
            session_id=session_id,
            state={output_keys.URL: url},
        )

        runner = Runner(
            agent=pipeline_orchestrator,
            app_name="conference_discovery",
            session_service=session_service,
        )

        last_author = None
        step_count = 0
        total_steps = len(self.STEP_NAMES)

        try:
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=Content(
                    role="user", parts=[Part(text="Process this conference")]
                ),
            ):
                author = event.author

                # Detect step start: author changed to a known step
                if author in self.STEP_NAMES and author != last_author:
                    step_label = self.STEP_NAMES[author]
                    elapsed = time.time() - t0
                    logger.info("Step [%s] started — %s (%.1fs)", author, step_label, elapsed)
                    yield StepProgress(
                        step_name=author,
                        step_label=step_label,
                        status="start",
                        elapsed=elapsed,
                    )
                    last_author = author

                # Detect step completion
                if event.is_final_response() and author in self.STEP_NAMES:
                    step_count += 1
                    elapsed = time.time() - t0
                    step_label = self.STEP_NAMES[author]
                    logger.info(
                        "Step [%s] completed — %s (%d/%d, %.1fs)",
                        author, step_label, step_count, total_steps, elapsed,
                    )
                    yield StepProgress(
                        step_name=author,
                        step_label=step_label,
                        status="complete",
                        elapsed=elapsed,
                    )

                # Detect errors (ADK Event has error_code/error_message fields)
                if event.error_code is not None:
                    error_msg = event.error_message or event.error_code
                    step_label = self.STEP_NAMES.get(author, author or "unknown")
                    elapsed = time.time() - t0
                    logger.error(
                        "Step [%s] error — %s (%.1fs): %s",
                        author, step_label, elapsed, error_msg,
                    )
                    yield StepProgress(
                        step_name=author or "unknown",
                        step_label=self.STEP_NAMES.get(author, author or "unknown"),
                        status="error",
                        error=error_msg,
                        elapsed=elapsed,
                    )

        except asyncio.CancelledError:
            # Client disconnected — yield error for current step, then result
            elapsed = time.time() - t0
            logger.warning("Pipeline cancelled — client disconnected (elapsed=%.1fs)", elapsed)
            if last_author and last_author in self.STEP_NAMES:
                yield StepProgress(
                    step_name=last_author,
                    step_label=self.STEP_NAMES[last_author],
                    status="error",
                    error="Client disconnected (CancelledError)",
                    elapsed=elapsed,
                )
            yield PipelineResult(
                conference=None,
                total_elapsed=elapsed,
                steps_completed=step_count,
            )
            return

        except Exception as exc:
            elapsed = time.time() - t0
            logger.exception(
                "Pipeline runner exception (elapsed=%.1fs, step=%s): %s",
                elapsed, last_author, exc,
            )
            if last_author and last_author in self.STEP_NAMES:
                yield StepProgress(
                    step_name=last_author,
                    step_label=self.STEP_NAMES[last_author],
                    status="error",
                    error=str(exc),
                    elapsed=elapsed,
                )
            yield PipelineResult(
                conference=None,
                total_elapsed=elapsed,
                steps_completed=step_count,
            )
            return

        # Pipeline finished — fetch final state
        elapsed = time.time() - t0
        logger.info(
            "Pipeline run loop completed — %d/%d steps (%.1fs), fetching final state",
            step_count, total_steps, elapsed,
        )
        updated = await session_service.get_session(
            app_name="conference_discovery",
            user_id=user_id,
            session_id=session_id,
        )
        if updated is None:
            state = {}
        else:
            state = updated.state or {}

        # Apply URL resolution fix (same as run_pipeline.py:80-104)
        base_url = state.get(output_keys.URL, "")
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

        # Extract Conference object
        conference = None
        conference_raw = state.get(output_keys.CONFERENCE_DATA, {})
        if isinstance(conference_raw, dict) and conference_raw.get("conference_id"):
            try:
                conference = Conference.model_validate(conference_raw)
                logger.info(
                    "Conference assembled — id=%s, name=%s, speakers=%d",
                    conference.conference_id,
                    conference.homepage.conference_name,
                    len(conference.speakers),
                )
            except Exception as e:
                logger.warning("Conference model validation failed: %s", e)
                conference = None
        else:
            logger.debug("No conference data in state (key=%s)", output_keys.CONFERENCE_DATA)

        yield PipelineResult(
            conference=conference,
            total_elapsed=elapsed,
            steps_completed=step_count,
            state=state,
        )
