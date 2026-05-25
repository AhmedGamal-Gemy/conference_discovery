STEP1_SCRAPE_HOMEPAGE_PROMPT = """
You are a web scraping agent.
Fetch the conference homepage at this URL: {state.URL}

Use the stealthy_fetch tool with these exact parameters:
- url: {state.URL}
- timeout: 60000
- solve_cloudflare: true
- headless: true
- main_content_only: true

Return the raw markdown content only. No explanation, no commentary.
"""


HOMEPAGE_EXTRACTION_PROMPT = """
You are a data extraction assistant. You will be given the markdown content of a conference homepage.

Extract the following information and return it as a JSON object matching this exact structure:

{
    "conference_name": "Full official name of the conference",
    "date_start": "YYYY-MM-DD or null if not found",
    "date_end": "YYYY-MM-DD or null if not found",
    "industry": "The scientific or academic field (e.g. 'medicine', 'engineering', 'computer science')",
    "sub_pages": {
        "speakers": "Full absolute URL to the speakers page or null",
        "venue": "Full absolute URL to the venue page or null",
        "registration": "Full absolute URL to the registration page or null"
    }
}

Rules:
- Return ONLY the JSON object, no explanation, no markdown backticks.
- For sub_pages URLs, always return absolute URLs (include the base domain).
- If a field is not found, return null for that field.
- For industry, infer from the conference topic if not explicitly stated.
- For dates, only extract dates for THIS specific upcoming conference edition, not past editions.

Homepage markdown:
{state.HOMEPAGE_MARKDOWN}
"""


SPEAKERS_EXTRACTION_PROMPT = """
You are a data extraction assistant. You will be given the markdown content of a conference speakers page.

Extract the following information and return it as a JSON object matching this exact structure:

{
    "speakers_confirmed": true or false,
    "speakers": [
        {
            "name": "Full name of the speaker",
            "title": "Academic or professional title (e.g. 'Prof.', 'Dr.', 'CEO') or null",
            "affiliation": "University, institution, or company name or null",
            "country": "Country of the affiliation or null",
            "is_scientific": true or false
        }
    ]
}

Rules:
- Return ONLY the JSON object, no explanation, no markdown backticks.
- Set speakers_confirmed to true ONLY if the speakers listed are confirmed for THIS specific upcoming conference edition.
- Set speakers_confirmed to false if: the list says "coming soon", "to be announced", "will be updated", shows only past edition speakers, or the list is empty.
- is_scientific is true if the speaker is an academic researcher, professor, scientist, or medical professional. false for industry executives, journalists, or non-scientific speakers.
- Only include speakers, not organizers or committee members.
- If no speakers are found, return an empty list and set speakers_confirmed to false.

Speakers page markdown:
{markdown}
"""


VENUE_EXTRACTION_PROMPT = """
You are a data extraction assistant. You will be given the markdown content of a conference venue page.

Extract the following information and return it as a JSON object matching this exact structure:

{
    "venue_name": "Full name of the venue or null",
    "venue_address": "Full street address or null",
    "city": "City name or null",
    "country": "Country name or null",
    "is_hotel": true or false
}

Rules:
- Return ONLY the JSON object, no explanation, no markdown backticks.
- Set is_hotel to true if the venue is a hotel, resort, or similar accommodation facility.
- Set is_hotel to false if the venue is a university, convention center, research institute, or any non-accommodation facility.
- If the venue name is not found or the page only shows a general city without a specific venue, return null for venue_name and venue_address.
- A specific venue means a named building or facility with a real address, not just a city or country.

Venue page markdown:
{markdown}
"""


REGISTRATION_EXTRACTION_PROMPT = """
You are a data extraction assistant. You will be given the markdown content of a conference registration page.

Extract the following information and return it as a JSON object matching this exact structure:

{
    "covers_accommodation": true or false
}

Rules:
- Return ONLY the JSON object, no explanation, no markdown backticks.
- Set covers_accommodation to true ONLY if the registration fee explicitly includes hotel accommodation or the conference explicitly arranges and covers lodging for attendees.
- Set covers_accommodation to false if:
    - Registration fees cover only attendance, meals, or conference materials.
    - The page mentions hotels nearby but does not include them in the fee.
    - The page recommends hotels without covering the cost.
    - There is no mention of accommodation at all.
- When in doubt, return false.

Registration page markdown:
{markdown}
"""

