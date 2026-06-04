"""
Step 5 — Extract structured data from scraped sub-pages (speakers, venue, registration).

Static prompt; ADK resolves {state.output_keys.SCRAPED_SUB_PAGES} at runtime.
No Python string building, no section parsing — ADK handles it.
"""

from google.adk.agents.llm_agent import LlmAgent
from google.adk.models.lite_llm import LiteLlm

from conference_agent.config import settings
from conference_agent.schemas.output_keys import output_keys
from conference_agent.schemas.sub_pages_data import SubPagesData
from conference_agent.prompts.extraction import SUB_PAGES_EXTRACTION_PROMPT
from conference_agent.steps._callbacks import strip_markdown_codeblock


extract_sub_pages_agent = LlmAgent(
    model=LiteLlm(model=settings.llm.extraction.model),
    name="extract_sub_pages",
    description="Extracts structured data from scraped speakers, venue, and registration pages",
    instruction=SUB_PAGES_EXTRACTION_PROMPT,
    output_schema=SubPagesData,
    output_key=output_keys.SUB_PAGES_DATA,
    after_model_callback=strip_markdown_codeblock,
)
