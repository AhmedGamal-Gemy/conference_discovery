"""
Speaker enrichment step — pure Python heuristic enrichment (no LLM calls).

Fills null country/affiliation fields on Speaker and KeynoteSpeaker objects
using Exa web search as a fallback source. Uses heuristic pattern matching
only — no LLM calls for snippet parsing.

Can be called standalone or wired into the ADK pipeline as a FunctionTool.
"""

import json
import logging
import re
import time
import urllib.parse
import urllib.request
from typing import Optional

from google.adk.tools import FunctionTool

from conference_agent.tools.exa_tool import search_speaker_info
from conference_agent.schemas.homepage import HomepageData
from conference_agent.schemas.speaker import SpeakersData
from conference_agent.schemas.sub_pages_data import SubPagesData
from conference_agent.schemas.venue import VenueData
from conference_agent.schemas.registration import RegistrationData

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Country lookup — heuristic, no external API
# ---------------------------------------------------------------------------

COUNTRY_LOOKUP: dict[str, str] = {
    "usa": "USA", "us": "USA", "united states": "USA",
    "united states of america": "USA", "america": "USA",
    "american": "USA",
    "uk": "UK", "united kingdom": "UK", "england": "UK",
    "scotland": "UK", "great britain": "UK", "british": "UK",
    "germany": "Germany", "deutschland": "Germany", "german": "Germany",
    "france": "France", "french": "France",
    "italy": "Italy", "italia": "Italy", "italian": "Italy",
    "spain": "Spain", "spanish": "Spain",
    "japan": "Japan", "japanese": "Japan",
    "china": "China", "chinese": "China",
    "india": "India", "indian": "India",
    "australia": "Australia", "australian": "Australia",
    "canada": "Canada", "canadian": "Canada",
    "brazil": "Brazil", "brasil": "Brazil",
    "south korea": "South Korea", "korea": "South Korea",
    "netherlands": "Netherlands", "holland": "Netherlands", "dutch": "Netherlands",
    "belgium": "Belgium", "belgian": "Belgium",
    "switzerland": "Switzerland", "swiss": "Switzerland",
    "austria": "Austria", "austrian": "Austria",
    "portugal": "Portugal", "portuguese": "Portugal",
    "sweden": "Sweden", "swedish": "Sweden",
    "norway": "Norway", "norwegian": "Norway",
    "denmark": "Denmark", "danish": "Denmark",
    "finland": "Finland", "finnish": "Finland",
    "poland": "Poland", "polish": "Poland",
    "turkey": "Turkey", "turkish": "Turkey",
    "russia": "Russia", "russian": "Russia",
    "israel": "Israel", "israeli": "Israel",
    "korean": "South Korea",
    "mexico": "Mexico", "mexican": "Mexico",
    "argentina": "Argentina",
    "egypt": "Egypt", "egyptian": "Egypt",
    "south africa": "South Africa",
    "ireland": "Ireland", "irish": "Ireland",
    "czech republic": "Czech Republic", "czechia": "Czech Republic",
    "romania": "Romania", "romanian": "Romania",
    "hungary": "Hungary", "hungarian": "Hungary",
    "greece": "Greece", "greek": "Greece",
    "thailand": "Thailand", "taiwan": "Taiwan",
    "hong kong": "Hong Kong",
    "singapore": "Singapore", "singaporean": "Singapore",
    "uae": "UAE", "united arab emirates": "UAE",
    "saudi arabia": "Saudi Arabia", "qatar": "Qatar",
}

UNIVERSITY_COUNTRY_MAP: dict[str, str] = {
    "harvard": "USA", "mit": "USA", "stanford": "USA",
    "princeton": "USA", "yale": "USA", "columbia": "USA",
    "caltech": "USA", "berkeley": "USA", "cornell": "USA",
    "johns hopkins": "USA", "duke": "USA", "northwestern": "USA",
    "university of michigan": "USA", "university of pennsylvania": "USA",
    "university of chicago": "USA", "ucla": "USA",
    "georgia tech": "USA", "purdue": "USA", "rice university": "USA",
    "carnegie mellon": "USA", "nyu": "USA", "boston university": "USA",
    "oxford": "UK", "cambridge": "UK", "imperial college": "UK",
    "ucl": "UK", "university of edinburgh": "UK",
    "sorbonne": "France", "école polytechnique": "France",
    "lmu münchen": "Germany", "max planck": "Germany",
    "fraunhofer": "Germany", "universität heidelberg": "Germany",
    "university of tokyo": "Japan", "keio university": "Japan",
    "tsinghua": "China", "peking university": "China",
    "iit": "India", "iisc": "India",
    "university of melbourne": "Australia", "monash": "Australia",
    "university of toronto": "Canada", "mcgill": "Canada",
    "kaist": "South Korea", "seoul national university": "South Korea",
    "eth zurich": "Switzerland", "epfl": "Switzerland",
    "tu delft": "Netherlands", "politecnico di milano": "Italy",
    "google": "USA", "microsoft": "USA", "apple": "USA",
    "meta": "USA", "amazon": "USA", "nvidia": "USA",
    "deepmind": "UK", "samsung": "South Korea",
    "siemens": "Germany", "bosch": "Germany", "sap": "Germany",
    "novartis": "Switzerland", "roche": "Switzerland",
}


def _infer_country_from_affiliation(affiliation: str) -> Optional[str]:
    """Heuristic: extract country from an affiliation string."""
    if not affiliation:
        return None
    lower = affiliation.lower().strip()
    for name, country in UNIVERSITY_COUNTRY_MAP.items():
        if name in lower:
            return country
    for cn in sorted(COUNTRY_LOOKUP.keys(), key=len, reverse=True):
        if cn in lower:
            return COUNTRY_LOOKUP[cn]
    paren_match = re.search(r'\(([A-Z]{2,3})\)\s*$', affiliation)
    if paren_match:
        abbrev = paren_match.group(1).lower()
        if abbrev in COUNTRY_LOOKUP:
            return COUNTRY_LOOKUP[abbrev]
    return None


def _extract_country_from_snippet(snippet: str) -> Optional[str]:
    """Heuristic: extract country from a search result snippet."""
    if not snippet:
        return None
    lower = snippet.lower()
    for pattern in [r'based in ([A-Za-z\s]+)', r'located in ([A-Za-z\s]+)',
                    r'from ([A-Za-z\s]+)']:
        match = re.search(pattern, lower)
        if match:
            place = match.group(1).strip()
            if place in COUNTRY_LOOKUP:
                return COUNTRY_LOOKUP[place]
    for cn in sorted(COUNTRY_LOOKUP.keys(), key=len, reverse=True):
        if cn in lower:
            return COUNTRY_LOOKUP[cn]
    return None


def _extract_affiliation_from_snippet(snippet: str) -> Optional[str]:
    """Heuristic: extract affiliation from a search result snippet."""
    if not snippet:
        return None
    for title in ["professor", "researcher", "scientist", "director",
                  "head", "chair", "lecturer"]:
        pattern = (rf'{title}\s+at\s+([A-Za-z\s,]+'
                   r'(?:University|Institute|College|Hospital|Lab'
                   r'|Center|Centre|School))')
        match = re.search(pattern, snippet, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    uni_match = re.search(
        r'((?:University|Institute|College|Hospital|Lab|Center|Centre|School)'
        r'\s+of\s+[A-Za-z\s]+|[A-Za-z\s]+\s+'
        r'(?:University|Institute|College|Hospital|Lab|Center|Centre|School))',
        snippet, re.IGNORECASE)
    if uni_match:
        return uni_match.group(1).strip()
    lower = snippet.lower()
    for name in UNIVERSITY_COUNTRY_MAP:
        if name in lower:
            return name.title() if len(name) > 3 else name.upper()
    return None


# ---------------------------------------------------------------------------
# OpenAlex enrichment (free academic author API — no key needed, 10 req/s)
# ---------------------------------------------------------------------------

OPENALEX_API = "https://api.openalex.org/authors"
OPENALEX_UA = "ConferenceDiscovery/1.0 (enrichment agent; python)"

COUNTRY_CODE_MAP: dict[str, str] = {
    "US": "USA", "GB": "UK", "CH": "Switzerland", "DE": "Germany",
    "FR": "France", "IT": "Italy", "ES": "Spain", "JP": "Japan",
    "CN": "China", "IN": "India", "AU": "Australia", "CA": "Canada",
    "BR": "Brazil", "KR": "South Korea", "NL": "Netherlands",
    "BE": "Belgium", "AT": "Austria", "PT": "Portugal",
    "SE": "Sweden", "NO": "Norway", "DK": "Denmark", "FI": "Finland",
    "PL": "Poland", "TR": "Turkey", "RU": "Russia", "IL": "Israel",
    "MX": "Mexico", "AR": "Argentina", "EG": "Egypt", "ZA": "South Africa",
    "IE": "Ireland", "CZ": "Czech Republic", "RO": "Romania",
    "HU": "Hungary", "GR": "Greece", "TH": "Thailand", "TW": "Taiwan",
    "HK": "Hong Kong", "SG": "Singapore", "AE": "UAE",
    "SA": "Saudi Arabia", "QA": "Qatar", "NZ": "New Zealand",
    "MY": "Malaysia", "ME": "Montenegro",
}


def _search_openalex(name: str) -> Optional[dict]:
    """Search OpenAlex for an academic author. Returns first match with
    affiliation data: {affiliation, country} or None."""
    params = urllib.parse.urlencode({
        "search": name, "per_page": 3,
    })
    req = urllib.request.Request(
        f"{OPENALEX_API}?{params}",
        headers={"User-Agent": OPENALEX_UA},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        for r in data.get("results", []):
            insts = r.get("last_known_institutions") or []
            if insts:
                inst = insts[0]
                country = COUNTRY_CODE_MAP.get(inst.get("country_code", ""))
                return {
                    "affiliation": inst.get("display_name"),
                    "country": country,
                }
        return None
    except Exception:
        return None


def _enrich_single_speaker(
    name: str,
    current_country: Optional[str],
    current_affiliation: Optional[str],
) -> dict:
    """Fill missing country/affiliation for one speaker via OpenAlex → Exa fallback.
    Values inferred — not authoritative.
    """
    if current_country and current_affiliation:
        return {"country": current_country, "affiliation": current_affiliation}

    inferred_country = _infer_country_from_affiliation(current_affiliation or "")
    if current_affiliation and inferred_country and not current_country:
        logger.info("ENRICH  Country inferred from affiliation for %r: %s",
                    name, inferred_country)
        return {"country": inferred_country, "affiliation": current_affiliation}

    # Try OpenAlex first (free academic API, structured data with country codes)
    if not current_country or not current_affiliation:
        oa_result = _search_openalex(name)
        if oa_result:
            if oa_result.get("affiliation") and not current_affiliation:
                current_affiliation = oa_result["affiliation"]
                logger.info("ENRICH  Affiliation from OpenAlex for %r: %s",
                            name, current_affiliation)
            if oa_result.get("country") and not current_country:
                current_country = oa_result["country"]
                inferred_country = current_country
                logger.info("ENRICH  Country from OpenAlex for %r: %s",
                            name, current_country)
            if current_country and current_affiliation:
                return {"country": current_country, "affiliation": current_affiliation}

    results = search_speaker_info(name, affiliation_hint=current_affiliation)
    if not results:
        logger.warning("ENRICH  No search results for speaker %r", name)
        return {"country": current_country or inferred_country,
                "affiliation": current_affiliation}

    found_country = current_country or inferred_country
    found_affiliation = current_affiliation

    for result in results:
        snippet = result.get("snippet", "")
        if not found_country:
            extracted = _extract_country_from_snippet(snippet)
            if extracted:
                found_country = extracted
                logger.info("ENRICH  Country from snippet for %r: %s",
                            name, extracted)
        if not found_affiliation:
            extracted = _extract_affiliation_from_snippet(snippet)
            if extracted:
                found_affiliation = extracted
                logger.info("ENRICH  Affiliation from snippet for %r: %s",
                            name, extracted)
        if found_country and found_affiliation:
            break

    return {"country": found_country, "affiliation": found_affiliation}


def enrich_speakers_data(
    homepage_data: dict,
    sub_pages_data: dict,
) -> dict:
    """Enrich speaker country/affiliation via Exa web search (heuristic only).

    Mutates speaker objects in-place, writes enriched data back to same keys
    plus a new ENRICHMENT_STATUS key.

    Returns dict with: homepage_data, sub_pages_data, status.
    """
    t0 = time.time()

    homepage = HomepageData.model_validate(homepage_data)
    sp_raw = sub_pages_data or {}
    sp = SubPagesData(
        speakers=SpeakersData(**sp_raw.get("speakers", {})),
        venue=VenueData(**sp_raw.get("venue", {})),
        registration=RegistrationData(**sp_raw.get("registration", {})),
        date_start=sp_raw.get("date_start"),
        date_end=sp_raw.get("date_end"),
    )

    enriched_count = 0
    total_incomplete = 0

    for ks in homepage.keynote_speakers:
        if not ks.country or not ks.affiliation:
            total_incomplete += 1
            result = _enrich_single_speaker(ks.name, ks.country, ks.affiliation)
            if result["country"] and not ks.country:
                ks.country = result["country"]
                enriched_count += 1
            if result["affiliation"] and not ks.affiliation:
                ks.affiliation = result["affiliation"]

    for speaker in sp.speakers.speakers:
        if not speaker.country or not speaker.affiliation:
            total_incomplete += 1
            result = _enrich_single_speaker(
                speaker.name, speaker.country, speaker.affiliation)
            if result["country"] and not speaker.country:
                speaker.country = result["country"]
                enriched_count += 1
            if result["affiliation"] and not speaker.affiliation:
                speaker.affiliation = result["affiliation"]

    status = {
        "enriched_count": enriched_count,
        "total_incomplete": total_incomplete,
        "keynote_enriched": sum(1 for ks in homepage.keynote_speakers if ks.country),
        "speakers_enriched": sum(1 for s in sp.speakers.speakers if s.country),
    }

    logger.info(
        "ENRICH  Completed — enriched %d/%d incomplete (%.0fms)",
        enriched_count, total_incomplete, (time.time() - t0) * 1000,
    )

    return {
        "homepage_data": homepage.model_dump(),
        "sub_pages_data": sp.model_dump(),
        "status": status,
    }


enrich_speakers_tool = FunctionTool(func=enrich_speakers_data)
