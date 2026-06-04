from pydantic import BaseModel
from typing import Optional


class SubPages(BaseModel):
    speakers: Optional[str] = None
    venue: Optional[str] = None
    registration: Optional[str] = None


class HomepageData(BaseModel):
    conference_name: str
    date_start: Optional[str] = None
    date_end: Optional[str] = None
    industry: Optional[str] = None
    sub_pages: SubPages
