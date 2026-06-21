"""
Regex-based date extractor for conference homepage markdown.

Falls back to regex patterns when the LLM extraction returns null dates.
Handles common date formats found on conference websites.

Usage:
    from conference_agent.tools.date_extractor import extract_dates_from_markdown
    date_start, date_end = extract_dates_from_markdown(markdown_text)
"""

import logging
import re
from calendar import month_abbr, month_name
from typing import Optional

logger = logging.getLogger(__name__)

# ── Month name → number mapping ──────────────────────────────────────────
_MONTH_MAP: dict[str, int] = {}
for _i, _name in enumerate(month_abbr):
    if _name:
        _MONTH_MAP[_name.lower()] = _i
for _i, _name in enumerate(month_name):
    if _name:
        _MONTH_MAP[_name.lower()] = _i

# Short month abbreviations with/without period
_MONTH_MAP["sept"] = 9
_MONTH_MAP["jun"] = 6
_MONTH_MAP["jul"] = 7


def _parse_month(part: str) -> Optional[int]:
    """Parse a month name/abbreviation to an integer 1-12."""
    cleaned = part.strip("., ").lower()
    return _MONTH_MAP.get(cleaned)


def _to_yyyy_mm_dd(month: int, day: int, year: int) -> str:
    """Format as YYYY-MM-DD string."""
    return f"{year:04d}-{month:02d}-{day:02d}"


# ── Regex patterns (ordered by specificity) ──────────────────────────────
# Each pattern captures (month1, day1, year1, month2, day2, year2)
# where the _2 groups may be None for single-day events.

_DATE_PATTERNS: list[re.Pattern] = [
    # "Sep 7 – Sep 10, 2026"  /  "September 7 – September 10, 2026"
    re.compile(
        r"(?P<m1>[A-Z][a-z]+)\s+(?P<d1>\d{1,2})\s*[–—-]\s*"
        r"(?P<m2>[A-Z][a-z]+)\s+(?P<d2>\d{1,2}),?\s*(?P<y>\d{4})",
        re.UNICODE,
    ),
    # "Sep 7–10, 2026"  /  "September 7–10, 2026"
    re.compile(
        r"(?P<m1>[A-Z][a-z]+)\s+(?P<d1>\d{1,2})\s*[–—-]\s*"
        r"(?P<d2>\d{1,2}),?\s*(?P<y>\d{4})",
        re.UNICODE,
    ),
    # "7–10 September 2026"  /  "18-20 June 2026"
    re.compile(
        r"(?P<d1>\d{1,2})\s*[–—-]\s*(?P<d2>\d{1,2})\s+"
        r"(?P<m1>[A-Z][a-z]+)\s*(?P<y>\d{4})",
        re.UNICODE,
    ),
    # "7 September – 10 September 2026"  /  "7 Sep – 10 Sep 2026"
    re.compile(
        r"(?P<d1>\d{1,2})\s+(?P<m1>[A-Z][a-z]+)\s*[–—-]\s*"
        r"(?P<d2>\d{1,2})\s+(?P<m2>[A-Z][a-z]+)\s*(?P<y>\d{4})",
        re.UNICODE,
    ),
    # "2026-09-07 – 2026-09-10"  (ISO range)
    re.compile(
        r"(?P<y1>\d{4})-(?P<mo1>\d{2})-(?P<d1>\d{2})\s*[–—-]\s*"
        r"(?P<y2>\d{4})-(?P<mo2>\d{2})-(?P<d2>\d{2})",
    ),
    # "2026/09/07 – 2026/09/10"
    re.compile(
        r"(?P<y1>\d{4})/(?P<mo1>\d{2})/(?P<d1>\d{2})\s*[–—-]\s*"
        r"(?P<y2>\d{4})/(?P<mo2>\d{2})/(?P<d2>\d{2})",
    ),
    # Single date: "September 7, 2026"  /  "Sep 7, 2026"
    re.compile(
        r"(?P<m1>[A-Z][a-z]+)\s+(?P<d1>\d{1,2}),?\s*(?P<y>\d{4})",
        re.UNICODE,
    ),
    # Single date: "7 September 2026"
    re.compile(
        r"(?P<d1>\d{1,2})\s+(?P<m1>[A-Z][a-z]+)\s*(?P<y>\d{4})",
        re.UNICODE,
    ),
    # Single date: "2026-09-07"  (ISO)
    re.compile(
        r"(?P<y>\d{4})-(?P<mo1>\d{2})-(?P<d1>\d{2})",
    ),
    # "September 7-10, 2026" (range, same month, dash between days)
    re.compile(
        r"(?P<m1>[A-Z][a-z]+)\s+(?P<d1>\d{1,2})\s*[–—-]\s*"
        r"(?P<d2>\d{1,2}),?\s*(?P<y>\d{4})",
        re.UNICODE,
    ),
    # "Sep 7th – Sep 10th, 2026"  (with ordinal suffixes)
    re.compile(
        r"(?P<m1>[A-Z][a-z]+)\s+(?P<d1>\d{1,2})(?:st|nd|rd|th)?\s*[–—-]\s*"
        r"(?P<m2>[A-Z][a-z]+)\s+(?P<d2>\d{1,2})(?:st|nd|rd|th)?,?\s*(?P<y>\d{4})",
        re.UNICODE,
    ),
    # "7th – 10th September 2026"
    re.compile(
        r"(?P<d1>\d{1,2})(?:st|nd|rd|th)?\s*[–—-]\s*"
        r"(?P<d2>\d{1,2})(?:st|nd|rd|th)?\s+"
        r"(?P<m1>[A-Z][a-z]+)\s*(?P<y>\d{4})",
        re.UNICODE,
    ),
    # "07-10 September 2026" (range, two days same month)
    re.compile(
        r"(?P<d1>\d{1,2})\s*[–—-]\s*(?P<d2>\d{1,2})\s+"
        r"(?P<m1>[A-Z][a-z]+)\s*,?\s*(?P<y>\d{4})",
        re.UNICODE,
    ),
]


def _normalize_year(year: int) -> int:
    """Normalize 2-digit year to 4-digit (assumes 2000+ for 0-29, 1900+ for 30-99)."""
    if year < 100:
        return 2000 + year if year < 30 else 1900 + year
    return year


def extract_dates_from_markdown(markdown: str) -> tuple[Optional[str], Optional[str]]:
    """Extract conference dates from markdown text using regex.

    Tries each pattern in order of specificity. Returns the first match
    as ``(date_start, date_end)`` in ``YYYY-MM-DD`` format.

    Args:
        markdown: Raw markdown text scraped from a conference homepage.

    Returns:
        Tuple of ``(date_start, date_end)`` where each is ``YYYY-MM-DD`` or
        ``None`` if no date pattern matched.
    """
    if not markdown:
        return None, None

    for pattern in _DATE_PATTERNS:
        match = pattern.search(markdown)
        if not match:
            continue

        groups = match.groupdict()

        # ── Determine which pattern variant matched ──
        # ISO range: y1, mo1, d1, y2, mo2, d2
        if "y1" in groups and "mo1" in groups:
            y1 = int(groups["y1"])
            mo1 = int(groups["mo1"])
            d1 = int(groups["d1"])
            y2 = int(groups.get("y2", y1))
            mo2 = int(groups.get("mo2", mo1))
            d2 = int(groups.get("d2", d1))
            logger.debug(
                "DATE_EXTRACTOR  ISO range matched: %s/%s/%s – %s/%s/%s",
                y1, mo1, d1, y2, mo2, d2,
            )
            return _to_yyyy_mm_dd(mo1, d1, y1), _to_yyyy_mm_dd(mo2, d2, y2)

        # Pattern with two named months (m1, m2) + days + year
        m1_str = groups.get("m1")
        m2_str = groups.get("m2")
        y_str = groups.get("y")

        if m1_str:
            m1 = _parse_month(m1_str)
            if m1 is None:
                continue

            year = int(y_str) if y_str else 0
            year = _normalize_year(year)

            d1 = int(groups["d1"])

            if m2_str:
                m2 = _parse_month(m2_str)
                if m2 is None:
                    continue
                d2 = int(groups["d2"])
                # Same year for both unless explicitly different
                y2_str = groups.get("y2", y_str)
                y2 = int(y2_str) if y2_str else year
                y2 = _normalize_year(y2)
                logger.debug(
                    "DATE_EXTRACTOR  Two-month range: %s %d %d – %s %d %d",
                    m1_str, d1, year, m2_str, d2, y2,
                )
                return _to_yyyy_mm_dd(m1, d1, year), _to_yyyy_mm_dd(m2, d2, y2)
            else:
                # Single month, possibly with day range
                d2_str = groups.get("d2")
                if d2_str:
                    d2 = int(d2_str)
                    logger.debug(
                        "DATE_EXTRACTOR  Single-month range: %s %d-%d %d",
                        m1_str, d1, d2, year,
                    )
                    return _to_yyyy_mm_dd(m1, d1, year), _to_yyyy_mm_dd(m1, d2, year)
                else:
                    # Single day
                    logger.debug(
                        "DATE_EXTRACTOR  Single date: %s %d %d",
                        m1_str, d1, year,
                    )
                    return _to_yyyy_mm_dd(m1, d1, year), _to_yyyy_mm_dd(m1, d1, year)

        # Day-first pattern: "7–10 September 2026"
        if "d1" in groups and groups.get("m1") and "y" in groups:
            d1 = int(groups["d1"])
            d2_str = groups.get("d2")
            m1 = _parse_month(groups["m1"])
            if m1 is None:
                continue
            year = _normalize_year(int(groups["y"]))
            if d2_str:
                d2 = int(d2_str)
                logger.debug(
                    "DATE_EXTRACTOR  Day-first range: %d-%d %s %d",
                    d1, d2, groups["m1"], year,
                )
                return _to_yyyy_mm_dd(m1, d1, year), _to_yyyy_mm_dd(m1, d2, year)
            else:
                logger.debug(
                    "DATE_EXTRACTOR  Day-first single: %d %s %d",
                    d1, groups["m1"], year,
                )
                return _to_yyyy_mm_dd(m1, d1, year), _to_yyyy_mm_dd(m1, d1, year)

    logger.debug("DATE_EXTRACTOR  No date pattern matched in markdown")
    return None, None
