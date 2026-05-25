import asyncio
import json
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part
from conference_agent.steps.step2_extract_homepage import extract_homepage_agent
from conference_agent.schemas.output_keys import output_keys
from conference_agent.schemas.homepage import HomepageData
from conference_agent.tools.intermediate_output import save_intermediate

async def test_extract_homepage():
    """Test step2_extract_homepage agent using Runner.
    
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

    # 2. Inject homepage markdown into state (simulates output from step1)
    # Using a known conference URL that step1 successfully scraped
    test_url = "https://after.org.in/event/index.php?id=100947439"
    
    # First, fetch the markdown using scrapling tool
    print(f"Fetching markdown from: {test_url}")
    from conference_agent.tools.scrapling_tool import scrapling_toolset
    from mcp.types import CallToolResult
    import json
    
    tools = await scrapling_toolset.get_tools()
    sf = next(t for t in tools if t.name == "stealthy_fetch")
    mcp_session = await scrapling_toolset._mcp_session_manager.create_session()
    
    result: CallToolResult = await mcp_session.call_tool("stealthy_fetch", arguments={
        "url": test_url,
        "timeout": 60000,
        "solve_cloudflare": True,
        "headless": True,
        "main_content_only": True,
    })
    
    raw = json.loads(result.content[0].text)
    markdown = "".join(raw.get("content", []))
    
    print(f"Fetched markdown: {len(markdown)} chars")
    
    # Store in session state
    session.state[output_keys.HOMEPAGE_MARKDOWN] = markdown
    session.state[output_keys.URL] = test_url
    
    print(f"Stored in state: {output_keys.HOMEPAGE_MARKDOWN} = {len(markdown)} chars")

    # 3. Create runner with step2 agent as root
    runner = Runner(
        agent=extract_homepage_agent,
        app_name="conference_discovery",
        session_service=session_service
    )

    # 4. Run it
    print(f"\nRunning extract_homepage agent...")
    final_text = ""
    
    async for event in runner.run_async(
        user_id="test_user",
        session_id="test_session",
        new_message=Content(role="user", parts=[Part(text="Extract structured data from homepage markdown")])
    ):
        # Print LLM responses as they happen
        if event.content and event.content.parts:
            part = event.content.parts[0]
            if part.text:
                print(f"\n>>> {event.author}: {part.text[:500]}")
            elif part.function_call:
                print(f"\n>>> {event.author}: [TOOL CALL] {part.function_call.name}")
        
        # Capture final response
        if event.is_final_response() and event.content and event.content.parts:
            final_text = event.content.parts[0].text or ""
            print("\n=== FINAL RESPONSE ===")

    # 5. Inspect state
    print("\n=== SESSION STATE ===")
    for key, value in session.state.items():
        if key == output_keys.HOMEPAGE_MARKDOWN:
            print(f"  {key}: {len(str(value))} chars (markdown)")
        else:
            preview = str(value)[:300] + "..." if len(str(value)) > 300 else str(value)
            print(f"  {key}: {preview}")

    # 6. Validate extracted data
    print("\n=== EXTRACTION RESULT ===")
    if final_text:
        try:
            # Parse JSON from final response
            parsed = json.loads(final_text)
            print(f"[OK] Parsed JSON ({len(final_text)} chars)")
            
            # Validate against HomepageData schema
            homepage_data = HomepageData.model_validate(parsed)
            print(f"\n[OK] Validated against HomepageData schema")
            print(f"  conference_name: {homepage_data.conference_name}")
            print(f"  date_start: {homepage_data.date_start}")
            print(f"  date_end: {homepage_data.date_end}")
            print(f"  industry: {homepage_data.industry}")
            print(f"  sub_pages.speakers: {homepage_data.sub_pages.speakers}")
            print(f"  sub_pages.venue: {homepage_data.sub_pages.venue}")
            print(f"  sub_pages.registration: {homepage_data.sub_pages.registration}")
            
            # Also store manually in state for downstream steps
            session.state[output_keys.HOMEPAGE_DATA] = homepage_data
            print(f"\n[OK] Stored in session.state['{output_keys.HOMEPAGE_DATA}']")
            
        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to parse JSON: {e}")
            print(f"Raw text: {final_text[:500]}")
        except Exception as e:
            print(f"[ERROR] Validation failed: {e}")
            print(f"Raw text: {final_text[:500]}")
    else:
        print("[WARN] No final response text captured.")
        print("Note: output_key only auto-stores when agent runs as a sub-agent in a parent workflow.")

    # 7. Save intermediate output to disk
    print("\n=== SAVING INTERMEDIATE OUTPUT ===")
    saved = []
    if output_keys.HOMEPAGE_MARKDOWN in session.state:
        path = save_intermediate("step2_input_markdown", session.state[output_keys.HOMEPAGE_MARKDOWN])
        saved.append(str(path))
    if output_keys.HOMEPAGE_DATA in session.state:
        path = save_intermediate("step2_homepage_data", session.state[output_keys.HOMEPAGE_DATA])
        saved.append(str(path))
    if final_text:
        path = save_intermediate("step2_final_response", final_text)
        saved.append(str(path))
    print(f"[OK] Saved {len(saved)} files to output/intermediate/")
    for s in saved:
        print(f"  - {s}")

if __name__ == "__main__":
    asyncio.run(test_extract_homepage())
