"""
Step 5 — Extract structured data from scraped sub-pages (speakers, venue, registration).

Static prompt; ADK resolves {state.output_keys.SCRAPED_SUB_PAGES} at runtime.
No Python string building, no section parsing — ADK handles it.
"""

import logging

from google.adk.agents.llm_agent import LlmAgent
from google.adk.models.lite_llm import LiteLlm

logger = logging.getLogger(__name__)

from conference_agent.config import settings
from conference_agent.schemas.output_keys import output_keys
from conference_agent.schemas.sub_pages_data import SubPagesData
from conference_agent.prompts.extraction import SUB_PAGES_EXTRACTION_PROMPT
from conference_agent.steps._callbacks import strip_markdown_codeblock

# Logging instrumentation for step5_extract_sub_pages
# DEBUG: Log entry point and what data is being processed
logger.debug(
    "step5_extract_sub_pages: entering step — extracting SubPagesData from scraped sub-page markdown, "
    "input_key=%s, output_key=%s",
    output_keys.SCRAPED_SUB_PAGES,
    output_keys.SUB_PAGES_DATA
)
# DEBUG: Log what the LLM is being asked to extract
logger.debug(
    "step5_extract_sub_pages: calling LLM to parse scraped sub-pages and extract SubPagesData, "
    "expected_fields=[speakers_data (name, bio, affiliation, topic), venue_data (name, address, capacity), "
    "registration_data (fee_range, early_bird_deadline, url)]"
)
# DEBUG: Log instruction template preview
logger.debug(
    "step5_extract_sub_pages: instruction template preview — %s",
    SUB_PAGES_EXTRACTION_PROMPT[:200] + "..." if len(SUB_PAGES_EXTRACTION_PROMPT) > 200 else SUB_PAGES_EXTRACTION_PROMPT
)

extract_sub_pages_agent = LlmAgent(
    model=LiteLlm(model=settings.llm.extraction.model),
    name="extract_sub_pages",
    description="Extracts structured data from scraped speakers, venue, and registration pages",
    instruction=SUB_PAGES_EXTRACTION_PROMPT,
    output_schema=SubPagesData,
    output_key=output_keys.SUB_PAGES_DATA,
    after_model_callback=strip_markdown_codeblock,
)
