from conference_agent.tools.exa_tool import search_conferences

results = search_conferences(
    "medical conferences June 2026 speakers"
)

print(results[:2])