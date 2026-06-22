"""
Validation step — pure Python validation logic (no LLM calls).

Runs 12 conditions on extracted conference data with fail-fast behavior.
Can be called standalone or wired into the ADK pipeline as a FunctionTool.
"""

import json
import logging
import os
import time
from datetime import date
from typing import Optional

from google.adk.tools import FunctionTool

from conference_agent.config import settings

logger = logging.getLogger(__name__)

from conference_agent.schemas.speaker import SpeakersData
from conference_agent.schemas.venue import VenueData
from conference_agent.schemas.registration import RegistrationData
from conference_agent.schemas.homepage import HomepageData
from conference_agent.schemas.validation import ValidationResult


SENT_FILE = os.path.join(
    os.path.dirname(__file__), "..", "..", "output", "sent.json"
)


def _load_sent() -> list[str]:
    """Load previously sent conference names for duplicate detection."""
    try:
        with open(SENT_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def validate_conference(
    conference_id: str,
    homepage_data: dict,
    sub_pages_data: dict,
) -> dict:
    """
    Runs 12 validation conditions on extracted conference data.

    Fail-fast — stops at the first failed condition and returns a rejection.
    Returns a ValidationResult as a dict (Pydantic model_dump).

    ``sub_pages_data`` should contain nested ``speakers``, ``venue``, and
    ``registration`` dicts — extracted internally.

    Conditions:
      1. Speakers confirmed for this edition
      2. At least one speaker found
      3. At least 5 scientific speakers
      4. Venue name exists
      5. Venue address exists
      6. Venue is not a hotel
      7. Conference does not cover accommodation
      8. Conference date found
      9. Date is not too soon (< 30 days away)
     10. Enough non-USA speakers
     11. Enough non-local speakers
     12. Not sent before (deduplication)
    """
    t0 = time.time()
    logger.info("VALIDATE  Starting validation — conference_id=%s", conference_id)

    homepage = HomepageData(**homepage_data)
    sp = sub_pages_data or {}
    speakers = SpeakersData(**sp.get("speakers", {}))
    venue = VenueData(**sp.get("venue", {}))
    registration = RegistrationData(**sp.get("registration", {}))

    # Date resolution — general strategy that works for ALL conferences.
    # Decision tree based on which sources have dates and whether they agree.
    hp_start = homepage.date_start
    hp_end = homepage.date_end
    sp_start = sp.get("date_start")
    sp_end = sp.get("date_end")

    both_have = hp_start and sp_start
    neither_has = not hp_start and not sp_start

    if both_have and hp_start == sp_start and hp_end == sp_end:
        # Case 1: both agree — use homepage (primary source)
        logger.info(
            "VALIDATE  Dates resolved — both sources agree on %s to %s",
            hp_start, hp_end,
        )
    elif hp_start and not sp_start:
        # Case 2: only homepage has dates
        logger.info(
            "VALIDATE  Dates resolved — only homepage has dates: %s to %s",
            hp_start, hp_end,
        )
    elif not hp_start and sp_start:
        # Case 3: only sub-pages have dates — use them
        homepage.date_start = sp_start
        homepage.date_end = sp_end
        logger.info(
            "VALIDATE  Dates resolved — only sub-pages have dates: %s to %s",
            sp_start, sp_end,
        )
    elif both_have:
        # Case 4: both have dates but disagree — heuristic resolution
        hp_matches_submission = (
            homepage.submission_deadline
            and hp_start == homepage.submission_deadline
        )
        hp_matches_early_bird = (
            registration.early_bird_deadline
            and hp_start == registration.early_bird_deadline
        )
        if hp_matches_submission:
            # 4a: homepage confused submission deadline with conference date
            homepage.date_start = sp_start
            homepage.date_end = sp_end
            logger.warning(
                "VALIDATE  Dates resolved — using sub-pages dates "
                "(homepage date %s matches submission_deadline)",
                hp_start,
            )
        elif hp_matches_early_bird:
            # 4b: homepage confused early-bird deadline with conference date
            homepage.date_start = sp_start
            homepage.date_end = sp_end
            logger.warning(
                "VALIDATE  Dates resolved — using sub-pages dates "
                "(homepage date %s matches registration.early_bird_deadline)",
                hp_start,
            )
        else:
            # 4c: disagree but no deadline confusion — prefer homepage (primary)
            logger.info(
                "VALIDATE  Dates resolved — using homepage dates (primary source): %s to %s",
                hp_start, hp_end,
            )
    elif neither_has:
        # Case 5: neither source has dates
        logger.warning("VALIDATE  Warning: No dates found from homepage or sub-pages")

    def reject(condition: int, reason: str) -> dict:
        elapsed = time.time() - t0
        logger.warning(
            "VALIDATE  ✗ Rule #%d FAILED — %s (%.0fms)",
            condition, reason, elapsed * 1000,
        )
        return ValidationResult(
            conference_id=conference_id,
            passed=False,
            failed_condition=condition,
            rejection_reason=reason,
            date_bucket="reject",
        ).model_dump()

    # Condition 1 — speakers confirmed for this edition
    # Pass only if speakers_confirmed=True or actual named speakers from sub-pages.
    # Keynote speakers from homepage do NOT satisfy this requirement.
    logger.debug("VALIDATE  Rule #1: speakers confirmed check")
    if not speakers.speakers_confirmed and len(speakers.speakers) == 0:
        return reject(1, "Speakers not confirmed for this edition")
    logger.info("VALIDATE  ✓ Rule #1 passed")

    # Condition 2 — at least one speaker found
    # Consider both sub-page speakers and homepage keynote_speakers.
    total_speakers = len(speakers.speakers) + len(homepage.keynote_speakers)
    logger.debug("VALIDATE  Rule #2: at least one speaker (sub=%d, keynote=%d)", len(speakers.speakers), len(homepage.keynote_speakers))
    if total_speakers == 0:
        return reject(2, "No speakers found")
    logger.info("VALIDATE  ✓ Rule #2 passed (%d total speakers)", total_speakers)

    # Condition 3 — at least 5 scientific speakers
    # Count scientific speakers from both sub-pages and homepage keynote_speakers.
    scientific_count = sum(1 for s in speakers.speakers if s.is_scientific) + sum(1 for ks in homepage.keynote_speakers if ks.is_scientific)
    logger.debug("VALIDATE  Rule #3: %d/%d scientific speakers", scientific_count, total_speakers)
    if scientific_count < settings.validation.min_speakers:
        return reject(3, f"Not enough scientific speakers ({scientific_count}/{settings.validation.min_speakers})")
    logger.info("VALIDATE  ✓ Rule #3 passed (%d scientific)", scientific_count)

    # Condition 4 — venue name exists
    logger.debug("VALIDATE  Rule #4: venue name")
    if not venue.venue_name:
        return reject(4, "Venue name not found")
    logger.info("VALIDATE  ✓ Rule #4 passed (%s)", venue.venue_name)

    # Condition 5 — venue address exists
    logger.debug("VALIDATE  Rule #5: venue address")
    if not venue.venue_address:
        return reject(5, "Venue address not found")
    logger.info("VALIDATE  ✓ Rule #5 passed (%s)", venue.venue_address[:50] if venue.venue_address else "N/A")

    # Condition 6 — venue is not a hotel
    logger.debug("VALIDATE  Rule #6: venue is hotel?")
    if venue.is_hotel:
        return reject(6, "Venue is a hotel")
    logger.info("VALIDATE  ✓ Rule #6 passed (not a hotel)")

    # Condition 7 — conference does not cover accommodation
    logger.debug("VALIDATE  Rule #7: covers accommodation?")
    if registration.covers_accommodation:
        return reject(7, "Conference covers accommodation")
    logger.info("VALIDATE  ✓ Rule #7 passed (no accommodation)")

    # Condition 8 — date exists
    logger.debug("VALIDATE  Rule #8: date exists")
    if not homepage.date_start:
        return reject(8, "Conference date not found")
    logger.info("VALIDATE  ✓ Rule #8 passed (%s)", homepage.date_start)

    # Condition 9 — date is not too soon
    conf_date = homepage.date_start
    if isinstance(conf_date, str):
        conf_date = date.fromisoformat(conf_date)
    delta = (conf_date - date.today()).days
    logger.debug("VALIDATE  Rule #9: date is %d days away", delta)
    if delta < settings.validation.date_window.min_days:
        return reject(9, f"Conference too soon ({delta} days away)")
    logger.info("VALIDATE  ✓ Rule #9 passed (%d days away)", delta)

    date_bucket = "now" if delta <= 90 else "future"

    # Condition 10 — enough non-USA speakers
    _USA_STRINGS = {"usa", "us", "united states", "united states of america", "america"}

    def _is_usa_country(country: Optional[str]) -> bool:
        if country is None:
            return False
        return country.strip().lower() in _USA_STRINGS

    min_non_usa = settings.validation.min_non_usa
    logger.debug("VALIDATE  Rule #10: non-USA speakers (min_non_usa=%s)", min_non_usa)
    if min_non_usa is not None:
        sp_non_usa = sum(1 for s in speakers.speakers if not _is_usa_country(s.country))
        ks_non_usa = sum(1 for ks in homepage.keynote_speakers if not _is_usa_country(ks.country))
        non_usa_count = sp_non_usa + ks_non_usa
        logger.debug(
            "VALIDATE  Rule #10: non-USA count=%d (sub=%d, keynote=%d), threshold=%d",
            non_usa_count, sp_non_usa, ks_non_usa, min_non_usa,
        )
        if non_usa_count < min_non_usa:
            return reject(10, f"Not enough non-USA speakers ({non_usa_count}/{min_non_usa})")
        logger.info("VALIDATE  ✓ Rule #10 passed (%d non-USA speakers)", non_usa_count)
    else:
        logger.info("VALIDATE  ✓ Rule #10 skipped — min_non_usa not set")

    # Condition 11 — enough non-local speakers
    min_non_local = settings.validation.min_non_local
    logger.debug("VALIDATE  Rule #11: non-local speakers (min_non_local=%s)", min_non_local)
    if min_non_local is not None:
        non_local_count = sum(1 for s in speakers.speakers if s.is_local is False)
        logger.debug(
            "VALIDATE  Rule #11: non-local count=%d, threshold=%d",
            non_local_count, min_non_local,
        )
        if non_local_count < min_non_local:
            return reject(11, f"Not enough non-local speakers ({non_local_count}/{min_non_local})")
        logger.info("VALIDATE  ✓ Rule #11 passed (%d non-local speakers)", non_local_count)
    else:
        logger.info("VALIDATE  ✓ Rule #11 skipped — min_non_local not set, geocoding not wired")

    # Condition 12 — not sent before (duplicate detection)
    sent = _load_sent()
    logger.debug("VALIDATE  Rule #12: duplicate check (%d sent names)", len(sent))
    if homepage.conference_name in sent:
        return reject(12, "Already sent before")
    logger.info("VALIDATE  ✓ Rule #12 passed (new conference)")

    elapsed = time.time() - t0
    logger.info(
        "VALIDATE  ✓ ALL 12 RULES PASSED — bucket=%s (%.0fms)",
        date_bucket, elapsed * 1000,
    )
    return ValidationResult(
        conference_id=conference_id,
        passed=True,
        failed_condition=None,
        rejection_reason=None,
        date_bucket=date_bucket,
    ).model_dump()


validate_conference_tool = FunctionTool(func=validate_conference)
