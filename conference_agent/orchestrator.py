"""
Workflow orchestrator that chains all step agents:
1. scrape_homepage_agent     → fetches markdown
2. extract_homepage_agent    → extracts HomepageData from markdown
3. discover_links_agent      → extracts and classifies all links from markdown
4. probe_paths_step          → probes common URL paths for sub-pages (FunctionNode, no LLM)
5. merge_links_agent         → picks best sub-page URLs from all discovered links
6. scrape_sub_pages_agent    → scrapes speakers, venue, registration sub-pages
7. extract_sub_pages_agent   → extracts structured data with auto context-window splitting
8. enrich_speakers_step      → fills null country/affiliation via Exa search (FunctionNode, no LLM)
9. validate_step             → validates extracted data against 12 business rules (FunctionNode, no LLM)

Uses Workflow (ADK 2.0 graph-based replacement for SequentialAgent).

Note: All LLM calls route through the local LiteLLM proxy (port 4000)
configured in config.py. The proxy handles rate limiting internally
(max retries: 20, exponential backoff). No manual delay agents needed.
"""

import logging

from google.adk import Workflow

from conference_agent.steps.step1_scrape_homepage import scrape_homepage_agent
from conference_agent.steps.step2_extract_homepage import extract_homepage_agent
from conference_agent.steps.step2_5_discover_links import discover_links_agent
from conference_agent.steps.step2_6_probe_paths import probe_paths_step
from conference_agent.steps.step3_merge_links import merge_links_agent
from conference_agent.steps.step4_scrape_sub_pages import scrape_sub_pages_agent
from conference_agent.steps.step5_extract_sub_pages import extract_sub_pages_agent
from conference_agent.steps.step_enrich_speakers import enrich_speakers_step
from conference_agent.steps.step6_validate import validate_step

logger = logging.getLogger(__name__)
logger.info(
    "PIPELINE  Workflow created — 9 steps: scrape → extract → discover → probe → merge → scrape_sub → extract_sub → enrich → validate"
)

pipeline_orchestrator = Workflow(
    name="pipeline_orchestrator",
    description="Full conference scraping and validation pipeline: fetch → extract → discover → probe → merge → scrape sub-pages → validate",
    edges=[
        (
            "START",
            scrape_homepage_agent,
            extract_homepage_agent,
            discover_links_agent,
            probe_paths_step,
            merge_links_agent,
            scrape_sub_pages_agent,
            extract_sub_pages_agent,
            enrich_speakers_step,
            validate_step,
        ),
    ],
)
