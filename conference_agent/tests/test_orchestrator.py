import asyncio
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part
from conference_agent.orchestrator import pipeline_orchestrator
from conference_agent.schemas.output_keys import output_keys
from conference_agent.schemas.homepage import HomepageData
from conference_agent.tools.intermediate_output import save_session_state


async def test_full_pipeline():
    """Test the full Workflow pipeline: scrape → extract → discover → probe → merge → scrape sub-pages.

    Prerequisites:
    - MCP server running at http://localhost:8016/mcp
    - MISTRAL_API_KEY set in environment
    - Valid config/settings.yaml
    """

    # 1. Create session service + session
    session_service = InMemorySessionService()
    session = await session_service.create_session(
        app_name="conference_discovery",
        user_id="test_user",
        session_id="test_session"
    )

    # 2. Inject URL into state
    test_url = "https://2026.emnlp.org/"
    session.state[output_keys.URL] = test_url
    print(f"Session initialized with URL: {test_url}")

    # 3. Create runner with pipeline orchestrator as root
    runner = Runner(
        agent=pipeline_orchestrator,
        app_name="conference_discovery",
        session_service=session_service
    )

    # 4. Run it
    print(f"\nRunning pipeline orchestrator (Workflow)...")
    print("Expected flow: scrape -> extract -> discover -> probe -> merge -> scrape_sub_pages\n")

    async for event in runner.run_async(
        user_id="test_user",
        session_id="test_session",
        new_message=Content(role="user", parts=[Part(text="Process this conference")])
    ):
        # Print events as they happen
        if event.content and event.content.parts:
            part = event.content.parts[0]
            if part.text:
                preview = part.text[:200].replace("\n", " ")
                print(f"[{event.author}]: {preview}")
            elif part.function_call:
                print(f"[{event.author}]: [TOOL CALL] {part.function_call.name}")

        if event.is_final_response():
            print(f"\n=== FINAL RESPONSE from {event.author} ===")

    # 5. Get updated session
    updated_session = await session_service.get_session(
        app_name="conference_discovery",
        user_id="test_user",
        session_id="test_session"
    )

    # 6. Inspect state
    print("\n=== SESSION STATE ===")
    for key, value in updated_session.state.items():
        if key == output_keys.HOMEPAGE_MARKDOWN:
            print(f"  {key}: {len(str(value))} chars (markdown)")
        elif key == output_keys.HOMEPAGE_DATA:
            print(f"  {key}:", end="")
            if isinstance(value, dict):
                print(f" {value.get('conference_name', '?')}")
                print(f"    date_start: {value.get('date_start')}")
                print(f"    date_end: {value.get('date_end')}")
                print(f"    industry: {value.get('industry')}")
                sp = value.get('sub_pages', {})
                print(f"    sub_pages: speakers={sp.get('speakers')}, venue={sp.get('venue')}, registration={sp.get('registration')}")
            elif isinstance(value, HomepageData):
                print(f" {value.conference_name}")
            else:
                print(f" {type(value).__name__}")
        elif key == output_keys.DISCOVERED_LINKS:
            print(f"  {key}: {type(value).__name__}")
        elif key == output_keys.PROBED_LINKS:
            print(f"  {key}: {type(value).__name__}")
        elif key == output_keys.SUB_PAGES_URLS:
            print(f"  {key}: {value}")
        elif key == output_keys.SCRAPED_SUB_PAGES:
            text = str(value)
            print(f"  {key}: {len(text)} chars")
        elif key == output_keys.URL:
            print(f"  {key}: {value}")
        else:
            preview = str(value)[:100]
            print(f"  {key}: {preview}")

    # 7. Validation
    print("\n=== VALIDATION ===")
    errors = []
    expected_keys = [
        output_keys.HOMEPAGE_MARKDOWN,
        output_keys.HOMEPAGE_DATA,
        output_keys.DISCOVERED_LINKS,
        output_keys.SUB_PAGES_URLS,
        output_keys.SCRAPED_SUB_PAGES,
    ]

    for ek in expected_keys:
        if ek not in updated_session.state:
            errors.append(f"Missing {ek} in state")
        else:
            val = updated_session.state[ek]
            size = len(str(val))
            print(f"[OK] {ek}: present ({size} chars)" if size > 100 else f"[OK] {ek}: present")

    if output_keys.HOMEPAGE_DATA in updated_session.state:
        raw_data = updated_session.state[output_keys.HOMEPAGE_DATA]
        try:
            data = HomepageData.model_validate(raw_data) if isinstance(raw_data, dict) else raw_data
            print(f"[OK] conference_name: {data.conference_name}")
        except Exception as e:
            errors.append(f"Failed to validate HomepageData: {e}")

    if errors:
        print("\n[FAIL] Errors:")
        for e in errors:
            print(f"  - {e}")
    else:
        print("\n[PASS] All validations passed!")
        print("\nPipeline flow verified:")
        print("  1. scrape_homepage_agent -> HOMEPAGE_MARKDOWN")
        print("  2. extract_homepage_agent -> HOMEPAGE_DATA")
        print("  3. discover_links_agent -> DISCOVERED_LINKS")
        print("  4. probe_paths_agent -> PROBED_LINKS")
        print("  5. merge_links_agent -> SUB_PAGES_URLS")
        print("  6. scrape_sub_pages_agent -> SCRAPED_SUB_PAGES")

    # 8. Save all intermediate outputs to disk
    print("\n=== SAVING INTERMEDIATE OUTPUTS ===")
    saved = save_session_state(updated_session.state, prefix="orchestrator_")
    print(f"[OK] Saved {len(saved)} files to output/intermediate/")
    for s in saved:
        print(f"  - {s.name}")


if __name__ == "__main__":
    asyncio.run(test_full_pipeline())
