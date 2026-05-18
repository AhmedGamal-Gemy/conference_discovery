from pydantic import BaseModel
from typing import Optional


class VenueData(BaseModel):
    """Output of Prompt B (venue page)."""

    venue_name: Optional[str] = None
    venue_address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    is_hotel: bool = False
