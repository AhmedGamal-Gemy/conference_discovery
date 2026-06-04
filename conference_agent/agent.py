from google.adk.agents.llm_agent import Agent
from google.adk.models import LiteLlm
 
from conference_agent.config import settings
from conference_agent.tools.discovery_tool import run_discovery
# from conference_agent.agents.discovery_agent import discovery_agent

root_agent = Agent(
    model=LiteLlm(settings.llm.orchestrator.model),
    name='orchestrator',
    description='Conference discovery orchestrator',
    instruction="""
    You are a conference discovery assistant.
    When the user asks to find conferences, call the run_discovery tool.
    Return the results to the user as a clean list.
    Do not search on your own. Always use the run_discovery tool.
    """,
    tools=[run_discovery],
    
)

