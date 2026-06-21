"""
Step 2.6 — Probe common URL paths to discover additional conference sub-pages.

Pure FunctionNode — no LLM call. Calls probe_common_paths() directly and
stores the result in session state. No risk of LLM tool-calling loops.
"""

import logging

from google.adk.workflow import node
from google.adk.agents import Context

from conference_agent.schemas.output_keys import output_keys
from conference_agent.tools.path_probe import probe_common_paths

logger = logging.getLogger(__name__)
logger.info("STEP  Registered — probe_paths_step (FunctionNode, no LLM)")


@node(name="probe_paths")
async def probe_paths_step(ctx: Context) -> list:
    """Probe common URL paths and store discovered sub-page URLs in session state.

    Reads the target URL from ctx.state, calls probe_common_paths, and
    writes the list of found paths to state[PROBED_LINKS].

    This is a FunctionNode (pure Python, no LLM) so it cannot loop.
    """
    url = ctx.state.get(output_keys.URL, "")
    if not url:
        logger.warning("PATH_PROBE  No URL in state — skipping")
        ctx.state[output_keys.PROBED_LINKS] = []
        return []

    result = await probe_common_paths(url)
    ctx.state[output_keys.PROBED_LINKS] = result
    logger.info(
        "PATH_PROBE  Step complete — %d path(s) found for %s",
        len(result), url,
    )
    return result
