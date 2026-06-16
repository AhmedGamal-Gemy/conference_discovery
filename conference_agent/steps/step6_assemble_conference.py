"""
Step 6 — Assemble the full Conference model from all pipeline outputs.

Takes all state outputs (HOMEPAGE_DATA, SUB_PAGES_DATA, URLs) and composes
them into the complete Conference model. This step does NOT validate —
that's handled by a separate validation step.

Static prompt; ADK resolves all {state.output_keys.KEY} references at runtime.
"""

import logging

from google.adk.agents.llm_agent import LlmAgent
from google.adk.models.lite_llm import LiteLlm

logger = logging.getLogger(__name__)

from conference_agent.config import settings
from conference_agent.schemas.output_keys import output_keys
from conference_agent.schemas.conference import Conference
from conference_agent.prompts.extraction import ASSEMBLE_CONFERENCE_PROMPT
from conference_agent.steps._callbacks import strip_markdown_codeblock

# Logging instrumentation for step6_assemble_conference
# DEBUG: Log entry point and all inputs being assembled
logger.debug(
    "step6_assemble_conference: entering step — assembling full Conference model from all pipeline outputs, "
    "input_keys=[%s, %s, %s, %s, %s], output_key=%s",
    output_keys.HOMEPAGE_DATA,
    output_keys.SUB_PAGES_DATA,
    output_keys.SUB_PAGES_URLS,
    output_keys.HOMEPAGE_MARKDOWN,
    output_keys.URL,
    output_keys.CONFERENCE_DATA
)
# DEBUG: Log what the LLM is being asked to do
logger.debug(
    "step6_assemble_conference: calling LLM to compose all extracted data into full Conference model, "
    "expected_output=Conference with all fields [name, dates, location, speakers, venue, registration, ...]"
)
# DEBUG: Log instruction template preview
logger.debug(
    "step6_assemble_conference: instruction template preview — %s",
    ASSEMBLE_CONFERENCE_PROMPT[:200] + "..." if len(ASSEMBLE_CONFERENCE_PROMPT) > 200 else ASSEMBLE_CONFERENCE_PROMPT
)

assemble_conference_agent = LlmAgent(
    model=LiteLlm(model=settings.llm.extraction.model),
    name="assemble_conference",
    description="Assembles all extracted data into the full Conference model",
    instruction=ASSEMBLE_CONFERENCE_PROMPT,
    output_schema=Conference,
    output_key=output_keys.CONFERENCE_DATA,
    after_model_callback=strip_markdown_codeblock,
)
