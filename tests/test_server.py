import pytest
from src.meilisearch_mcp.server import create_server


def test_server_creation():
    """Test that we can create a server instance"""
    server = create_server()
    assert server is not None
    assert server.meili_client is not None
