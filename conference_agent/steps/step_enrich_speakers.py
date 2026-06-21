"""
Step — Enrich speaker country/affiliation via Exa web search.

Pure FunctionNode — no LLM call. Reads state via ctx parameter,
calls enrich_speakers_data() directly, writes enriched data back
to session state (in-place enrichment pattern).
"""

import logging

from google.adk.workflow import node
from google.adk.agents import Context

from conference_agent.schemas.output_keys import output_keys
from conference_agent.steps.steps_enrich import enrich_speakers_data

logger = logging.getLogger(__name__)
logger.info("STEP  Registered — enrich_speakers_step (FunctionNode, pure-Python enrichment)")

@node(name="enrich_speakers")
def enrich_speakers_step(ctx: Context) -> dict:
    """Read speaker data from session state, enrich null fields via Exa, store results."""
    homepage_data = ctx.state.get(output_keys.HOMEPAGE_DATA)
    sub_pages_data = ctx.state.get(output_keys.SUB_PAGES_DATA)

    result = enrich_speakers_data(
        homepage_data=homepage_data,
        sub_pages_data=sub_pages_data,
    )

    # In-place enrichment: write enriched data back to same state keys
    ctx.state[output_keys.HOMEPAGE_DATA] = result["homepage_data"]
    ctx.state[output_keys.SUB_PAGES_DATA] = result["sub_pages_data"]
    ctx.state[output_keys.ENRICHMENT_STATUS] = result["status"]

    return result
