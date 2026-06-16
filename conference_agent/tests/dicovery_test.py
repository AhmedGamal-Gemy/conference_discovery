import asyncio
from conference_agent.tools.discovery_tool import run_discovery

async def main():
    results = await run_discovery()
    print(f"\n Got {len(results)} conferences:")
    for r in results:
        print(f"  - {r['title']}")
        print(f"    {r['url']}")

asyncio.run(main())