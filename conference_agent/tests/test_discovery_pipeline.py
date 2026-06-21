"""End-to-end discovery pipeline test — verify redesigned pipeline finds valid conference URLs."""
import logging
logging.basicConfig(level=logging.INFO, format="%(name)s  %(message)s")

from conference_agent.tools.discovery_tool import run_discovery

results = list(run_discovery())

print("\n=== DISCOVERY RESULTS ===")
print(f"Total accepted: {len(results)}")
for r in results:
    print(f"  {r['title'][:80]}  |  {r['url']}")
