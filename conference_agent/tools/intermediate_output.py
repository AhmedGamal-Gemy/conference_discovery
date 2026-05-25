"""Persist intermediate pipeline results to disk.

Each step agent stores its output in session.state via output_key.
This module reads from state and writes human-readable files to output/intermediate/.
"""

import json
import os
from datetime import date
from pathlib import Path
from typing import Any

_OUTPUT_DIR = Path(__file__).parent.parent.parent / "output" / "intermediate"


def _ensure_dir():
    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _serialize(value: Any) -> Any:
    """Recursively serialize values for JSON."""
    if isinstance(value, date):
        return value.isoformat()
    if hasattr(value, "model_dump"):
        return _serialize(value.model_dump())
    if isinstance(value, dict):
        return {k: _serialize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_serialize(v) for v in value]
    if hasattr(value, "__dict__"):
        return _serialize(value.__dict__)
    return value


def save_intermediate(key: str, value: Any, suffix: str = "") -> Path:
    """Save a single state value to output/intermediate/.
    
    Args:
        key: state key (e.g. 'homepage_markdown')
        value: the value to save
        suffix: optional filename suffix for disambiguation
    
    Returns:
        Path to the written file.
    """
    _ensure_dir()
    
    filename = f"{key}{suffix}"
    filepath = _OUTPUT_DIR / filename
    
    if isinstance(value, str):
        # Raw text / markdown — write as-is
        filepath = filepath.with_suffix(".md")
        filepath.write_text(value, encoding="utf-8")
    else:
        # Structured data — write as JSON
        filepath = filepath.with_suffix(".json")
        data = _serialize(value)
        filepath.write_text(
            json.dumps(data, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8"
        )
    
    return filepath


def save_session_state(state: dict, prefix: str = "") -> list[Path]:
    """Save all known pipeline keys from session state.
    
    Args:
        state: session.state dict
        prefix: filename prefix (e.g. '01_')
    
    Returns:
        List of written file paths.
    """
    written = []
    for key, value in state.items():
        if value is not None:
            path = save_intermediate(f"{prefix}{key}", value)
            written.append(path)
    return written
