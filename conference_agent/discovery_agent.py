#Search + Exa + filtering + return conferences

from conference_agent.config import settings
from exa_py import Exa
import os

exa = Exa(api_key=os.getenv("EXA_API_KEY"))


class DiscoveryAgent:

    def run(self):

        topic = settings.discovery.topic
        months = settings.discovery.months_ahead

        queries = self.generate_queries(topic, months)

        results = []

        for q in queries:
            res = self.search_exa(q)
            results.extend(res)

        results = self.deduplicate(results)
        results = self.filter_with_llm(results, topic)

        return results
        
    
if __name__ == "__main__":

    print("Discovery agent started")
    