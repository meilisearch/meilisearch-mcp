import json
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import Field
from mcp.server import MCPServer
from mcp.types import CallToolResult, TextContent, ToolAnnotations

from .client import MeilisearchClient
from .chat import ChatManager
from .__version__ import __version__

logger = logging.getLogger(__name__)

READ_ONLY = ToolAnnotations(read_only_hint=True)
WRITE = ToolAnnotations(read_only_hint=False, destructive_hint=False)
DESTRUCTIVE = ToolAnnotations(read_only_hint=False, destructive_hint=True)


def json_serializer(obj: Any) -> str:
    """Custom JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    # Handle Meilisearch model objects by using their __dict__ if available
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    return str(obj)


def _data(obj: Any) -> Optional[Dict[str, Any]]:
    """Flatten Meilisearch model objects/datetimes into plain JSON data for
    structured tool output. Non-dict results are wrapped in {"result": ...}."""
    plain = json.loads(json.dumps(obj, default=json_serializer))
    if plain is None:
        return None
    return plain if isinstance(plain, dict) else {"result": plain}


def _result(text: str, data: Any = None) -> CallToolResult:
    """Build a tool result with legacy text content plus structured output."""
    return CallToolResult(
        content=[TextContent(type="text", text=text)],
        structured_content=_data(data) if data is not None else None,
    )


def create_server(
    url: str = "http://localhost:7700", api_key: Optional[str] = None
) -> "MeilisearchMCPServer":
    """Create and return a configured MeilisearchMCPServer instance"""
    return MeilisearchMCPServer(url, api_key)


class MeilisearchMCPServer:
    def __init__(
        self,
        url: str = "http://localhost:7700",
        api_key: Optional[str] = None,
    ):
        """Initialize MCP server for Meilisearch"""
        self.url = url
        self.api_key = api_key
        self.meili_client = MeilisearchClient(url, api_key)
        self.chat_manager = ChatManager(self.meili_client.client)
        self.mcp = MCPServer("meilisearch", version=__version__)
        self._register_tools()

    def update_connection(
        self, url: Optional[str] = None, api_key: Optional[str] = None
    ):
        """Update connection settings and reinitialize client if needed"""
        if url:
            self.url = url
        if api_key:
            self.api_key = api_key

        self.meili_client = MeilisearchClient(self.url, self.api_key)
        self.chat_manager = ChatManager(self.meili_client.client)
        logger.info(f"Updated Meilisearch connection settings: url={self.url}")

    def _register_tools(self):
        """Register all MCP tools"""
        mcp = self.mcp

        @mcp.tool(name="get-connection-settings", annotations=READ_ONLY)
        def get_connection_settings() -> CallToolResult:
            """Get current Meilisearch connection settings"""
            return _result(
                f"Current connection settings:\nURL: {self.url}\nAPI Key: {'*' * 8 if self.api_key else 'Not set'}"
            )

        @mcp.tool(name="update-connection-settings", annotations=WRITE)
        def update_connection_settings(
            url: Optional[str] = None, api_key: Optional[str] = None
        ) -> CallToolResult:
            """Update Meilisearch connection settings"""
            self.update_connection(url, api_key)
            return _result(
                f"Successfully updated connection settings to URL: {self.url}"
            )

        @mcp.tool(name="health-check", annotations=READ_ONLY)
        def health_check() -> CallToolResult:
            """Check Meilisearch server health"""
            is_healthy = self.meili_client.health_check()
            return _result(
                f"Meilisearch is {is_healthy and 'available' or 'unavailable'}"
            )

        @mcp.tool(name="get-version", annotations=READ_ONLY)
        def get_version() -> CallToolResult:
            """Get Meilisearch version information"""
            version = self.meili_client.get_version()
            return _result(f"Version info: {version}", version)

        @mcp.tool(name="get-stats", annotations=READ_ONLY)
        def get_stats() -> CallToolResult:
            """Get database statistics"""
            stats = self.meili_client.get_stats()
            return _result(f"Database stats: {stats}", stats)

        @mcp.tool(name="create-index", annotations=WRITE)
        def create_index(uid: str, primaryKey: Optional[str] = None) -> CallToolResult:
            """Create a new Meilisearch index"""
            result = self.meili_client.indexes.create_index(uid, primaryKey)
            return _result(f"Created index: {result}", result)

        @mcp.tool(name="list-indexes", annotations=READ_ONLY)
        def list_indexes() -> CallToolResult:
            """List all Meilisearch indexes"""
            indexes = self.meili_client.get_indexes()
            formatted_json = json.dumps(indexes, indent=2, default=json_serializer)
            return _result(f"Indexes:\n{formatted_json}", indexes)

        @mcp.tool(name="delete-index", annotations=DESTRUCTIVE)
        def delete_index(uid: str) -> CallToolResult:
            """Delete a Meilisearch index"""
            self.meili_client.indexes.delete_index(uid)
            return _result(f"Successfully deleted index: {uid}")

        @mcp.tool(name="get-documents", annotations=READ_ONLY)
        def get_documents(
            indexUid: str, offset: int = 0, limit: int = 20
        ) -> CallToolResult:
            """Get documents from an index"""
            documents = self.meili_client.documents.get_documents(
                indexUid, offset, limit
            )
            formatted_json = json.dumps(documents, indent=2, default=json_serializer)
            return _result(f"Documents:\n{formatted_json}", documents)

        @mcp.tool(name="add-documents", annotations=WRITE)
        def add_documents(
            indexUid: str,
            documents: List[Dict[str, Any]],
            primaryKey: Optional[str] = None,
        ) -> CallToolResult:
            """Add documents to an index"""
            result = self.meili_client.documents.add_documents(
                indexUid, documents, primaryKey
            )
            return _result(f"Added documents: {result}", result)

        @mcp.tool(name="get-settings", annotations=READ_ONLY)
        def get_settings(indexUid: str) -> CallToolResult:
            """Get current settings for an index"""
            settings = self.meili_client.settings.get_settings(indexUid)
            return _result(f"Current settings: {settings}", settings)

        @mcp.tool(name="update-settings", annotations=WRITE)
        def update_settings(indexUid: str, settings: Dict[str, Any]) -> CallToolResult:
            """Update settings for an index"""
            result = self.meili_client.settings.update_settings(indexUid, settings)
            return _result(f"Settings updated: {result}", result)

        @mcp.tool(name="search", annotations=READ_ONLY)
        def search(
            query: str,
            indexUid: Optional[str] = None,
            limit: Optional[int] = None,
            offset: Optional[int] = None,
            filter: Optional[str] = None,
            sort: Optional[List[str]] = None,
            hybrid: Optional[Dict[str, Any]] = None,
        ) -> CallToolResult:
            """Search through Meilisearch indices. If indexUid is not provided, it will search across all indices."""
            search_results = self.meili_client.search(
                query=query,
                index_uid=indexUid,
                limit=limit,
                offset=offset,
                filter=filter,
                sort=sort,
                hybrid=hybrid,
            )
            formatted_results = json.dumps(
                search_results, indent=2, default=json_serializer
            )
            return _result(
                f"Search results for '{query}':\n{formatted_results}", search_results
            )

        @mcp.tool(name="get-task", annotations=READ_ONLY)
        def get_task(taskUid: int) -> CallToolResult:
            """Get information about a specific task"""
            task = self.meili_client.tasks.get_task(taskUid)
            return _result(f"Task information: {task}", task)

        @mcp.tool(name="get-tasks", annotations=READ_ONLY)
        def get_tasks(
            limit: Optional[int] = None,
            from_: Optional[int] = Field(default=None, validation_alias="from"),
            reverse: Optional[bool] = None,
            batchUids: Optional[List[str]] = None,
            uids: Optional[List[int]] = None,
            canceledBy: Optional[List[str]] = None,
            types: Optional[List[str]] = None,
            statuses: Optional[List[str]] = None,
            indexUids: Optional[List[str]] = None,
            afterEnqueuedAt: Optional[str] = None,
            beforeEnqueuedAt: Optional[str] = None,
            afterStartedAt: Optional[str] = None,
            beforeStartedAt: Optional[str] = None,
            afterFinishedAt: Optional[str] = None,
            beforeFinishedAt: Optional[str] = None,
        ) -> CallToolResult:
            """Get list of tasks with optional filters"""
            params = {
                "limit": limit,
                "from": from_,
                "reverse": reverse,
                "batchUids": batchUids,
                "uids": uids,
                "canceledBy": canceledBy,
                "types": types,
                "statuses": statuses,
                "indexUids": indexUids,
                "afterEnqueuedAt": afterEnqueuedAt,
                "beforeEnqueuedAt": beforeEnqueuedAt,
                "afterStartedAt": afterStartedAt,
                "beforeStartedAt": beforeStartedAt,
                "afterFinishedAt": afterFinishedAt,
                "beforeFinishedAt": beforeFinishedAt,
            }
            filtered = {k: v for k, v in params.items() if v is not None}
            tasks = self.meili_client.tasks.get_tasks(filtered)
            return _result(f"Tasks: {tasks}", tasks)

        @mcp.tool(name="cancel-tasks", annotations=DESTRUCTIVE)
        def cancel_tasks(
            uids: Optional[str] = None,
            indexUids: Optional[str] = None,
            types: Optional[str] = None,
            statuses: Optional[str] = None,
        ) -> CallToolResult:
            """Cancel tasks based on filters"""
            params = {
                "uids": uids,
                "indexUids": indexUids,
                "types": types,
                "statuses": statuses,
            }
            filtered = {k: v for k, v in params.items() if v is not None}
            result = self.meili_client.tasks.cancel_tasks(filtered)
            return _result(f"Tasks cancelled: {result}", result)

        @mcp.tool(name="get-keys", annotations=READ_ONLY)
        def get_keys(
            offset: Optional[int] = None, limit: Optional[int] = None
        ) -> CallToolResult:
            """Get list of API keys"""
            params = {"offset": offset, "limit": limit}
            filtered = {k: v for k, v in params.items() if v is not None}
            keys = self.meili_client.keys.get_keys(filtered)
            return _result(f"API keys: {keys}", keys)

        @mcp.tool(name="create-key", annotations=WRITE)
        def create_key(
            actions: List[str],
            indexes: List[str],
            description: Optional[str] = None,
            expiresAt: Optional[str] = None,
        ) -> CallToolResult:
            """Create a new API key"""
            key = self.meili_client.keys.create_key(
                {
                    "description": description,
                    "actions": actions,
                    "indexes": indexes,
                    "expiresAt": expiresAt,
                }
            )
            return _result(f"Created API key: {key}", key)

        @mcp.tool(name="delete-key", annotations=DESTRUCTIVE)
        def delete_key(key: str) -> CallToolResult:
            """Delete an API key"""
            self.meili_client.keys.delete_key(key)
            return _result(f"Successfully deleted API key: {key}")

        @mcp.tool(name="get-health-status", annotations=READ_ONLY)
        def get_health_status() -> CallToolResult:
            """Get comprehensive health status of Meilisearch"""
            status = self.meili_client.monitoring.get_health_status()
            return _result(
                f"Health status: {json.dumps(status.__dict__, default=json_serializer)}",
                status.__dict__,
            )

        @mcp.tool(name="get-index-metrics", annotations=READ_ONLY)
        def get_index_metrics(indexUid: str) -> CallToolResult:
            """Get detailed metrics for an index"""
            metrics = self.meili_client.monitoring.get_index_metrics(indexUid)
            return _result(
                f"Index metrics: {json.dumps(metrics.__dict__, default=json_serializer)}",
                metrics.__dict__,
            )

        @mcp.tool(name="get-system-info", annotations=READ_ONLY)
        def get_system_info() -> CallToolResult:
            """Get system-level information"""
            info = self.meili_client.monitoring.get_system_information()
            return _result(f"System information: {info}", info)

        @mcp.tool(name="create-chat-completion", annotations=WRITE)
        async def create_chat_completion(
            workspace_uid: str = Field(
                description="Unique identifier of the chat workspace"
            ),
            messages: List[Dict[str, Any]] = Field(
                description="List of message objects comprising the chat history"
            ),
            model: str = Field(
                default="gpt-3.5-turbo", description="The model to use for completion"
            ),
            stream: bool = Field(
                default=True,
                description="Whether to stream the response (currently must be true)",
            ),
        ) -> CallToolResult:
            """Create a conversational chat completion using Meilisearch's chat feature"""
            response = await self.chat_manager.create_chat_completion(
                workspace_uid=workspace_uid,
                messages=messages,
                model=model,
                stream=stream,
            )
            return _result(f"Chat completion response:\n{response}")

        @mcp.tool(name="get-chat-workspaces", annotations=READ_ONLY)
        async def get_chat_workspaces(
            offset: Optional[int] = Field(
                default=None, description="Number of workspaces to skip"
            ),
            limit: Optional[int] = Field(
                default=None, description="Maximum number of workspaces to return"
            ),
        ) -> CallToolResult:
            """Get list of available chat workspaces"""
            workspaces = await self.chat_manager.get_chat_workspaces(
                offset=offset, limit=limit
            )
            formatted_json = json.dumps(workspaces, indent=2, default=json_serializer)
            return _result(f"Chat workspaces:\n{formatted_json}", workspaces)

        @mcp.tool(name="get-chat-workspace-settings", annotations=READ_ONLY)
        async def get_chat_workspace_settings(
            workspace_uid: str = Field(
                description="Unique identifier of the chat workspace"
            ),
        ) -> CallToolResult:
            """Get settings for a specific chat workspace"""
            settings = await self.chat_manager.get_chat_workspace_settings(
                workspace_uid=workspace_uid
            )
            formatted_json = json.dumps(settings, indent=2, default=json_serializer)
            return _result(
                f"Workspace settings for '{workspace_uid}':\n{formatted_json}", settings
            )

        @mcp.tool(name="update-chat-workspace-settings", annotations=WRITE)
        async def update_chat_workspace_settings(
            workspace_uid: str = Field(
                description="Unique identifier of the chat workspace"
            ),
            settings: Dict[str, Any] = Field(
                description="Settings to update for the workspace"
            ),
        ) -> CallToolResult:
            """Update settings for a specific chat workspace"""
            updated_settings = await self.chat_manager.update_chat_workspace_settings(
                workspace_uid=workspace_uid, settings=settings
            )
            formatted_json = json.dumps(
                updated_settings, indent=2, default=json_serializer
            )
            return _result(
                f"Updated workspace settings for '{workspace_uid}':\n{formatted_json}",
                updated_settings,
            )

        # Keep additionalProperties: false on all schemas for OpenAI Agent SDK
        # compatibility (issue #27). ponytail: reaches into the private tool
        # manager because the SDK has no public schema hook; revisit if v2 grows one.
        for tool in mcp._tool_manager.list_tools():
            tool.parameters["additionalProperties"] = False

    def run(self):
        """Run the MCP server over stdio"""
        logger.info("Starting Meilisearch MCP server...")
        self.mcp.run(transport="stdio")

    def cleanup(self):
        """Clean shutdown"""
        logger.info("Shutting down MCP server")


def main():
    """Main entry point"""
    logging.basicConfig(level=logging.INFO, stream=sys.stderr)
    url = os.getenv("MEILI_HTTP_ADDR", "http://localhost:7700")
    api_key = os.getenv("MEILI_MASTER_KEY")

    server = create_server(url, api_key)
    server.run()


if __name__ == "__main__":
    main()
