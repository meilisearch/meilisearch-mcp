import httpx
from meilisearch import Client
from typing import Optional, Dict, Any, List

from .indexes import IndexManager
from .documents import DocumentManager
from .tasks import TaskManager
from .settings import SettingsManager
from .templates import ConfigTemplates
from .keys import KeyManager
from .logging import MCPLogger
from .monitoring import MonitoringManager

logger = MCPLogger()


class MeilisearchClient:
    def __init__(
        self, url: str = "http://localhost:7700", api_key: Optional[str] = None
    ):
        """Initialize Meilisearch client"""
        self.url = url
        self.api_key = api_key
        self.client = Client(url, api_key)
        self.indexes = IndexManager(self.client)
        self.documents = DocumentManager(self.client)
        self.settings = SettingsManager(self.client)
        self.templates = ConfigTemplates()
        self.tasks = TaskManager(self.client)
        self.keys = KeyManager(self.client)
        self.monitoring = MonitoringManager(self.client)

    async def health_check(self) -> bool:
        """Check if Meilisearch is healthy"""
        try:
            response = self.client.health()
            return response.get("status") == "available"
        except Exception:
            return False

    async def get_version(self) -> Dict[str, Any]:
        """Get Meilisearch version information"""
        return self.client.get_version()

    async def get_stats(self) -> Dict[str, Any]:
        """Get database stats"""
        # return self.client.get_stats()
        return "This method has not yet been implemented in the Meilisearch client."

    async def get_indexes(self) -> Dict[str, Any]:
        """Get all indexes"""
        indexes = self.client.get_indexes()
        # Convert Index objects to serializable dictionaries
        serialized_indexes = []
        for index in indexes["results"]:
            serialized_indexes.append(
                {
                    "uid": index.uid,
                    "primaryKey": index.primary_key,
                    "createdAt": index.created_at,
                    "updatedAt": index.updated_at,
                }
            )

        return {
            "results": serialized_indexes,
            "offset": indexes["offset"],
            "limit": indexes["limit"],
            "total": indexes["total"],
        }
