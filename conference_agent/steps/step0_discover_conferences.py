"""
Step 0 — Discover candidate conference URLs via Exa API.

Runs BEFORE the scrape pipeline. Uses the existing discovery tools
(query_generator, exa_tool, relevance_filter) to search for conferences
matching the configured topic, filters with an LLM relevance check,
and stores the result list in session state.

No output_schema — result is stored as a plain dict list via output_key.
"""

from google.adk.agents.llm_agent import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import FunctionTool

from conference_agent.config import settings
from conference_agent.schemas.output_keys import output_keys
from conference_agent.tools.discovery_tool import run_discovery


async def discover_conferences(
    topic: str = "",
    months_ahead: int = 0,
    num_results: int = 0,
) -> list[dict]:
    """Discover conference URLs via Exa search + LLM relevance filter.

    Args:
        topic: Conference topic (defaults to settings.discovery.topic).
        months_ahead: How many months ahead to search.
        num_results: Max results per query.
    """
    topic = topic or settings.discovery.topic
    months_ahead = months_ahead or settings.discovery.months_ahead
    num_results = num_results or settings.exa.num_results

    return await run_discovery(topic, months_ahead, num_results)


discover_conferences_tool = FunctionTool(func=discover_conferences)

discover_conferences_agent = LlmAgent(
    model=LiteLlm(model=settings.llm.extraction.model),
    name="discover_conferences",
    description=(
        "Searches for conference URLs using Exa API filtered by LLM relevance. "
        "Returns a list of candidate conference URLs with titles."
    ),
    instruction=(
        "You are a conference discovery agent. "
        "Call the `discover_conferences` tool ONCE with no arguments (uses defaults from settings). "
        "Return the tool result as-is — a JSON list of {url, title} dicts. "
        "Do NOT call the tool more than once. "
        "Do NOT fabricate URLs — only return what the tool returns."
    ),
    tools=[discover_conferences_tool],
    output_key=output_keys.DISCOVERY_RESULTS,
)
