"""Registration page extraction target for the LLM."""

from pydantic import BaseModel
from typing import Optional, List


class RegistrationData(BaseModel):
    """Output of the registration page extraction prompt."""

    covers_accommodation: bool = False
    fee_range_usd: Optional[str] = None              # P2: e.g. "400–1900 USD"
    early_bird_deadline: Optional[str] = None        # P2: YYYY-MM-DD or null
