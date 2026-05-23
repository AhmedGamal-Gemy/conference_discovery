import asyncio

from conference_agent.discovery_agent import (
    run_discovery
)


async def main():

    results = await run_discovery()

    print("\nFinal Clean Results:\n")

    for r in results:
        print(r)


if __name__ == "__main__":
    asyncio.run(main())