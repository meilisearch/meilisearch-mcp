from typing import Dict, Any, List, Optional
from meilisearch import Client
from datetime import datetime


class KeyManager:
    """Manage Meilisearch API keys"""

    def __init__(self, client: Client):
        self.client = client

    async def get_keys(
        self, parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get list of API keys"""
        try:
            return self.client.get_keys(parameters)
        except Exception as e:
            raise Exception(f"Failed to get keys: {str(e)}")

    async def get_key(self, key: str) -> Dict[str, Any]:
        """Get information about a specific key"""
        try:
            return self.client.get_key(key)
        except Exception as e:
            raise Exception(f"Failed to get key: {str(e)}")

    async def create_key(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new API key"""
        try:
            return self.client.create_key(options)
        except Exception as e:
            raise Exception(f"Failed to create key: {str(e)}")

    async def update_key(self, key: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing API key"""
        try:
            return self.client.update_key(key, options)
        except Exception as e:
            raise Exception(f"Failed to update key: {str(e)}")

    async def delete_key(self, key: str) -> None:
        """Delete an API key"""
        try:
            return self.client.delete_key(key)
        except Exception as e:
            raise Exception(f"Failed to delete key: {str(e)}")
