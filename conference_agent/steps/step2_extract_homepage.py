import logging

from google.adk.agents.llm_agent import LlmAgent
from google.adk.models.lite_llm import LiteLlm

logger = logging.getLogger(__name__)

from conference_agent.config import settings
from conference_agent.schemas.homepage import HomepageData
from conference_agent.schemas.output_keys import output_keys
from conference_agent.prompts.extraction import HOMEPAGE_EXTRACTION_PROMPT
from conference_agent.steps._callbacks import strip_markdown_codeblock, resolve_relative_urls

# Logging instrumentation for step2_extract_homepage
# DEBUG: Log entry point and what data is being processed
logger.debug(
    "step2_extract_homepage: entering step — extracting HomepageData from homepage markdown, "
    "input_key=%s, output_key=%s",
    output_keys.HOMEPAGE_MARKDOWN,
    output_keys.HOMEPAGE_DATA
)
# DEBUG: Log what the LLM is being asked to extract
logger.debug(
    "step2_extract_homepage: calling LLM to parse homepage markdown and extract HomepageData schema, "
    "expected_fields=[name, dates, location, description, sector_tags, ...]"
)
# DEBUG: Log instruction template preview
logger.debug(
    "step2_extract_homepage: instruction template preview — %s",
    HOMEPAGE_EXTRACTION_PROMPT[:200] + "..." if len(HOMEPAGE_EXTRACTION_PROMPT) > 200 else HOMEPAGE_EXTRACTION_PROMPT
)

extract_homepage_agent = LlmAgent(
    model=LiteLlm(settings.llm.extraction.model),
    name="extract_homepage",
    description="Extracts structured data from homepage markdown",
    instruction=HOMEPAGE_EXTRACTION_PROMPT,
    output_key=output_keys.HOMEPAGE_DATA,
    output_schema=HomepageData,
    after_model_callback=[strip_markdown_codeblock, resolve_relative_urls],
)

