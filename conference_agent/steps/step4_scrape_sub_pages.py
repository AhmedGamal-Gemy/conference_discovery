"""
Step 4 — Scrape sub-pages for speakers, venue, and registration.

This agent reads SUB_PAGES_URLS from state and calls stealthy_fetch
for each URL. It returns the raw markdown content for all 3 pages.

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

    url_lines = []
    for key, url in urls.items():
        if url:
            url_lines.append(f"- {key.upper()}: {url}")
        else:
            url_lines.append(f"- {key.upper()}: (null — skip this one)")

    url_block = "\n".join(url_lines)

    return f"""You are a web scraping assistant.

You have 3 URLs to scrape. For each URL that is not null:
1. Call the stealthy_fetch tool with these exact parameters:
   - url: <the URL>
   - timeout: 30000
   - solve_cloudflare: true
   - headless: true
   - main_content_only: true
2. Save the returned markdown

If a URL is null, skip it — do NOT call the tool for that one.

After scraping ALL non-null URLs, return your results in this exact format:

SPEAKERS:
<markdown content or "null">

VENUE:
<markdown content or "null">

REGISTRATION:
<markdown content or "null">

URLs to scrape:
{url_block}
"""


scrape_sub_pages_agent = LlmAgent(
    model=LiteLlm(model=settings.llm.extraction.model),
    name="scrape_sub_pages",
    description="Scrapes speakers, venue, and registration sub-pages",
    instruction=_build_step4_instruction,
    tools=[scrapling_toolset],
    output_key=output_keys.SCRAPED_SUB_PAGES,
)
