"""
Step 2.5 — Discover links from the scraped homepage markdown.

Static prompt; ADK resolves {state.output_keys.URL} and
{state.output_keys.HOMEPAGE_MARKDOWN} at runtime.
"""

import logging

from google.adk.agents.llm_agent import LlmAgent
from google.adk.models.lite_llm import LiteLlm

from conference_agent.config import settings
from conference_agent.schemas.discovered_links import DiscoveredLinksData
from conference_agent.schemas.output_keys import output_keys
from conference_agent.prompts.extraction import DISCOVER_LINKS_PROMPT
from conference_agent.steps._callbacks import strip_markdown_codeblock

logger = logging.getLogger(__name__)
logger.info("STEP  Registered — discover_links_agent (output_schema=DiscoveredLinksData)")

discover_links_agent = LlmAgent(
    model=LiteLlm(model=settings.llm.extraction.model),
    name="discover_links",
    description="Extracts and classifies all links from the scraped homepage markdown",
    instruction=DISCOVER_LINKS_PROMPT,
    output_schema=DiscoveredLinksData,
    output_key=output_keys.DISCOVERED_LINKS,
    after_model_callback=strip_markdown_codeblock,
)
