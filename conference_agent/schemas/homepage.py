from pydantic import BaseModel
from typing import Optional


class KeynoteSpeaker(BaseModel):
    """Simplified speaker extracted from homepage (no geocoding fields)."""

    name: str
    title: Optional[str] = None
    affiliation: Optional[str] = None
    country: Optional[str] = None
    is_scientific: bool = True


class SubPages(BaseModel):
    speakers: Optional[str] = None
    venue: Optional[str] = None
    registration: Optional[str] = None


class HomepageData(BaseModel):
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
    keynote_speakers: list[KeynoteSpeaker] = []
    sub_pages: SubPages = SubPages()
