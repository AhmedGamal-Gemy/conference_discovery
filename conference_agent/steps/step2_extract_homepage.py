from google.adk.agents.llm_agent import LlmAgent
from google.adk.models.lite_llm import LiteLlm

from conference_agent.config import settings
from conference_agent.schemas.homepage import HomepageData
from conference_agent.schemas.output_keys import output_keys
from conference_agent.prompts.extraction import HOMEPAGE_EXTRACTION_PROMPT



extract_homepage_agent = LlmAgent(
    model=LiteLlm(settings.llm.extraction.model),
    name="extract_homepage",
    description="Extracts structured data from homepage markdown",
    instruction=HOMEPAGE_EXTRACTION_PROMPT,
    output_key=output_keys.HOMEPAGE_DATA,
    output_schema=HomepageData,
)

