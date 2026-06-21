import json
import logging

from google.adk.agents.llm_agent import LlmAgent
from google.adk.models.lite_llm import LiteLlm

from conference_agent.config import settings
from conference_agent.schemas.homepage import HomepageData
from conference_agent.schemas.output_keys import output_keys
from conference_agent.prompts.extraction import HOMEPAGE_EXTRACTION_PROMPT
from conference_agent.steps._callbacks import make_homepage_extraction_callback

logger = logging.getLogger(__name__)
logger.info("STEP  Registered — extract_homepage_agent (output_schema=HomepageData)")

_HOMEPAGE_FALLBACK = json.dumps({
    "conference_name": "Unknown Conference",
    "date_start": None,
    "date_end": None,
    "industry": None,
    "keynote_speakers": [],
    "sub_pages": {
        "speakers": None,
        "venue": None,
        "registration": None,
    },
})

extract_homepage_agent = LlmAgent(
    model=LiteLlm(settings.llm.extraction.model),
    name="extract_homepage",
    description="Extracts structured data from homepage markdown",
    instruction=HOMEPAGE_EXTRACTION_PROMPT,
    output_key=output_keys.HOMEPAGE_DATA,
    output_schema=HomepageData,
    after_model_callback=make_homepage_extraction_callback(_HOMEPAGE_FALLBACK),
)

