import json
import os
from datetime import date
from typing import Optional

from google.adk.tools import FunctionTool

from conference_agent.schemas.speaker import SpeakersData
from conference_agent.schemas.venue import VenueData
from conference_agent.schemas.registration import RegistrationData
from conference_agent.schemas.homepage import HomepageData
from conference_agent.schemas.validation import ValidationResult


SENT_FILE = os.path.join(
    os.path.dirname(__file__), "..", "..", "output", "sent.json"
)


def _load_sent() -> list[str]:
    try:
        with open(SENT_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def validate_conference(
    conference_id: str,
    homepage_data: dict,
    speakers_data: dict,
    venue_data: dict,
    registration_data: dict,
) -> dict:
    """
    Runs 9 validation conditions on extracted conference data.
    Fail fast — stops at first failed condition.
    Returns a ValidationResult as dict.
    """

    homepage = HomepageData(**homepage_data)   # convert dict to schema
    speakers = SpeakersData(**speakers_data)
    venue = VenueData(**venue_data)
    registration = RegistrationData(**registration_data)

    def reject(condition: int, reason: str) -> dict:
        return ValidationResult(
            conference_id=conference_id,
            passed=False,
            failed_condition=condition,
            rejection_reason=reason,
            date_bucket="reject",
        ).model_dump()

    # Condition 1 — speakers confirmed for this edition
    if not speakers.speakers_confirmed:
        return reject(1, "Speakers not confirmed for this edition")

    # Condition 2 — at least one speaker found
    if len(speakers.speakers) == 0:
        return reject(2, "No speakers found")

    # Condition 3 — at least 5 scientific speakers
    scientific_count = sum(1 for s in speakers.speakers if s.is_scientific)
    if scientific_count < 5:
        return reject(3, f"Not enough scientific speakers ({scientific_count}/5)")

    # Condition 4 — venue name exists
    if not venue.venue_name:
        return reject(4, "Venue name not found")

    # Condition 5 — venue address exists
    if not venue.venue_address:
        return reject(5, "Venue address not found")

    # Condition 6 — venue is not a hotel
    if venue.is_hotel:
        return reject(6, "Venue is a hotel")

    # Condition 7 — conference does not cover accommodation
    if registration.covers_accommodation:
        return reject(7, "Conference covers accommodation")

    # Condition 8 — date window check
    if not homepage.date_start:
        return reject(8, "Conference date not found")

    conf_date = homepage.date_start   
    
    delta = (conf_date - date.today()).days

    if delta < 30:
        return reject(8, f"Conference too soon ({delta} days away)")

    date_bucket = "now" if delta <= 90 else "future"

    # Condition 9 — not sent before (duplicates)
    sent = _load_sent()
    if homepage.conference_name in sent:
        return reject(9, "Already sent before")

    return ValidationResult(
        conference_id=conference_id,
        passed=True,
        failed_condition=None,
        rejection_reason=None,
        date_bucket=date_bucket,
    ).model_dump()


validate_conference_tool = FunctionTool(func=validate_conference)