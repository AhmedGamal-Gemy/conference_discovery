"""
Run the full pipeline against a given URL, save output to JSON, and show progress.
Usage: uv run python run_pipeline.py <url>
"""

import asyncio
import json
import sys
import time
from datetime import datetime
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part

from conference_agent.orchestrator import pipeline_orchestrator
from conference_agent.schemas.output_keys import output_keys
from conference_agent.schemas.homepage import HomepageData
from conference_agent.schemas.conference import Conference


async def run_pipeline(url: str):
    t0 = time.time()
    print(f"\n{'='*60}")
    print(f"URL: {url}")
    print(f"Started: {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*60}\n")

    session_service = InMemorySessionService()
    session = await session_service.create_session(
        app_name="conference_discovery",
        user_id="qa_user",
        session_id="qa_session",
        state={output_keys.URL: url},
    )

    runner = Runner(
        agent=pipeline_orchestrator,
        app_name="conference_discovery",
        session_service=session_service,
    )

    step_names = {
        "scrape_homepage": "1. Scrape homepage",
        "extract_homepage": "2. Extract homepage",
        "discover_links": "3. Discover links",
        "probe_paths": "4. Probe paths",
        "merge_links": "5. Merge links",
        "scrape_sub_pages": "6. Scrape sub-pages",
        "extract_sub_pages": "7. Extract sub-pages",
        "assemble_conference": "8. Assemble Conference",
    }

    total_steps = len(step_names)
    step_count = 0
    async for event in runner.run_async(
        user_id="qa_user",
        session_id="qa_session",
        new_message=Content(role="user", parts=[Part(text="Process this conference")]),
    ):
        if event.is_final_response() and event.author in step_names:
            step_count += 1
            elapsed = time.time() - t0
            step_label = step_names[event.author]
            print(f"  [{step_count}/{total_steps}] {step_label} ({elapsed:.1f}s)")

    if step_count == 0:
        print("\n  ERROR: No steps completed. Pipeline may have timed out.")
        return None

    elapsed = time.time() - t0
    print(f"\n  Pipeline completed: {elapsed:.1f}s")

    updated = await session_service.get_session(
        app_name="conference_discovery",
        user_id="qa_user",
        session_id="qa_session",
    )
    state = updated.state

    # Fix URL resolution: resolve relative URLs to absolute using proper urljoin
    from urllib.parse import urljoin
    base_url = state.get(output_keys.URL, "")
    if base_url:
        # Fix sub_pages URLs in homepage_data
        homepage_data = state.get(output_keys.HOMEPAGE_DATA, {})
        if isinstance(homepage_data, dict):
            sub_pages = homepage_data.get("sub_pages", {})
            for key in ["speakers", "venue", "registration"]:
                if sub_pages.get(key):
                    sub_pages[key] = urljoin(base_url, sub_pages[key])
        
        # Fix discovered_links URLs
        discovered_links = state.get(output_keys.DISCOVERED_LINKS, {})
        if isinstance(discovered_links, dict):
            for link in discovered_links.get("links", []):
                if link.get("url"):
                    link["url"] = urljoin(base_url, link["url"])
        
        # Fix sub_pages_urls
        sub_pages_urls = state.get(output_keys.SUB_PAGES_URLS, {})
        if isinstance(sub_pages_urls, dict):
            for key in ["speakers", "venue", "registration"]:
                if sub_pages_urls.get(key):
                    sub_pages_urls[key] = urljoin(base_url, sub_pages_urls[key])

    # Save full state to JSON
    output_file = f"output/intermediate/pipeline_state_{int(time.time())}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False, default=str)
    print(f"  State saved: {output_file}")

    print(f"\n{'='*60}")
    print("FULL CONFERENCE MODEL")
    print(f"{'='*60}")

    conference_raw = state.get(output_keys.CONFERENCE_DATA, {})
    if isinstance(conference_raw, dict) and conference_raw.get("conference_id"):
        try:
            c = Conference.model_validate(conference_raw)
            print(f"\n  Conference ID : {c.conference_id}")
            print(f"  Name         : {c.homepage.conference_name}")
            print(f"  Acronym      : {c.homepage.conference_acronym}")
            print(f"  Dates        : {c.homepage.date_start or '?'} -> {c.homepage.date_end or '?'}")
            print(f"  Format       : {c.homepage.conference_format or '?'}")
            print(f"  Industry     : {c.homepage.industry or '?'}")
            print(f"  Organizer    : {c.homepage.organizer or '?'}")
            print(f"  Submission   : {c.homepage.submission_deadline or '?'}")
            print(f"  Website      : {c.website_url}")
            print(f"\n  -- Venue --")
            print(f"     Name    : {c.venue.venue_name or '?'}")
            print(f"     Address : {c.venue.venue_address or '?'}")
            print(f"     City    : {c.venue.city or c.homepage.venue_city or '?'}")
            print(f"     Country : {c.venue.country or c.homepage.venue_country or '?'}")
            print(f"     Is hotel: {c.venue.is_hotel}")
            print(f"\n  -- Registration --")
            print(f"     Covers accommodation: {c.registration.covers_accommodation}")
            print(f"\n  -- Speakers ({len(c.speakers)}) --")
            print(f"     Confirmed   : {c.speakers_page_url or 'not available'}")
            for s in c.speakers[:5]:
                aff = f" ({s.affiliation})" if s.affiliation else ""
                print(f"     - {s.name}{aff}")
            if len(c.speakers) > 5:
                print(f"     ... and {len(c.speakers)-5} more")
            if not c.speakers:
                print(f"     (no speakers extracted)")
            print(f"\n  -- Derived --")
            print(f"     Total speakers : {c.total_speakers}")
            print(f"     Non-local     : {c.non_local_count}")
            print(f"     Non-USA       : {c.non_usa_count}")
        except Exception as e:
            print(f"\n  Conference parse error: {e}")
            print(f"  Raw: {json.dumps(conference_raw, indent=2, default=str)[:1000]}")
    else:
        print(f"\n  Conference data not assembled. Showing raw state:")
        homepage_raw = state.get(output_keys.HOMEPAGE_DATA, {})
        if isinstance(homepage_raw, dict):
            try:
                hd = HomepageData.model_validate(homepage_raw)
                print(f"\n  Conference : {hd.conference_name}")
                print(f"  Acronym    : {hd.conference_acronym or '?'}")
                print(f"  Dates      : {hd.date_start or '?'} -> {hd.date_end or '?'}")
                print(f"  Format     : {hd.conference_format or '?'}")
                print(f"  Organizer  : {hd.organizer or '?'}")
                print(f"  Industry   : {hd.industry or '?'}")
            except Exception as e:
                print(f"\n  HomepageData: {json.dumps(homepage_raw, indent=2, default=str)[:300]}")

        # Sub-pages data
        sp_data = state.get(output_keys.SUB_PAGES_DATA, {})
        if isinstance(sp_data, dict):
            speakers = sp_data.get("speakers", {})
            s_list = speakers.get("speakers", [])
            print(f"\n  Speakers: {len(s_list)} (confirmed: {speakers.get('speakers_confirmed')})")
            venue = sp_data.get("venue", {})
            print(f"  Venue   : {venue.get('venue_name') or '?'} ({venue.get('city') or '?'}, {venue.get('country') or '?'})")
            reg = sp_data.get("registration", {})
            print(f"  Reg     : covers accommodation: {reg.get('covers_accommodation')}")

        urls = state.get(output_keys.SUB_PAGES_URLS, {})
        md = state.get(output_keys.HOMEPAGE_MARKDOWN, "")
        sp_scraped = state.get(output_keys.SCRAPED_SUB_PAGES, "")
        print(f"\n  Homepage scraped: {len(str(md))} chars")
        print(f"  Sub-pages scraped: {len(str(sp_scraped))} chars")
        print(f"  Speakers URL     : {urls.get('speakers', 'not found')}")
        print(f"  Venue URL        : {urls.get('venue', 'not found')}")
        print(f"  Registration URL : {urls.get('registration', 'not found')}")

    print(f"\n{'='*60}\n")
    return state


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "https://2026.emnlp.org/"
    result = asyncio.run(run_pipeline(url))
    if result is None:
        sys.exit(1)
