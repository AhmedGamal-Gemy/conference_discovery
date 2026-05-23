from google.adk.agents.llm_agent import Agent
from google.adk.models import LiteLlm

from conference_agent.discovery_agent import (
    discovery_agent
)

root_agent = Agent(
    model=LiteLlm("mistral/mistral-large-latest"),
    name='orchestrator',
    description='A helpful assistant for user questions.',
    instruction='Answer user questions to the best of your knowledge',
)

# attach sub-agent 
root_agent.sub_agents = [discovery_agent]