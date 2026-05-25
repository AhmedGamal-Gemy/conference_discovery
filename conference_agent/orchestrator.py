"""
Sequential orchestrator that chains step agents:
1. scrape_homepage_agent  → fetches markdown, stores in state[HOMEPAGE_MARKDOWN]
2. extract_homepage_agent → reads state[HOMEPAGE_MARKDOWN], extracts HomepageData

This uses ADK's SequentialAgent which runs sub-agents in order and manages
state propagation between them.
"""

from google.adk.agents.sequential_agent import SequentialAgent

from conference_agent.steps.step1_scrape_homepage import scrape_homepage_agent
from conference_agent.steps.step_rate_limit_delay import rate_limit_delay_agent
from conference_agent.steps.step2_extract_homepage import extract_homepage_agent

# Sequential orchestrator: runs sub-agents in order and manages
# state propagation between them.
# SequentialAgent is a shell — it doesn't need a model; it delegates to sub-agents.
sequential_orchestrator = SequentialAgent(
    name="sequential_orchestrator",
    description="Fetches conference homepage, waits, then extracts structured data",
    sub_agents=[
        scrape_homepage_agent,
        rate_limit_delay_agent,   # sleep 30s between LLM-heavy steps
        extract_homepage_agent,
    ],
)
