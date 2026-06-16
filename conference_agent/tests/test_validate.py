import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from conference_agent.steps.steps_validate import validate_conference

# ── Mock data ──────────────────────────────────────────────────────

HOMEPAGE_PASS = {
    "conference_name": "International Medical Summit 2026",
    "date_start": "2026-08-15",
    "date_end": "2026-08-17",
    "industry": "medical",
    "sub_pages": {"speakers": None, "venue": None, "registration": None},
}

SPEAKERS_PASS = {
    "speakers": [
        {"name": "Dr. Alice Smith", "affiliation": "Harvard", "country": "UK", "is_scientific": True},
        {"name": "Dr. Bob Jones", "affiliation": "Oxford", "country": "Germany", "is_scientific": True},
        {"name": "Dr. Carol Lee", "affiliation": "MIT", "country": "France", "is_scientific": True},
        {"name": "Dr. David Kim", "affiliation": "Stanford", "country": "Japan", "is_scientific": True},
        {"name": "Dr. Eva Müller", "affiliation": "Berlin Uni", "country": "Italy", "is_scientific": True},
    ],
    "speakers_confirmed": True,
    "notes": "",
}

VENUE_PASS = {
    "venue_name": "Berlin Congress Center",
    "venue_address": "Messedamm 22, 14055 Berlin",
    "city": "Berlin",
    "country": "Germany",
    "is_hotel": False,
}

REGISTRATION_PASS = {
    "covers_accommodation": False,
}

# ── Test 1: passes all conditions ──────────────────────────────────

def test_pass():
    result = validate_conference(
        conference_id="test-001",
        homepage_data=HOMEPAGE_PASS,
        speakers_data=SPEAKERS_PASS,
        venue_data=VENUE_PASS,
        registration_data=REGISTRATION_PASS,
    )
    assert result["passed"] is True
    assert result["date_bucket"] in ("now", "future")
    print(f"[OK] Test 1 passed - date_bucket: {result['date_bucket']}")

# ── Test 2: fails condition 3 (not enough scientific speakers) ─────

def test_fail_condition_3():
    speakers_fail = {
        "speakers": [
            {"name": "Dr. Alice Smith", "affiliation": "Harvard", "country": "UK", "is_scientific": True},
            {"name": "John Doe", "affiliation": "Event Co", "country": "USA", "is_scientific": False},
        ],
        "speakers_confirmed": True,
        "notes": "",
    }
    result = validate_conference(
        conference_id="test-002",
        homepage_data=HOMEPAGE_PASS,
        speakers_data=speakers_fail,
        venue_data=VENUE_PASS,
        registration_data=REGISTRATION_PASS,
    )
    assert result["passed"] is False
    assert result["failed_condition"] == 3
    print(f"[OK] Test 2 passed - rejected at condition 3: {result['rejection_reason']}")

# ── Test 3: fails condition 6 (venue is hotel) ─────────────────────

def test_fail_condition_6():
    venue_hotel = {
        "venue_name": "Hilton Berlin",
        "venue_address": "Mohrenstrasse 30, 10117 Berlin",
        "city": "Berlin",
        "country": "Germany",
        "is_hotel": True,
    }
    result = validate_conference(
        conference_id="test-003",
        homepage_data=HOMEPAGE_PASS,
        speakers_data=SPEAKERS_PASS,
        venue_data=venue_hotel,
        registration_data=REGISTRATION_PASS,
    )
    assert result["passed"] is False
    assert result["failed_condition"] == 6
    print(f"[OK] Test 3 passed - rejected at condition 6: {result['rejection_reason']}")

# ── Run all ────────────────────────────────────────────────────────

if __name__ == "__main__":
    test_pass()
    test_fail_condition_3()
    test_fail_condition_6()
    print("\n[OK] All tests passed!")
