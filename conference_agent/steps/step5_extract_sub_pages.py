"""
Step 5 — Extract structured data from scraped sub-pages (speakers, venue, registration).

FunctionNode that auto-detects content size:
- Fits within 200K tokens → single LLM call
- Too large → splits into SPEAKERS/VENUE/REGISTRATION sections, 3 calls, merges
"""

import json
import logging
import re

from google.adk.agents import Context
from google.adk.workflow import node

from conference_agent.config import settings
from conference_agent.schemas.output_keys import output_keys
from conference_agent.prompts.extraction import SUB_PAGES_EXTRACTION_PROMPT

logger = logging.getLogger(__name__)

_MAX_TOKENS = 200_000  # safety margin under mistral-large's 262K

_FALLBACK = json.dumps({
    "speakers": {"speakers": [], "speakers_confirmed": False, "notes": ""},
    "venue": {
        "venue_name": None, "venue_address": None,
        "city": None, "country": None, "is_hotel": False,
    },
    "registration": {"covers_accommodation": False},
})


def _estimate_tokens(text: str) -> int:
    try:
        import tiktoken
        return len(tiktoken.get_encoding("cl100k_base").encode(text))
    except Exception:
        return len(text) // 4  # fallback


def _call_llm(scraped_content: str) -> dict:
    import litellm
    placeholder = f"{{{output_keys.SCRAPED_SUB_PAGES.value}?}}"
    prompt = SUB_PAGES_EXTRACTION_PROMPT.replace(placeholder, scraped_content)

    response = litellm.completion(
        model=settings.llm.extraction.model,
        messages=[{"role": "user", "content": prompt}],
        temperature=settings.llm.extraction.temperature,
    )
    text = response.choices[0].message.content or ""
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```\s*$", "", text)

    if text.strip():
        try:
            return json.loads(text)
        except (json.JSONDecodeError, ValueError):
            logger.warning("LLM response not valid JSON, using fallback")
    return json.loads(_FALLBACK)


def _parse_sections(scraped: str) -> dict[str, str]:
    sections = {"SPEAKERS": "", "VENUE": "", "REGISTRATION": ""}
    current = None
    for line in scraped.split("\n"):
        upper = line.strip().upper()
        if upper == "SPEAKERS:":
            current = "SPEAKERS"
        elif upper == "VENUE:":
            current = "VENUE"
        elif upper == "REGISTRATION:":
            current = "REGISTRATION"
        elif current:
            sections[current] += line + "\n"
    for k in sections:
        sections[k] = sections[k].strip()
    return sections


def _build_chunk(target: str, content: str) -> str:
    parts = []
    for s in ["SPEAKERS", "VENUE", "REGISTRATION"]:
        parts.append(f"{s}:\n{content}" if s == target and content else f"{s}:\nnull")
    return "\n\n".join(parts)


def _merge(results: list[dict]) -> dict:
    merged = json.loads(_FALLBACK)
    for r in results:
        for k in ("speakers", "venue", "registration"):
            if r.get(k) and isinstance(r[k], dict):
                merged[k] = r[k]
        for dk in ("date_start", "date_end"):
            if r.get(dk) and not merged.get(dk):
                merged[dk] = r[dk]
    return merged


@node(name="extract_sub_pages")
def extract_sub_pages_step(ctx: Context) -> dict:
    scraped = str(ctx.state.get(output_keys.SCRAPED_SUB_PAGES, ""))
    estimated = _estimate_tokens(scraped)
    logger.info("EXTRACT  ~%d tokens (limit=%d)", estimated, _MAX_TOKENS)

    if estimated <= _MAX_TOKENS:
        result = _call_llm(scraped)
    else:
        logger.info("EXTRACT  Splitting into sections")
        sections = _parse_sections(scraped)
        results = []
        for section in ("SPEAKERS", "VENUE", "REGISTRATION"):
            content = sections.get(section, "")
            if content and content != "null":
                chunk = _build_chunk(section, content)
                sec_result = _call_llm(chunk)
                results.append(sec_result)
        result = _merge(results)

    ctx.state[output_keys.SUB_PAGES_DATA] = result
    return result


# alias so orchestrator import doesn't change
extract_sub_pages_agent = extract_sub_pages_step
