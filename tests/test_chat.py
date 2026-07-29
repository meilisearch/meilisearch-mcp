import pytest
from datetime import datetime
from unittest.mock import MagicMock, Mock
from meilisearch.errors import MeilisearchApiError

from src.meilisearch_mcp.server import MeilisearchMCPServer


@pytest.fixture
def server():
    return MeilisearchMCPServer(url="http://localhost:7700", api_key="test_key")


@pytest.fixture
def setup_mock_chat_client(server):
    """Mock the Meilisearch client for chat-related methods"""
    # Create a mock client with chat methods
    mock_client = MagicMock()

    # Mock create_chat_completion to return an iterator
    def mock_chat_completion(*args, **kwargs):
        # Simulate streaming response chunks
        chunks = [
            {"choices": [{"delta": {"content": "This is "}}]},
            {"choices": [{"delta": {"content": "a test "}}]},
            {"choices": [{"delta": {"content": "response."}}]},
        ]
        for chunk in chunks:
            yield chunk

    mock_client.create_chat_completion = mock_chat_completion

    # Mock get_chat_workspaces
    mock_client.get_chat_workspaces.return_value = {
        "results": [
            {"uid": "workspace1", "name": "Customer Support"},
            {"uid": "workspace2", "name": "Documentation"},
        ],
        "limit": 10,
        "offset": 0,
        "total": 2,
    }

    # Mock get_chat_workspace_settings
    mock_client.get_chat_workspace_settings.return_value = {
        "model": "gpt-3.5-turbo",
        "indexUids": ["products", "docs"],
        "temperature": 0.7,
    }

    # Mock update_chat_workspace_settings
    mock_client.update_chat_workspace_settings.return_value = {
        "model": "gpt-4",
        "indexUids": ["products", "docs"],
        "temperature": 0.5,
    }

    # Replace the chat manager's client
    server.chat_manager.client = mock_client
    return server


class TestChatTools:
    @pytest.mark.asyncio
    async def test_create_chat_completion(self, setup_mock_chat_client):
        """Test creating a chat completion"""
        server = setup_mock_chat_client

        # Simulate the tool call
        result = await server.chat_manager.create_chat_completion(
            workspace_uid="test-workspace",
            messages=[
                {"role": "user", "content": "What is Meilisearch?"},
            ],
            model="gpt-3.5-turbo",
            stream=True,
        )

        # The result should be the combined response
        assert result == "This is a test response."

    @pytest.mark.asyncio
    async def test_get_chat_workspaces(self, setup_mock_chat_client):
        """Test getting chat workspaces"""
        server = setup_mock_chat_client

        result = await server.chat_manager.get_chat_workspaces(offset=0, limit=10)

        assert "results" in result
        assert len(result["results"]) == 2
        assert result["results"][0]["uid"] == "workspace1"
        assert result["total"] == 2

    @pytest.mark.asyncio
    async def test_get_chat_workspace_settings(self, setup_mock_chat_client):
        """Test getting chat workspace settings"""
        server = setup_mock_chat_client

        result = await server.chat_manager.get_chat_workspace_settings(
            workspace_uid="workspace1"
        )

        assert result["model"] == "gpt-3.5-turbo"
        assert "indexUids" in result
        assert result["temperature"] == 0.7

    @pytest.mark.asyncio
    async def test_update_chat_workspace_settings(self, setup_mock_chat_client):
        """Test updating chat workspace settings"""
        server = setup_mock_chat_client

        result = await server.chat_manager.update_chat_workspace_settings(
            workspace_uid="workspace1",
            settings={"model": "gpt-4", "temperature": 0.5},
        )

        assert result["model"] == "gpt-4"
        assert result["temperature"] == 0.5

    @pytest.mark.asyncio
    async def test_chat_completion_error_handling(self, server):
        """Test error handling in chat completion"""
        # Mock the client to raise an error
        server.chat_manager.client = MagicMock()
        # Create a mock request object for the error with proper JSON text
        mock_request = MagicMock()
        mock_request.status_code = 400
        mock_request.text = '{"message": "Chat feature not enabled", "code": "chat_not_enabled", "type": "invalid_request", "link": "https://docs.meilisearch.com/errors#chat_not_enabled"}'
        server.chat_manager.client.create_chat_completion.side_effect = (
            MeilisearchApiError("Chat feature not enabled", mock_request)
        )

        with pytest.raises(MeilisearchApiError):
            await server.chat_manager.create_chat_completion(
                workspace_uid="test",
                messages=[{"role": "user", "content": "test"}],
            )

    @pytest.mark.asyncio
    async def test_empty_chat_response(self, server):
        """Test handling empty chat response"""
        # Mock empty response
        server.chat_manager.client = MagicMock()

        def mock_empty_completion(*args, **kwargs):
            # Return empty chunks
            return iter([])

        server.chat_manager.client.create_chat_completion = mock_empty_completion

        result = await server.chat_manager.create_chat_completion(
            workspace_uid="test",
            messages=[{"role": "user", "content": "test"}],
        )

        assert result == ""  # Empty response should return empty string
