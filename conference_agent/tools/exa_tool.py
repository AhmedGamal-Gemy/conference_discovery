from exa_py import Exa
import os
from dotenv import load_dotenv

load_dotenv()

exa = Exa(api_key=os.getenv("EXA_API_KEY"))


def search_conferences(query: str, num_results: int = 10):
    result = exa.search(
        query,
        num_results=num_results,
    )

    return [
        {
            "url": r.url,
            "title": r.title or "",
            "snippet": r.text[:500] if r.text else ""
        }
        for r in result.results
    ]