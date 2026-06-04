"""
Step 2.5 — Discover links from the scraped homepage markdown.

This agent extracts and classifies all links from the homepage markdown using
an LLM with a structured output schema.
"""

from google.adk.agents.llm_agent import LlmAgent
from google.adk.models.lite_llm import LiteLlm

from conference_agent.config import settings
from conference_agent.schemas.discovered_links import DiscoveredLinksData
from conference_agent.schemas.output_keys import output_keys


def _build_discover_links_instruction(ctx):
    """Dynamic instruction that reads markdown from session state."""
    markdown = ""
    url = ""
    
    if hasattr(ctx.state, 'get'):
        markdown = ctx.state.get(output_keys.HOMEPAGE_MARKDOWN, "")
        url = ctx.state.get(output_keys.URL, "")
    
    return f"""You are a link extraction assistant. Given the conference homepage markdown below, extract ALL links and classify each one.

Return ONLY a JSON object matching this exact structure:

{{
    "links": [
        {{
            "url": "Full absolute URL (include domain)",
            "link_text": "The visible text of the link, or empty string if raw URL",
            "category": "speakers|venue|registration|schedule|blog|news|other"
        }}
    ]
}}

Classification rules:
- "speakers": links about keynote speakers, invited talks, presenters, or speaker lists
- "venue": links about conference location, hotels, travel directions, or accommodation
- "registration": links about registering, tickets, fees, payment, or attending
- "schedule": links about program, agenda, dates, timetable, sessions, or calendar
- "blog": links to blog posts, articles, or stories about the conference
- "news": links to news announcements, press releases, or updates
- "other": everything else (sponsors, FAQ, code of conduct, etc.)

Rules:
- Return ONLY the JSON object, no explanation, no markdown backticks.
- Convert all relative URLs (e.g. "/speakers") to absolute URLs using the base URL.
- If a URL is already absolute, keep it as-is.
- Include every distinct link found in the markdown, even if category is "other".
- If no links are found, return {{"links": []}}.

Base URL: {url}

Homepage markdown:
{markdown}
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


discover_links_agent = LlmAgent(
    model=LiteLlm(model=settings.llm.extraction.model),
    name="discover_links",
    description="Extracts and classifies all links from the scraped homepage markdown",
    instruction=_build_discover_links_instruction,
    output_schema=DiscoveredLinksData,
    output_key=output_keys.DISCOVERED_LINKS,
    after_model_callback=_strip_markdown_codeblock,
)
