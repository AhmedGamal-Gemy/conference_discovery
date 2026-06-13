
from google.adk.tools.mcp_tool import McpToolset, StreamableHTTPConnectionParams
from mcp.types import CallToolResult
import asyncio
from conference_agent.config import settings

scrapling_toolset = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url=settings.scrapling_mcp_url,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        },
        timeout=30.0,
        sse_read_timeout=600.0,
    ),
)



async def test():

    tools = await scrapling_toolset.get_tools()

    sf = next(t for t in tools if t.name == "stealthy_fetch")

    # print("Params:", sf.raw_mcp_tool.inputSchema)  # public property, no type error
    
    # Session via the session manager — runtime works, Pylance complains about _mcp_session_manager
    session = await scrapling_toolset._mcp_session_manager.create_session()

    result : CallToolResult = await session.call_tool("stealthy_fetch", arguments={
        "url": "https://after.org.in/event/index.php?id=100947439",
        "timeout": 60000,          # increase to 60s
        "solve_cloudflare": True,  # bypass Cloudflare
        "headless": True,
        "main_content_only": True,
    })

    import json, os

    # result.content[0].text is a JSON string with a nested "content" array
    raw = json.loads(result.content[0].text)
    markdown = "".join(raw.get("content", []))
    
    output_path = os.path.join("output", "scrapling_test_result.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(markdown)

    print(f"[OK] Saved to {output_path} ({len(markdown)} chars)")

if __name__ == "__main__":
    asyncio.run(test())