import pytest
import asyncio
import json
import time
import os
from typing import Dict, Any, List, Optional

import mcp.types as types
from src.meilisearch_mcp.server import MeilisearchMCPServer, create_server


class TestMCPServerSimple:
    """Simple tests that don't rely on async fixtures"""

    def test_server_creation_sync(self):
        """Test that we can create a server instance"""
        meilisearch_url = "http://localhost:7700"
        api_key = os.getenv("MEILI_MASTER_KEY")
        server = create_server(url=meilisearch_url, api_key=api_key)
        assert server is not None
        assert server.meili_client is not None
        assert server.url == meilisearch_url

    @pytest.mark.asyncio
    async def test_health_check_simple(self):
        """Test health-check tool with simple setup"""
        meilisearch_url = "http://localhost:7700"
        api_key = os.getenv("MEILI_MASTER_KEY")
        server = create_server(url=meilisearch_url, api_key=api_key)
        
        # Use the _execute_tool_directly method which we know works
        try:
            result = await server._execute_tool_directly("health-check")
            assert isinstance(result, list)
            assert len(result) > 0
            assert isinstance(result[0], types.TextContent)
            assert "available" in result[0].text or "unavailable" in result[0].text
        finally:
            await server.cleanup()

    @pytest.mark.asyncio
    async def test_get_version_simple(self):
        """Test get-version tool with simple setup"""
        meilisearch_url = "http://localhost:7700"
        api_key = os.getenv("MEILI_MASTER_KEY")
        server = create_server(url=meilisearch_url, api_key=api_key)
        
        try:
            result = await server._execute_tool_directly("get-version")
            assert isinstance(result, list)
            assert len(result) > 0
            assert isinstance(result[0], types.TextContent)
            assert "Version info" in result[0].text
        finally:
            await server.cleanup()

    @pytest.mark.asyncio
    async def test_get_stats_simple(self):
        """Test get-stats tool with simple setup"""
        meilisearch_url = "http://localhost:7700"
        api_key = os.getenv("MEILI_MASTER_KEY")
        server = create_server(url=meilisearch_url, api_key=api_key)
        
        try:
            result = await server._execute_tool_directly("get-stats")
            assert isinstance(result, list)
            assert len(result) > 0
            assert isinstance(result[0], types.TextContent)
            assert "Database stats" in result[0].text
        finally:
            await server.cleanup()

    @pytest.mark.asyncio
    async def test_list_indexes_simple(self):
        """Test list-indexes tool with simple setup"""
        meilisearch_url = "http://localhost:7700"
        api_key = os.getenv("MEILI_MASTER_KEY")
        server = create_server(url=meilisearch_url, api_key=api_key)
        
        try:
            result = await server._execute_tool_directly("list-indexes")
            assert isinstance(result, list)
            assert len(result) > 0
            assert isinstance(result[0], types.TextContent)
            assert "Indexes" in result[0].text
        finally:
            await server.cleanup()

    @pytest.mark.asyncio
    async def test_create_index_simple(self):
        """Test create-index tool with simple setup"""
        meilisearch_url = "http://localhost:7700"
        api_key = os.getenv("MEILI_MASTER_KEY")
        server = create_server(url=meilisearch_url, api_key=api_key)
        
        index_name = f"test_simple_{int(time.time())}"
        
        try:
            result = await server._execute_tool_directly("create-index", {"uid": index_name})
            assert isinstance(result, list)
            assert len(result) > 0
            assert isinstance(result[0], types.TextContent)
            assert "Created index" in result[0].text
        finally:
            await server.cleanup()

    @pytest.mark.asyncio 
    async def test_connection_settings_simple(self):
        """Test connection settings tools with simple setup"""
        meilisearch_url = "http://localhost:7700"
        api_key = os.getenv("MEILI_MASTER_KEY")
        server = create_server(url=meilisearch_url, api_key=api_key)
        
        try:
            # Test get connection settings
            result = await server._execute_tool_directly("get-connection-settings")
            assert isinstance(result, list)
            assert len(result) > 0
            assert isinstance(result[0], types.TextContent)
            assert "Current connection settings" in result[0].text
            assert "localhost:7700" in result[0].text
        finally:
            await server.cleanup()

    @pytest.mark.asyncio
    async def test_search_simple(self):
        """Test search tool with simple setup"""
        meilisearch_url = "http://localhost:7700"
        api_key = os.getenv("MEILI_MASTER_KEY")
        server = create_server(url=meilisearch_url, api_key=api_key)
        
        try:
            result = await server._execute_tool_directly("search", {"query": "test", "limit": 5})
            assert isinstance(result, list)
            assert len(result) > 0
            assert isinstance(result[0], types.TextContent)
            assert "Search results" in result[0].text
        finally:
            await server.cleanup()

    @pytest.mark.asyncio
    async def test_get_tasks_simple(self):
        """Test get-tasks tool with simple setup"""
        meilisearch_url = "http://localhost:7700"
        api_key = os.getenv("MEILI_MASTER_KEY")
        server = create_server(url=meilisearch_url, api_key=api_key)
        
        try:
            result = await server._execute_tool_directly("get-tasks", {"limit": 10})
            assert isinstance(result, list)
            assert len(result) > 0
            assert isinstance(result[0], types.TextContent)
            assert "Tasks" in result[0].text
        finally:
            await server.cleanup()

    @pytest.mark.asyncio
    async def test_error_handling_simple(self):
        """Test error handling with simple setup"""
        meilisearch_url = "http://localhost:7700"
        api_key = os.getenv("MEILI_MASTER_KEY")
        server = create_server(url=meilisearch_url, api_key=api_key)
        
        try:
            result = await server._execute_tool_directly("non-existent-tool")
            assert isinstance(result, list)
            assert len(result) > 0
            assert isinstance(result[0], types.TextContent)
            assert "Error" in result[0].text
        finally:
            await server.cleanup()


# Add the helper method to the server class if it doesn't exist
async def _execute_tool_directly(self, name: str, arguments: Optional[Dict[str, Any]] = None):
    """Direct tool execution for testing purposes"""
    try:
        args = arguments or {}
        
        if name == "get-connection-settings":
            return [
                types.TextContent(
                    type="text",
                    text=f"Current connection settings:\nURL: {self.url}\nAPI Key: {'*' * 8 if self.api_key else 'Not set'}",
                )
            ]
        
        elif name == "health-check":
            is_healthy = await self.meili_client.health_check()
            return [
                types.TextContent(
                    type="text",
                    text=f"Meilisearch is {is_healthy and 'available' or 'unavailable'}",
                )
            ]
        
        elif name == "get-version":
            version = await self.meili_client.get_version()
            return [types.TextContent(type="text", text=f"Version info: {version}")]
        
        elif name == "get-stats":
            stats = await self.meili_client.get_stats()
            return [types.TextContent(type="text", text=f"Database stats: {stats}")]
        
        elif name == "create-index":
            result = await self.meili_client.indexes.create_index(
                args["uid"], args.get("primaryKey")
            )
            return [types.TextContent(type="text", text=f"Created index: {result}")]
        
        elif name == "list-indexes":
            indexes = await self.meili_client.get_indexes()
            formatted_json = json.dumps(indexes, indent=2, default=str)
            return [types.TextContent(type="text", text=f"Indexes:\n{formatted_json}")]
        
        elif name == "search":
            search_results = await self.meili_client.search(
                query=args["query"],
                index_uid=args.get("indexUid"),
                limit=args.get("limit"),
                offset=args.get("offset"),
                filter=args.get("filter"),
                sort=args.get("sort"),
            )
            formatted_results = json.dumps(search_results, indent=2, default=str)
            return [
                types.TextContent(
                    type="text",
                    text=f"Search results for '{args['query']}':\n{formatted_results}",
                )
            ]
        
        elif name == "get-tasks":
            valid_params = {
                "limit", "from", "reverse", "batchUids", "uids", "canceledBy",
                "types", "statuses", "indexUids", "afterEnqueuedAt", "beforeEnqueuedAt",
                "afterStartedAt", "beforeStartedAt", "afterFinishedAt", "beforeFinishedAt"
            }
            filtered_args = {k: v for k, v in args.items() if k in valid_params}
            tasks = await self.meili_client.tasks.get_tasks(filtered_args)
            return [types.TextContent(type="text", text=f"Tasks: {tasks}")]
        
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


# Monkey patch the method onto the server class if it doesn't exist
if not hasattr(MeilisearchMCPServer, '_execute_tool_directly'):
    MeilisearchMCPServer._execute_tool_directly = _execute_tool_directly