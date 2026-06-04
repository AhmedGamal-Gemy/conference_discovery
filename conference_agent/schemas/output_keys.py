from enum import StrEnum, auto


class output_keys(StrEnum):
    URL = "URL"                # input — set by Orchestrator
    HOMEPAGE_MARKDOWN = "HOMEPAGE_MARKDOWN"
    HOMEPAGE_DATA = "HOMEPAGE_DATA"
    DISCOVERED_LINKS = "DISCOVERED_LINKS"
    SUB_PAGES_URLS = "SUB_PAGES_URLS"
    SCRAPED_SUB_PAGES = "SCRAPED_SUB_PAGES"
    PROBED_LINKS = "PROBED_LINKS"

