"""
Step 6 — Validate extracted conference data against business rules.

Pure FunctionNode — no LLM call. Reads state via ctx parameter,
calls validate_conference() directly, writes result to session state.
"""

import logging

from google.adk.workflow import node
from google.adk.agents import Context

from conference_agent.schemas.output_keys import output_keys
from conference_agent.steps.steps_validate import validate_conference

logger = logging.getLogger(__name__)
logger.info("STEP  Registered — validate_step (FunctionNode, pure-Python validation)")

@node(name="validate_conference")
def validate_step(ctx: Context) -> dict:
    """Read conference data from session state, validate against 12 rules, store result."""
    conference_id = ctx.state.get(output_keys.URL)
    homepage_data = ctx.state.get(output_keys.HOMEPAGE_DATA)
    sub_pages_data = ctx.state.get(output_keys.SUB_PAGES_DATA)

    result = validate_conference(
        conference_id=conference_id,
        homepage_data=homepage_data,
        sub_pages_data=sub_pages_data,
    )

    ctx.state[output_keys.VALIDATION_DATA] = result
    return result
