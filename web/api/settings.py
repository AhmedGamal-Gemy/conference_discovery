"""Settings endpoint — read/write SystemSettings for the frontend."""

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from conference_agent.config import settings
from web.schemas import SettingsResponse, SettingsUpdateRequest

logger = logging.getLogger(__name__)

router = APIRouter()


def _apply_update(target: BaseModel, patch: dict) -> None:
    """Recursively merge patch into a Pydantic model in place.

    Dict values that match a nested Pydantic sub-model are recursed into,
    preserving the model type. Scalars replace.
    """
    for key, value in patch.items():
        if not hasattr(target, key):
            setattr(target, key, value)
            continue
        if isinstance(value, dict):
            sub = getattr(target, key)
            if isinstance(sub, BaseModel):
                _apply_update(sub, value)
            else:
                setattr(target, key, value)
        else:
            setattr(target, key, value)


@router.get("/settings")
def get_settings() -> SettingsResponse:
    """Return current system settings."""
    return SettingsResponse.from_system_settings(settings)


@router.put("/settings")
def update_settings(body: SettingsUpdateRequest) -> SettingsResponse:
    """Update settings in memory. Restart to persist YAML changes."""
    patch = body.model_dump(exclude_none=True)
    _apply_update(settings, patch)
    if not settings.is_valid_topic(settings.discovery.topic):
        raise HTTPException(
            status_code=422,
            detail=f"Unknown topic: {settings.discovery.topic}. Valid: {list(settings.topics)}",
        )
    return SettingsResponse.from_system_settings(settings)
