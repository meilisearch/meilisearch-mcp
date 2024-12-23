from typing import Dict, Any, List, Optional
from meilisearch import Client
from dataclasses import dataclass
from datetime import datetime
import json


@dataclass
class HealthStatus:
    """Detailed health status information"""

    is_healthy: bool
    database_size: int
    last_update: datetime
    indexes_count: int
    indexes_info: List[Dict[str, Any]]


@dataclass
class IndexMetrics:
    """Detailed index metrics"""

    number_of_documents: int
    field_distribution: Dict[str, int]
    is_indexing: bool
    index_size: Optional[int] = None


class MonitoringManager:
    """Enhanced monitoring and statistics for Meilisearch"""

    def __init__(self, client: Client):
        self.client = client

    async def get_health_status(self) -> HealthStatus:
        """Get comprehensive health status"""
        try:
            # Get various stats to build health picture
            stats = self.client.get_stats()
            indexes = self.client.get_indexes()

            indexes_info = []
            for index in indexes:
                index_stats = self.client.index(index.uid).get_stats()
                indexes_info.append(
                    {
                        "uid": index.uid,
                        "documents_count": index_stats["numberOfDocuments"],
                        "is_indexing": index_stats["isIndexing"],
                    }
                )

            return HealthStatus(
                is_healthy=True,
                database_size=stats["databaseSize"],
                last_update=datetime.fromisoformat(
                    stats["lastUpdate"].replace("Z", "+00:00")
                ),
                indexes_count=len(indexes),
                indexes_info=indexes_info,
            )
        except Exception as e:
            raise Exception(f"Failed to get health status: {str(e)}")

    async def get_index_metrics(self, index_uid: str) -> IndexMetrics:
        """Get detailed metrics for an index"""
        try:
            index = self.client.index(index_uid)
            stats = index.get_stats()

            return IndexMetrics(
                number_of_documents=stats["numberOfDocuments"],
                field_distribution=stats["fieldDistribution"],
                is_indexing=stats["isIndexing"],
                index_size=stats.get("indexSize"),
            )
        except Exception as e:
            raise Exception(f"Failed to get index metrics: {str(e)}")

    async def get_system_information(self) -> Dict[str, Any]:
        """Get system-level information"""
        try:
            version = self.client.get_version()
            stats = self.client.get_stats()

            return {
                "version": version,
                "database_size": stats["databaseSize"],
                "last_update": stats["lastUpdate"],
                "indexes": stats["indexes"],
            }
        except Exception as e:
            raise Exception(f"Failed to get system information: {str(e)}")
