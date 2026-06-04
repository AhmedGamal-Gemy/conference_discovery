"""
Step 2.6 — Probe common URL paths to discover additional conference sub-pages.

This agent probes well-known paths (speakers, venue, registration, etc.)
on the conference website to find sub-pages that may not be linked from
the homepage. Results are appended to DISCOVERED_LINKS.

NO output_schema — pure tool-calling agent to avoid the known ADK
conflict between tools + output_schema.
"""

from google.adk.agents.llm_agent import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import FunctionTool

from conference_agent.config import settings
from conference_agent.schemas.output_keys import output_keys
from conference_agent.tools.path_probe import probe_common_paths


def _build_probe_instruction(ctx):
    """Dynamic instruction that reads URL from session state."""
    url = ""
    if hasattr(ctx.state, 'get'):
        url = ctx.state.get(output_keys.URL, "")

    return f"""You are a conference website exploration assistant.

Your task:
1. Call the `probe_common_paths` tool with the base URL of the conference.
2. It will probe common sub-page paths and return any that exist.

Base URL: {url}

Call the tool and return the results. Do NOT make up URLs or guess.
"""


probe_paths_agent = LlmAgent(
    model=LiteLlm(model=settings.llm.extraction.model),
    name="probe_paths",
    description="Probes common URL paths to discover sub-pages",
    instruction=_build_probe_instruction,
    tools=[
        FunctionTool(func=probe_common_paths),
    ],
    output_key=output_keys.PROBED_LINKS,
)
