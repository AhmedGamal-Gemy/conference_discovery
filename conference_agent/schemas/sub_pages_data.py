"""Combined output of step5 — all sub-page extractions."""

from pydantic import BaseModel

from .speaker import SpeakersData
from .venue import VenueData
from .registration import RegistrationData


class SubPagesData(BaseModel):
    """Step 5 output — all sub-page extractions in a single model."""

    speakers: SpeakersData
    venue: VenueData
    registration: RegistrationData
