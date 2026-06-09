from datetime import datetime
from dateutil.relativedelta import relativedelta
from conference_agent.config import settings

def generate_queries(topic: str, months_ahead: int):
    queries = []
    now = datetime.now()

    for i in range(months_ahead):
        date = now + relativedelta(months=i)
        month = date.strftime("%B")
        year = date.year
        query = f"{topic} conferences {month} {year} speakers"
        queries.append(query)

    return queries