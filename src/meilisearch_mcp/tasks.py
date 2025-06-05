from typing import Dict, Any, List, Optional
from meilisearch import Client
from datetime import datetime


def serialize_task_results(obj: Any) -> Any:
    """Serialize task results into JSON-compatible format"""
    if hasattr(obj, "__dict__"):
        return {k: serialize_task_results(v) for k, v in obj.__dict__.items()}
    elif isinstance(obj, (list, tuple)):
        return [serialize_task_results(item) for item in obj]
    elif isinstance(obj, datetime):
        return obj.isoformat()
    return obj


class TaskManager:
    def __init__(self, client: Client):
        """Initialize TaskManager with Meilisearch client"""
        self.client = client

    async def get_task(self, task_uid: int) -> Dict[str, Any]:
        """Get information about a specific task"""
        try:
            task = self.client.get_task(task_uid)
            return serialize_task_results(task)
        except Exception as e:
            raise Exception(f"Failed to get task: {str(e)}")

    async def get_tasks(
        self, parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get list of tasks with optional filters"""
        try:
            tasks = self.client.get_tasks(parameters)
            return serialize_task_results(tasks)
        except Exception as e:
            raise Exception(f"Failed to get tasks: {str(e)}")

    async def cancel_tasks(self, query_parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Cancel tasks based on query parameters"""
        try:
            result = self.client.cancel_tasks(query_parameters)
            return serialize_task_results(result)
        except Exception as e:
            raise Exception(f"Failed to cancel tasks: {str(e)}")

    async def delete_tasks(self, query_parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Delete tasks based on query parameters"""
        try:
            result = self.client.delete_tasks(query_parameters)
            return serialize_task_results(result)
        except Exception as e:
            raise Exception(f"Failed to delete tasks: {str(e)}")
