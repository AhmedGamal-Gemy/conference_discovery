"""
Step 5 — Extract structured data from scraped sub-pages (speakers, venue, registration).

This agent reads the raw SCRAPED_SUB_PAGES markdown output from step 4, splits it
into three sections (SPEAKERS, VENUE, REGISTRATION), and runs a single LLM extraction
pass over all three. The result is a combined SubPagesData model stored under a single
output key — one LLM call instead of three.
"""

import re

from google.adk.agents.llm_agent import LlmAgent
from google.adk.models.lite_llm import LiteLlm

from conference_agent.config import settings
from conference_agent.schemas.output_keys import output_keys
from conference_agent.schemas.sub_pages_data import SubPagesData
from conference_agent.prompts.extraction import (
    SPEAKERS_EXTRACTION_PROMPT,
    VENUE_EXTRACTION_PROMPT,
    REGISTRATION_EXTRACTION_PROMPT,
)


# ---------------------------------------------------------------------------
# Section parser — splits SCRAPED_SUB_PAGES into speakers / venue / registration
# ---------------------------------------------------------------------------
def _parse_sections(text: str) -> dict[str, str]:
    """Split SCRAPED_SUB_PAGES by SPEAKERS: / VENUE: / REGISTRATION: headers.

    Returns a dict with keys ``speakers``, ``venue``, ``registration``.
    Sections whose content is empty or ``null`` are returned as ``"null"``.
    """
    default: dict[str, str] = {
        "speakers": "null",
        "venue": "null",
        "registration": "null",
    }
    if not text or text.strip() in ("", "null"):
        return default

    sections: dict[str, str] = {}

    m = re.search(r"SPEAKERS:\s*(.*?)(?=\n\s*VENUE:\s|\Z)", text, re.DOTALL)
    if m:
        content = m.group(1).strip()
        sections["speakers"] = content if (content and content != "null") else "null"

    m = re.search(r"VENUE:\s*(.*?)(?=\n\s*REGISTRATION:\s|\Z)", text, re.DOTALL)
    if m:
        content = m.group(1).strip()
        sections["venue"] = content if (content and content != "null") else "null"

    m = re.search(r"REGISTRATION:\s*(.*?)\Z", text, re.DOTALL)
    if m:
        content = m.group(1).strip()
        sections["registration"] = content if (content and content != "null") else "null"

    return {**default, **sections}


# ---------------------------------------------------------------------------
# Shared helpers — same pattern as step2_5 / step3
# ---------------------------------------------------------------------------
def _strip_markdown_codeblock(*args, **kwargs):
    """After-model callback to strip markdown code blocks from JSON responses."""
    from google.adk.models.llm_response import LlmResponse
    llm_response = None
    for arg in args:
        if isinstance(arg, LlmResponse):
            llm_response = arg
            break
    if not llm_response:
        for v in kwargs.values():
            if isinstance(v, LlmResponse):
                llm_response = v
                break

    if llm_response and llm_response.content and llm_response.content.parts:
        text = llm_response.content.parts[0].text or ""
        cleaned = re.sub(r"^```json\s*", "", text)
        cleaned = re.sub(r"\s*```\s*$", "", cleaned)
        if cleaned != text:
            llm_response.content.parts[0].text = cleaned
    return llm_response or args[0] if args else None


# ---------------------------------------------------------------------------
# Dynamic instruction — builds a combined extraction prompt
# ---------------------------------------------------------------------------
def _build_step5_instruction(ctx):
    """Read SCRAPED_SUB_PAGES from state, split into sections, build combined prompt."""
    raw = ""
    if hasattr(ctx.state, "get"):
        raw = ctx.state.get(output_keys.SCRAPED_SUB_PAGES, "")

    sections = _parse_sections(raw)

    # Fill each extraction prompt with its section content
    speakers_inst = SPEAKERS_EXTRACTION_PROMPT.replace("{markdown}", sections["speakers"])
    venue_inst = VENUE_EXTRACTION_PROMPT.replace("{markdown}", sections["venue"])
    reg_inst = REGISTRATION_EXTRACTION_PROMPT.replace("{markdown}", sections["registration"])

    return f"""You are a data extraction assistant. Extract structured data from the scraped sub-pages of a conference website.

Below are the markdown contents of three sub-pages — speakers, venue, and registration. For each section, follow the extraction instructions and schema provided.

{speakers_inst}

{venue_inst}

{reg_inst}

Return ALL THREE extractions as a single JSON object matching this exact structure:
{{
    "speakers": {{
        "speakers": [
            {{
                "name": "Full name",
                "title": "Title or null",
                "affiliation": "Institution or null",
                "country": "Country or null",
                "is_scientific": true or false
            }}
        ],
        "speakers_confirmed": true or false,
        "notes": "Any relevant notes or empty string"
    }},
    "venue": {{
        "venue_name": "Name or null",
        "venue_address": "Address or null",
        "city": "City or null",
        "country": "Country or null",
        "is_hotel": true or false
    }},
    "registration": {{
        "covers_accommodation": true or false
    }}
}}

Rules:
- Return ONLY the JSON object, no explanation, no markdown backticks.
- Follow the extraction rules for each individual section (speakers_confirmed logic, venue specificity, etc.).
- If a section is marked as "null" (no data available), return appropriate null values for that section.
"""


# ---------------------------------------------------------------------------
# Agent definition
# ---------------------------------------------------------------------------
extract_sub_pages_agent = LlmAgent(
    model=LiteLlm(model=settings.llm.extraction.model),
    name="extract_sub_pages",
    description="Extracts structured data from scraped speakers, venue, and registration pages",
    instruction=_build_step5_instruction,
    output_schema=SubPagesData,
    output_key=output_keys.SUB_PAGES_DATA,
    after_model_callback=_strip_markdown_codeblock,
)
