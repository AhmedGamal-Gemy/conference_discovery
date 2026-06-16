from enum import StrEnum, auto


class output_keys(StrEnum):
    URL = auto()
    HOMEPAGE_MARKDOWN = auto()
    HOMEPAGE_DATA = auto()
    DISCOVERED_LINKS = auto()
    PROBED_LINKS = auto()
    SUB_PAGES_URLS = auto()
    SCRAPED_SUB_PAGES = auto()
    SPEAKERS_DATA = auto()
    VENUE_DATA = auto()
    REGISTRATION_DATA = auto()
    SUB_PAGES_DATA = auto()
    VALIDATION_DATA = auto()

