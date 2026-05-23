from google.adk.agents.llm_agent import Agent
from google.adk.models import LiteLlm
 
from conference_agent.config import settings
from conference_agent.agents.discovery_agent import discovery_agent

root_agent = Agent(
    model=LiteLlm(settings.llm.orchestrator.model),
    name='orchestrator',
    description='A helpful assistant for user questions.',
    instruction="""
You are a conference discovery orchestrator.
When the user asks to find conferences, delegate to the discovery_agent.
""",
    sub_agents=[
        discovery_agent
    ]
)
