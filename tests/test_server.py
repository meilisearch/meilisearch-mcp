import asyncio
import os
import sys
import tempfile
import time
import pytest
import subprocess
import json

import pytest_asyncio

MCP_SERVER_CMD = [sys.executable, "-m", "src.meilisearch_mcp"]

@pytest_asyncio.fixture(scope="session")
def mcp_server():
    # Start the MCP server as a subprocess
    env = os.environ.copy()
    env["MEILI_HTTP_ADDR"] = env.get("MEILI_HTTP_ADDR", "http://localhost:7700")
    proc = subprocess.Popen(
        MCP_SERVER_CMD,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        text=True,
        bufsize=1,
    )
    # Wait for server to be ready (simple sleep, or poll health-check)
    time.sleep(2)
    try:
        yield proc
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()

async def send_mcp_request(proc, method, params=None, id=1):
    # Send a JSON-RPC request to the MCP server via stdio
    req = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params or {},
        "id": id,
    }
    msg = json.dumps(req) + "\n"
    proc.stdin.write(msg)
    proc.stdin.flush()
    # Read response
    while True:
        line = proc.stdout.readline()
        if not line:
            continue
        try:
            resp = json.loads(line)
            if resp.get("id") == id:
                return resp
        except Exception:
            continue

@pytest.mark.asyncio
async def test_health_check(mcp_server):
    resp = await send_mcp_request(mcp_server, "call_tool", {"name": "health-check"}, id=1)
    assert "Meilisearch is available" in resp["result"][0]["text"]

@pytest.mark.asyncio
async def test_create_and_list_index(mcp_server):
    # Create index
    resp = await send_mcp_request(mcp_server, "call_tool", {"name": "create-index", "arguments": {"uid": "movies"}}, id=2)
    assert "Created index" in resp["result"][0]["text"]
    # List indexes
    resp = await send_mcp_request(mcp_server, "call_tool", {"name": "list-indexes"}, id=3)
    assert "movies" in resp["result"][0]["text"]

@pytest.mark.asyncio
async def test_add_and_get_documents(mcp_server):
    # Add documents
    docs = [{"id": 1, "title": "Inception"}, {"id": 2, "title": "Interstellar"}]
    resp = await send_mcp_request(mcp_server, "call_tool", {"name": "add-documents", "arguments": {"indexUid": "movies", "documents": docs}}, id=4)
    assert "Added documents" in resp["result"][0]["text"]
    # Get documents
    resp = await send_mcp_request(mcp_server, "call_tool", {"name": "get-documents", "arguments": {"indexUid": "movies"}}, id=5)
    assert "Inception" in resp["result"][0]["text"]
    assert "Interstellar" in resp["result"][0]["text"]

@pytest.mark.asyncio
async def test_search(mcp_server):
    # Search for a document
    resp = await send_mcp_request(mcp_server, "call_tool", {"name": "search", "arguments": {"query": "Inception", "indexUid": "movies"}}, id=6)
    assert "Inception" in resp["result"][0]["text"]

@pytest.mark.asyncio
async def test_get_version(mcp_server):
    resp = await send_mcp_request(mcp_server, "call_tool", {"name": "get-version"}, id=7)
    assert "Version info" in resp["result"][0]["text"]

@pytest.mark.asyncio
async def test_get_stats(mcp_server):
    resp = await send_mcp_request(mcp_server, "call_tool", {"name": "get-stats"}, id=8)
    assert "Database stats" in resp["result"][0]["text"]

@pytest.mark.asyncio
async def test_get_settings(mcp_server):
    resp = await send_mcp_request(mcp_server, "call_tool", {"name": "get-settings", "arguments": {"indexUid": "movies"}}, id=9)
    assert "Current settings" in resp["result"][0]["text"]

@pytest.mark.asyncio
async def test_update_settings(mcp_server):
    new_settings = {"searchableAttributes": ["title"]}
    resp = await send_mcp_request(mcp_server, "call_tool", {"name": "update-settings", "arguments": {"indexUid": "movies", "settings": new_settings}}, id=10)
    assert "Settings updated" in resp["result"][0]["text"]

@pytest.mark.asyncio
async def test_get_connection_settings(mcp_server):
    resp = await send_mcp_request(mcp_server, "call_tool", {"name": "get-connection-settings"}, id=11)
    assert "Current connection settings" in resp["result"][0]["text"]

@pytest.mark.asyncio
async def test_update_connection_settings(mcp_server):
    # Just update to the same URL for test
    resp = await send_mcp_request(mcp_server, "call_tool", {"name": "update-connection-settings", "arguments": {"url": "http://localhost:7700"}}, id=12)
    assert "Successfully updated connection settings" in resp["result"][0]["text"]
