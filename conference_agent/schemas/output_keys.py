from enum import StrEnum, auto


class output_keys(StrEnum):
    URL = auto()               # input — set by Orchestrator
    HOMEPAGE_MARKDOWN = auto()
    HOMEPAGE_DATA = auto()

