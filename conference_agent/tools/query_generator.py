from datetime import datetime
from dateutil.relativedelta import relativedelta
from conference_agent.config import settings

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