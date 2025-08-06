import pytest
import json
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from mcp.types import CallToolRequest, CallToolRequestParams
from src.meilisearch_mcp.server import create_server


@pytest.fixture
def mock_server():
    """Create a mock server for testing chat features"""
    server = create_server("http://localhost:7700", "test_key")
    return server


async def simulate_mcp_call(server, tool_name, arguments=None):
    """Simulate an MCP client call to the server"""
    handler = server.server.request_handlers.get(CallToolRequest)
    if not handler:
        raise RuntimeError("No call_tool handler found")

    request = CallToolRequest(
        method="tools/call",
        params=CallToolRequestParams(name=tool_name, arguments=arguments or {}),
    )

    return await handler(request)


class TestChatCompletion:
    """Test chat completion functionality"""

    @pytest.mark.asyncio
    @patch("src.meilisearch_mcp.chat.httpx.AsyncClient")
    async def test_chat_completion_streaming(self, mock_async_client, mock_server):
        """Test streaming chat completion"""
        # Mock the streaming response
        mock_response = AsyncMock()
        mock_response.raise_for_status = MagicMock()

        # Simulate SSE stream chunks
        async def mock_aiter_lines():
            yield 'data: {"choices": [{"delta": {"content": "Hello"}}]}'
            yield 'data: {"choices": [{"delta": {"content": " world"}}]}'
            yield "data: [DONE]"

        mock_response.aiter_lines = mock_aiter_lines
        mock_async_client.return_value.__aenter__.return_value.stream.return_value.__aenter__.return_value = (
            mock_response
        )

        # Call the tool
        result = await simulate_mcp_call(
            mock_server,
            "chat-completion",
            {
                "query": "Test query",
                "stream": True,
                "model": "gpt-4",
                "temperature": 0.7,
                "indexUids": ["movies", "books"],
            },
        )

        # Verify the response
        assert result.content
        assert len(result.content) == 1
        assert result.content[0].type == "text"
        assert "Hello world" in result.content[0].text

    @pytest.mark.asyncio
    @patch("src.meilisearch_mcp.chat.httpx.Client")
    async def test_chat_completion_non_streaming(self, mock_client, mock_server):
        """Test non-streaming chat completion"""
        # Mock the response
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "This is a complete response"}}],
            "model": "gpt-4",
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        }
        mock_client.return_value.__enter__.return_value.post.return_value = (
            mock_response
        )

        # Call the tool
        result = await simulate_mcp_call(
            mock_server,
            "chat-completion",
            {"query": "Test query", "stream": False, "model": "gpt-4"},
        )

        # Verify the response
        assert len(result.content) == 1
        assert result.content[0].type == "text"
        response_data = json.loads(result.content[0].text)
        assert "choices" in response_data
        assert (
            response_data["choices"][0]["message"]["content"]
            == "This is a complete response"
        )


class TestChatWorkspaces:
    """Test chat workspace management"""

    @pytest.mark.asyncio
    @patch("src.meilisearch_mcp.chat.httpx.Client")
    async def test_create_chat_workspace(self, mock_client, mock_server):
        """Test creating a chat workspace"""
        # Mock the response
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "uid": "support-chat",
            "name": "Customer Support",
            "description": "Workspace for customer support queries",
            "model": "gpt-4",
            "temperature": 0.5,
            "maxTokens": 1000,
            "indexUids": ["products", "faqs"],
            "createdAt": "2024-01-01T00:00:00Z",
            "updatedAt": "2024-01-01T00:00:00Z",
        }
        mock_client.return_value.__enter__.return_value.post.return_value = (
            mock_response
        )

        # Call the tool
        result = await simulate_mcp_call(
            mock_server,
            "create-chat-workspace",
            {
                "uid": "support-chat",
                "name": "Customer Support",
                "description": "Workspace for customer support queries",
                "model": "gpt-4",
                "temperature": 0.5,
                "maxTokens": 1000,
                "indexUids": ["products", "faqs"],
            },
        )

        # Verify the response
        assert len(result.content) == 1
        assert result.content[0].type == "text"
        assert "Chat workspace created" in result.content[0].text
        assert "support-chat" in result.content[0].text

    @pytest.mark.asyncio
    @patch("src.meilisearch_mcp.chat.httpx.Client")
    async def test_update_chat_workspace(self, mock_client, mock_server):
        """Test updating a chat workspace"""
        # Mock the response
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "uid": "support-chat",
            "name": "Updated Customer Support",
            "temperature": 0.7,
            "updatedAt": "2024-01-02T00:00:00Z",
        }
        mock_client.return_value.__enter__.return_value.patch.return_value = (
            mock_response
        )

        # Call the tool
        result = await simulate_mcp_call(
            mock_server,
            "update-chat-workspace",
            {
                "uid": "support-chat",
                "name": "Updated Customer Support",
                "temperature": 0.7,
            },
        )

        # Verify the response
        assert len(result.content) == 1
        assert result.content[0].type == "text"
        assert "Chat workspace updated" in result.content[0].text
        assert "Updated Customer Support" in result.content[0].text

    @pytest.mark.asyncio
    @patch("src.meilisearch_mcp.chat.httpx.Client")
    async def test_list_chat_workspaces(self, mock_client, mock_server):
        """Test listing chat workspaces"""
        # Mock the response
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {"uid": "support-chat", "name": "Customer Support"},
                {"uid": "sales-chat", "name": "Sales Assistant"},
            ],
            "offset": 0,
            "limit": 20,
            "total": 2,
        }
        mock_client.return_value.__enter__.return_value.get.return_value = mock_response

        # Call the tool
        result = await simulate_mcp_call(
            mock_server, "list-chat-workspaces", {"limit": 10, "offset": 0}
        )

        # Verify the response
        assert len(result.content) == 1
        assert result.content[0].type == "text"
        assert "Chat workspaces" in result.content[0].text
        response_data = json.loads(
            result.content[0].text.replace("Chat workspaces: ", "")
        )
        assert len(response_data["results"]) == 2

    @pytest.mark.asyncio
    @patch("src.meilisearch_mcp.chat.httpx.Client")
    async def test_get_chat_workspace(self, mock_client, mock_server):
        """Test getting a specific chat workspace"""
        # Mock the response
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "uid": "support-chat",
            "name": "Customer Support",
            "description": "Workspace for customer support queries",
            "model": "gpt-4",
            "temperature": 0.5,
            "maxTokens": 1000,
            "indexUids": ["products", "faqs"],
        }
        mock_client.return_value.__enter__.return_value.get.return_value = mock_response

        # Call the tool
        result = await simulate_mcp_call(
            mock_server, "get-chat-workspace", {"uid": "support-chat"}
        )

        # Verify the response
        assert len(result.content) == 1
        assert result.content[0].type == "text"
        assert "Chat workspace" in result.content[0].text
        assert "support-chat" in result.content[0].text

    @pytest.mark.asyncio
    @patch("src.meilisearch_mcp.chat.httpx.Client")
    async def test_delete_chat_workspace(self, mock_client, mock_server):
        """Test deleting a chat workspace"""
        # Mock the response
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "taskUid": 12345,
            "status": "enqueued",
            "type": "workspaceDeletion",
        }
        mock_client.return_value.__enter__.return_value.delete.return_value = (
            mock_response
        )

        # Call the tool
        result = await simulate_mcp_call(
            mock_server, "delete-chat-workspace", {"uid": "support-chat"}
        )

        # Verify the response
        assert len(result.content) == 1
        assert result.content[0].type == "text"
        assert "Chat workspace deleted" in result.content[0].text


class TestChatErrorHandling:
    """Test error handling in chat features"""

    @pytest.mark.asyncio
    @patch("src.meilisearch_mcp.chat.httpx.Client")
    async def test_chat_completion_error(self, mock_client, mock_server):
        """Test error handling in chat completion"""
        # Mock an error response
        mock_client.return_value.__enter__.return_value.post.side_effect = Exception(
            "API Error"
        )

        # Call the tool
        result = await simulate_mcp_call(
            mock_server, "chat-completion", {"query": "Test query", "stream": False}
        )

        # Verify error handling
        assert len(result.content) == 1
        assert result.content[0].type == "text"
        assert "Error" in result.content[0].text

    @pytest.mark.asyncio
    @patch("src.meilisearch_mcp.chat.httpx.AsyncClient")
    async def test_streaming_error(self, mock_async_client, mock_server):
        """Test error handling in streaming"""
        # Mock an error during streaming
        mock_async_client.return_value.__aenter__.return_value.stream.side_effect = (
            Exception("Streaming Error")
        )

        # Call the tool
        result = await simulate_mcp_call(
            mock_server, "chat-completion", {"query": "Test query", "stream": True}
        )

        # Verify error handling
        assert len(result.content) == 1
        assert result.content[0].type == "text"
        assert "Error" in result.content[0].text
