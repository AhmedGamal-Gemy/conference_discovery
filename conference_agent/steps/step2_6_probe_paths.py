"""
Step 2.6 — Probe common URL paths to discover additional conference sub-pages.

Static prompt; ADK resolves {state.output_keys.URL} at runtime.

NO output_schema — pure tool-calling agent to avoid the known ADK
conflict between tools + output_schema.
"""

import logging

from google.adk.agents.llm_agent import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import FunctionTool

logger = logging.getLogger(__name__)

from conference_agent.config import settings
from conference_agent.schemas.output_keys import output_keys
from conference_agent.tools.path_probe import probe_common_paths
from conference_agent.prompts.extraction import PROBE_PATHS_PROMPT
from conference_agent.steps._callbacks import strip_reasoning_content_before_model

# Logging instrumentation for step2_6_probe_paths
# DEBUG: Log entry point and what paths are being probed
logger.debug(
    "step2_6_probe_paths: entering step — probing common URL paths for sub-pages, "
    "url=URL from state (resolved by ADK at runtime via {state.output_keys.URL}), output_key=%s",
    output_keys.PROBED_LINKS
)
# DEBUG: Log what paths are being probed
logger.debug(
    "step2_6_probe_paths: calling probe_common_paths tool to check common paths like "
    "/speakers/, /venue/, /registration/, /schedule/, /program/, /cfp/, /about/"
)
# DEBUG: Log instruction template preview
logger.debug(
    "step2_6_probe_paths: instruction template preview — %s",
    PROBE_PATHS_PROMPT[:200] + "..." if len(PROBE_PATHS_PROMPT) > 200 else PROBE_PATHS_PROMPT
)

probe_paths_agent = LlmAgent(
    model=LiteLlm(model=settings.llm.extraction.model),
    name="probe_paths",
    description="Probes common URL paths to discover sub-pages",
    instruction=PROBE_PATHS_PROMPT,
    tools=[
        FunctionTool(func=probe_common_paths),
    ],
    output_key=output_keys.PROBED_LINKS,
    before_model_callback=strip_reasoning_content_before_model,
)
