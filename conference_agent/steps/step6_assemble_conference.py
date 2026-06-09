"""
Step 6 — Assemble the full Conference model from all pipeline outputs.

Takes all state outputs (HOMEPAGE_DATA, SUB_PAGES_DATA, URLs) and composes
them into the complete Conference model. This step does NOT validate —
that's handled by a separate validation step.

Static prompt; ADK resolves all {state.output_keys.KEY} references at runtime.
"""

from google.adk.agents.llm_agent import LlmAgent
from google.adk.models.lite_llm import LiteLlm

from conference_agent.config import settings
from conference_agent.schemas.output_keys import output_keys
from conference_agent.schemas.conference import Conference
from conference_agent.prompts.extraction import ASSEMBLE_CONFERENCE_PROMPT
from conference_agent.steps._callbacks import strip_markdown_codeblock


assemble_conference_agent = LlmAgent(
    model=LiteLlm(model=settings.llm.extraction.model),
    name="assemble_conference",
    description="Assembles all extracted data into the full Conference model",
    instruction=ASSEMBLE_CONFERENCE_PROMPT,
    output_schema=Conference,
    output_key=output_keys.CONFERENCE_DATA,
    after_model_callback=strip_markdown_codeblock,
)
