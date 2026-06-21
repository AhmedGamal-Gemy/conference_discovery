import asyncio
import logging

from google.adk.tools.mcp_tool import McpToolset, StreamableHTTPConnectionParams
from mcp.types import CallToolResult
from conference_agent.config import settings

logger = logging.getLogger(__name__)

scrapling_toolset = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url=settings.scrapling_mcp_url,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        },
        timeout=30.0,
        sse_read_timeout=300.0,
    ),
)




logger.info(
    "TOOL  Scrapling MCP toolset created — url=%s, timeout=%s, sse_read_timeout=%s",
    settings.scrapling_mcp_url,
    scrapling_toolset._connection_params.timeout,
    getattr(scrapling_toolset._connection_params, "sse_read_timeout", "N/A"),
)


async def test() -> None:
    """Test the scrapling MCP connection by fetching a single URL."""
    logger.info("TOOL  MCP test starting — connecting to %s", settings.scrapling_mcp_url)
    try:
        tools = await scrapling_toolset.get_tools()
        logger.info("TOOL  MCP tools loaded — %d available: %s", len(tools), [t.name for t in tools])
    except Exception as exc:
        logger.error("TOOL  MCP get_tools() failed: %s", exc)
        return

    sf = next((t for t in tools if t.name == "stealthy_fetch"), None)
    if sf is None:
        logger.error("TOOL  stealthy_fetch tool not found in MCP toolset")
        return

    session = await scrapling_toolset._mcp_session_manager.create_session()
    logger.info("TOOL  MCP session created")

    test_url = "https://after.org.in/event/index.php?id=100947439"
    logger.info("TOOL  Fetching test URL: %s", test_url)
    try:
        result: CallToolResult = await session.call_tool("stealthy_fetch", arguments={
            "url": test_url,
            "timeout": 60000,
            "solve_cloudflare": True,
            "headless": True,
            "main_content_only": True,
        })

        import json, os

        raw = json.loads(result.content[0].text)
        markdown = "".join(raw.get("content", []))
        logger.info("TOOL  Fetch succeeded — %d chars received", len(markdown))

        output_path = os.path.join("output", "scrapling_test_result.md")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown)
        logger.info("TOOL  Saved to %s", output_path)
    except Exception as exc:
        logger.error("TOOL  Fetch failed: %s", exc)
    finally:
        await scrapling_toolset._mcp_session_manager.close()
        logger.info("TOOL  MCP session closed")


if __name__ == "__main__":
    asyncio.run(test())