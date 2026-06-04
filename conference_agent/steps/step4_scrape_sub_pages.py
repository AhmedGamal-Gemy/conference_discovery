"""
Step 4 — Scrape sub-pages for speakers, venue, and registration.

This agent reads SUB_PAGES_URLS from state and calls bulk_stealthy_fetch
with all URLs at once (single tool call instead of 3 sequential calls).

NO output_schema — this is a pure tool-calling agent to avoid the
known ADK conflict between tools + output_schema in a single agent.
"""

from google.adk.agents.llm_agent import LlmAgent
from google.adk.models.lite_llm import LiteLlm

from conference_agent.config import settings
from conference_agent.schemas.output_keys import output_keys
from conference_agent.tools.scrapling_tool import scrapling_toolset


def _build_step4_instruction(ctx):
    """Dynamic instruction that reads URLs from session state."""
    urls = {"speakers": None, "venue": None, "registration": None}

    if hasattr(ctx.state, 'get'):
        raw = ctx.state.get(output_keys.SUB_PAGES_URLS, {})
        if isinstance(raw, dict):
            urls = raw
        else:
            # Pydantic model stored in state
            urls = {
                "speakers": getattr(raw, "speakers", None),
                "venue": getattr(raw, "venue", None),
                "registration": getattr(raw, "registration", None),
            }

    # Collect non-null URLs into an array
    non_null = {k: v for k, v in urls.items() if v}
    url_list = list(non_null.values())

    if not url_list:
        return """You are a web scraping assistant.

All 3 sub-page URLs are null — nothing to scrape. Return:
SPEAKERS: null
VENUE: null
REGISTRATION: null
"""

    url_array = "\n".join(f'  "{u}"' for u in url_list)
    labels = "\n".join(f"  - {k.upper()}: {v}" for k, v in non_null.items())

    return f"""You are a web scraping assistant.

Scrape all sub-pages in a SINGLE call using bulk_stealthy_fetch:

Tool: bulk_stealthy_fetch
Parameters:
  urls: [{url_array}]
  timeout: 30000
  solve_cloudflare: true
  headless: true
  main_content_only: true

The tool returns results for all URLs simultaneously. Each result's
markdown content corresponds to the URL at the same index in the input.

Mapping (index → section):
{labels}

After the tool returns, format your response as:

SPEAKERS:
<markdown content or "null">

VENUE:
<markdown content or "null">

REGISTRATION:
<markdown content or "null">
"""


scrape_sub_pages_agent = LlmAgent(
    model=LiteLlm(model=settings.llm.extraction.model),
    name="scrape_sub_pages",
    description="Scrapes speakers, venue, and registration sub-pages",
    instruction=_build_step4_instruction,
    tools=[scrapling_toolset],
    output_key=output_keys.SCRAPED_SUB_PAGES,
)
