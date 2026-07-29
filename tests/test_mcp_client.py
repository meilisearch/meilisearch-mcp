"""
MCP Client Integration Tests

These tests connect a real MCP client (in-memory transport) to the server to test:
1. Tool discovery functionality
2. Connection settings verification

The tests require a running Meilisearch instance in the background.
"""

import asyncio
import json
import os
import time
from typing import Dict, Any
import pytest
from unittest.mock import MagicMock, patch

from mcp import Client
from mcp.types import CallToolResult
from src.meilisearch_mcp.server import MeilisearchMCPServer, create_server

# Test configuration constants
INDEXING_WAIT_TIME = 0.5
TEST_URL = "http://localhost:7700"
ALT_TEST_URL = "http://localhost:7701"
ALT_TEST_URL_2 = "http://localhost:7702"
TEST_API_KEY = "test_api_key_123"
FINAL_TEST_KEY = "final_test_key"


def generate_unique_index_name(prefix: str = "test") -> str:
    """Generate a unique index name for testing"""
    return f"{prefix}_{int(time.time() * 1000)}"


async def wait_for_indexing() -> None:
    """Wait for Meilisearch indexing to complete"""
    await asyncio.sleep(INDEXING_WAIT_TIME)


class InMemoryToolClient:
    """Drives the server through a real MCP client over the in-memory transport.

    Opens a fresh connection per call so anyio cancel scopes stay within the
    test's own task (pytest-asyncio runs fixture setup/teardown in different
    tasks, which breaks a long-lived Client held across a fixture yield).
    """

    def __init__(self, server: MeilisearchMCPServer):
        self._server = server

    async def call_tool(self, name: str, arguments: Dict[str, Any] = None):
        async with Client(self._server.mcp) as client:
            return await client.call_tool(name, arguments or {})

    async def list_tools(self):
        async with Client(self._server.mcp) as client:
            return await client.list_tools()


async def list_tools(client: InMemoryToolClient):
    """List tools through the MCP client"""
    result = await client.list_tools()
    return result.tools


async def create_test_index_with_documents(
    client: "InMemoryToolClient", index_name: str, documents: list
) -> None:
    """Helper to create index and add documents for testing"""
    await client.call_tool("create-index", {"uid": index_name})
    await client.call_tool(
        "add-documents", {"indexUid": index_name, "documents": documents}
    )
    await wait_for_indexing()


def assert_text_content_response(
    result: CallToolResult, expected_content: str = None
) -> str:
    """Common assertions for successful text content responses"""
    assert not result.is_error, f"Unexpected tool error: {result.content}"
    assert len(result.content) >= 1
    assert result.content[0].type == "text"

    text = result.content[0].text
    if expected_content:
        assert expected_content in text

    return text


def assert_error_response(result: CallToolResult, expected_content: str = None) -> str:
    """Common assertions for tool error responses"""
    assert result.is_error, f"Expected tool error, got: {result.content}"
    text = result.content[0].text
    if expected_content:
        assert expected_content in text
    return text


@pytest.fixture
async def mcp_server():
    """Shared fixture for creating MCP server instances"""
    url = os.getenv("MEILI_HTTP_ADDR", TEST_URL)
    api_key = os.getenv("MEILI_MASTER_KEY")

    server = create_server(url, api_key)
    yield server
    server.cleanup()


@pytest.fixture
def mcp_client(mcp_server):
    """A real MCP client driving the server over an in-memory transport"""
    return InMemoryToolClient(mcp_server)


class TestMCPClientIntegration:
    """Test MCP client interaction with the server"""

    async def test_tool_discovery(self, mcp_client):
        """Test that MCP client can discover all available tools from the server"""
        tools = await list_tools(mcp_client)

        tool_names = [tool.name for tool in tools]

        # Verify basic structure
        assert isinstance(tools, list)
        assert len(tools) > 0

        # Check for essential tools
        essential_tools = [
            "get-connection-settings",
            "update-connection-settings",
            "health-check",
            "get-version",
            "get-stats",
            "create-index",
            "list-indexes",
            "get-documents",
            "add-documents",
            "search",
            "get-settings",
            "update-settings",
        ]

        for tool_name in essential_tools:
            assert tool_name in tool_names, f"Essential tool '{tool_name}' not found"

        # Verify tool structure
        for tool in tools:
            assert isinstance(tool.name, str)
            assert isinstance(tool.description, str)
            assert isinstance(tool.input_schema, dict)

        print(f"Discovered {len(tools)} tools: {tool_names}")

    async def test_connection_settings_verification(self, mcp_server, mcp_client):
        """Test connection settings tools to verify MCP client can connect to server"""
        # Test getting current connection settings
        result = await mcp_client.call_tool("get-connection-settings", {})
        text = assert_text_content_response(result, "Current connection settings:")
        assert "URL:" in text

        # Test updating connection settings
        update_result = await mcp_client.call_tool(
            "update-connection-settings", {"url": ALT_TEST_URL}
        )
        update_text = assert_text_content_response(
            update_result, "Successfully updated connection settings"
        )
        assert ALT_TEST_URL in update_text

        # Verify the update took effect
        verify_result = await mcp_client.call_tool("get-connection-settings", {})
        verify_text = assert_text_content_response(verify_result)
        assert ALT_TEST_URL in verify_text

    async def test_health_check_tool(self, mcp_server, mcp_client):
        """Test health check tool through MCP client interface"""
        # Mock the health check to avoid requiring actual Meilisearch
        with patch.object(
            mcp_server.meili_client, "health_check", new=MagicMock(return_value=True)
        ) as mock_health:
            result = await mcp_client.call_tool("health-check", {})

            assert_text_content_response(result, "available")
            mock_health.assert_called_once()

    async def test_tool_error_handling(self, mcp_client):
        """Test that MCP client receives proper error responses from server"""
        result = await mcp_client.call_tool("non-existent-tool", {})
        assert_error_response(result, "Unknown tool")

    async def test_tool_schema_validation(self, mcp_client):
        """Test that tools have proper input schemas for MCP client validation"""
        tools = await list_tools(mcp_client)

        # Check specific tool schemas
        create_index_tool = next(tool for tool in tools if tool.name == "create-index")
        assert create_index_tool.input_schema["type"] == "object"
        assert "uid" in create_index_tool.input_schema["required"]
        assert "uid" in create_index_tool.input_schema["properties"]
        assert create_index_tool.input_schema["properties"]["uid"]["type"] == "string"

        search_tool = next(tool for tool in tools if tool.name == "search")
        assert search_tool.input_schema["type"] == "object"
        assert "query" in search_tool.input_schema["required"]
        assert "query" in search_tool.input_schema["properties"]
        assert search_tool.input_schema["properties"]["query"]["type"] == "string"

    async def test_mcp_server_initialization(self, mcp_server):
        """Test that MCP server initializes correctly for client connections"""
        # Verify server has required attributes
        assert hasattr(mcp_server, "mcp")
        assert hasattr(mcp_server, "meili_client")
        assert hasattr(mcp_server, "url")
        assert hasattr(mcp_server, "api_key")

        # Verify server name and basic configuration
        assert mcp_server.mcp.name == "meilisearch"
        assert mcp_server.url is not None
        assert mcp_server.meili_client is not None


class TestMCPToolDiscovery:
    """Detailed tests for MCP tool discovery functionality"""

    async def test_complete_tool_list(self, mcp_client):
        """Test that all expected tools are discoverable by MCP clients"""
        tools = await list_tools(mcp_client)
        tool_names = [tool.name for tool in tools]

        # Complete list of expected tools (26 total - includes 4 chat tools)
        expected_tools = [
            "get-connection-settings",
            "update-connection-settings",
            "health-check",
            "get-version",
            "get-stats",
            "create-index",
            "list-indexes",
            "delete-index",
            "get-documents",
            "add-documents",
            "get-settings",
            "update-settings",
            "search",
            "get-task",
            "get-tasks",
            "cancel-tasks",
            "get-keys",
            "create-key",
            "delete-key",
            "get-health-status",
            "get-index-metrics",
            "get-system-info",
            "create-chat-completion",
            "get-chat-workspaces",
            "get-chat-workspace-settings",
            "update-chat-workspace-settings",
        ]

        assert set(tool_names) == set(expected_tools)

    async def test_tool_categorization(self, mcp_client):
        """Test that tools can be categorized for MCP client organization"""
        tools = await list_tools(mcp_client)

        # Categorize tools by functionality
        categories = {
            "connection": [t for t in tools if "connection" in t.name],
            "index": [
                t
                for t in tools
                if any(
                    word in t.name
                    for word in [
                        "index",
                        "create-index",
                        "list-indexes",
                        "delete-index",
                    ]
                )
            ],
            "document": [t for t in tools if "document" in t.name],
            "search": [t for t in tools if "search" in t.name],
            "task": [t for t in tools if "task" in t.name],
            "key": [t for t in tools if "key" in t.name],
            "monitoring": [
                t
                for t in tools
                if any(
                    word in t.name
                    for word in ["health", "stats", "version", "system", "metrics"]
                )
            ],
            "chat": [t for t in tools if "chat" in t.name],
        }

        # Verify minimum expected tools per category
        expected_counts = {
            "connection": 2,
            "index": 3,
            "document": 2,
            "search": 1,
            "task": 2,
            "key": 3,
            "monitoring": 4,
            "chat": 4,
        }

        for category, min_count in expected_counts.items():
            assert (
                len(categories[category]) >= min_count
            ), f"Category '{category}' has insufficient tools"

    async def test_tool_annotations(self, mcp_client):
        """Test that tools carry MCP tool annotations (read-only/destructive hints)"""
        tools = await list_tools(mcp_client)
        by_name = {tool.name: tool for tool in tools}

        assert by_name["search"].annotations.read_only_hint is True
        assert by_name["list-indexes"].annotations.read_only_hint is True
        assert by_name["delete-index"].annotations.destructive_hint is True
        assert by_name["delete-key"].annotations.destructive_hint is True
        assert by_name["create-index"].annotations.destructive_hint is False


class TestMCPConnectionSettings:
    """Detailed tests for MCP connection settings functionality"""

    async def test_get_connection_settings_format(self, mcp_server, mcp_client):
        """Test connection settings response format for MCP clients"""
        result = await mcp_client.call_tool("get-connection-settings", {})
        text = assert_text_content_response(result, "Current connection settings:")

        # Verify required fields are present
        required_fields = ["URL:", "API Key:"]
        for field in required_fields:
            assert field in text

        # Check URL is properly displayed
        assert mcp_server.url in text

        # Check API key is masked for security
        expected_key_display = "********" if mcp_server.api_key else "Not set"
        assert expected_key_display in text or "Not set" in text


class TestIssue16GetDocumentsJsonSerialization:
    """Test for issue #16 - get-documents should return JSON, not Python object representations"""

    async def test_get_documents_returns_json_not_python_object(self, mcp_client):
        """Test that get-documents returns JSON-formatted text, not Python object string representation (issue #16)"""
        test_index = generate_unique_index_name("test_issue16")
        test_document = {"id": 1, "title": "Test Document", "content": "Test content"}

        # Create index and add test document
        await create_test_index_with_documents(mcp_client, test_index, [test_document])

        # Get documents with explicit parameters
        result = await mcp_client.call_tool(
            "get-documents",
            {"indexUid": test_index, "offset": 0, "limit": 10},
        )

        response_text = assert_text_content_response(result, "Documents:")

        # Issue #16 assertion: Should NOT contain Python object representation
        assert (
            "<meilisearch.models.document.DocumentsResults object at"
            not in response_text
        )
        assert "DocumentsResults" not in response_text

        # Should contain actual document content
        assert "Test Document" in response_text
        assert "Test content" in response_text

        # Should be valid JSON after the "Documents:" prefix
        json_part = response_text.replace("Documents:", "").strip()
        try:
            parsed_data = json.loads(json_part)
            assert isinstance(parsed_data, dict)
            assert "results" in parsed_data
            assert len(parsed_data["results"]) > 0
        except json.JSONDecodeError:
            pytest.fail(f"get-documents returned non-JSON data: {response_text}")

        # Structured output (MCP spec >= 2025-06-18) should carry the same data
        assert result.structured_content is not None
        assert "results" in result.structured_content

    async def test_update_connection_settings_persistence(self, mcp_server, mcp_client):
        """Test that connection updates persist for MCP client sessions"""
        # Test URL update
        await mcp_client.call_tool("update-connection-settings", {"url": ALT_TEST_URL})
        assert mcp_server.url == ALT_TEST_URL
        assert mcp_server.meili_client.client.config.url == ALT_TEST_URL

        # Test API key update
        await mcp_client.call_tool(
            "update-connection-settings", {"api_key": TEST_API_KEY}
        )
        assert mcp_server.api_key == TEST_API_KEY
        assert mcp_server.meili_client.client.config.api_key == TEST_API_KEY

        # Test both updates together
        await mcp_client.call_tool(
            "update-connection-settings",
            {"url": ALT_TEST_URL_2, "api_key": FINAL_TEST_KEY},
        )
        assert mcp_server.url == ALT_TEST_URL_2
        assert mcp_server.api_key == FINAL_TEST_KEY

    async def test_connection_settings_validation(self, mcp_server, mcp_client):
        """Test that MCP client receives validation for connection settings"""
        # Test with empty updates
        result = await mcp_client.call_tool("update-connection-settings", {})
        assert_text_content_response(result, "Successfully updated")

        # Test partial updates
        original_url = mcp_server.url
        await mcp_client.call_tool(
            "update-connection-settings", {"api_key": "new_key_only"}
        )

        assert mcp_server.url == original_url  # URL unchanged
        assert mcp_server.api_key == "new_key_only"  # Key updated


class TestIssue17DefaultLimitOffset:
    """Test for issue #17 - get-documents should use default limit and offset to avoid None parameter errors"""

    async def test_get_documents_without_limit_offset_parameters(self, mcp_client):
        """Test that get-documents works without providing limit/offset parameters (issue #17)"""
        test_index = generate_unique_index_name("test_issue17")
        test_documents = [
            {"id": 1, "title": "Test Document 1", "content": "Content 1"},
            {"id": 2, "title": "Test Document 2", "content": "Content 2"},
            {"id": 3, "title": "Test Document 3", "content": "Content 3"},
        ]

        # Create index and add test documents
        await create_test_index_with_documents(mcp_client, test_index, test_documents)

        # Test get-documents without any limit/offset parameters (should use defaults)
        result = await mcp_client.call_tool("get-documents", {"indexUid": test_index})
        assert_text_content_response(result, "Documents:")
        # Should not get any errors about None parameters

    async def test_get_documents_with_explicit_parameters(self, mcp_client):
        """Test that get-documents still works with explicit limit/offset parameters"""
        test_index = generate_unique_index_name("test_issue17_explicit")
        test_documents = [
            {"id": 1, "title": "Test Document 1", "content": "Content 1"},
            {"id": 2, "title": "Test Document 2", "content": "Content 2"},
        ]

        # Create index and add test documents
        await create_test_index_with_documents(mcp_client, test_index, test_documents)

        # Test get-documents with explicit parameters
        result = await mcp_client.call_tool(
            "get-documents",
            {"indexUid": test_index, "offset": 0, "limit": 1},
        )
        assert_text_content_response(result, "Documents:")

    async def test_get_documents_default_values_applied(self, mcp_client):
        """Test that default values (offset=0, limit=20) are properly applied"""
        test_index = generate_unique_index_name("test_issue17_defaults")
        test_documents = [{"id": i, "title": f"Document {i}"} for i in range(1, 6)]

        # Create index and add test documents
        await create_test_index_with_documents(mcp_client, test_index, test_documents)

        # Test that both calls with and without parameters work
        result_no_params = await mcp_client.call_tool(
            "get-documents", {"indexUid": test_index}
        )
        result_with_defaults = await mcp_client.call_tool(
            "get-documents",
            {"indexUid": test_index, "offset": 0, "limit": 20},
        )

        # Both should work and return similar results
        assert_text_content_response(result_no_params)
        assert_text_content_response(result_with_defaults)


class TestIssue23DeleteIndexTool:
    """Test for issue #23 - Add delete-index MCP tool functionality"""

    async def test_delete_index_tool_discovery(self, mcp_client):
        """Test that delete-index tool is discoverable by MCP clients (issue #23)"""
        tools = await list_tools(mcp_client)
        tool_names = [tool.name for tool in tools]

        assert "delete-index" in tool_names

        # Find the delete-index tool and verify its schema
        delete_tool = next(tool for tool in tools if tool.name == "delete-index")
        assert delete_tool.description == "Delete a Meilisearch index"
        assert delete_tool.input_schema["type"] == "object"
        assert "uid" in delete_tool.input_schema["required"]
        assert "uid" in delete_tool.input_schema["properties"]
        assert delete_tool.input_schema["properties"]["uid"]["type"] == "string"

    async def test_delete_index_successful_deletion(self, mcp_client):
        """Test successful index deletion through MCP client (issue #23)"""
        test_index = generate_unique_index_name("test_delete_success")

        # Create index first
        await mcp_client.call_tool("create-index", {"uid": test_index})
        await wait_for_indexing()

        # Verify index exists by listing indexes
        list_result = await mcp_client.call_tool("list-indexes", {})
        list_text = assert_text_content_response(list_result)
        assert test_index in list_text

        # Delete the index
        result = await mcp_client.call_tool("delete-index", {"uid": test_index})
        response_text = assert_text_content_response(
            result, "Successfully deleted index:"
        )
        assert test_index in response_text

        # Verify index no longer exists by listing indexes
        await wait_for_indexing()
        list_result_after = await mcp_client.call_tool("list-indexes", {})
        list_text_after = assert_text_content_response(list_result_after)
        assert test_index not in list_text_after

    async def test_delete_index_with_documents(self, mcp_client):
        """Test deleting index that contains documents (issue #23)"""
        test_index = generate_unique_index_name("test_delete_with_docs")
        test_documents = [
            {"id": 1, "title": "Test Document 1", "content": "Content 1"},
            {"id": 2, "title": "Test Document 2", "content": "Content 2"},
        ]

        # Create index and add documents
        await create_test_index_with_documents(mcp_client, test_index, test_documents)

        # Verify documents exist
        docs_result = await mcp_client.call_tool(
            "get-documents", {"indexUid": test_index}
        )
        docs_text = assert_text_content_response(docs_result, "Documents:")
        assert "Test Document 1" in docs_text

        # Delete the index (should also delete all documents)
        result = await mcp_client.call_tool("delete-index", {"uid": test_index})
        response_text = assert_text_content_response(
            result, "Successfully deleted index:"
        )
        assert test_index in response_text

        # Verify index and documents are gone
        await wait_for_indexing()
        list_result = await mcp_client.call_tool("list-indexes", {})
        list_text = assert_text_content_response(list_result)
        assert test_index not in list_text

    async def test_delete_nonexistent_index_behavior(self, mcp_client):
        """Test behavior when deleting non-existent index (issue #23)"""
        nonexistent_index = generate_unique_index_name("nonexistent")

        # Try to delete non-existent index
        # Note: Meilisearch allows deleting non-existent indexes without error
        result = await mcp_client.call_tool("delete-index", {"uid": nonexistent_index})
        response_text = assert_text_content_response(
            result, "Successfully deleted index:"
        )
        assert nonexistent_index in response_text

    async def test_delete_index_input_validation(self, mcp_client):
        """Test input validation for delete-index tool (issue #23)"""
        # Test missing uid parameter - the MCP SDK rejects it against the schema
        result = await mcp_client.call_tool("delete-index", {})
        assert_error_response(result, "uid")

    async def test_delete_index_integration_workflow(self, mcp_client):
        """Test complete workflow: create -> add docs -> search -> delete (issue #23)"""
        test_index = generate_unique_index_name("test_delete_workflow")
        test_documents = [
            {"id": 1, "title": "Workflow Document", "content": "Testing workflow"},
        ]

        # Create index and add documents
        await create_test_index_with_documents(mcp_client, test_index, test_documents)

        # Search to verify functionality
        search_result = await mcp_client.call_tool(
            "search", {"query": "workflow", "indexUid": test_index}
        )
        search_text = assert_text_content_response(search_result)
        assert "Workflow Document" in search_text

        # Delete the index
        delete_result = await mcp_client.call_tool("delete-index", {"uid": test_index})
        assert_text_content_response(delete_result, "Successfully deleted index:")

        # Verify search no longer works on deleted index
        await wait_for_indexing()
        search_after_delete = await mcp_client.call_tool(
            "search", {"query": "workflow", "indexUid": test_index}
        )
        assert_error_response(search_after_delete)


class TestIssue27OpenAISchemaCompatibility:
    """Test for issue #27 - Fix JSON schemas for OpenAI Agent SDK compatibility"""

    async def test_all_schemas_have_additional_properties_false(self, mcp_client):
        """Test that all tool schemas include additionalProperties: false for OpenAI compatibility (issue #27)"""
        tools = await list_tools(mcp_client)

        for tool in tools:
            schema = tool.input_schema
            assert schema["type"] == "object"
            assert (
                "additionalProperties" in schema
            ), f"Tool '{tool.name}' missing additionalProperties"
            assert (
                schema["additionalProperties"] is False
            ), f"Tool '{tool.name}' additionalProperties should be false"

    async def test_array_schemas_have_items_property(self, mcp_client):
        """Test that all array schemas include items property for OpenAI compatibility (issue #27)"""
        tools = await list_tools(mcp_client)

        tools_with_arrays = ["add-documents", "search", "get-tasks", "create-key"]

        for tool in tools:
            if tool.name in tools_with_arrays:
                schema = tool.input_schema
                properties = schema.get("properties", {})

                for prop_name, prop_schema in properties.items():
                    if prop_schema.get("type") == "array":
                        assert (
                            "items" in prop_schema
                        ), f"Tool '{tool.name}' property '{prop_name}' missing items"
                        assert isinstance(
                            prop_schema["items"], dict
                        ), f"Tool '{tool.name}' property '{prop_name}' items should be object"

    async def test_no_custom_optional_properties(self, mcp_client):
        """Test that schemas don't use non-standard 'optional' property (issue #27)"""
        tools = await list_tools(mcp_client)

        for tool in tools:
            schema = tool.input_schema
            properties = schema.get("properties", {})

            for prop_name, prop_schema in properties.items():
                assert (
                    "optional" not in prop_schema
                ), f"Tool '{tool.name}' property '{prop_name}' uses non-standard 'optional'"

    async def test_specific_add_documents_schema_compliance(self, mcp_client):
        """Test add-documents schema specifically mentioned in issue #27"""
        tools = await list_tools(mcp_client)
        add_docs_tool = next(tool for tool in tools if tool.name == "add-documents")

        schema = add_docs_tool.input_schema

        # Verify overall structure
        assert schema["type"] == "object"
        assert schema["additionalProperties"] is False
        assert "properties" in schema
        assert "required" in schema

        # Verify documents array property
        documents_prop = schema["properties"]["documents"]
        assert documents_prop["type"] == "array"
        assert (
            "items" in documents_prop
        ), "add-documents documents array missing items property"
        assert documents_prop["items"]["type"] == "object"

        # Verify required fields
        assert "indexUid" in schema["required"]
        assert "documents" in schema["required"]
        assert "primaryKey" not in schema["required"]  # Should be optional

    async def test_openai_compatible_tool_schema_format(self, mcp_client):
        """Test that tool schemas follow OpenAI function calling format (issue #27)"""
        tools = await list_tools(mcp_client)

        for tool in tools:
            # Verify schema structure matches OpenAI expectations
            schema = tool.input_schema
            assert isinstance(schema, dict)
            assert schema.get("type") == "object"
            assert "properties" in schema
            assert isinstance(schema["properties"], dict)

            # If tool has required parameters, they should be in required array
            if "required" in schema:
                assert isinstance(schema["required"], list)

                # All required fields should exist in properties
                for required_field in schema["required"]:
                    assert required_field in schema["properties"]


class TestStructuredOutput:
    """Structured tool output (MCP spec >= 2025-06-18) is returned alongside text"""

    async def test_search_returns_structured_content(self, mcp_client):
        """Search results are available as structuredContent for programmatic use"""
        test_index = generate_unique_index_name("test_structured")
        await create_test_index_with_documents(
            mcp_client,
            test_index,
            [{"id": 1, "title": "Structured Doc", "content": "structured output"}],
        )

        result = await mcp_client.call_tool(
            "search", {"query": "structured", "indexUid": test_index}
        )
        assert_text_content_response(result)
        assert result.structured_content is not None
        assert "hits" in result.structured_content
        assert result.structured_content["hits"][0]["title"] == "Structured Doc"

    async def test_list_indexes_returns_structured_content(self, mcp_client):
        """list-indexes results include structuredContent with the raw data"""
        result = await mcp_client.call_tool("list-indexes", {})
        assert_text_content_response(result, "Indexes:")
        assert result.structured_content is not None
        assert "results" in result.structured_content

    async def test_get_tasks_supports_from_parameter(self, mcp_client):
        """The reserved-word 'from' parameter still works on the wire"""
        result = await mcp_client.call_tool("get-tasks", {"from": 0, "limit": 2})
        assert_text_content_response(result, "Tasks:")
        assert result.structured_content is not None
