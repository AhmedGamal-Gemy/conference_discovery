#Search + Exa + filtering + return conferences
import os
from exa_py import Exa
from datetime import datetime
from dateutil.relativedelta import relativedelta
from conference_agent.config import settings

exa = Exa(api_key=os.getenv("EXA_API_KEY"))

# 1. Generate queries
def generate_queries(topic: str, months_ahead: int):
    queries = []
    now = datetime.now()

    for i in range(months_ahead):
        date = now + relativedelta(months=i)
        month = date.strftime("%B")
        year = date.strftime("%Y")

        queries.append(f"{topic} conferences {month} {year} speakers")

    return queries

# 2. Exa search
def search_exa(exa, query: str):
    results = exa.search_and_contents(
        query,
        num_results=settings.exa.num_results,
        text=True
    )

    return [
        {
            "url": r.url,
            "title": r.title or "",
            "snippet": r.text[:500] if r.text else ""
        }
        for r in results.results
    ]

# 3. Deduplicate
def deduplicate(results):
    seen = set()
    clean = []

    for r in results:
        if r["url"] not in seen:
            seen.add(r["url"])
            clean.append(r)

    return clean

# 4. Prompt builder
def build_prompt(topic, item):
    return f"""
You are filtering conference search results.

Topic: {topic}

Title: {item['title']}
URL: {item['url']}
Snippet: {item['snippet']}

Question:
Is this a REAL conference relevant to the topic?

Rules:
- YES only if it's an actual conference/event page
- NO for blogs, lists, directories, SEO pages

Answer only YES or NO
"""
# 5. Filter with LLM
async def filter_results(llm, topic, results):
    filtered = []

    for r in results:
        prompt = build_prompt(topic, r)
        response = await llm.generate(prompt)

        if "YES" in response.upper():
            filtered.append({
                "url": r["url"],
                "title": r["title"]
            })

    return filtered

# 6. MAIN AGENT
class DiscoveryAgent:
    def __init__(self, exa, llm):
        self.exa = exa
        self.llm = llm

    async def run(self):
        topic = settings.discovery.topic
        months = settings.discovery.months_ahead

        # step 1: queries
        queries = generate_queries(topic, months)

        # step 2: search
        all_results = []
        for q in queries:
            all_results.extend(search_exa(self.exa, q))

        # step 3: dedup
        unique = deduplicate(all_results)

        # step 4: filter
        final = await filter_results(self.llm, topic, unique)

        return final


# Note: llm is not defined in this module. Do not execute on import.
# Example usage (run from an async context after creating an llm instance):
#   await DiscoveryAgent(exa, llm).run()
