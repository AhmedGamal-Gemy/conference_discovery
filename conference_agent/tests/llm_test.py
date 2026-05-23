import asyncio
from conference_agent.tools.relevance_filter import is_relevant_conference


async def main():
    result = await is_relevant_conference(
        topic="medical",
        title="International Medical Conference 2026",
        snippet="Join leading researchers...",
        url="https://example.com"
    )

    print(result)


asyncio.run(main())