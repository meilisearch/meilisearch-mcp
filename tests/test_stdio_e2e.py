"""
End-to-end MCP test over the real stdio transport.

Spawns the server as a subprocess (exactly how Claude Desktop runs it) and
drives it with a real MCP client. Requires a running Meilisearch instance.
"""

import os
import sys
import time

from mcp import Client
from mcp.client.stdio import StdioServerParameters, stdio_client


def _server_params() -> StdioServerParameters:
    return StdioServerParameters(
        command=sys.executable,
        args=["-m", "src.meilisearch_mcp"],
        env={
            **os.environ,
            "MEILI_HTTP_ADDR": os.getenv("MEILI_HTTP_ADDR", "http://localhost:7700"),
        },
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    )


async def test_stdio_round_trip():
    """Full CRUD round-trip over stdio: list tools, create, add, search, delete"""
    test_index = f"test_stdio_e2e_{int(time.time() * 1000)}"

    async with Client(stdio_client(_server_params())) as client:
        tools = await client.list_tools()
        assert len(tools.tools) == 26

        result = await client.call_tool("health-check", {})
        assert not result.is_error
        assert "available" in result.content[0].text

        result = await client.call_tool(
            "create-index", {"uid": test_index, "primaryKey": "id"}
        )
        assert not result.is_error
        assert "Created index" in result.content[0].text

        result = await client.call_tool(
            "add-documents",
            {
                "indexUid": test_index,
                "documents": [{"id": 1, "title": "Stdio E2E Doc"}],
            },
        )
        assert not result.is_error

        # Wait for indexing, then search
        import asyncio

        await asyncio.sleep(0.5)
        result = await client.call_tool(
            "search", {"query": "stdio", "indexUid": test_index}
        )
        assert not result.is_error
        assert "Stdio E2E Doc" in result.content[0].text
        assert result.structured_content is not None
        assert result.structured_content["hits"][0]["title"] == "Stdio E2E Doc"

        result = await client.call_tool("delete-index", {"uid": test_index})
        assert not result.is_error
        assert "Successfully deleted index" in result.content[0].text
