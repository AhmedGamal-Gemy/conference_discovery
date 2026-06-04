"""
Step 4 — Scrape sub-pages for speakers, venue, and registration.

Static prompt; ADK resolves {state.output_keys.SUB_PAGES_URLS} at runtime.
The LLM reads the URL dict and calls bulk_stealthy_fetch with non-null URLs.

NO output_schema — pure tool-calling agent to avoid the known ADK
conflict between tools + output_schema.
"""

from google.adk.agents.llm_agent import LlmAgent
from google.adk.models.lite_llm import LiteLlm

from conference_agent.config import settings
from conference_agent.schemas.output_keys import output_keys
from conference_agent.tools.scrapling_tool import scrapling_toolset
from conference_agent.prompts.extraction import SCRAPE_SUB_PAGES_PROMPT


scrape_sub_pages_agent = LlmAgent(
    model=LiteLlm(model=settings.llm.extraction.model),
    name="scrape_sub_pages",
    description="Scrapes speakers, venue, and registration sub-pages",
    instruction=SCRAPE_SUB_PAGES_PROMPT,
    tools=[scrapling_toolset],
    output_key=output_keys.SCRAPED_SUB_PAGES,
)
