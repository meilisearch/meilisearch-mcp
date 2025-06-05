import os
import time
import asyncio
from src.meilisearch_mcp.server import MeilisearchMCPServer, create_server


class TestMCPServerSynchronous:
    """Synchronous tests for MCP server functionality"""

    def test_server_creation(self):
        """Test that we can create a server instance"""
        meilisearch_url = "http://localhost:7700"
        api_key = os.getenv("MEILI_MASTER_KEY")
        server = create_server(url=meilisearch_url, api_key=api_key)
        assert server is not None
        assert server.meili_client is not None
        assert server.url == meilisearch_url

    def test_health_check_sync(self):
        """Test health check functionality synchronously"""
        meilisearch_url = "http://localhost:7700"
        api_key = os.getenv("MEILI_MASTER_KEY")
        server = create_server(url=meilisearch_url, api_key=api_key)

        # Use asyncio.run to run the async method synchronously
        async def run_health_check():
            result = await server._execute_tool_directly("health-check")
            return result

        result = asyncio.run(run_health_check())

        assert isinstance(result, list)
        assert len(result) > 0
        assert "available" in result[0].text or "unavailable" in result[0].text

        # Cleanup
        asyncio.run(server.cleanup())

    def test_get_version_sync(self):
        """Test get version functionality synchronously"""
        meilisearch_url = "http://localhost:7700"
        api_key = os.getenv("MEILI_MASTER_KEY")
        server = create_server(url=meilisearch_url, api_key=api_key)

        async def run_get_version():
            result = await server._execute_tool_directly("get-version")
            return result

        result = asyncio.run(run_get_version())

        assert isinstance(result, list)
        assert len(result) > 0
        assert "Version info" in result[0].text

        # Cleanup
        asyncio.run(server.cleanup())

    def test_get_stats_sync(self):
        """Test get stats functionality synchronously"""
        meilisearch_url = "http://localhost:7700"
        api_key = os.getenv("MEILI_MASTER_KEY")
        server = create_server(url=meilisearch_url, api_key=api_key)

        async def run_get_stats():
            result = await server._execute_tool_directly("get-stats")
            return result

        result = asyncio.run(run_get_stats())

        assert isinstance(result, list)
        assert len(result) > 0
        assert "Database stats" in result[0].text

        # Cleanup
        asyncio.run(server.cleanup())

    def test_list_indexes_sync(self):
        """Test list indexes functionality synchronously"""
        meilisearch_url = "http://localhost:7700"
        api_key = os.getenv("MEILI_MASTER_KEY")
        server = create_server(url=meilisearch_url, api_key=api_key)

        async def run_list_indexes():
            result = await server._execute_tool_directly("list-indexes")
            return result

        result = asyncio.run(run_list_indexes())

        assert isinstance(result, list)
        assert len(result) > 0
        assert "Indexes" in result[0].text

        # Cleanup
        asyncio.run(server.cleanup())

    def test_create_index_sync(self):
        """Test create index functionality synchronously"""
        meilisearch_url = "http://localhost:7700"
        api_key = os.getenv("MEILI_MASTER_KEY")
        server = create_server(url=meilisearch_url, api_key=api_key)

        index_name = f"test_sync_{int(time.time())}"

        async def run_create_index():
            result = await server._execute_tool_directly(
                "create-index", {"uid": index_name}
            )
            return result

        result = asyncio.run(run_create_index())

        assert isinstance(result, list)
        assert len(result) > 0
        assert "Created index" in result[0].text

        # Cleanup
        asyncio.run(server.cleanup())

    def test_connection_settings_sync(self):
        """Test connection settings functionality synchronously"""
        meilisearch_url = "http://localhost:7700"
        api_key = os.getenv("MEILI_MASTER_KEY")
        server = create_server(url=meilisearch_url, api_key=api_key)

        async def run_connection_settings():
            result = await server._execute_tool_directly("get-connection-settings")
            return result

        result = asyncio.run(run_connection_settings())

        assert isinstance(result, list)
        assert len(result) > 0
        assert "Current connection settings" in result[0].text
        assert "localhost:7700" in result[0].text

        # Cleanup
        asyncio.run(server.cleanup())

    def test_search_sync(self):
        """Test search functionality synchronously"""
        meilisearch_url = "http://localhost:7700"
        api_key = os.getenv("MEILI_MASTER_KEY")
        server = create_server(url=meilisearch_url, api_key=api_key)

        async def run_search():
            result = await server._execute_tool_directly(
                "search", {"query": "test", "limit": 5}
            )
            return result

        result = asyncio.run(run_search())

        assert isinstance(result, list)
        assert len(result) > 0
        assert "Search results" in result[0].text

        # Cleanup
        asyncio.run(server.cleanup())

    def test_get_tasks_sync(self):
        """Test get tasks functionality synchronously"""
        meilisearch_url = "http://localhost:7700"
        api_key = os.getenv("MEILI_MASTER_KEY")
        server = create_server(url=meilisearch_url, api_key=api_key)

        async def run_get_tasks():
            result = await server._execute_tool_directly("get-tasks", {"limit": 10})
            return result

        result = asyncio.run(run_get_tasks())

        assert isinstance(result, list)
        assert len(result) > 0
        assert "Tasks" in result[0].text

        # Cleanup
        asyncio.run(server.cleanup())

    def test_error_handling_sync(self):
        """Test error handling functionality synchronously"""
        meilisearch_url = "http://localhost:7700"
        api_key = os.getenv("MEILI_MASTER_KEY")
        server = create_server(url=meilisearch_url, api_key=api_key)

        async def run_error_test():
            result = await server._execute_tool_directly("non-existent-tool")
            return result

        result = asyncio.run(run_error_test())

        assert isinstance(result, list)
        assert len(result) > 0
        assert "Error" in result[0].text

        # Cleanup
        asyncio.run(server.cleanup())


# Add the helper method to the server class if it doesn't exist
async def _execute_tool_directly_sync(self, name: str, arguments: dict = None):
    """Direct tool execution for sync testing purposes"""
    try:
        args = arguments or {}

        if name == "get-connection-settings":
            from mcp.types import TextContent

            return [
                TextContent(
                    type="text",
                    text=f"Current connection settings:\nURL: {self.url}\nAPI Key: {'*' * 8 if self.api_key else 'Not set'}",
                )
            ]

        elif name == "health-check":
            from mcp.types import TextContent

            is_healthy = await self.meili_client.health_check()
            return [
                TextContent(
                    type="text",
                    text=f"Meilisearch is {is_healthy and 'available' or 'unavailable'}",
                )
            ]

        elif name == "get-version":
            from mcp.types import TextContent

            version = await self.meili_client.get_version()
            return [TextContent(type="text", text=f"Version info: {version}")]

        elif name == "get-stats":
            from mcp.types import TextContent

            stats = await self.meili_client.get_stats()
            return [TextContent(type="text", text=f"Database stats: {stats}")]

        elif name == "create-index":
            from mcp.types import TextContent

            result = await self.meili_client.indexes.create_index(
                args["uid"], args.get("primaryKey")
            )
            return [TextContent(type="text", text=f"Created index: {result}")]

        elif name == "list-indexes":
            from mcp.types import TextContent
            import json

            indexes = await self.meili_client.get_indexes()
            formatted_json = json.dumps(indexes, indent=2, default=str)
            return [TextContent(type="text", text=f"Indexes:\n{formatted_json}")]

        elif name == "search":
            from mcp.types import TextContent
            import json

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
                TextContent(
                    type="text",
                    text=f"Search results for '{args['query']}':\n{formatted_results}",
                )
            ]

        elif name == "get-tasks":
            from mcp.types import TextContent

            valid_params = {
                "limit",
                "from",
                "reverse",
                "batchUids",
                "uids",
                "canceledBy",
                "types",
                "statuses",
                "indexUids",
                "afterEnqueuedAt",
                "beforeEnqueuedAt",
                "afterStartedAt",
                "beforeStartedAt",
                "afterFinishedAt",
                "beforeFinishedAt",
            }
            filtered_args = {k: v for k, v in args.items() if k in valid_params}
            tasks = await self.meili_client.tasks.get_tasks(filtered_args)
            return [TextContent(type="text", text=f"Tasks: {tasks}")]

        else:
            from mcp.types import TextContent

            raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        from mcp.types import TextContent

        return [TextContent(type="text", text=f"Error: {str(e)}")]


# Monkey patch the method onto the server class if it doesn't exist
if not hasattr(MeilisearchMCPServer, "_execute_tool_directly"):
    MeilisearchMCPServer._execute_tool_directly = _execute_tool_directly_sync
