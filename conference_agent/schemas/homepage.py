from pydantic import BaseModel
from typing import Optional, List


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
    sector_tags: List[str] = []                       # P2: full topic list
    conference_format: Optional[str] = None
    organizer: Optional[str] = None
    submission_deadline: Optional[str] = None
    venue_city: Optional[str] = None
    venue_country: Optional[str] = None
    sub_pages: SubPages