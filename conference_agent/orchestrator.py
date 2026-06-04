"""
Workflow orchestrator that chains all step agents:
1. scrape_homepage_agent  → fetches markdown
2. extract_homepage_agent → extracts HomepageData from markdown
3. discover_links_agent   → extracts and classifies all links from markdown
4. probe_paths_agent      → probes common URL paths for sub-pages
5. merge_links_agent      → picks best sub-page URLs from all discovered links
6. scrape_sub_pages_agent → scrapes speakers, venue, registration sub-pages

Uses Workflow (ADK 2.0 graph-based replacement for SequentialAgent).

Note: All LLM calls route through the local LiteLLM proxy (port 4000)
configured in config.py. The proxy handles rate limiting internally
(max retries: 20, exponential backoff). No manual delay agents needed.
"""

from google.adk import Workflow

from conference_agent.config import settings

from conference_agent.steps.step1_scrape_homepage import scrape_homepage_agent
from conference_agent.steps.step2_extract_homepage import extract_homepage_agent
from conference_agent.steps.step2_5_discover_links import discover_links_agent
from conference_agent.steps.step2_6_probe_paths import probe_paths_agent
from conference_agent.steps.step3_merge_links import merge_links_agent
from conference_agent.steps.step4_scrape_sub_pages import scrape_sub_pages_agent

pipeline_orchestrator = Workflow(
    name="pipeline_orchestrator",
    description="Full conference scraping pipeline: fetch → extract → discover → probe → merge → scrape sub-pages",
    edges=[
        (
            "START",
            scrape_homepage_agent,
            extract_homepage_agent,
            discover_links_agent,
            probe_paths_agent,
            merge_links_agent,
            scrape_sub_pages_agent,
        ),
    ],
)
