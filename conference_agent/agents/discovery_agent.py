
from google.adk.agents.llm_agent import Agent
from google.adk.models import LiteLlm

from conference_agent.config import settings

MODEL = LiteLlm(
    settings.llm.discovery.model
)

discovery_agent = Agent(
    model=MODEL,
    name="discovery_agent",
    description="Discovers and filters conference URLs",
    instruction="""
    You are a conference discovery agent.

    Your job:
    1. Generate conference search queries
    2. Search using Exa
    3. Filter irrelevant results
    4. Return only real conference URLs
"""
)
