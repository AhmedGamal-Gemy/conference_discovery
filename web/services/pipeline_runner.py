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
from conference_agent.schemas.homepage import HomepageData
from conference_agent.schemas.speaker import Speaker, SpeakersData
from conference_agent.schemas.venue import VenueData
from conference_agent.schemas.registration import RegistrationData
from conference_agent.tools.intermediate_output import save_session_state


class PipelineRetry(Exception):
    """Internal exception to signal a transient pipeline failure — retry."""


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
        "validate_conference": "9. Validate",
    }

    # Maximum wall-clock seconds allowed for the entire pipeline run.
    # Individual steps inherit this budget; the runner aborts and yields
    # an error if the deadline is exceeded.
    PIPELINE_TIMEOUT: float = 600.0  # 10 minutes

    async def run(
        self,
        url: str,
        user_id: str = "web_user",
        session_id: str | None = None,
        max_retries: int = 0,
    ) -> AsyncGenerator[StepProgress | PipelineResult, None]:
        """Run the full pipeline against *url*, with optional retries.

        If *max_retries* > 0, the pipeline is restarted from scratch each time
        it fails (with exponential backoff).  Events are only yielded on the
        final attempt — transient failures are invisible to the consumer.

        Yields:
            StepProgress for each step transition (start/complete/error).
            PipelineResult when the pipeline finishes (or fails).
        """
        attempts = 1 + max_retries
        for attempt in range(attempts):
            attempt_suffix = f"_retry_{attempt}" if attempt > 0 else ""
            attempt_session_id = f"{session_id or 'web_session'}{attempt_suffix}"

            if attempt > 0:
                delay = min(2 ** (attempt - 1), 30)
                logger.warning(
                    "Pipeline retry %d/%d — waiting %.1fs then restarting from scratch",
                    attempt + 1, attempts, delay,
                )
                yield StepProgress(
                    step_name="retry",
                    step_label=f"Retry {attempt + 1}/{attempts}",
                    status="start",
                    elapsed=0.0,
                )
                await asyncio.sleep(delay)

            t0 = time.time()
            logger.info(
                "Pipeline attempt %d/%d — url=%s, session=%s",
                attempt + 1, attempts, url, attempt_session_id,
            )

            session_service = InMemorySessionService()
            await session_service.create_session(
                app_name="conference_discovery",
                user_id=user_id,
                session_id=attempt_session_id,
                state={output_keys.URL: url},
            )

            runner = Runner(
                agent=pipeline_orchestrator,
                app_name="conference_discovery",
                session_service=session_service,
            )

            last_step = None
            step_count = 0
            total_steps = len(self.STEP_NAMES)

            try:
                async for event in runner.run_async(
                    user_id=user_id,
                    session_id=attempt_session_id,
                    new_message=Content(
                        role="user",
                        parts=[Part(text="Process this conference")],
                    ),
                ):
                    # Enforce pipeline-level timeout
                    if time.time() - t0 > self.PIPELINE_TIMEOUT:
                        logger.error(
                            "Pipeline timeout — %.1fs exceeded (limit=%.1fs), step=%s",
                            time.time() - t0, self.PIPELINE_TIMEOUT, last_step,
                        )
                        if last_step and last_step in self.STEP_NAMES:
                            yield StepProgress(
                                step_name=last_step,
                                step_label=self.STEP_NAMES[last_step],
                                status="error",
                                error=f"Pipeline timed out after {self.PIPELINE_TIMEOUT:.0f}s (step: {last_step})",
                                elapsed=time.time() - t0,
                            )
                        yield PipelineResult(
                            conference=None,
                            total_elapsed=time.time() - t0,
                            steps_completed=step_count,
                        )
                        return

                    # Use node_info.name (clean node name) instead of event.author.
                    # Workflow sets ctx.event_author = "pipeline_orchestrator" for ALL
                    # child events, so event.author is always the workflow name and
                    # never matches STEP_NAMES keys. node_info.name strips @run_id
                    # from the path segment, returning "probe_paths", "scrape_homepage",
                    # etc. — which exactly matches STEP_NAMES keys.
                    step_name = event.node_info.name or event.author

                    # Detect step start (first event from a new step)
                    if step_name in self.STEP_NAMES and step_name != last_step:
                        step_label = self.STEP_NAMES[step_name]
                        elapsed = time.time() - t0
                        logger.info("Step [%s] started — %s (%.1fs)", step_name, step_label, elapsed)
                        yield StepProgress(
                            step_name=step_name,
                            step_label=step_label,
                            status="start",
                            elapsed=elapsed,
                        )
                        last_step = step_name

                    # Detect step completion.
                    # LlmAgent steps: event.is_final_response() fires when LLM
                    #   produces a final text response.
                    # FunctionNode steps: event.output is not None fires when the
                    #   function returns a non-None value (Event(output=data)).
                    #   These events NEVER satisfy is_final_response() because they
                    #   lack content parts with text.
                    is_step_complete = (
                        event.is_final_response()
                        or (event.output is not None and step_name in self.STEP_NAMES)
                    )
                    if is_step_complete and step_name in self.STEP_NAMES:
                        step_count += 1
                        elapsed = time.time() - t0
                        step_label = self.STEP_NAMES[step_name]
                        logger.info(
                            "Step [%s] completed — %s (%d/%d, %.1fs)",
                            step_name, step_label, step_count, total_steps, elapsed,
                        )
                        yield StepProgress(
                            step_name=step_name,
                            step_label=step_label,
                            status="complete",
                            elapsed=elapsed,
                        )

                    # Detect errors (ADK Event has error_code/error_message fields)
                    if event.error_code is not None:
                        error_msg = event.error_message or event.error_code
                        step_label = self.STEP_NAMES.get(step_name, step_name or "unknown")
                        elapsed = time.time() - t0
                        logger.error(
                            "Step [%s] error — %s (%.1fs): %s",
                            step_name, step_label, elapsed, error_msg,
                        )
                        if attempt < attempts - 1:
                            raise PipelineRetry(f"Step {step_name} failed: {error_msg}")
                        yield StepProgress(
                            step_name=step_name or "unknown",
                            step_label=self.STEP_NAMES.get(step_name, step_name or "unknown"),
                            status="error",
                            error=error_msg,
                            elapsed=elapsed,
                        )

            except asyncio.CancelledError:
                elapsed = time.time() - t0
                logger.warning("Pipeline cancelled — client disconnected (elapsed=%.1fs)", elapsed)
                if last_step and last_step in self.STEP_NAMES:
                    yield StepProgress(
                        step_name=last_step,
                        step_label=self.STEP_NAMES[last_step],
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

            except PipelineRetry:
                continue  # Loop will restart from scratch

            except Exception as exc:
                elapsed = time.time() - t0
                logger.exception(
                    "Pipeline runner exception (elapsed=%.1fs, step=%s): %s",
                    elapsed, last_step, exc,
                )
                if attempt < attempts - 1:
                    continue
                if last_step and last_step in self.STEP_NAMES:
                    yield StepProgress(
                        step_name=last_step,
                        step_label=self.STEP_NAMES[last_step],
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

            # Pipeline finished successfully — fetch final state
            elapsed = time.time() - t0
            logger.info(
                "Pipeline run loop completed — %d/%d steps (%.1fs), fetching final state",
                step_count, total_steps, elapsed,
            )
            updated = await session_service.get_session(
                app_name="conference_discovery",
                user_id=user_id,
                session_id=attempt_session_id,
            )
            if updated is None:
                state = {}
            else:
                state = updated.state or {}

            # Log what we got from state
            logger.info(
                "PIPELINE  Final state keys: %s",
                list(state.keys()) if state else "empty",
            )

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

            # Assemble Conference object from individual state components
            conference = None
            conference_raw = state.get(output_keys.CONFERENCE_DATA)

            if isinstance(conference_raw, dict) and conference_raw.get("conference_id"):
                # Already stored as a complete Conference dict — use as-is
                try:
                    conference = Conference.model_validate(conference_raw)
                except Exception as e:
                    logger.warning("Conference model validation failed: %s", e)

            if conference is None:
                # Build from individual components in state
                hp_raw = state.get(output_keys.HOMEPAGE_DATA, {})
                sp_raw = state.get(output_keys.SUB_PAGES_DATA, {})
                sub_pages_urls = state.get(output_keys.SUB_PAGES_URLS, {})
                url = state.get(output_keys.URL, "")

                if isinstance(hp_raw, dict) and hp_raw.get("conference_name"):
                    try:
                        homepage = HomepageData.model_validate(hp_raw)
                        sp = sp_raw if isinstance(sp_raw, dict) else {}
                        speakers_data = SpeakersData.model_validate(sp.get("speakers", {}))
                        venue = VenueData.model_validate(sp.get("venue", {}))
                        registration = RegistrationData.model_validate(sp.get("registration", {}))

                        # Merge sub-page speakers with homepage keynote_speakers.
                        # KeynoteSpeaker → Speaker conversion fills in default
                        # geocoding fields that KeynoteSpeaker doesn't have.
                        # Dedup by name (case-insensitive) to avoid double-counting
                        # when a keynote also appears on the speakers page.
                        sub_speakers = list(speakers_data.speakers)
                        existing_names = {s.name.strip().lower() for s in sub_speakers if s.name}
                        for ks in homepage.keynote_speakers:
                            if ks.name and ks.name.strip().lower() not in existing_names:
                                sub_speakers.append(
                                    Speaker(
                                        name=ks.name,
                                        title=ks.title,
                                        affiliation=ks.affiliation,
                                        country=ks.country,
                                        is_scientific=ks.is_scientific,
                                    )
                                )
                                existing_names.add(ks.name.strip().lower())

                        speakers = sub_speakers
                        # Use the higher of merged count vs raw sources — the homepage
                        # often advertises more speakers than we could extract names for.
                        total = max(len(speakers), len(speakers_data.speakers) + len(homepage.keynote_speakers))
                        non_local = sum(1 for s in speakers if s.is_local is False)
                        non_usa = sum(1 for s in speakers if s.country is None or s.country != "USA")

                        conference = Conference(
                            conference_id=url,
                            homepage=homepage,
                            venue=venue,
                            registration=registration,
                            speakers=speakers,
                            total_speakers=total,
                            non_local_count=non_local,
                            non_usa_count=non_usa,
                            website_url=url,
                            speakers_page_url=(
                                sub_pages_urls.get("speakers")
                                if isinstance(sub_pages_urls, dict) else None
                            ),
                        )

                        state[output_keys.CONFERENCE_DATA] = conference.model_dump()

                        logger.info(
                            "Conference assembled from components — id=%s, name=%s, speakers=%d",
                            conference.conference_id,
                            conference.homepage.conference_name,
                            len(conference.speakers),
                        )
                    except Exception as e:
                        logger.warning("Conference assembly from components failed: %s", e)
                else:
                    logger.debug("No homepage data in state (key=%s)", output_keys.HOMEPAGE_DATA)

            # Save intermediate outputs to disk for debugging
            try:
                saved = save_session_state(state, prefix="")
                for path in saved:
                    logger.debug("Saved intermediate output: %s", path)
            except Exception as e:
                logger.warning("Failed to save intermediate output: %s", e)

            yield PipelineResult(
                conference=conference,
                total_elapsed=elapsed,
                steps_completed=step_count,
                state=state,
            )
            return  # Exit retry loop — pipeline succeeded
