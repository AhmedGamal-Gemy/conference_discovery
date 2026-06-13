"""
Step 2.5 — Discover links from the scraped homepage markdown.

Static prompt; ADK resolves {state.output_keys.URL} and
{state.output_keys.HOMEPAGE_MARKDOWN} at runtime.
"""

import logging

from google.adk.agents.llm_agent import LlmAgent
from google.adk.models.lite_llm import LiteLlm

logger = logging.getLogger(__name__)

from conference_agent.config import settings
from conference_agent.schemas.discovered_links import DiscoveredLinksData
from conference_agent.schemas.output_keys import output_keys
from conference_agent.prompts.extraction import DISCOVER_LINKS_PROMPT
from conference_agent.steps._callbacks import strip_reasoning_content_before_model, strip_markdown_codeblock, resolve_relative_urls

# Logging instrumentation for step2_5_discover_links
# DEBUG: Log entry point and what data is being processed
logger.debug(
    "step2_5_discover_links: entering step — extracting and classifying all links from homepage markdown, "
    "input_key=%s, output_key=%s",
    output_keys.HOMEPAGE_MARKDOWN,
    output_keys.DISCOVERED_LINKS
)
# DEBUG: Log what the LLM is being asked to find
logger.debug(
    "step2_5_discover_links: calling LLM to parse homepage markdown and classify all links, "
    "expected_output=DiscoveredLinksData with categories [speakers, venue, registration, ...]"
)
# DEBUG: Log instruction template preview
logger.debug(
    "step2_5_discover_links: instruction template preview — %s",
    DISCOVER_LINKS_PROMPT[:200] + "..." if len(DISCOVER_LINKS_PROMPT) > 200 else DISCOVER_LINKS_PROMPT
)

discover_links_agent = LlmAgent(
    model=LiteLlm(model=settings.llm.extraction.model),
    name="discover_links",
    description="Extracts and classifies all links from the scraped homepage markdown",
    instruction=DISCOVER_LINKS_PROMPT,
    output_schema=DiscoveredLinksData,
    output_key=output_keys.DISCOVERED_LINKS,
    before_model_callback=strip_reasoning_content_before_model,
    after_model_callback=[strip_markdown_codeblock, resolve_relative_urls],
)
