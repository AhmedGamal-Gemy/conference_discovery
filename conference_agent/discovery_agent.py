from datetime import datetime
from dateutil.relativedelta import relativedelta
import asyncio

from google.adk.agents.llm_agent import Agent
from google.adk.models import LiteLlm

from conference_agent.config import settings
from conference_agent.tools.exa_tool import search_conferences
from conference_agent.tools.relevance_filter import (
    is_relevant_conference
)

MODEL = LiteLlm(
    settings.llm.relevance_filter.model
)

def generate_queries():
    topic = settings.discovery.topic
    months = settings.discovery.months_ahead

    now = datetime.now()

    queries = []

    for i in range(months):
        date = now + relativedelta(months=i)

        month = date.strftime("%B")
        year = date.year

        query = f"{topic} conferences {month} {year} speakers"

        queries.append(query)

    return queries


async def run_discovery():

    print("\nGenerating queries...\n")

    queries = generate_queries()

    for q in queries:
        print(q)

    raw_results = []

    print("\nSearching Exa...\n")

    for query in queries:
        results = search_conferences(
            query,
            settings.exa.num_results
        )

        raw_results.extend(results)

    print(f"Found {len(raw_results)} raw results")

    dedup = {}

    for r in raw_results:
        dedup[r["url"]] = r

    deduped_results = list(dedup.values())

    print(f"Deduplicated → {len(deduped_results)}")

    print("\nRunning relevance filter...\n")

    clean_results = []

    for r in deduped_results:

        try:
            relevant = await is_relevant_conference(
                topic=settings.discovery.topic,
                title=r["title"],
                snippet=r["snippet"],
                url=r["url"]
            )

            if relevant:
                print(f"ACCEPTED: {r['title']}")
                clean_results.append({
                    "url": r["url"],
                    "title": r["title"]
                })

            else:
                print(f"REJECTED: {r['title']}")

        except Exception as e:
            print(f"ERROR: {e}")

    return clean_results


discovery_agent = Agent(
    model=MODEL,
    name="discovery_agent",
    description="Discovers and filters conference URLs",
    instruction="""
You discover scientific conference URLs.
""",
)