"""
Step 3 — Merge discovered links into HomepageData.

Static prompt; ADK resolves {state.output_keys.HOMEPAGE_DATA},
{state.output_keys.DISCOVERED_LINKS}, and {state.output_keys.PROBED_LINKS}
at runtime.
"""

from google.adk.agents.llm_agent import LlmAgent
from google.adk.models.lite_llm import LiteLlm

from conference_agent.config import settings
from conference_agent.schemas.homepage import SubPages
from conference_agent.schemas.output_keys import output_keys
from conference_agent.prompts.extraction import MERGE_LINKS_PROMPT
from conference_agent.steps._callbacks import strip_markdown_codeblock


merge_links_agent = LlmAgent(
    model=LiteLlm(model=settings.llm.extraction.model),
    name="merge_links",
    description="Picks best sub-page URLs from discovered links",
    instruction=MERGE_LINKS_PROMPT,
    output_schema=SubPages,
    output_key=output_keys.SUB_PAGES_URLS,
    after_model_callback=strip_markdown_codeblock,
)
