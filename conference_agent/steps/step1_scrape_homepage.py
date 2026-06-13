
import logging

from google.adk.agents.llm_agent import LlmAgent
from google.adk.models.lite_llm import LiteLlm

logger = logging.getLogger(__name__)

from conference_agent.tools.scrapling_tool import scrapling_toolset
from conference_agent.config import settings
from conference_agent.prompts.extraction import STEP1_SCRAPE_HOMEPAGE_PROMPT
from conference_agent.schemas.output_keys import output_keys
from conference_agent.steps._callbacks import strip_reasoning_content_before_model

# Logging instrumentation for step1_scrape_homepage
# DEBUG: Log entry point and URL being scraped
logger.debug(
    "step1_scrape_homepage: entering step — fetching conference homepage via MCP stealthy_fetch, "
    "url=URL from state (resolved by ADK at runtime via {state.output_keys.URL})"
)
# DEBUG: Log what the LLM is being asked to do
logger.debug(
    "step1_scrape_homepage: calling LLM to invoke stealthy_fetch tool, "
    "expected_output=HOMEPAGE_MARKDOWN (clean markdown of conference homepage)"
)
# DEBUG: Log instruction template preview
logger.debug(
    "step1_scrape_homepage: instruction template preview — %s",
    STEP1_SCRAPE_HOMEPAGE_PROMPT[:200] + "..." if len(STEP1_SCRAPE_HOMEPAGE_PROMPT) > 200 else STEP1_SCRAPE_HOMEPAGE_PROMPT
)

scrape_homepage_agent = LlmAgent(

    model=LiteLlm(model = settings.llm.extraction.model),

    name="scrape_homepage",

    description="Fetches a conference homepage and returns clean markdown",

    instruction=STEP1_SCRAPE_HOMEPAGE_PROMPT,

    tools=[scrapling_toolset],

    output_key=output_keys.HOMEPAGE_MARKDOWN,

    before_model_callback=strip_reasoning_content_before_model,
)


