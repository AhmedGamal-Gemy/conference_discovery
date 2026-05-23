import asyncio
from conference_agent.agent import root_agent

async def main():
    result = await root_agent.run(
        "Find medical conferences in 2026"
    )

    print(result)


asyncio.run(main())