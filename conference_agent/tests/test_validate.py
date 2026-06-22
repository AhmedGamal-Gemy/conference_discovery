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

SUB_PAGES_PASS = {
    "speakers": SPEAKERS_PASS,
    "venue": VENUE_PASS,
    "registration": REGISTRATION_PASS,
}

# ── Test 1: passes all conditions ──────────────────────────────────

def test_pass():
    result = validate_conference(
        conference_id="test-001",
        homepage_data=HOMEPAGE_PASS,
        sub_pages_data=SUB_PAGES_PASS,
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
        sub_pages_data={
            "speakers": speakers_fail,
            "venue": VENUE_PASS,
            "registration": REGISTRATION_PASS,
        },
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
        sub_pages_data={
            "speakers": SPEAKERS_PASS,
            "venue": venue_hotel,
            "registration": REGISTRATION_PASS,
        },
    )
    assert result["passed"] is False
    assert result["failed_condition"] == 6
    print(f"[OK] Test 3 passed - rejected at condition 6: {result['rejection_reason']}")

# ── Test 4: speakers_confirmed=False, empty speakers list, has keynotes → FAIL Rule #1 ──

def test_fail_rule1_keynotes_not_enough():
    homepage_with_keynotes = {**HOMEPAGE_PASS, "keynote_speakers": [{"name": "Dr. Keynote", "affiliation": "MIT", "country": "USA", "is_scientific": True}]}
    result = validate_conference(
        conference_id="test-004",
        homepage_data=homepage_with_keynotes,
        sub_pages_data={
            "speakers": {"speakers": [], "speakers_confirmed": False, "notes": ""},
            "venue": VENUE_PASS,
            "registration": REGISTRATION_PASS,
        },
    )
    assert result["passed"] is False
    assert result["failed_condition"] == 1
    print(f"[OK] Test 4 passed - rejected at condition 1: {result['rejection_reason']}")

# ── Test 5: speakers_confirmed=False, non-empty speakers list, no keynotes → PASS Rule #1 ──

def test_pass_rule1_speakers_present():
    result = validate_conference(
        conference_id="test-005",
        homepage_data=HOMEPAGE_PASS,
        sub_pages_data={
            "speakers": {**SPEAKERS_PASS, "speakers_confirmed": False},
            "venue": VENUE_PASS,
            "registration": REGISTRATION_PASS,
        },
    )
    assert result["passed"] is True
    print(f"[OK] Test 5 passed - date_bucket: {result['date_bucket']}")

# ── Run all ────────────────────────────────────────────────────────

if __name__ == "__main__":
    test_pass()
    test_fail_condition_3()
    test_fail_condition_6()
    test_fail_rule1_keynotes_not_enough()
    test_pass_rule1_speakers_present()
    print("\n[OK] All tests passed!")
