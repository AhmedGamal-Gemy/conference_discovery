import asyncio
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part
from conference_agent.steps.step1_scrape_homepage import scrape_homepage_agent
from conference_agent.schemas.output_keys import output_keys

async def test_scrape_homepage():
    """Test step1_scrape_homepage agent using Runner.
    
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

    # 2. Inject the URL into state (feeds the {url} template in STEP1_SCRAPE_HOMEPAGE_PROMPT)
    test_url = "https://after.org.in/event/index.php?id=100947439"
    session.state["url"] = test_url

    # 3. Create runner with step1 agent as root
    runner = Runner(
        agent=scrape_homepage_agent,
        app_name="conference_discovery",
        session_service=session_service
    )

    # 4. Run it
    print(f"Running scrape_homepage agent for URL: {test_url}")

    final_text = ""
    
    async for event in runner.run_async(
        user_id="test_user",
        session_id="test_session",
        new_message=Content(role="user", parts=[Part(text="Scrape the conference homepage")])
    ):
        # Print LLM responses / tool calls as they happen
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
        preview = str(value)[:300] + "..." if len(str(value)) > 300 else str(value)
        print(f"  {key}: {preview}")

    # 6. Check output_key result
    print("\n=== OUTPUT_KEY CHECK ===")
    if output_keys.HOMEPAGE_MARKDOWN in session.state:
        md = session.state[output_keys.HOMEPAGE_MARKDOWN]
        print(f"[OK] output_keys.HOMEPAGE_MARKDOWN found in state ({len(str(md))} chars)")
        print(f"Preview: {str(md)[:300]}...")
    else:
        print(f"[WARN] output_keys.HOMEPAGE_MARKDOWN NOT found in session.state")
        print(f"output_key may only work when agent is a sub-agent, not root.")
        if final_text:
            print(f"\nFinal response text ({len(final_text)} chars):")
            print(final_text[:1000])
        else:
            print("No final response text captured.")

if __name__ == "__main__":
    asyncio.run(test_scrape_homepage())
