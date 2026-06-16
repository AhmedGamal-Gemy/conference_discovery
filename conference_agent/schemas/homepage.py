from datetime import date
from pydantic import BaseModel
from typing import Optional


class SubPages(BaseModel):
    speakers: Optional[str] = None
    venue: Optional[str] = None
    registration: Optional[str] = None


class HomepageData(BaseModel):
    conference_name: str
    date_start: Optional[date] = None
    date_end: Optional[date] = None
    industry: Optional[str] = None
    sub_pages: SubPages
