"""Shared after-model callbacks used by multiple step agents."""

import json
import re
from typing import Any, Optional
from urllib.parse import urljoin

from google.adk.models.llm_response import LlmResponse
from google.adk.models.llm_request import LlmRequest

from conference_agent.config import settings


def strip_reasoning_content_before_model(
    callback_context: Any, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """Before-model callback: rename reasoning_content → reasoning for Cerebras.

    Cerebras API rejects reasoning_content in INPUT messages but returns it in
    OUTPUT. ADK stores it in session history, so subsequent calls fail with:
    'messages.N.assistant.reasoning_content: property is unsupported'

    This renames reasoning_content → reasoning only when Cerebras is used.
    Only affects assistant role messages.
    """
    # Only strip when using Cerebras (check settings, not llm_request.model)
    if "cerebras" not in settings.llm.extraction.model.lower():
        return None

    if llm_request.contents:
        for content in llm_request.contents:
            if content.role == "assistant":
                _strip_reasoning_content(content)
    return None


def _strip_reasoning_content(content: Any) -> None:
    """Remove reasoning_content from a Content object, rename to reasoning if needed."""
    # Handle __dict__ (Pydantic extra fields, direct attributes)
    if hasattr(content, "__dict__"):
        d = content.__dict__
        if "reasoning_content" in d:
            val = d.pop("reasoning_content")
            if "reasoning" not in d:
                d["reasoning"] = val
    # Also handle parts
    if hasattr(content, "parts") and content.parts:
        for part in content.parts:
            if hasattr(part, "__dict__"):
                pd = part.__dict__
                if "reasoning_content" in pd:
                    val = pd.pop("reasoning_content")
                    if "reasoning" not in pd:
                        pd["reasoning"] = val


def strip_markdown_codeblock(*args, **kwargs):
    """After-model callback to strip markdown code blocks from JSON responses."""
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
        cleaned = re.sub(r"^```json\s*", "", text)
        cleaned = re.sub(r"\s*```\s*$", "", cleaned)
        if cleaned != text:
            llm_response.content.parts[0].text = cleaned
    return llm_response or args[0] if args else None


def resolve_relative_urls(*args, **kwargs):
    """After-model callback to resolve relative URLs to absolute.
    
    Fixes the common bug where LLMs resolve relative URLs against the domain
    root instead of the base URL's directory path.
    """
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
    
    if not llm_response or not llm_response.content or not llm_response.content.parts:
        return llm_response or args[0] if args else None
    
    text = llm_response.content.parts[0].text or ""
    if not text:
        return llm_response
    
    # Try to find the base URL in the session context
    # The runner's session context is available via kwargs
    base_url = None
    for key in ["url", "URL", "base_url", "homepage_url"]:
        if key in kwargs:
            base_url = kwargs[key]
            break
    
    # If we can't find base_url, try to extract from the text itself
    if not base_url:
        # Look for a URL pattern in the text
        url_match = re.search(r'"url"\s*:\s*"(https?://[^"]+)"', text)
        if url_match:
            base_url = url_match.group(1)
    
    if not base_url:
        return llm_response
    
    # Resolve all relative URLs in the text
    # Pattern: "url": "path/to/page.php" or "url": "/path/to/page.php"
    def resolve_url(match):
        url = match.group(1)
        if url.startswith("http://") or url.startswith("https://") or url.startswith("//"):
            return match.group(0)  # Already absolute
        resolved = urljoin(base_url, url)
        return match.group(0).replace(url, resolved)
    
    # Fix URLs in JSON format
    text = re.sub(r'"url"\s*:\s*"([^"]+)"', resolve_url, text)
    
    # Also fix sub_pages URLs
    def resolve_subpage_url(match):
        url = match.group(1)
        if url.startswith("http://") or url.startswith("https://") or url.startswith("//"):
            return match.group(0)
        resolved = urljoin(base_url, url)
        return match.group(0).replace(url, resolved)
    
    text = re.sub(r'"(speakers|venue|registration)"\s*:\s*"([^"]+)"', resolve_subpage_url, text)
    
    if text != llm_response.content.parts[0].text:
        llm_response.content.parts[0].text = text
    
    return llm_response
