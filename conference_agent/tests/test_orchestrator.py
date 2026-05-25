import asyncio
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part
from conference_agent.orchestrator import sequential_orchestrator
from conference_agent.schemas.output_keys import output_keys
from conference_agent.schemas.homepage import HomepageData

async def test_sequential_orchestrator():
    """Test the sequential orchestrator that chains step1 → step2.
    
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
    test_url = "https://after.org.in/event/index.php?id=100947439"
    session.state[output_keys.URL] = test_url
    print(f"Session initialized with URL: {test_url}")

    # 3. Create runner with sequential orchestrator as root
    runner = Runner(
        agent=sequential_orchestrator,
        app_name="conference_discovery",
        session_service=session_service
    )

    # 4. Run it
    print(f"\nRunning sequential orchestrator...")
    print("Expected flow: step1_scrape -> step2_extract\n")
    
    async for event in runner.run_async(
        user_id="test_user",
        session_id="test_session",
        new_message=Content(role="user", parts=[Part(text="Process this conference")])
    ):
        # Print events as they happen
        if event.content and event.content.parts:
            part = event.content.parts[0]
            if part.text:
                print(f">>> {event.author}: {part.text[:300]}")
            elif part.function_call:
                print(f">>> {event.author}: [TOOL CALL] {part.function_call.name}")
        
        if event.is_final_response():
            print(f"\n=== FINAL RESPONSE from {event.author} ===")

    # 5. Get UPDATED session from service (ADK pattern: state lives in session_service)
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
            print(f"  {key}: {type(value).__name__}")
            if isinstance(value, HomepageData):
                print(f"    conference_name: {value.conference_name}")
                print(f"    date_start: {value.date_start}")
                print(f"    date_end: {value.date_end}")
                print(f"    industry: {value.industry}")
                print(f"    sub_pages.speakers: {value.sub_pages.speakers}")
                print(f"    sub_pages.venue: {value.sub_pages.venue}")
                print(f"    sub_pages.registration: {value.sub_pages.registration}")
            else:
                preview = str(value)[:200]
                print(f"    value: {preview}")
        else:
            preview = str(value)[:100]
            print(f"  {key}: {preview}")

    # 7. Validation
    print("\n=== VALIDATION ===")
    errors = []
    
    if output_keys.HOMEPAGE_MARKDOWN not in updated_session.state:
        errors.append(f"Missing {output_keys.HOMEPAGE_MARKDOWN} in state")
    else:
        md_len = len(updated_session.state[output_keys.HOMEPAGE_MARKDOWN])
        print(f"[OK] {output_keys.HOMEPAGE_MARKDOWN}: {md_len} chars")
    
    if output_keys.HOMEPAGE_DATA not in updated_session.state:
        errors.append(f"Missing {output_keys.HOMEPAGE_DATA} in state")
    else:
        raw_data = updated_session.state[output_keys.HOMEPAGE_DATA]
        # ADK output_schema stores as dict in state, convert to HomepageData
        try:
            if isinstance(raw_data, dict):
                data = HomepageData.model_validate(raw_data)
                print(f"[OK] {output_keys.HOMEPAGE_DATA}: dict -> HomepageData")
                print(f"[OK] conference_name: {data.conference_name}")
                print(f"[OK] date_start: {data.date_start}")
                print(f"[OK] date_end: {data.date_end}")
                print(f"[OK] industry: {data.industry}")
                print(f"[OK] sub_pages: speakers={data.sub_pages.speakers}, venue={data.sub_pages.venue}, registration={data.sub_pages.registration}")
            elif isinstance(raw_data, HomepageData):
                print(f"[OK] {output_keys.HOMEPAGE_DATA}: HomepageData object")
                print(f"[OK] conference_name: {raw_data.conference_name}")
            else:
                errors.append(f"Expected dict or HomepageData, got {type(raw_data).__name__}")
        except Exception as e:
            errors.append(f"Failed to validate HomepageData: {e}")
    
    if errors:
        print("\n[FAIL] Errors:")
        for e in errors:
            print(f"  - {e}")
    else:
        print("\n[PASS] All validations passed!")
        print("\nPipeline flow verified:")
        print("  1. scrape_homepage_agent -> fetched markdown")
        print("  2. extract_homepage_agent -> extracted HomepageData")
        print("  3. output_key propagation working between steps")

if __name__ == "__main__":
    asyncio.run(test_sequential_orchestrator())
