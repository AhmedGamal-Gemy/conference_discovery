"""Pydantic request/response models for the conference discovery demo UI.

Imports and reuses models from conference_agent.schemas — no duplication.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Literal, Optional

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict

# ── Load .env BEFORE importing conference_agent (triggers Exa init) ──

_ROOT = Path(__file__).parent.parent
load_dotenv(_ROOT / "conference_agent" / ".env", override=False)

# ── Reuse core models from the agent package ─────────────────────────
# Import directly from schema modules to avoid conference_agent.__init__
# which eagerly loads tools (Exa, MCP) requiring env vars.

from conference_agent.schemas.speaker import Speaker  # noqa: E402
from conference_agent.schemas.homepage import HomepageData, SubPages  # noqa: E402
from conference_agent.schemas.venue import VenueData  # noqa: E402
from conference_agent.schemas.registration import RegistrationData  # noqa: E402
from conference_agent.schemas.conference import Conference  # noqa: E402
from conference_agent.schemas.validation import ValidationResult  # noqa: E402
from conference_agent.schemas.output_keys import output_keys  # noqa: E402

if TYPE_CHECKING:
    from conference_agent.config import SystemSettings

# SystemSettings must be imported after .env is loaded by the API layer.
# We defer the import to the classmethod that needs it.

# ── SSE event type constants ─────────────────────────────────────────

STEP_START = "step_start"
STEP_COMPLETE = "step_complete"
STEP_ERROR = "step_error"
PIPELINE_COMPLETE = "pipeline_complete"
DONE = "done"
DISCOVERY_STEP = "discovery_step"
DISCOVERY_COMPLETE = "discovery_complete"

# ── Pipeline request / response ──────────────────────────────────────


class PipelineRequest(BaseModel):
    """Request to run the conference discovery pipeline."""

    url: str
    user_id: str = "web_user"


class PipelineBatchRequest(BaseModel):
    """Request to run the pipeline on multiple conferences sequentially."""

    urls: list[str]
    user_id: str = "web_user"


class StepProgress(BaseModel):
    """Progress update for a single pipeline step (emitted via SSE)."""

    model_config = ConfigDict(extra="forbid")

    step: str
    label: str
    index: int
    total: int
    elapsed: float
    status: Literal["start", "complete", "error"]
    error: Optional[str] = None


class PipelineResult(BaseModel):
    """Final result after the pipeline completes."""

    model_config = ConfigDict(extra="forbid")

    conference: dict
    total_elapsed: float
    steps_completed: int
    validation: Optional[dict] = None
    state: Optional[dict] = None


# ── Discovery request / response ─────────────────────────────────────


class DiscoveryRequest(BaseModel):
    """Request to run the discovery pipeline (searches for conferences)."""

    model_config = ConfigDict(extra="forbid")

    topic: str = "medical"
    months_ahead: int = 3
    num_results: int = 5


class DiscoveryResultItem(BaseModel):
    """A single discovered conference result."""

    model_config = ConfigDict(extra="forbid")

    url: str
    title: str


class DiscoveryComplete(BaseModel):
    """Final result after the discovery pipeline completes."""

    model_config = ConfigDict(extra="forbid")

    results: list[DiscoveryResultItem]
    total_elapsed: float
    steps_completed: int
    total_found: int
    accepted: int


# ── Settings ─────────────────────────────────────────────────────────


class SettingsResponse(BaseModel):
    """Mirrors SystemSettings structure for the frontend."""

    model_config = ConfigDict(extra="forbid")

    discovery: dict
    exa: dict
    validation: dict
    output: dict
    llm: dict
    scrapling_mcp_url: str
    debug: bool

    @classmethod
    def from_system_settings(cls, settings: "SystemSettings") -> "SettingsResponse":
        """Create from SystemSettings.model_dump()."""
        dump = settings.model_dump()
        return cls(**dump)


class SettingsUpdateRequest(BaseModel):
    """Partial update — all fields optional, nested structures as dicts."""

    model_config = ConfigDict(extra="forbid")

    discovery: Optional[dict] = None
    exa: Optional[dict] = None
    validation: Optional[dict] = None
    output: Optional[dict] = None
    llm: Optional[dict] = None
    scrapling_mcp_url: Optional[str] = None
    debug: Optional[bool] = None


# ── Conference response (flattened for frontend) ─────────────────────


class SpeakerResponse(BaseModel):
    """Flattened speaker for frontend consumption."""

    model_config = ConfigDict(extra="forbid")

    name: str
    title: Optional[str] = None
    affiliation: Optional[str] = None
    country: Optional[str] = None
    is_scientific: bool
    travel_hours: Optional[float] = None
    is_local: Optional[bool] = None
    is_usa: Optional[bool] = None


class VenueResponse(BaseModel):
    """Flattened venue for frontend."""

    model_config = ConfigDict(extra="forbid")

    venue_name: Optional[str] = None
    venue_address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    is_hotel: bool = False


class RegistrationResponse(BaseModel):
    """Flattened registration for frontend."""

    model_config = ConfigDict(extra="forbid")

    covers_accommodation: bool
    fee_range_usd: Optional[str] = None
    early_bird_deadline: Optional[str] = None


class SubPagesResponse(BaseModel):
    """Flattened sub-pages URLs for frontend."""

    model_config = ConfigDict(extra="forbid")

    speakers: Optional[str] = None
    venue: Optional[str] = None
    registration: Optional[str] = None


class HomepageResponse(BaseModel):
    """Flattened homepage data for frontend."""

    model_config = ConfigDict(extra="forbid")

    conference_name: str
    conference_acronym: Optional[str] = None
    date_start: Optional[str] = None
    date_end: Optional[str] = None
    industry: Optional[str] = None
    sector_tags: list[str] = []
    conference_format: Optional[str] = None
    organizer: Optional[str] = None
    submission_deadline: Optional[str] = None
    venue_city: Optional[str] = None
    venue_country: Optional[str] = None
    sub_pages: SubPagesResponse


class ConferenceResponse(BaseModel):
    """Flattened conference model for frontend consumption.

    All fields are optional with sensible defaults — missing or null pipeline
    data produces null/empty values in JSON, never validation errors.
    """

    model_config = ConfigDict(extra="forbid")

    # Identity
    conference_id: str = ""

    # Homepage fields (flattened)
    conference_name: str = ""
    conference_acronym: Optional[str] = None
    date_start: Optional[str] = None
    date_end: Optional[str] = None
    industry: Optional[str] = None
    sector_tags: list[str] = []
    conference_format: Optional[str] = None
    organizer: Optional[str] = None
    submission_deadline: Optional[str] = None
    venue_city: Optional[str] = None
    venue_country: Optional[str] = None
    sub_pages: Optional[SubPagesResponse] = None

    # Venue fields (flattened)
    venue_name: Optional[str] = None
    venue_address: Optional[str] = None
    venue_country_detail: Optional[str] = None

    # Registration fields (flattened)
    covers_accommodation: bool = False
    fee_range_usd: Optional[str] = None
    early_bird_deadline: Optional[str] = None

    # Speakers
    speakers: list[SpeakerResponse] = []

    # Derived counters
    total_speakers: int = 0
    non_local_count: int = 0
    non_usa_count: int = 0

    # URLs
    website_url: str = ""
    speakers_page_url: Optional[str] = None

    @classmethod
    def from_pipeline_state(cls, state: dict) -> "ConferenceResponse":
        """Extract ConferenceResponse from pipeline state dict.

        Uses output_keys.CONFERENCE_DATA to locate the conference data
        in the session state. Handles all edge cases gracefully:
        - Missing key: returns empty defaults
        - None value: returns empty defaults
        - Dict value: validates and constructs
        - Pydantic Conference instance: calls .model_dump() first

        Never raises — frontend always gets a valid response.
        """
        raw = state.get(output_keys.CONFERENCE_DATA)

        if raw is None:
            return cls()

        # If it's already a Pydantic Conference model, dump to dict
        if isinstance(raw, Conference):
            raw = raw.model_dump()

        # If it's not a dict at this point, return empty defaults
        if not isinstance(raw, dict):
            return cls()

        # If the dict has no conference_id, treat as empty
        if "conference_id" not in raw or raw["conference_id"] is None:
            return cls()

        # Validate against the Conference model first to normalize structure
        try:
            conference = Conference.model_validate(raw)
        except Exception:
            return cls()

        return cls(
            conference_id=conference.conference_id,
            conference_name=conference.homepage.conference_name,
            conference_acronym=conference.homepage.conference_acronym,
            date_start=conference.homepage.date_start,
            date_end=conference.homepage.date_end,
            industry=conference.homepage.industry,
            sector_tags=conference.homepage.sector_tags,
            conference_format=conference.homepage.conference_format,
            organizer=conference.homepage.organizer,
            submission_deadline=conference.homepage.submission_deadline,
            venue_city=conference.venue.city,
            venue_country=conference.venue.country,
            sub_pages=SubPagesResponse(
                speakers=conference.homepage.sub_pages.speakers,
                venue=conference.homepage.sub_pages.venue,
                registration=conference.homepage.sub_pages.registration,
            ),
            venue_name=conference.venue.venue_name,
            venue_address=conference.venue.venue_address,
            venue_country_detail=conference.venue.country,
            covers_accommodation=conference.registration.covers_accommodation,
            fee_range_usd=conference.registration.fee_range_usd,
            early_bird_deadline=conference.registration.early_bird_deadline,
            speakers=[
                SpeakerResponse(
                    name=s.name,
                    title=s.title,
                    affiliation=s.affiliation,
                    country=s.country,
                    is_scientific=s.is_scientific,
                    travel_hours=s.travel_hours,
                    is_local=s.is_local,
                    is_usa=s.is_usa,
                )
                for s in conference.speakers
            ],
            total_speakers=conference.total_speakers,
            non_local_count=conference.non_local_count,
            non_usa_count=conference.non_usa_count,
            website_url=conference.website_url,
            speakers_page_url=conference.speakers_page_url,
        )
