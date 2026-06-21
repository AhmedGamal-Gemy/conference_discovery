from pydantic import BaseModel
from typing import Optional


class RegistrationData(BaseModel):
    """Output of Prompt B (registration page)."""

    covers_accommodation: bool
    fee_range_usd: Optional[str] = None
    early_bird_deadline: Optional[str] = None
