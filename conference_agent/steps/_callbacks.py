"""Shared after-model callbacks (strip markdown, resolve URLs, etc.)."""

import logging
import re
from typing import Any, Optional
from urllib.parse import urljoin

from google.adk.models.llm_response import LlmResponse

logger = logging.getLogger(__name__)


# ── LiteLLM CustomLogger: intercepts reasoning_content BEFORE network ──────


class CerebrasReasoningInterceptor:
    """LiteLLM CustomLogger that strips reasoning_content from assistant messages.

    Cerebras API rejects ``reasoning_content`` in INPUT messages but returns it
    in OUTPUT. ADK stores ``Part(thought=True)`` in session history, then
    ``_content_to_message_param()`` re-serialises it as ``reasoning_content`` on
    subsequent calls -> 400 Bad Request.

    This hook runs AFTER ADK builds the final request dict but BEFORE LiteLLM
    sends the HTTP request, so it catches the field at the right layer.

    Reasoning is preserved via special think-tags prepended to ``content``
    (Cerebras GPT-OSS multi-turn format).
    """

    # Cerebras GPT-OSS expects reasoning inside  tags
    # within the content field, NOT as a separate reasoning_content property.
    # Using chr() to avoid tooling confusion with these tag names.
    _THINK_OPEN = "<" + "think" + ">"
    _THINK_CLOSE = "</" + "think" + ">"

    async def async_pre_call_hook(
        self, user_api_key_dict, cache, data, call_type
    ):
        """Mutate the outgoing payload to strip reasoning_content."""
        if call_type != "completion":
            return data

        messages = data.get("messages", [])
        stripped = 0

        for msg in messages:
            if msg.get("role") != "assistant":
                continue
            if "reasoning_content" not in msg:
                continue

            # 1. Pop the field Cerebras rejects
            reasoning = msg.pop("reasoning_content")
            stripped += 1

            # 2. Prepend as think-tags so multi-turn reasoning context survives
            if reasoning:
                existing = msg.get("content", "") or ""
                think_block = f"{self._THINK_OPEN}\n{reasoning}\n{self._THINK_CLOSE}"
                msg["content"] = f"{think_block}\n{existing}"

        if stripped:
            logger.debug(
                f"CerebrasReasoningInterceptor: moved {stripped} "
                f"reasoning_content field(s) to think-tags in content"
            )

        # 3. Must return data for mutations to persist
        return data


def strip_reasoning_content_before_model(*args, **kwargs):
    """No-op: Cerebras reasoning_content stripping is no longer needed."""
    # Return the first positional arg as-is if present
    return args[0] if args else None


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
    base_url = None
    for key in ["url", "URL", "base_url", "homepage_url"]:
        if key in kwargs:
            base_url = kwargs[key]
            break

    # If we can't find base_url, try to extract from the text itself
    if not base_url:
        url_match = re.search(r'"url"\s*:\s*"(https?://[^"]+)"', text)
        if url_match:
            base_url = url_match.group(1)

    if not base_url:
        return llm_response

    # Resolve all relative URLs in the text
    def resolve_url(match):
        url = match.group(1)
        if url.startswith("http://") or url.startswith("https://") or url.startswith("//"):
            return match.group(0)
        resolved = urljoin(base_url, url)
        return match.group(0).replace(url, resolved)

    text = re.sub(r'"url"\s*:\s*"([^"]+)"', resolve_url, text)

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