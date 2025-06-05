import httpx
from meilisearch import Client
from typing import Optional, Dict, Any, List

from .indexes import IndexManager
from .documents import DocumentManager
from .tasks import TaskManager
from .settings import SettingsManager
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
        return self.client.get_all_stats()

    async def search(
        self,
        query: str,
        index_uid: Optional[str] = None,
        limit: Optional[int] = 20,
        offset: Optional[int] = 0,
        filter: Optional[str] = None,
        sort: Optional[List[str]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Search through Meilisearch indices.
        If index_uid is provided, search in that specific index.
        If not provided, search across all available indices.
        """
        try:
            # Prepare search parameters, removing None values
            search_params = {
                "limit": limit if limit is not None else 20,
                "offset": offset if offset is not None else 0,
            }

            if filter is not None:
                search_params["filter"] = filter
            if sort is not None:
                search_params["sort"] = sort

            # Add any additional parameters
            search_params.update({k: v for k, v in kwargs.items() if v is not None})

            if index_uid:
                # Search in specific index
                index = self.client.index(index_uid)
                return index.search(query, search_params)
            else:
                # Search across all indices
                results = {}
                indexes = self.client.get_indexes()

                for index in indexes["results"]:
                    try:
                        search_result = index.search(query, search_params)
                        if search_result["hits"]:  # Only include indices with matches
                            results[index.uid] = search_result
                    except Exception as e:
                        logger.warning(f"Failed to search index {index.uid}: {str(e)}")
                        continue

                return {"multi_index": True, "query": query, "results": results}

        except Exception as e:
            raise Exception(f"Search failed: {str(e)}")

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
