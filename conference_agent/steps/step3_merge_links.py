"""
Step 3 — Merge discovered links into HomepageData.

This agent reads HOMEPAGE_DATA and DISCOVERED_LINKS from state,
picks the best URL for each sub_pages field (speakers, venue, registration),
and returns the updated sub_pages URLs.
"""

from google.adk.agents.llm_agent import LlmAgent
from google.adk.models.lite_llm import LiteLlm

from conference_agent.config import settings
from conference_agent.schemas.homepage import SubPages
from conference_agent.schemas.output_keys import output_keys


def _merge_links_data(ctx) -> str:
    """Combine discovered links and probed links into a single readable block."""
    discovered = ""
    probed = ""

    if hasattr(ctx.state, 'get'):
        discovered = ctx.state.get(output_keys.DISCOVERED_LINKS, "")
        probed = ctx.state.get(output_keys.PROBED_LINKS, "")

    parts = []
    if discovered:
        parts.append("=== Links from homepage markdown ===")
        parts.append(str(discovered))
    if probed:
        parts.append("=== Links from URL path probing ===")
        parts.append(str(probed))

    return "\n\n".join(parts) if parts else "(no links found)"


def _build_step3_instruction(ctx):
    """Dynamic instruction that reads data from session state."""
    homepage_data = ""
    if hasattr(ctx.state, 'get'):
        homepage_data = ctx.state.get(output_keys.HOMEPAGE_DATA, "")

    links_block = _merge_links_data(ctx)

    return f"""You are a data merging assistant.

You have two inputs:
1. Current HomepageData (extracted earlier, may have null sub_pages)
2. Discovered links from the homepage (already classified by category)
3. Probed links from URL path probing (additional paths found)

Your task:
- Pick the BEST URL for each sub_pages field: speakers, venue, registration
- Return ONLY a JSON object with those 3 fields

CRITICAL rules for picking URLs:
- A blog post titled "Announcing the Invited Talks" IS the speakers page, even if its URL contains /blog/.
- A blog post about "Registration Update" IS the registration page, even if its URL contains /blog/.
- "Program Committee" is NOT the speakers page — it's about organizers/reviewers.
- "View All Dates" is a schedule page, not speakers.
- Match by CONTENT and INTENT, not just URL patterns.
- If a field is already set with a good URL, keep it unless you find a clearly better match.
- If a field is null, fill it with the best matching discovered link.
- If no good match exists for a field, return null for that field.

Return ONLY this exact JSON structure (no markdown, no commentary):
{{"speakers": "URL or null", "venue": "URL or null", "registration": "URL or null"}}

Current HomepageData:
{homepage_data}

All discovered links:
{links_block}
"""


def _strip_markdown_codeblock(*args, **kwargs):
    """After-model callback to strip markdown code blocks from JSON responses."""
    from google.adk.models.llm_response import LlmResponse
    llm_response = None
    for arg in args:
        if isinstance(arg, LlmResponse):
            llm_response = arg
            break
    if not llm_response:
        for v in kwargs.values():
            if isinstance(v, LlmResponse):
                llm_response = v
                break

    if llm_response and llm_response.content and llm_response.content.parts:
        text = llm_response.content.parts[0].text or ""
        import re
        cleaned = re.sub(r'^```json\s*', '', text)
        cleaned = re.sub(r'\s*```\s*$', '', cleaned)
        if cleaned != text:
            llm_response.content.parts[0].text = cleaned
    return llm_response or args[0] if args else None


merge_links_agent = LlmAgent(
    model=LiteLlm(model=settings.llm.extraction.model),
    name="merge_links",
    description="Picks best sub-page URLs from discovered links",
    instruction=_build_step3_instruction,
    output_schema=SubPages,
    output_key=output_keys.SUB_PAGES_URLS,
    after_model_callback=_strip_markdown_codeblock,
)
