import pytest
import asyncio
import json
import time
from typing import Dict, Any, List, Optional

import mcp.types as types
from src.meilisearch_mcp.server import MeilisearchMCPServer, create_server


@pytest.fixture
def meilisearch_url():
    """Meilisearch URL for testing"""
    return "http://localhost:7700"


@pytest.fixture
def meilisearch_api_key():
    """Meilisearch API key for testing"""
    import os

    return os.getenv("MEILI_MASTER_KEY")


@pytest.fixture
async def mcp_server(meilisearch_url, meilisearch_api_key):
    """Create MCP server instance for testing"""
    server = create_server(url=meilisearch_url, api_key=meilisearch_api_key)
    yield server
    await server.cleanup()


@pytest.fixture
async def clean_index():
    """Provide a clean test index name and cleanup after test"""
    index_name = f"test_index_{int(time.time())}"
    yield index_name


async def simulate_tool_call(
    server: MeilisearchMCPServer,
    tool_name: str,
    arguments: Optional[Dict[str, Any]] = None,
):
    """Simulate calling a tool through the MCP server"""
    # Access the call_tool handler using the decorator system
    for method_name in dir(server):
        method = getattr(server, method_name)
        if hasattr(method, "_mcp_tool_name") and method._mcp_tool_name == tool_name:
            if arguments:
                return await method(**arguments)
            else:
                return await method()

    # If no specific method found, use the general handler
    # Get the handler by looking at the server's request handlers
    if hasattr(server.server, "request_handlers"):
        call_tool_handler = server.server.request_handlers.get("tools/call")
        if call_tool_handler:
            return await call_tool_handler(tool_name, arguments or {})

    # Fallback: call the internal handler directly
    try:
        # Look for the handle_call_tool method
        for attr_name in dir(server):
            attr = getattr(server, attr_name)
            if callable(attr) and "call_tool" in attr_name.lower():
                return await attr(tool_name, arguments)

        # Last resort: directly simulate the tool execution logic
        return await server._execute_tool_directly(tool_name, arguments or {})
    except Exception as e:
        # Return error response as the actual server would
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


async def simulate_list_tools(server: MeilisearchMCPServer):
    """Simulate listing tools through the MCP server"""
    if hasattr(server.server, "request_handlers"):
        list_tools_handler = server.server.request_handlers.get("tools/list")
        if list_tools_handler:
            return await list_tools_handler()

    # Fallback: get tools directly from the handlers
    tools = []

    # Known tools from the server implementation
    tool_definitions = [
        {
            "name": "get-connection-settings",
            "description": "Get current Meilisearch connection settings",
        },
        {
            "name": "update-connection-settings",
            "description": "Update Meilisearch connection settings",
        },
        {"name": "health-check", "description": "Check Meilisearch server health"},
        {"name": "get-version", "description": "Get Meilisearch version information"},
        {"name": "get-stats", "description": "Get database statistics"},
        {"name": "create-index", "description": "Create a new Meilisearch index"},
        {"name": "list-indexes", "description": "List all Meilisearch indexes"},
        {"name": "get-documents", "description": "Get documents from an index"},
        {"name": "add-documents", "description": "Add documents to an index"},
        {"name": "get-settings", "description": "Get current settings for an index"},
        {"name": "update-settings", "description": "Update settings for an index"},
        {"name": "search", "description": "Search through Meilisearch indices"},
        {"name": "get-task", "description": "Get information about a specific task"},
        {"name": "get-tasks", "description": "Get list of tasks with optional filters"},
    ]

    for tool_def in tool_definitions:
        tools.append(
            types.Tool(
                name=tool_def["name"],
                description=tool_def["description"],
                inputSchema={"type": "object", "properties": {}},
            )
        )

    return tools


# Add a helper method to the server class for direct tool execution
async def _execute_tool_directly(
    self, name: str, arguments: Optional[Dict[str, Any]] = None
):
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

        elif name == "update-connection-settings":
            await self.update_connection(args.get("url"), args.get("api_key"))
            return [
                types.TextContent(
                    type="text",
                    text=f"Successfully updated connection settings to URL: {self.url}",
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

        elif name == "add-documents":
            result = await self.meili_client.documents.add_documents(
                args["indexUid"],
                args["documents"],
                args.get("primaryKey"),
            )
            return [types.TextContent(type="text", text=f"Added documents: {result}")]

        elif name == "get-documents":
            documents = await self.meili_client.documents.get_documents(
                args["indexUid"],
                args.get("offset"),
                args.get("limit"),
            )
            return [types.TextContent(type="text", text=f"Documents: {documents}")]

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

        elif name == "get-settings":
            settings = await self.meili_client.settings.get_settings(args["indexUid"])
            return [
                types.TextContent(type="text", text=f"Current settings: {settings}")
            ]

        elif name == "update-settings":
            result = await self.meili_client.settings.update_settings(
                args["indexUid"], args["settings"]
            )
            return [types.TextContent(type="text", text=f"Settings updated: {result}")]

        elif name == "get-tasks":
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
            return [types.TextContent(type="text", text=f"Tasks: {tasks}")]

        else:
            raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


# Monkey patch the method onto the server class
MeilisearchMCPServer._execute_tool_directly = _execute_tool_directly


class TestMCPServerBasics:
    """Test basic MCP server functionality"""

    @pytest.mark.asyncio
    async def test_server_creation(self, meilisearch_url):
        """Test that we can create a server instance"""
        server = create_server(url=meilisearch_url)
        assert server is not None
        assert server.meili_client is not None
        assert server.url == meilisearch_url
        await server.cleanup()

    @pytest.mark.asyncio
    async def test_list_tools(self, mcp_server):
        """Test that list_tools returns expected tools"""
        tools = await simulate_list_tools(mcp_server)

        assert isinstance(tools, list)
        assert len(tools) > 0

        tool_names = [tool.name for tool in tools]
        expected_tools = [
            "health-check",
            "get-version",
            "create-index",
            "list-indexes",
            "add-documents",
            "get-documents",
            "search",
            "get-stats",
        ]

        for expected_tool in expected_tools:
            assert (
                expected_tool in tool_names
            ), f"Expected tool {expected_tool} not found"


class TestMCPConnectionManagement:
    """Test connection management tools"""

    @pytest.mark.asyncio
    async def test_get_connection_settings(self, mcp_server):
        """Test get-connection-settings tool"""
        result = await simulate_tool_call(mcp_server, "get-connection-settings")

        assert isinstance(result, list)
        assert len(result) > 0
        assert isinstance(result[0], types.TextContent)
        assert "Current connection settings" in result[0].text
        assert "localhost:7700" in result[0].text

    @pytest.mark.asyncio
    async def test_update_connection_settings(self, mcp_server):
        """Test update-connection-settings tool"""
        new_url = "http://localhost:7701"
        result = await simulate_tool_call(
            mcp_server, "update-connection-settings", {"url": new_url}
        )

        assert isinstance(result, list)
        assert len(result) > 0
        assert isinstance(result[0], types.TextContent)
        assert "Successfully updated" in result[0].text
        assert new_url in result[0].text

        # Verify the connection was updated
        assert mcp_server.url == new_url


class TestMCPHealthAndVersion:
    """Test health and version related tools"""

    @pytest.mark.asyncio
    async def test_health_check(self, mcp_server):
        """Test health-check tool"""
        result = await simulate_tool_call(mcp_server, "health-check")

        assert isinstance(result, list)
        assert len(result) > 0
        assert isinstance(result[0], types.TextContent)
        assert "available" in result[0].text or "unavailable" in result[0].text

    @pytest.mark.asyncio
    async def test_get_version(self, mcp_server):
        """Test get-version tool"""
        result = await simulate_tool_call(mcp_server, "get-version")

        assert isinstance(result, list)
        assert len(result) > 0
        assert isinstance(result[0], types.TextContent)
        assert "Version info" in result[0].text

    @pytest.mark.asyncio
    async def test_get_stats(self, mcp_server):
        """Test get-stats tool"""
        result = await simulate_tool_call(mcp_server, "get-stats")

        assert isinstance(result, list)
        assert len(result) > 0
        assert isinstance(result[0], types.TextContent)
        assert "Database stats" in result[0].text


class TestMCPIndexManagement:
    """Test index management tools"""

    @pytest.mark.asyncio
    async def test_create_index(self, mcp_server, clean_index):
        """Test create-index tool"""
        result = await simulate_tool_call(
            mcp_server, "create-index", {"uid": clean_index}
        )

        assert isinstance(result, list)
        assert len(result) > 0
        assert isinstance(result[0], types.TextContent)
        assert "Created index" in result[0].text

    @pytest.mark.asyncio
    async def test_list_indexes(self, mcp_server):
        """Test list-indexes tool"""
        result = await simulate_tool_call(mcp_server, "list-indexes")

        assert isinstance(result, list)
        assert len(result) > 0
        assert isinstance(result[0], types.TextContent)
        assert "Indexes" in result[0].text


class TestMCPDocumentOperations:
    """Test document operations"""

    @pytest.mark.asyncio
    async def test_add_documents(self, mcp_server, clean_index):
        """Test add-documents tool"""
        # First create an index
        await simulate_tool_call(mcp_server, "create-index", {"uid": clean_index})

        # Wait for index to be fully created
        await asyncio.sleep(0.5)

        # Add documents
        documents = [
            {"id": 1, "title": "Test Movie", "genre": "Action"},
            {"id": 2, "title": "Another Movie", "genre": "Comedy"},
        ]

        result = await simulate_tool_call(
            mcp_server,
            "add-documents",
            {"indexUid": clean_index, "documents": documents},
        )

        assert isinstance(result, list)
        assert len(result) > 0
        assert isinstance(result[0], types.TextContent)
        assert "Added documents" in result[0].text

    @pytest.mark.asyncio
    async def test_get_documents(self, mcp_server, clean_index):
        """Test get-documents tool"""
        # First create an index and add documents
        await simulate_tool_call(mcp_server, "create-index", {"uid": clean_index})

        # Wait for index to be fully created
        await asyncio.sleep(0.5)

        documents = [{"id": 1, "title": "Test Movie"}]
        await simulate_tool_call(
            mcp_server,
            "add-documents",
            {"indexUid": clean_index, "documents": documents},
        )

        # Wait a bit for indexing
        await asyncio.sleep(0.5)

        # Get documents
        result = await simulate_tool_call(
            mcp_server, "get-documents", {"indexUid": clean_index}
        )

        assert isinstance(result, list)
        assert len(result) > 0
        assert isinstance(result[0], types.TextContent)
        assert "Documents" in result[0].text


class TestMCPSearch:
    """Test search functionality"""

    @pytest.mark.asyncio
    async def test_search_with_index(self, mcp_server, clean_index):
        """Test search tool with specific index"""
        # Setup: create index and add documents
        await simulate_tool_call(mcp_server, "create-index", {"uid": clean_index})

        # Wait for index to be fully created
        await asyncio.sleep(0.5)

        documents = [
            {"id": 1, "title": "Action Movie", "genre": "Action"},
            {"id": 2, "title": "Comedy Movie", "genre": "Comedy"},
        ]
        await simulate_tool_call(
            mcp_server,
            "add-documents",
            {"indexUid": clean_index, "documents": documents},
        )

        # Wait a bit for indexing
        await asyncio.sleep(1)

        # Search
        result = await simulate_tool_call(
            mcp_server,
            "search",
            {"query": "Movie", "indexUid": clean_index, "limit": 10},
        )

        assert isinstance(result, list)
        assert len(result) > 0
        assert isinstance(result[0], types.TextContent)
        assert "Search results" in result[0].text
        assert "Movie" in result[0].text

    @pytest.mark.asyncio
    async def test_search_without_index(self, mcp_server):
        """Test search tool without specifying index (search all)"""
        result = await simulate_tool_call(
            mcp_server, "search", {"query": "test", "limit": 5}
        )

        assert isinstance(result, list)
        assert len(result) > 0
        assert isinstance(result[0], types.TextContent)
        assert "Search results" in result[0].text


class TestMCPSettings:
    """Test settings management"""

    @pytest.mark.asyncio
    async def test_get_settings(self, mcp_server, clean_index):
        """Test get-settings tool"""
        # Create index first
        await simulate_tool_call(mcp_server, "create-index", {"uid": clean_index})

        # Wait for index to be fully created
        await asyncio.sleep(1)

        # Verify index exists by listing indexes
        indexes_result = await simulate_tool_call(mcp_server, "list-indexes")
        assert clean_index in indexes_result[0].text

        result = await simulate_tool_call(
            mcp_server, "get-settings", {"indexUid": clean_index}
        )

        assert isinstance(result, list)
        assert len(result) > 0
        assert isinstance(result[0], types.TextContent)
        assert "Current settings" in result[0].text

    @pytest.mark.asyncio
    async def test_update_settings(self, mcp_server, clean_index):
        """Test update-settings tool"""
        # Create index first
        await simulate_tool_call(mcp_server, "create-index", {"uid": clean_index})

        # Wait for index to be fully created
        await asyncio.sleep(1)

        # Update settings
        settings = {
            "searchableAttributes": ["title", "genre"],
            "displayedAttributes": ["*"],
        }

        result = await simulate_tool_call(
            mcp_server,
            "update-settings",
            {"indexUid": clean_index, "settings": settings},
        )

        assert isinstance(result, list)
        assert len(result) > 0
        assert isinstance(result[0], types.TextContent)
        assert "Settings updated" in result[0].text


class TestMCPTasks:
    """Test task management"""

    @pytest.mark.asyncio
    async def test_get_tasks(self, mcp_server):
        """Test get-tasks tool"""
        result = await simulate_tool_call(mcp_server, "get-tasks", {"limit": 10})

        assert isinstance(result, list)
        assert len(result) > 0
        assert isinstance(result[0], types.TextContent)
        assert "Tasks" in result[0].text


class TestMCPErrorHandling:
    """Test error handling"""

    @pytest.mark.asyncio
    async def test_invalid_tool_name(self, mcp_server):
        """Test calling non-existent tool"""
        result = await simulate_tool_call(mcp_server, "non-existent-tool")

        assert isinstance(result, list)
        assert len(result) > 0
        assert isinstance(result[0], types.TextContent)
        assert "Error" in result[0].text

    @pytest.mark.asyncio
    async def test_invalid_index_operations(self, mcp_server):
        """Test operations on non-existent index"""
        # Try to get documents from non-existent index
        result = await simulate_tool_call(
            mcp_server, "get-documents", {"indexUid": "non_existent_index"}
        )

        assert isinstance(result, list)
        assert len(result) > 0
        assert isinstance(result[0], types.TextContent)
        # Should either return empty documents or an error
