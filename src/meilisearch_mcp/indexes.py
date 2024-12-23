from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from meilisearch import Client


@dataclass
class IndexConfig:
    """Index configuration model"""

    uid: str
    primary_key: Optional[str] = None


class IndexManager:
    """Manage Meilisearch indexes"""

    def __init__(self, client: Client):
        self.client = client

    async def create_index(
        self, uid: str, primary_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new index"""
        try:
            return self.client.create_index(uid, {"primaryKey": primary_key})
        except Exception as e:
            raise Exception(f"Failed to create index: {str(e)}")

    async def get_index(self, uid: str) -> Dict[str, Any]:
        """Get index information"""
        try:
            return self.client.get_index(uid)
        except Exception as e:
            raise Exception(f"Failed to get index: {str(e)}")

    async def list_indexes(self) -> List[Dict[str, Any]]:
        """List all indexes"""
        try:
            return self.client.get_indexes()
        except Exception as e:
            raise Exception(f"Failed to list indexes: {str(e)}")

    async def delete_index(self, uid: str) -> Dict[str, Any]:
        """Delete an index"""
        try:
            return self.client.delete_index(uid)
        except Exception as e:
            raise Exception(f"Failed to delete index: {str(e)}")

    async def update_index(self, uid: str, primary_key: str) -> Dict[str, Any]:
        """Update index primary key"""
        try:
            return self.client.update_index(uid, {"primaryKey": primary_key})
        except Exception as e:
            raise Exception(f"Failed to update index: {str(e)}")

    async def swap_indexes(self, indexes: List[List[str]]) -> Dict[str, Any]:
        """Swap indexes"""
        try:
            return self.client.swap_indexes(indexes)
        except Exception as e:
            raise Exception(f"Failed to swap indexes: {str(e)}")
