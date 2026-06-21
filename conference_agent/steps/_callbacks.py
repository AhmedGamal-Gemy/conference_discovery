"""Shared after-model callbacks used by multiple step agents."""

import json
import logging
import re

from google.adk.agents.context import Context
from google.adk.models.llm_response import LlmResponse

from conference_agent.schemas.output_keys import output_keys
from conference_agent.tools.date_extractor import extract_dates_from_markdown

logger = logging.getLogger(__name__)


def _find_llm_response(args, kwargs):
    """Extract LlmResponse from positional or keyword args."""
    for arg in args:
        if isinstance(arg, LlmResponse):
            return arg
    for v in kwargs.values():
        if isinstance(v, LlmResponse):
            return v
    return None


def _find_context(args, kwargs):
    """Extract Context (CallbackContext) from positional or keyword args."""
    for arg in args:
        if isinstance(arg, Context):
            return arg
    for v in kwargs.values():
        if isinstance(v, Context):
            return v
    return None


def strip_markdown_codeblock(*args, **kwargs):
    """After-model callback to strip markdown code blocks from JSON responses."""
    llm_response = _find_llm_response(args, kwargs)
    if llm_response and llm_response.content and llm_response.content.parts:
        text = llm_response.content.parts[0].text or ""
        cleaned = re.sub(r"^```json\s*", "", text)
        cleaned = re.sub(r"\s*```\s*$", "", cleaned)
        if cleaned != text:
            llm_response.content.parts[0].text = cleaned
    return llm_response or args[0] if args else None


def make_fallback_callback(fallback_json: str):
    """Create an after-model callback with markdown-stripping + JSON fallback.

    The callback does three things:
      1. Strips markdown fences from the response.
      2. Attempts ``json.loads()`` — on failure the *entire* response is
         replaced with *fallback_json*.
      3. After a successful parse, merges the result with *fallback_json* so
         that any field the LLM returned as ``null`` is filled with the
         fallback default.  This prevents ADK's schema validation from
         crashing on required fields that the LLM refused to supply.

    Example:
        If the LLM returns ``{"conference_name": null}`` and the fallback
        has ``{"conference_name": "Unknown Conference"}``, the callback
        produces ``{"conference_name": "Unknown Conference"}``.
    """

    def _merge_nulls(data: dict, fallback: dict) -> dict:
        """Recursively fill null/dict fields in *data* from *fallback* defaults."""
        for key, fb_val in fallback.items():
            if key not in data:
                data[key] = fb_val
            elif data[key] is None and fb_val is not None:
                data[key] = fb_val
            elif isinstance(data[key], dict) and isinstance(fb_val, dict):
                _merge_nulls(data[key], fb_val)
        return data

    def callback(*args, **kwargs):
        llm_response = _find_llm_response(args, kwargs)
        if llm_response and llm_response.content and llm_response.content.parts:
            text = llm_response.content.parts[0].text or ""
            # Strip markdown fences
            cleaned = re.sub(r"^```(?:json)?\s*", "", text)
            cleaned = re.sub(r"\s*```\s*$", "", cleaned)
            if cleaned != text:
                text = cleaned
            # Validate JSON — fall back on parse failure
            if text.strip():
                try:
                    parsed = json.loads(text)
                    # Merge with fallback to fill null required fields
                    if isinstance(parsed, dict):
                        fallback_parsed = json.loads(fallback_json)
                        parsed = _merge_nulls(parsed, fallback_parsed)
                        text = json.dumps(parsed, ensure_ascii=False, indent=None)
                except (json.JSONDecodeError, ValueError):
                    text = fallback_json
            else:
                text = fallback_json
            llm_response.content.parts[0].text = text
        return llm_response or (args[0] if args else None)

    return callback


def make_homepage_extraction_callback(fallback_json: str):
    """After-model callback for homepage extraction with date regex fallback.

    Does everything ``make_fallback_callback`` does (markdown stripping, JSON
    parsing, null-field merging), then if ``date_start`` is still null/empty,
    runs a regex-based date extractor on the raw homepage markdown from session
    state as a last resort.

    The callback signature is ``(callback_context, llm_response)`` as per the
    ADK ``after_model_callback`` protocol.
    """
    _fallback = make_fallback_callback(fallback_json)

    def callback(*args, **kwargs):
        # Step 1: Run the standard fallback logic (strip fences, parse JSON,
        #         merge null fields with fallback defaults).
        _fallback(*args, **kwargs)
        llm_response = _find_llm_response(args, kwargs)

        if not (llm_response and llm_response.content and llm_response.content.parts):
            return llm_response or (args[0] if args else None)

        text = llm_response.content.parts[0].text or ""
        try:
            parsed = json.loads(text) if text.strip() else {}
        except json.JSONDecodeError:
            return llm_response or (args[0] if args else None)

        # Step 2: If date_start is still null/empty, try regex fallback
        if not parsed.get("date_start"):
            callback_ctx = _find_context(args, kwargs)
            markdown = ""
            if callback_ctx and hasattr(callback_ctx, "state"):
                markdown = callback_ctx.state.get(
                    output_keys.HOMEPAGE_MARKDOWN.value, ""
                )
            else:
                logger.warning(
                    "DATE_FALLBACK  No Context/CallbackContext found in args — "
                    "cannot access homepage markdown for regex extraction"
                )

            if markdown:
                regex_start, regex_end = extract_dates_from_markdown(markdown)
                if regex_start:
                    logger.info(
                        "DATE_FALLBACK  Regex extracted dates: %s – %s "
                        "(LLM returned null)",
                        regex_start, regex_end or regex_start,
                    )
                    parsed["date_start"] = regex_start
                    if regex_end:
                        parsed["date_end"] = regex_end
                    llm_response.content.parts[0].text = json.dumps(
                        parsed, ensure_ascii=False, indent=None,
                    )
                else:
                    logger.info(
                        "DATE_FALLBACK  Regex also found no date in markdown "
                        "(%d chars)", len(markdown),
                    )

        return llm_response or (args[0] if args else None)

    return callback
