from google.adk.agents.llm_agent import Agent
from google.adk.models import LiteLlm

root_agent = Agent(
    model=LiteLlm("mistral/mistral-large-latest"),
    name='orchestrator',
    description='A helpful assistant for user questions.',
    instruction='Answer user questions to the best of your knowledge',
)

