"""Generate diverse search queries for conference discovery.

Produces 3-4 queries per month using configurable templates:
  - Broad:      "{topic} conference {year}"         — finds homepages (no month, no "speakers")
  - CFP-based:  "{topic} call for papers {year}"    — finds active conferences seeking submissions
  - Date-specific: "{topic} conference {month} {year}" — month-targeted but no "speakers"
  - Subfield:   "{topic} {subfield} conference {month} {year}" — topic + subfield per month, rotating

IMPORTANT: Never includes "speakers" keyword — it biases toward pages that mention
"speakers" as a section heading without listing names, causing validation failures.
"""
from datetime import datetime
from dateutil.relativedelta import relativedelta
from conference_agent.config import settings

# Default templates used when settings.discovery.query_templates is empty.
# Each template is a format string with available placeholders:
#   {topic}, {month}, {year}, {subfield}
DEFAULT_QUERY_TEMPLATES = [
    "{topic} conference {year}",              # Broad — finds conference homepages
    "{topic} call for papers {year}",         # CFP-based — active conferences seeking submissions
    "{topic} conference {month} {year}",      # Date-specific — month-targeted
]


def generate_queries(topic: str = "") -> list[str]:
    """Return a list of diverse search queries for the given topic and configured months."""
    topic = topic or settings.discovery.topic
    months_ahead = settings.discovery.months_ahead
    templates = settings.discovery.query_templates or DEFAULT_QUERY_TEMPLATES
    subfields = settings.discovery.subfields

    now = datetime.now()
    queries = []

    for i in range(months_ahead):
        date = now + relativedelta(months=i)
        month = date.strftime("%B")
        year = date.year

        # Apply all templates per month
        for template in templates:
            query = template.format(topic=topic, month=month, year=year, subfield="")
            queries.append(query)

        # Subfield queries — one subfield per month, rotating
        if subfields:
            subfield = subfields[i % len(subfields)]
            subfield_query = f"{topic} {subfield} conference {month} {year}"
            queries.append(subfield_query)

    return queries
