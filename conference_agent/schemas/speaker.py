from pydantic import BaseModel
from typing import Optional


class Speaker(BaseModel):
    """Represents a single conference speaker.
    Fields marked "added after Maps API call" are enriched post-geocoding.
    """

    name: str
    title: Optional[str] = None
    affiliation: Optional[str] = None
    country: Optional[str] = None
    is_scientific: bool
    travel_hours: Optional[float] = None
    is_local: Optional[bool] = None
    is_usa: Optional[bool] = None
    # Added after Maps API call — populated via geocoding enrichment


class SpeakersData(BaseModel):
    """Output of Prompt B (speakers page)."""

    speakers: list[Speaker] = []
    speakers_confirmed: bool = False
    notes: str = ""