from typing import Dict, Any, List, Optional
from meilisearch import Client


class TaskManager:
    """Manage Meilisearch tasks"""

    def __init__(self, client: Client):
        self.client = client

    async def get_task(self, task_uid: int) -> Dict[str, Any]:
        """Get information about a specific task"""
        try:
            return self.client.get_task(task_uid)
        except Exception as e:
            raise Exception(f"Failed to get task: {str(e)}")

    async def get_tasks(
        self, parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get list of tasks with optional filters"""
        try:
            return self.client.get_tasks(parameters)
        except Exception as e:
            raise Exception(f"Failed to get tasks: {str(e)}")

    async def cancel_tasks(self, query_parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Cancel tasks based on query parameters"""
        try:
            return self.client.cancel_tasks(query_parameters)
        except Exception as e:
            raise Exception(f"Failed to cancel tasks: {str(e)}")

    async def delete_tasks(self, query_parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Delete tasks based on query parameters"""
        try:
            return self.client.delete_tasks(query_parameters)
        except Exception as e:
            raise Exception(f"Failed to delete tasks: {str(e)}")
