"""
LLM extraction prompts.

NOTE: Prompts use {state.output_keys.KEY} uppercase placeholders for readability.
A DRY resolver at the bottom replaces each with the ADK-native {state.key} syntax
at module load time — before ADK's template engine resolves against session state.
"""

from conference_agent.schemas.output_keys import output_keys


STEP1_SCRAPE_HOMEPAGE_PROMPT = """
You are a web scraping agent.
Fetch the conference homepage at this URL: {state.output_keys.URL}

Use the stealthy_fetch tool with these exact parameters:
- url: {state.output_keys.URL}
- timeout: 60000
- solve_cloudflare: true
- headless: true
- main_content_only: true

Return the raw markdown content only. No explanation, no commentary.
"""


HOMEPAGE_EXTRACTION_PROMPT = """
You are a data extraction assistant. You will be given the markdown content of a conference homepage.

Extract ALL available information and return it as a JSON object matching this exact structure:

{
    "conference_name": "Full official name of the conference",
    "conference_acronym": "Short acronym or abbreviation (e.g. 'AIME 2026', 'ICEST 2026') or null",
    "date_start": "YYYY-MM-DD or null if not found",
    "date_end": "YYYY-MM-DD or null. IMPORTANT: If a date range is given (e.g. July 7-10, 2026), BOTH start AND end dates must be extracted. Do NOT drop the end date."
  "industry": "The primary scientific or academic field as a SINGLE short label (e.g. 'medicine', 'engineering', 'computer science', 'environmental science'). Use the most specific one-word or two-word label.",
  "sector_tags": ["List of ALL scientific/technical/industry topics mentioned for this conference (e.g. ['marine biology', 'oceanography', 'environmental health']). Include every distinct field mentioned. Return an empty list if none found."],
  "conference_format": "The event format: 'hybrid', 'in-person', 'virtual', or null if not specified",
    "organizer": "The organizing institution or society name, or null",
    "submission_deadline": "YYYY-MM-DD of the paper/abstract submission deadline, or null",
    "venue_city": "City where the conference is held, or null",
    "venue_country": "Country where the conference is held, or null",
    "sub_pages": {
        "speakers": "Full absolute URL to the speakers page or null",
        "venue": "Full absolute URL to the venue page or null",
        "registration": "Full absolute URL to the registration page or null"
    }
}

Rules:
- Return ONLY the JSON object, no explanation, no markdown backticks.
- Extract EVERY field. Only use null if the information is truly not available in the provided markdown.
- For sub_pages URLs, always return absolute URLs (include the full domain).
- For industry: use the most specific single label available (e.g. "marine biology" beats "environmental science").
- For sector_tags: list ALL distinct topics/fields mentioned, even if they span multiple disciplines. Use short human-readable tags.
- For dates, only extract dates for THIS specific upcoming conference edition, not past editions.
- conference_format: look for keywords like "hybrid", "in-person", "virtual", "online", "onsite".
- submission_deadline: look for "submission deadline", "paper deadline", "abstract deadline", "call for papers".

Homepage markdown:
{state.output_keys.HOMEPAGE_MARKDOWN}
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
  "covers_accommodation": true or false,
  "fee_range_usd": "e.g. '400-1900 USD' or 'early bird: 300 USD / regular: 500 USD' or null if not shown",
  "early_bird_deadline": "YYYY-MM-DD of the early-bird registration deadline, or null"
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
- fee_range_usd: extract the lowest and highest fee mentioned, or the early-bird/regular split. Write it as a short readable string.
- early_bird_deadline: look for "early bird", "early registration", "discount deadline". Convert to YYYY-MM-DD.

Registration page markdown:
{markdown}
"""


SUB_PAGES_EXTRACTION_PROMPT = """
You are a data extraction assistant. Extract structured data from the scraped sub-pages of a conference website.

Below is the raw markdown content of three sub-pages — speakers, venue, and registration — separated by SPEAKERS:, VENUE:, and REGISTRATION: headers. Extract ALL three sections and return them as a single JSON object.

Extract the following for each section:

=== SPEAKERS EXTRACTION ===
{
    "speakers": {
        "speakers": [
            {
                "name": "Full name of the speaker",
                "title": "Academic or professional title (e.g. 'Prof.', 'Dr.', 'CEO') or null",
                "affiliation": "University, institution, or company name or null",
                "country": "Country of the affiliation or null",
                "is_scientific": true or false
            }
        ],
        "speakers_confirmed": true or false,
        "notes": "Any relevant notes or empty string"
    }
}

Rules for speakers:
- Set speakers_confirmed to true ONLY if the speakers listed are confirmed for THIS specific upcoming conference edition.
- Set speakers_confirmed to false if: the list says "coming soon", "to be announced", "will be updated", shows only past edition speakers, or the list is empty.
- is_scientific is true if the speaker is an academic researcher, professor, scientist, or medical professional. false for industry executives, journalists, or non-scientific speakers.
- Only include speakers, not organizers or committee members.
- If no speakers are found, return an empty list and set speakers_confirmed to false.

=== VENUE EXTRACTION ===
{
    "venue": {
        "venue_name": "Full name of the venue or null",
        "venue_address": "Full street address or null",
        "city": "City name or null",
        "country": "Country name or null",
        "is_hotel": true or false
    }
}

Rules for venue:
- Set is_hotel to true if the venue is a hotel, resort, or similar accommodation facility.
- Set is_hotel to false if the venue is a university, convention center, research institute, or any non-accommodation facility.
- If the venue name is not found or the page only shows a general city without a specific venue, return null for venue_name and venue_address.

=== REGISTRATION EXTRACTION ===
{
    "registration": {
        "covers_accommodation": true or false
    }
}

Rules for registration:
- Set covers_accommodation to true ONLY if the registration fee explicitly includes hotel accommodation or the conference explicitly arranges and covers lodging for attendees.
- Set covers_accommodation to false if:
    - Registration fees cover only attendance, meals, or conference materials.
    - The page mentions hotels nearby but does not include them in the fee.
    - The page recommends hotels without covering the cost.
    - There is no mention of accommodation at all.
- When in doubt, return false.

Return ONLY the JSON object with all three sections. No explanation, no markdown backticks.

Raw sub-page markdown:
{state.output_keys.SCRAPED_SUB_PAGES}

FALLBACK: If any section above (SPEAKERS, VENUE, or REGISTRATION) has null or empty content, extract that section's data from the homepage markdown below instead. The homepage may contain speaker names, venue information, and registration details even when no dedicated sub-page exists.

Homepage markdown (for fallback extraction):
{state.output_keys.HOMEPAGE_MARKDOWN}
"""


DISCOVER_LINKS_PROMPT = """
You are a link extraction assistant. Given the conference homepage markdown below, extract ALL links and classify each one.

Return ONLY a JSON object matching this exact structure:
{{
    "links": [
        {{
            "url": "Full absolute URL (include domain)",
            "link_text": "The visible text of the link, or empty string if raw URL",
            "category": "speakers|venue|registration|schedule|blog|news|other"
        }}
    ]
}}

Classification rules:
- "speakers": links about keynote speakers, invited talks, presenters, or speaker lists
- "venue": links about conference location, hotels, travel directions, or accommodation
- "registration": links about registering, tickets, fees, payment, or attending
- "schedule": links about program, agenda, dates, timetable, sessions, or calendar
- "blog": links to blog posts, articles, or stories about the conference
- "news": links to news announcements, press releases, or updates
- "other": everything else (sponsors, FAQ, code of conduct, etc.)

Rules:
- Return ONLY the JSON object, no explanation, no markdown backticks.
- Convert ALL relative URLs to absolute URLs using the base URL.
- IMPORTANT: The base URL includes a directory path. For example, if the base URL is "https://example.com/event/index.php?id=123", then a relative URL like "speakers.php?id=123" should become "https://example.com/event/speakers.php?id=123" (NOT "https://example.com/speakers.php?id=123"). The relative URL is resolved against the DIRECTORY containing the base URL.
- If a URL is already absolute, keep it as-is.
- Include every distinct link found in the markdown, even if category is "other".
- If no links are found, return {{"links": []}}.

Base URL: {state.output_keys.URL}

Homepage markdown:
{state.output_keys.HOMEPAGE_MARKDOWN}
"""


PROBE_PATHS_PROMPT = """
You are a conference website exploration assistant.

Your task:
1. Call the `probe_common_paths` tool with the base URL of the conference.
2. It will probe common sub-page paths and return any that exist.

Base URL: {state.output_keys.URL}

Call the tool and return the results. Do NOT make up URLs or guess.
"""


MERGE_LINKS_PROMPT = """
You are a data merging assistant.

You have three inputs:
1. Current HomepageData (extracted earlier, may have null sub_pages)
2. Discovered links from the homepage (already classified by category)
3. Probed links from URL path probing (additional paths found)

Your task:
- Pick the BEST URL for each sub_pages field: speakers, venue, registration
- Return ONLY a JSON object with those 3 fields

CRITICAL rules for picking URLs:
- A blog post titled "Announcing the Invited Talks" IS the speakers page, even if its URL contains /blog/.
- A blog post about "Registration Update" IS the registration page, even if its URL contains /blog/.
- "Program Committee" is NOT the speakers page — it's about organizers/reviewers.
- "View All Dates" is a schedule page, not speakers.
- Match by CONTENT and INTENT, not just URL patterns.
- If a field is already set with a good URL, keep it unless you find a clearly better match.
- If a field is null, fill it with the best matching discovered link.
- If no good match exists for a field, return null for that field.

Return ONLY this exact JSON structure (no markdown, no commentary):
{{"speakers": "URL or null", "venue": "URL or null", "registration": "URL or null"}}

Current HomepageData:
{state.output_keys.HOMEPAGE_DATA}

All discovered links:
{state.output_keys.DISCOVERED_LINKS}

Probed links:
{state.output_keys.PROBED_LINKS}
"""


SCRAPE_SUB_PAGES_PROMPT = """
You are a web scraping assistant.

Scrape all available sub-pages in a SINGLE call using bulk_stealthy_fetch.
The tool returns results for all URLs simultaneously.

Tool: bulk_stealthy_fetch
Parameters:
  urls: [list of non-null URLs from the sub-page data below]
  timeout: 30000
  solve_cloudflare: true
  headless: true
  main_content_only: true

Sub-page URLs:
{state.output_keys.SUB_PAGES_URLS}

IMPORTANT:
- Only include URLs that are not null.
- After the tool returns, label each result by its section (SPEAKERS, VENUE, REGISTRATION).
- If ALL URLs are null, return: SPEAKERS: null / VENUE: null / REGISTRATION: null
- Format your response as:

SPEAKERS:
<markdown content or "null">

VENUE:
<markdown content or "null">

REGISTRATION:
<markdown content or "null">
"""


ASSEMBLE_CONFERENCE_PROMPT = """
You are a data assembly assistant. Combine all extracted conference data into a single complete model.

You have three sources:
1. HOMEPAGE_DATA — extracted from the homepage (name, dates, industry, etc.)
2. SUB_PAGES_DATA — extracted from speakers/venue/registration sub-pages
3. SUB_PAGES_URLS — the URLs used for the sub-pages

Assemble them into this exact JSON structure:

{
    "conference_id": "Short unique ID (use the conference acronym like 'AIME2026' or a slug from the name)",
    "homepage": {
        "conference_name": "from HOMEPAGE_DATA",
        "conference_acronym": "from HOMEPAGE_DATA",
        "date_start": "from HOMEPAGE_DATA",
        "date_end": "from HOMEPAGE_DATA",
        "industry": "from HOMEPAGE_DATA",
        "conference_format": "from HOMEPAGE_DATA",
        "organizer": "from HOMEPAGE_DATA",
        "submission_deadline": "from HOMEPAGE_DATA",
        "venue_city": "from HOMEPAGE_DATA",
        "venue_country": "from HOMEPAGE_DATA",
        "sub_pages": {
            "speakers": "from HOMEPAGE_DATA.sub_pages.speakers or null",
            "venue": "from HOMEPAGE_DATA.sub_pages.venue or null",
            "registration": "from HOMEPAGE_DATA.sub_pages.registration or null"
        }
    },
    "venue": {
        "venue_name": "from SUB_PAGES_DATA.venue.venue_name or null",
        "venue_address": "from SUB_PAGES_DATA.venue.venue_address or null",
        "city": "from SUB_PAGES_DATA.venue.city or HOMEPAGE_DATA.venue_city",
        "country": "from SUB_PAGES_DATA.venue.country or HOMEPAGE_DATA.venue_country",
        "is_hotel": "from SUB_PAGES_DATA.venue.is_hotel or false"
    },
    "registration": {
        "covers_accommodation": "from SUB_PAGES_DATA.registration.covers_accommodation or false"
    },
    "speakers": "list from SUB_PAGES_DATA.speakers.speakers (include ALL speakers, or empty list)",
    "total_speakers": "length of speakers list",
    "non_local_count": "count of speakers where is_local is false or null, 0 if empty list",
    "non_usa_count": "count of speakers where is_usa is false or null, 0 if empty list",
    "website_url": "the original conference URL from the system state",
    "speakers_page_url": "from SUB_PAGES_URLS.speakers or null"
}

IMPORTANT RULES:
- Include EVERY field. Use null for missing data, 0 for missing counts.
- For venue.city and venue.country: prefer SUB_PAGES_DATA, fall back to HOMEPAGE_DATA.
- For speakers: pass EXACTLY what's in SUB_PAGES_DATA.speakers — do not modify.
- total_speakers, non_local_count, non_usa_count are DERIVED — compute them from the speakers list.
- The website_url is: {state.output_keys.URL}

Return ONLY the raw JSON. No explanation, no markdown backticks.

HOMEPAGE_DATA:
{state.output_keys.HOMEPAGE_DATA}

SUB_PAGES_DATA:
{state.output_keys.SUB_PAGES_DATA}

SUB_PAGES_URLS:
{state.output_keys.SUB_PAGES_URLS}
"""

# ---------------------------------------------------------------------------
# DRY resolver: replace {state.output_keys.KEY} with output_keys enum values.
# Runs once at module load time — before ADK's template engine. Prompts use
# the self-documenting {state.output_keys.KEY} form; this converts them to
# ADK-native {key} syntax (e.g. {state.output_keys.URL} → {url}) resolves at runtime.
# ---------------------------------------------------------------------------
def _resolve_state_keys(text: str) -> str:
    for member in output_keys:
        text = text.replace(
            f"{{state.output_keys.{member.name}}}",
            f"{{{member.value}?}}",
        )
    return text


# Apply to all prompts that reference output_keys
ALL_PROMPTS = [
    STEP1_SCRAPE_HOMEPAGE_PROMPT,
    HOMEPAGE_EXTRACTION_PROMPT,
    SUB_PAGES_EXTRACTION_PROMPT,
    DISCOVER_LINKS_PROMPT,
    PROBE_PATHS_PROMPT,
    MERGE_LINKS_PROMPT,
    SCRAPE_SUB_PAGES_PROMPT,
    ASSEMBLE_CONFERENCE_PROMPT,
]
for i, p in enumerate(ALL_PROMPTS):
    ALL_PROMPTS[i] = _resolve_state_keys(p)

STEP1_SCRAPE_HOMEPAGE_PROMPT = ALL_PROMPTS[0]
HOMEPAGE_EXTRACTION_PROMPT = ALL_PROMPTS[1]
SUB_PAGES_EXTRACTION_PROMPT = ALL_PROMPTS[2]
DISCOVER_LINKS_PROMPT = ALL_PROMPTS[3]
PROBE_PATHS_PROMPT = ALL_PROMPTS[4]
MERGE_LINKS_PROMPT = ALL_PROMPTS[5]
SCRAPE_SUB_PAGES_PROMPT = ALL_PROMPTS[6]
ASSEMBLE_CONFERENCE_PROMPT = ALL_PROMPTS[7]

