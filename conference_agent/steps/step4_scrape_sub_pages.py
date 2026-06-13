"""
Step 4 — Scrape sub-pages for speakers, venue, and registration.

Static prompt; ADK resolves {state.output_keys.SUB_PAGES_URLS} at runtime.
The LLM reads the URL dict and calls bulk_stealthy_fetch with non-null URLs.

NO output_schema — pure tool-calling agent to avoid the known ADK
conflict between tools + output_schema.
"""

import logging

from google.adk.agents.llm_agent import LlmAgent
from google.adk.models.lite_llm import LiteLlm

logger = logging.getLogger(__name__)

from conference_agent.config import settings
from conference_agent.schemas.output_keys import output_keys
from conference_agent.tools.scrapling_tool import scrapling_toolset
from conference_agent.prompts.extraction import SCRAPE_SUB_PAGES_PROMPT
from conference_agent.steps._callbacks import strip_reasoning_content_before_model

# Logging instrumentation for step4_scrape_sub_pages
# DEBUG: Log entry point and what URLs are being scraped
logger.debug(
    "step4_scrape_sub_pages: entering step — scraping sub-pages via MCP stealthy_fetch, "
    "input_key=%s, output_key=%s",
    output_keys.SUB_PAGES_URLS,
    output_keys.SCRAPED_SUB_PAGES
)
# DEBUG: Log what the LLM is being asked to do
logger.debug(
    "step4_scrape_sub_pages: calling LLM to invoke stealthy_fetch tool for each sub-page URL "
    "(speakers, venue, registration), expected_output=SCRAPED_SUB_PAGES (markdown for each page)"
)
# DEBUG: Log instruction template preview
logger.debug(
    "step4_scrape_sub_pages: instruction template preview — %s",
    SCRAPE_SUB_PAGES_PROMPT[:200] + "..." if len(SCRAPE_SUB_PAGES_PROMPT) > 200 else SCRAPE_SUB_PAGES_PROMPT
)

scrape_sub_pages_agent = LlmAgent(
  model=LiteLlm(model=settings.llm.extraction.model),
  name="scrape_sub_pages",
  description="Scrapes speakers, venue, and registration sub-pages. Calls stealthy_fetch 3 times (speakers, venue, registration URLs).",
  instruction=SCRAPE_SUB_PAGES_PROMPT,
  tools=[scrapling_toolset],
  output_key=output_keys.SCRAPED_SUB_PAGES,
  before_model_callback=strip_reasoning_content_before_model,
)
