import logging

from google.adk.agents.llm_agent import LlmAgent
from google.adk.models.lite_llm import LiteLlm

from conference_agent.tools.scrapling_tool import scrapling_toolset
from conference_agent.config import settings
from conference_agent.prompts.extraction import STEP1_SCRAPE_HOMEPAGE_PROMPT
from conference_agent.schemas.output_keys import output_keys

logger = logging.getLogger(__name__)
logger.info("STEP  Registered — scrape_homepage_agent (uses scrapling MCP toolset)")

scrape_homepage_agent = LlmAgent(

    model=LiteLlm(model = settings.llm.extraction.model),

    name="scrape_homepage",

    description="Fetches a conference homepage and returns clean markdown",
    
    instruction=STEP1_SCRAPE_HOMEPAGE_PROMPT,

    tools=[scrapling_toolset],

    output_key=output_keys.HOMEPAGE_MARKDOWN,
)


