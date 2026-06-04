"""Pydantic schema for discovered links output.

Used by the discover_links LlmAgent with output_schema.
"""

from pydantic import BaseModel
from typing import Literal


class DiscoveredLink(BaseModel):
    """A single link extracted from a conference homepage."""

    url: str
    link_text: str
    category: Literal[
        "speakers",
        "venue",
        "registration",
        "schedule",
        "blog",
        "news",
        "other",
    ]


class DiscoveredLinksData(BaseModel):
    """Output of the discover_links extraction step."""

    links: list[DiscoveredLink]
