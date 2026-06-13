"""
Step 3 — Merge discovered links into HomepageData.

Static prompt; ADK resolves {state.output_keys.HOMEPAGE_DATA},
{state.output_keys.DISCOVERED_LINKS}, and {state.output_keys.PROBED_LINKS}
at runtime.
"""

import logging

from google.adk.agents.llm_agent import LlmAgent
from google.adk.models.lite_llm import LiteLlm

logger = logging.getLogger(__name__)

from conference_agent.config import settings
from conference_agent.schemas.homepage import SubPages
from conference_agent.schemas.output_keys import output_keys
from conference_agent.prompts.extraction import MERGE_LINKS_PROMPT
from conference_agent.steps._callbacks import strip_reasoning_content_before_model, strip_markdown_codeblock, resolve_relative_urls

# Logging instrumentation for step3_merge_links
# DEBUG: Log entry point and what data is being merged
logger.debug(
    "step3_merge_links: entering step — merging discovered + probed links into SubPages URLs, "
    "input_keys=[%s, %s, %s], output_key=%s",
    output_keys.HOMEPAGE_DATA,
    output_keys.DISCOVERED_LINKS,
    output_keys.PROBED_LINKS,
    output_keys.SUB_PAGES_URLS
)
# DEBUG: Log what the LLM is being asked to do
logger.debug(
    "step3_merge_links: calling LLM to pick best sub-page URLs from discovered and probed links, "
    "expected_output=SubPages with fields [speakers_url, venue_url, registration_url, ...]"
)
# DEBUG: Log instruction template preview
logger.debug(
    "step3_merge_links: instruction template preview — %s",
    MERGE_LINKS_PROMPT[:200] + "..." if len(MERGE_LINKS_PROMPT) > 200 else MERGE_LINKS_PROMPT
)

merge_links_agent = LlmAgent(
    model=LiteLlm(model=settings.llm.extraction.model),
    name="merge_links",
    description="Picks best sub-page URLs from discovered links",
    instruction=MERGE_LINKS_PROMPT,
    output_schema=SubPages,
    output_key=output_keys.SUB_PAGES_URLS,
    before_model_callback=strip_reasoning_content_before_model,
    after_model_callback=[strip_markdown_codeblock, resolve_relative_urls],
)
