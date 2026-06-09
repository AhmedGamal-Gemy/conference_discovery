from pydantic import BaseModel
from typing import Optional, List

from .homepage import HomepageData
from .venue import VenueData
from .registration import RegistrationData
from .speaker import Speaker


class Conference(BaseModel):
    """Fully assembled conference model.

    Composes HomepageData + VenueData + RegistrationData + speakers,
    plus derived counters and new enrichment fields (sector_tags, fees).
    """

    # Identity
    conference_id: str

    # Composed sub-models
    homepage: HomepageData
    venue: VenueData
    registration: RegistrationData
    speakers: List[Speaker]

    # Derived counters
    total_speakers: int
    non_local_count: int
    non_usa_count: int

    # URLs
    website_url: str
    speakers_page_url: Optional[str] = None

    # Enrichment (mirrors HomepageData.sector_tags + RegistrationData fee fields)
    sector_tags: List[str] = []
    fee_range_usd: Optional[str] = None
    early_bird_deadline: Optional[str] = None
