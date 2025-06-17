import pytest
from unittest.mock import patch, MagicMock
from src.meilisearch_mcp.client import MeilisearchClient
from src.meilisearch_mcp.__version__ import __version__


def test_meilisearch_client_sets_custom_user_agent():
    """
    Verifies that MeilisearchClient sets a custom user agent string during initialization.
    
    This test ensures that the internal Client is instantiated with the correct URL, API key, and a client_agents tuple containing the package name and version.
    """
    with patch("src.meilisearch_mcp.client.Client") as mock_client:
        # Create a MeilisearchClient instance
        client = MeilisearchClient(url="http://localhost:7700", api_key="test_key")

        # Verify that Client was called with the correct parameters
        mock_client.assert_called_once_with(
            "http://localhost:7700",
            "test_key",
            client_agents=("meilisearch-mcp", f"v{__version__}"),
        )


def test_user_agent_includes_correct_version():
    """
    Verifies that MeilisearchClient sets the user agent to include the correct version string.
    
    This test ensures that the internal client is initialized with a user agent tuple containing the package name and the version string from the __version__ module.
    """
    with patch("src.meilisearch_mcp.client.Client") as mock_client:
        client = MeilisearchClient()

        # Extract the client_agents parameter from the call
        call_args = mock_client.call_args
        client_agents = call_args[1]["client_agents"]

        # Verify format and version
        assert client_agents[0] == "meilisearch-mcp"
        assert client_agents[1] == "v0.5.0"
        assert client_agents[1] == f"v{__version__}"
