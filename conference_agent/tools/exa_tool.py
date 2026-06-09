"""
Exa Search API wrapper.

Thin sync wrapper around exa-py. Dotenv is loaded at the entry point
(web/app.py, web/api/__init__.py) before any conference_agent modules
are imported, so this module relies on the environment already being set.
"""

from exa_py import Exa
import os

# EXA_API_KEY must be in the environment (loaded by .env loader upstream).
# We intentionally do NOT call load_dotenv() here to avoid doing I/O
# at module import time and to respect the app's dotenv loading order.
_exa_api_key = os.environ.get("EXA_API_KEY")
if not _exa_api_key:
    # Only warn at import time; actual errors surface on first call.
    import warnings
    warnings.warn(
        "EXA_API_KEY not set in environment. "
        "Set it in conference_agent/.env or export it.",
        RuntimeWarning,
        stacklevel=2,
    )

_exa = Exa(api_key=_exa_api_key) if _exa_api_key else None


def search_conferences(query: str, num_results: int = 10) -> list[dict]:
    """Search Exa and return normalized result dicts.

    Returns empty list if EXA_API_KEY is not configured or the search fails.
    """
    if _exa is None:
        return []
    try:
        result = _exa.search(query, num_results=num_results)
    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning("Exa search error: %s", exc)
        return []

    return [
        {
            "url": r.url,
            "title": r.title or "",
            "snippet": r.text[:500] if r.text else "",
        }
        for r in getattr(result, "results", [])
    ]
