"""
Step 2.6 — Probe common URL paths to discover additional conference sub-pages.

Static prompt; ADK resolves {state.output_keys.URL} at runtime.

NO output_schema — pure tool-calling agent to avoid the known ADK
conflict between tools + output_schema.
"""

from google.adk.agents.llm_agent import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import FunctionTool

from conference_agent.config import settings
from conference_agent.schemas.output_keys import output_keys
from conference_agent.tools.path_probe import probe_common_paths
from conference_agent.prompts.extraction import PROBE_PATHS_PROMPT


probe_paths_agent = LlmAgent(
    model=LiteLlm(model=settings.llm.extraction.model),
    name="probe_paths",
    description="Probes common URL paths to discover sub-pages",
    instruction=PROBE_PATHS_PROMPT,
    tools=[
        FunctionTool(func=probe_common_paths),
    ],
    output_key=output_keys.PROBED_LINKS,
)
