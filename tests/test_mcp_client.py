"""
MCP Client Integration Tests

These tests simulate an MCP client connecting to the MCP server to test:
1. Tool discovery functionality
2. Connection settings verification

The tests require a running Meilisearch instance in the background.
"""

import asyncio
import json
import os
import time
from typing import Dict, Any, List
import pytest
from unittest.mock import AsyncMock, patch

from mcp.types import CallToolRequest, CallToolRequestParams, ListToolsRequest
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


async def simulate_mcp_call(
    server: MeilisearchMCPServer, tool_name: str, arguments: Dict[str, Any] = None
) -> List[Any]:
    """Simulate an MCP client call to the server"""
    handler = server.server.request_handlers.get(CallToolRequest)
    if not handler:
        raise RuntimeError("No call_tool handler found")

    request = CallToolRequest(
        method="tools/call",
        params=CallToolRequestParams(name=tool_name, arguments=arguments or {}),
    )

    result = await handler(request)
    return result.root.content


async def simulate_list_tools(server: MeilisearchMCPServer) -> List[Any]:
    """Simulate an MCP client request to list tools"""
    handler = server.server.request_handlers.get(ListToolsRequest)
    if not handler:
        raise RuntimeError("No list_tools handler found")

    request = ListToolsRequest(method="tools/list")
    result = await handler(request)
    return result.root.tools


async def create_test_index_with_documents(
    server: MeilisearchMCPServer, index_name: str, documents: List[Dict[str, Any]]
) -> None:
    """Helper to create index and add documents for testing"""
    await simulate_mcp_call(server, "create-index", {"uid": index_name})
    await simulate_mcp_call(
        server, "add-documents", {"indexUid": index_name, "documents": documents}
    )
    await wait_for_indexing()


def assert_text_content_response(
    result: List[Any], expected_content: str = None
) -> str:
    """Common assertions for text content responses"""
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0].type == "text"

    text = result[0].text
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
    await server.cleanup()


class TestMCPClientIntegration:
    """Test MCP client interaction with the server"""

    async def test_tool_discovery(self, mcp_server):
        """Test that MCP client can discover all available tools from the server"""
        # Simulate MCP list_tools request
        tools = await simulate_list_tools(mcp_server)

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
            assert all(
                hasattr(tool, attr) for attr in ["name", "description", "inputSchema"]
            )
            assert all(
                isinstance(getattr(tool, attr), expected_type)
                for attr, expected_type in [
                    ("name", str),
                    ("description", str),
                    ("inputSchema", dict),
                ]
            )

        print(f"Discovered {len(tools)} tools: {tool_names}")

    async def test_connection_settings_verification(self, mcp_server):
        """Test connection settings tools to verify MCP client can connect to server"""
        # Test getting current connection settings
        result = await simulate_mcp_call(mcp_server, "get-connection-settings")
        text = assert_text_content_response(result, "Current connection settings:")
        assert "URL:" in text

        # Test updating connection settings
        update_result = await simulate_mcp_call(
            mcp_server, "update-connection-settings", {"url": ALT_TEST_URL}
        )
        update_text = assert_text_content_response(
            update_result, "Successfully updated connection settings"
        )
        assert ALT_TEST_URL in update_text

        # Verify the update took effect
        verify_result = await simulate_mcp_call(mcp_server, "get-connection-settings")
        verify_text = assert_text_content_response(verify_result)
        assert ALT_TEST_URL in verify_text

    async def test_health_check_tool(self, mcp_server):
        """Test health check tool through MCP client interface"""
        # Mock the health check to avoid requiring actual Meilisearch
        with patch.object(
            mcp_server.meili_client, "health_check", new_callable=AsyncMock
        ) as mock_health:
            mock_health.return_value = True
            result = await simulate_mcp_call(mcp_server, "health-check")

            assert_text_content_response(result, "available")
            mock_health.assert_called_once()

    async def test_tool_error_handling(self, mcp_server):
        """Test that MCP client receives proper error responses from server"""
        result = await simulate_mcp_call(mcp_server, "non-existent-tool")
        text = assert_text_content_response(result, "Error:")
        assert "Unknown tool" in text

    async def test_tool_schema_validation(self, mcp_server):
        """Test that tools have proper input schemas for MCP client validation"""
        tools = await simulate_list_tools(mcp_server)

        # Check specific tool schemas
        create_index_tool = next(tool for tool in tools if tool.name == "create-index")
        assert create_index_tool.inputSchema["type"] == "object"
        assert "uid" in create_index_tool.inputSchema["required"]
        assert "uid" in create_index_tool.inputSchema["properties"]
        assert create_index_tool.inputSchema["properties"]["uid"]["type"] == "string"

        search_tool = next(tool for tool in tools if tool.name == "search")
        assert search_tool.inputSchema["type"] == "object"
        assert "query" in search_tool.inputSchema["required"]
        assert "query" in search_tool.inputSchema["properties"]
        assert search_tool.inputSchema["properties"]["query"]["type"] == "string"

    async def test_mcp_server_initialization(self, mcp_server):
        """Test that MCP server initializes correctly for client connections"""
        # Verify server has required attributes
        assert hasattr(mcp_server, "server")
        assert hasattr(mcp_server, "meili_client")
        assert hasattr(mcp_server, "url")
        assert hasattr(mcp_server, "api_key")
        assert hasattr(mcp_server, "logger")

        # Verify server name and basic configuration
        assert mcp_server.server.name == "meilisearch"
        assert mcp_server.url is not None
        assert mcp_server.meili_client is not None


class TestMCPToolDiscovery:
    """Detailed tests for MCP tool discovery functionality"""

    async def test_complete_tool_list(self, mcp_server):
        """Test that all expected tools are discoverable by MCP clients"""
        tools = await simulate_list_tools(mcp_server)
        tool_names = [tool.name for tool in tools]

        # Complete list of expected tools (22 total)
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
        ]

        assert len(tools) == len(expected_tools)
        for tool_name in expected_tools:
            assert tool_name in tool_names

    async def test_tool_categorization(self, mcp_server):
        """Test that tools can be categorized for MCP client organization"""
        tools = await simulate_list_tools(mcp_server)

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
        }

        for category, min_count in expected_counts.items():
            assert (
                len(categories[category]) >= min_count
            ), f"Category '{category}' has insufficient tools"


class TestMCPConnectionSettings:
    """Detailed tests for MCP connection settings functionality"""

    async def test_get_connection_settings_format(self, mcp_server):
        """Test connection settings response format for MCP clients"""
        result = await simulate_mcp_call(mcp_server, "get-connection-settings")
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

    async def test_get_documents_returns_json_not_python_object(self, mcp_server):
        """Test that get-documents returns JSON-formatted text, not Python object string representation (issue #16)"""
        test_index = generate_unique_index_name("test_issue16")
        test_document = {"id": 1, "title": "Test Document", "content": "Test content"}

        # Create index and add test document
        await create_test_index_with_documents(mcp_server, test_index, [test_document])

        # Get documents with explicit parameters
        result = await simulate_mcp_call(
            mcp_server,
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

    async def test_update_connection_settings_persistence(self, mcp_server):
        """Test that connection updates persist for MCP client sessions"""
        # Test URL update
        await simulate_mcp_call(
            mcp_server, "update-connection-settings", {"url": ALT_TEST_URL}
        )
        assert mcp_server.url == ALT_TEST_URL
        assert mcp_server.meili_client.client.config.url == ALT_TEST_URL

        # Test API key update
        await simulate_mcp_call(
            mcp_server, "update-connection-settings", {"api_key": TEST_API_KEY}
        )
        assert mcp_server.api_key == TEST_API_KEY
        assert mcp_server.meili_client.client.config.api_key == TEST_API_KEY

        # Test both updates together
        await simulate_mcp_call(
            mcp_server,
            "update-connection-settings",
            {"url": ALT_TEST_URL_2, "api_key": FINAL_TEST_KEY},
        )
        assert mcp_server.url == ALT_TEST_URL_2
        assert mcp_server.api_key == FINAL_TEST_KEY

    async def test_connection_settings_validation(self, mcp_server):
        """Test that MCP client receives validation for connection settings"""
        # Test with empty updates
        result = await simulate_mcp_call(mcp_server, "update-connection-settings", {})
        assert_text_content_response(result, "Successfully updated")

        # Test partial updates
        original_url = mcp_server.url
        await simulate_mcp_call(
            mcp_server, "update-connection-settings", {"api_key": "new_key_only"}
        )

        assert mcp_server.url == original_url  # URL unchanged
        assert mcp_server.api_key == "new_key_only"  # Key updated


class TestIssue17DefaultLimitOffset:
    """Test for issue #17 - get-documents should use default limit and offset to avoid None parameter errors"""

    async def test_get_documents_without_limit_offset_parameters(self, mcp_server):
        """Test that get-documents works without providing limit/offset parameters (issue #17)"""
        test_index = generate_unique_index_name("test_issue17")
        test_documents = [
            {"id": 1, "title": "Test Document 1", "content": "Content 1"},
            {"id": 2, "title": "Test Document 2", "content": "Content 2"},
            {"id": 3, "title": "Test Document 3", "content": "Content 3"},
        ]

        # Create index and add test documents
        await create_test_index_with_documents(mcp_server, test_index, test_documents)

        # Test get-documents without any limit/offset parameters (should use defaults)
        result = await simulate_mcp_call(
            mcp_server, "get-documents", {"indexUid": test_index}
        )
        assert_text_content_response(result, "Documents:")
        # Should not get any errors about None parameters

    async def test_get_documents_with_explicit_parameters(self, mcp_server):
        """Test that get-documents still works with explicit limit/offset parameters"""
        test_index = generate_unique_index_name("test_issue17_explicit")
        test_documents = [
            {"id": 1, "title": "Test Document 1", "content": "Content 1"},
            {"id": 2, "title": "Test Document 2", "content": "Content 2"},
        ]

        # Create index and add test documents
        await create_test_index_with_documents(mcp_server, test_index, test_documents)

        # Test get-documents with explicit parameters
        result = await simulate_mcp_call(
            mcp_server,
            "get-documents",
            {"indexUid": test_index, "offset": 0, "limit": 1},
        )
        assert_text_content_response(result, "Documents:")

    async def test_get_documents_default_values_applied(self, mcp_server):
        """Test that default values (offset=0, limit=20) are properly applied"""
        test_index = generate_unique_index_name("test_issue17_defaults")
        test_documents = [{"id": i, "title": f"Document {i}"} for i in range(1, 6)]

        # Create index and add test documents
        await create_test_index_with_documents(mcp_server, test_index, test_documents)

        # Test that both calls with and without parameters work
        result_no_params = await simulate_mcp_call(
            mcp_server, "get-documents", {"indexUid": test_index}
        )
        result_with_defaults = await simulate_mcp_call(
            mcp_server,
            "get-documents",
            {"indexUid": test_index, "offset": 0, "limit": 20},
        )

        # Both should work and return similar results
        assert_text_content_response(result_no_params)
        assert_text_content_response(result_with_defaults)


class TestIssue23DeleteIndexTool:
    """Test for issue #23 - Add delete-index MCP tool functionality"""

    async def test_delete_index_tool_discovery(self, mcp_server):
        """Test that delete-index tool is discoverable by MCP clients (issue #23)"""
        tools = await simulate_list_tools(mcp_server)
        tool_names = [tool.name for tool in tools]

        assert "delete-index" in tool_names

        # Find the delete-index tool and verify its schema
        delete_tool = next(tool for tool in tools if tool.name == "delete-index")
        assert delete_tool.description == "Delete a Meilisearch index"
        assert delete_tool.inputSchema["type"] == "object"
        assert "uid" in delete_tool.inputSchema["required"]
        assert "uid" in delete_tool.inputSchema["properties"]
        assert delete_tool.inputSchema["properties"]["uid"]["type"] == "string"

    async def test_delete_index_successful_deletion(self, mcp_server):
        """Test successful index deletion through MCP client (issue #23)"""
        test_index = generate_unique_index_name("test_delete_success")

        # Create index first
        await simulate_mcp_call(mcp_server, "create-index", {"uid": test_index})
        await wait_for_indexing()

        # Verify index exists by listing indexes
        list_result = await simulate_mcp_call(mcp_server, "list-indexes")
        list_text = assert_text_content_response(list_result)
        assert test_index in list_text

        # Delete the index
        result = await simulate_mcp_call(
            mcp_server, "delete-index", {"uid": test_index}
        )
        response_text = assert_text_content_response(
            result, "Successfully deleted index:"
        )
        assert test_index in response_text

        # Verify index no longer exists by listing indexes
        await wait_for_indexing()
        list_result_after = await simulate_mcp_call(mcp_server, "list-indexes")
        list_text_after = assert_text_content_response(list_result_after)
        assert test_index not in list_text_after

    async def test_delete_index_with_documents(self, mcp_server):
        """Test deleting index that contains documents (issue #23)"""
        test_index = generate_unique_index_name("test_delete_with_docs")
        test_documents = [
            {"id": 1, "title": "Test Document 1", "content": "Content 1"},
            {"id": 2, "title": "Test Document 2", "content": "Content 2"},
        ]

        # Create index and add documents
        await create_test_index_with_documents(mcp_server, test_index, test_documents)

        # Verify documents exist
        docs_result = await simulate_mcp_call(
            mcp_server, "get-documents", {"indexUid": test_index}
        )
        docs_text = assert_text_content_response(docs_result, "Documents:")
        assert "Test Document 1" in docs_text

        # Delete the index (should also delete all documents)
        result = await simulate_mcp_call(
            mcp_server, "delete-index", {"uid": test_index}
        )
        response_text = assert_text_content_response(
            result, "Successfully deleted index:"
        )
        assert test_index in response_text

        # Verify index and documents are gone
        await wait_for_indexing()
        list_result = await simulate_mcp_call(mcp_server, "list-indexes")
        list_text = assert_text_content_response(list_result)
        assert test_index not in list_text

    async def test_delete_nonexistent_index_behavior(self, mcp_server):
        """Test behavior when deleting non-existent index (issue #23)"""
        nonexistent_index = generate_unique_index_name("nonexistent")

        # Try to delete non-existent index
        # Note: Meilisearch allows deleting non-existent indexes without error
        result = await simulate_mcp_call(
            mcp_server, "delete-index", {"uid": nonexistent_index}
        )
        response_text = assert_text_content_response(
            result, "Successfully deleted index:"
        )
        assert nonexistent_index in response_text

    async def test_delete_index_input_validation(self, mcp_server):
        """Test input validation for delete-index tool (issue #23)"""
        # Test missing uid parameter
        result = await simulate_mcp_call(mcp_server, "delete-index", {})
        response_text = assert_text_content_response(result, "Error:")
        assert "Error:" in response_text

    async def test_delete_index_integration_workflow(self, mcp_server):
        """Test complete workflow: create -> add docs -> search -> delete (issue #23)"""
        test_index = generate_unique_index_name("test_delete_workflow")
        test_documents = [
            {"id": 1, "title": "Workflow Document", "content": "Testing workflow"},
        ]

        # Create index and add documents
        await create_test_index_with_documents(mcp_server, test_index, test_documents)

        # Search to verify functionality
        search_result = await simulate_mcp_call(
            mcp_server, "search", {"query": "workflow", "indexUid": test_index}
        )
        search_text = assert_text_content_response(search_result)
        assert "Workflow Document" in search_text

        # Delete the index
        delete_result = await simulate_mcp_call(
            mcp_server, "delete-index", {"uid": test_index}
        )
        assert_text_content_response(delete_result, "Successfully deleted index:")

        # Verify search no longer works on deleted index
        await wait_for_indexing()
        search_after_delete = await simulate_mcp_call(
            mcp_server, "search", {"query": "workflow", "indexUid": test_index}
        )
        search_after_text = assert_text_content_response(search_after_delete, "Error:")
        assert "Error:" in search_after_text


class TestIssue27OpenAISchemaCompatibility:
    """Test for issue #27 - Fix JSON schemas for OpenAI Agent SDK compatibility"""

    async def test_all_schemas_have_additional_properties_false(self, mcp_server):
        """Test that all tool schemas include additionalProperties: false for OpenAI compatibility (issue #27)"""
        tools = await simulate_list_tools(mcp_server)

        for tool in tools:
            schema = tool.inputSchema
            assert schema["type"] == "object"
            assert (
                "additionalProperties" in schema
            ), f"Tool '{tool.name}' missing additionalProperties"
            assert (
                schema["additionalProperties"] is False
            ), f"Tool '{tool.name}' additionalProperties should be false"

    async def test_array_schemas_have_items_property(self, mcp_server):
        """Test that all array schemas include items property for OpenAI compatibility (issue #27)"""
        tools = await simulate_list_tools(mcp_server)

        tools_with_arrays = ["add-documents", "search", "get-tasks", "create-key"]

        for tool in tools:
            if tool.name in tools_with_arrays:
                schema = tool.inputSchema
                properties = schema.get("properties", {})

                for prop_name, prop_schema in properties.items():
                    if prop_schema.get("type") == "array":
                        assert (
                            "items" in prop_schema
                        ), f"Tool '{tool.name}' property '{prop_name}' missing items"
                        assert isinstance(
                            prop_schema["items"], dict
                        ), f"Tool '{tool.name}' property '{prop_name}' items should be object"

    async def test_no_custom_optional_properties(self, mcp_server):
        """Test that schemas don't use non-standard 'optional' property (issue #27)"""
        tools = await simulate_list_tools(mcp_server)

        for tool in tools:
            schema = tool.inputSchema
            properties = schema.get("properties", {})

            for prop_name, prop_schema in properties.items():
                assert (
                    "optional" not in prop_schema
                ), f"Tool '{tool.name}' property '{prop_name}' uses non-standard 'optional'"

    async def test_specific_add_documents_schema_compliance(self, mcp_server):
        """Test add-documents schema specifically mentioned in issue #27"""
        tools = await simulate_list_tools(mcp_server)
        add_docs_tool = next(tool for tool in tools if tool.name == "add-documents")

        schema = add_docs_tool.inputSchema

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

    async def test_openai_compatible_tool_schema_format(self, mcp_server):
        """Test that tool schemas follow OpenAI function calling format (issue #27)"""
        tools = await simulate_list_tools(mcp_server)

        for tool in tools:
            # Verify tool has required OpenAI attributes
            assert hasattr(tool, "name")
            assert hasattr(tool, "description")
            assert hasattr(tool, "inputSchema")

            # Verify schema structure matches OpenAI expectations
            schema = tool.inputSchema
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
