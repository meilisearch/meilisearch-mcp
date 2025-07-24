import asyncio
import json
import os
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
import mcp.types as types
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio

from .client import MeilisearchClient
from .logging import MCPLogger

logger = MCPLogger()


def json_serializer(obj: Any) -> str:
    """Custom JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    # Handle Meilisearch model objects by using their __dict__ if available
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    return str(obj)


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
        log_dir: Optional[str] = None,
    ):
        """Initialize MCP server for Meilisearch"""
        # Set up logging directory
        if not log_dir:
            log_dir = os.path.expanduser("~/.meilisearch-mcp/logs")

        self.logger = MCPLogger("meilisearch-mcp", log_dir)
        self.url = url
        self.api_key = api_key
        self.meili_client = MeilisearchClient(url, api_key)
        self.server = Server("meilisearch")
        self._setup_handlers()

    def update_connection(
        self, url: Optional[str] = None, api_key: Optional[str] = None
    ):
        """Update connection settings and reinitialize client if needed"""
        if url:
            self.url = url
        if api_key:
            self.api_key = api_key

        self.meili_client = MeilisearchClient(self.url, self.api_key)
        self.logger.info("Updated Meilisearch connection settings", url=self.url)

    def _setup_handlers(self):
        """Setup MCP request handlers"""

        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            """List available tools"""
            return [
                types.Tool(
                    name="get-connection-settings",
                    description="Get current Meilisearch connection settings",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False,
                    },
                ),
                types.Tool(
                    name="update-connection-settings",
                    description="Update Meilisearch connection settings",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "url": {"type": "string"},
                            "api_key": {"type": "string"},
                        },
                        "additionalProperties": False,
                    },
                ),
                types.Tool(
                    name="health-check",
                    description="Check Meilisearch server health",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False,
                    },
                ),
                types.Tool(
                    name="get-version",
                    description="Get Meilisearch version information",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False,
                    },
                ),
                types.Tool(
                    name="get-stats",
                    description="Get database statistics",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False,
                    },
                ),
                types.Tool(
                    name="create-index",
                    description="Create a new Meilisearch index",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "uid": {"type": "string"},
                            "primaryKey": {"type": "string"},
                        },
                        "required": ["uid"],
                        "additionalProperties": False,
                    },
                ),
                types.Tool(
                    name="list-indexes",
                    description="List all Meilisearch indexes",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False,
                    },
                ),
                types.Tool(
                    name="delete-index",
                    description="Delete a Meilisearch index",
                    inputSchema={
                        "type": "object",
                        "properties": {"uid": {"type": "string"}},
                        "required": ["uid"],
                        "additionalProperties": False,
                    },
                ),
                types.Tool(
                    name="get-documents",
                    description="Get documents from an index",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "indexUid": {"type": "string"},
                            "offset": {"type": "integer"},
                            "limit": {"type": "integer"},
                        },
                        "required": ["indexUid"],
                        "additionalProperties": False,
                    },
                ),
                types.Tool(
                    name="add-documents",
                    description="Add documents to an index",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "indexUid": {"type": "string"},
                            "documents": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "additionalProperties": True,
                                },
                            },
                            "primaryKey": {"type": "string"},
                        },
                        "required": ["indexUid", "documents"],
                        "additionalProperties": False,
                    },
                ),
                types.Tool(
                    name="get-settings",
                    description="Get current settings for an index",
                    inputSchema={
                        "type": "object",
                        "properties": {"indexUid": {"type": "string"}},
                        "required": ["indexUid"],
                        "additionalProperties": False,
                    },
                ),
                types.Tool(
                    name="update-settings",
                    description="Update settings for an index",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "indexUid": {"type": "string"},
                            "settings": {
                                "type": "object",
                                "additionalProperties": True,
                            },
                        },
                        "required": ["indexUid", "settings"],
                        "additionalProperties": False,
                    },
                ),
                types.Tool(
                    name="search",
                    description="Search through Meilisearch indices. If indexUid is not provided, it will search across all indices.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                            "indexUid": {"type": "string"},
                            "limit": {"type": "integer"},
                            "offset": {"type": "integer"},
                            "filter": {"type": "string"},
                            "sort": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                        "required": ["query"],
                        "additionalProperties": False,
                    },
                ),
                types.Tool(
                    name="get-task",
                    description="Get information about a specific task",
                    inputSchema={
                        "type": "object",
                        "properties": {"taskUid": {"type": "integer"}},
                        "required": ["taskUid"],
                        "additionalProperties": False,
                    },
                ),
                types.Tool(
                    name="get-tasks",
                    description="Get list of tasks with optional filters",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "limit": {"type": "integer"},
                            "from": {"type": "integer"},
                            "reverse": {"type": "boolean"},
                            "batchUids": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "uids": {
                                "type": "array",
                                "items": {"type": "integer"},
                            },
                            "canceledBy": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "types": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "statuses": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "indexUids": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "afterEnqueuedAt": {"type": "string"},
                            "beforeEnqueuedAt": {"type": "string"},
                            "afterStartedAt": {"type": "string"},
                            "beforeStartedAt": {"type": "string"},
                            "afterFinishedAt": {"type": "string"},
                            "beforeFinishedAt": {"type": "string"},
                        },
                        "additionalProperties": False,
                    },
                ),
                types.Tool(
                    name="cancel-tasks",
                    description="Cancel tasks based on filters",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "uids": {"type": "string"},
                            "indexUids": {"type": "string"},
                            "types": {"type": "string"},
                            "statuses": {"type": "string"},
                        },
                        "additionalProperties": False,
                    },
                ),
                types.Tool(
                    name="get-keys",
                    description="Get list of API keys",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "offset": {"type": "integer"},
                            "limit": {"type": "integer"},
                        },
                        "additionalProperties": False,
                    },
                ),
                types.Tool(
                    name="create-key",
                    description="Create a new API key",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "description": {"type": "string"},
                            "actions": {"type": "array", "items": {"type": "string"}},
                            "indexes": {"type": "array", "items": {"type": "string"}},
                            "expiresAt": {"type": "string"},
                        },
                        "required": ["actions", "indexes"],
                        "additionalProperties": False,
                    },
                ),
                types.Tool(
                    name="delete-key",
                    description="Delete an API key",
                    inputSchema={
                        "type": "object",
                        "properties": {"key": {"type": "string"}},
                        "required": ["key"],
                        "additionalProperties": False,
                    },
                ),
                types.Tool(
                    name="get-health-status",
                    description="Get comprehensive health status of Meilisearch",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False,
                    },
                ),
                types.Tool(
                    name="get-index-metrics",
                    description="Get detailed metrics for an index",
                    inputSchema={
                        "type": "object",
                        "properties": {"indexUid": {"type": "string"}},
                        "required": ["indexUid"],
                        "additionalProperties": False,
                    },
                ),
                types.Tool(
                    name="get-system-info",
                    description="Get system-level information",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "additionalProperties": False,
                    },
                ),
            ]

        @self.server.call_tool()
        async def handle_call_tool(
            name: str, arguments: Optional[Dict[str, Any]] = None
        ) -> list[types.TextContent]:
            """Handle tool execution"""
            try:
                if name == "get-connection-settings":
                    return [
                        types.TextContent(
                            type="text",
                            text=f"Current connection settings:\nURL: {self.url}\nAPI Key: {'*' * 8 if self.api_key else 'Not set'}",
                        )
                    ]

                elif name == "update-connection-settings":
                    self.update_connection(
                        arguments.get("url"), arguments.get("api_key")
                    )
                    return [
                        types.TextContent(
                            type="text",
                            text=f"Successfully updated connection settings to URL: {self.url}",
                        )
                    ]

                elif name == "create-index":
                    result = self.meili_client.indexes.create_index(
                        arguments["uid"], arguments.get("primaryKey")
                    )
                    return [
                        types.TextContent(type="text", text=f"Created index: {result}")
                    ]

                elif name == "list-indexes":
                    indexes = self.meili_client.get_indexes()
                    formatted_json = json.dumps(
                        indexes, indent=2, default=json_serializer
                    )
                    return [
                        types.TextContent(
                            type="text", text=f"Indexes:\n{formatted_json}"
                        )
                    ]

                elif name == "delete-index":
                    result = self.meili_client.indexes.delete_index(arguments["uid"])
                    return [
                        types.TextContent(
                            type="text",
                            text=f"Successfully deleted index: {arguments['uid']}",
                        )
                    ]

                elif name == "get-documents":
                    # Use default values to fix None parameter issues (related to issue #17)
                    offset = arguments.get("offset", 0)
                    limit = arguments.get("limit", 20)
                    documents = self.meili_client.documents.get_documents(
                        arguments["indexUid"],
                        offset,
                        limit,
                    )
                    # Convert DocumentsResults object to proper JSON format (fixes issue #16)
                    formatted_json = json.dumps(
                        documents, indent=2, default=json_serializer
                    )
                    return [
                        types.TextContent(
                            type="text", text=f"Documents:\n{formatted_json}"
                        )
                    ]

                elif name == "add-documents":
                    result = self.meili_client.documents.add_documents(
                        arguments["indexUid"],
                        arguments["documents"],
                        arguments.get("primaryKey"),
                    )
                    return [
                        types.TextContent(
                            type="text", text=f"Added documents: {result}"
                        )
                    ]

                elif name == "health-check":
                    is_healthy = self.meili_client.health_check()
                    return [
                        types.TextContent(
                            type="text",
                            text=f"Meilisearch is {is_healthy and 'available' or 'unavailable'}",
                        )
                    ]

                elif name == "get-version":
                    version = self.meili_client.get_version()
                    return [
                        types.TextContent(type="text", text=f"Version info: {version}")
                    ]

                elif name == "get-stats":
                    stats = self.meili_client.get_stats()
                    return [
                        types.TextContent(type="text", text=f"Database stats: {stats}")
                    ]

                elif name == "get-settings":
                    settings = self.meili_client.settings.get_settings(
                        arguments["indexUid"]
                    )
                    return [
                        types.TextContent(
                            type="text", text=f"Current settings: {settings}"
                        )
                    ]

                elif name == "update-settings":
                    result = self.meili_client.settings.update_settings(
                        arguments["indexUid"], arguments["settings"]
                    )
                    return [
                        types.TextContent(
                            type="text", text=f"Settings updated: {result}"
                        )
                    ]

                elif name == "search":
                    search_results = self.meili_client.search(
                        query=arguments["query"],
                        index_uid=arguments.get("indexUid"),
                        limit=arguments.get("limit"),
                        offset=arguments.get("offset"),
                        filter=arguments.get("filter"),
                        sort=arguments.get("sort"),
                    )

                    # Format the results for better readability
                    formatted_results = json.dumps(
                        search_results, indent=2, default=json_serializer
                    )
                    return [
                        types.TextContent(
                            type="text",
                            text=f"Search results for '{arguments['query']}':\n{formatted_results}",
                        )
                    ]

                elif name == "get-task":
                    task = self.meili_client.tasks.get_task(arguments["taskUid"])
                    return [
                        types.TextContent(type="text", text=f"Task information: {task}")
                    ]

                elif name == "get-tasks":
                    # Filter out any invalid parameters
                    valid_params = {
                        "limit",
                        "from",
                        "reverse",
                        "batchUids",
                        "uids",
                        "canceledBy",
                        "types",
                        "statuses",
                        "indexUids",
                        "afterEnqueuedAt",
                        "beforeEnqueuedAt",
                        "afterStartedAt",
                        "beforeStartedAt",
                        "afterFinishedAt",
                        "beforeFinishedAt",
                    }
                    filtered_args = (
                        {k: v for k, v in arguments.items() if k in valid_params}
                        if arguments
                        else {}
                    )
                    tasks = self.meili_client.tasks.get_tasks(filtered_args)
                    return [types.TextContent(type="text", text=f"Tasks: {tasks}")]

                elif name == "cancel-tasks":
                    result = self.meili_client.tasks.cancel_tasks(arguments)
                    return [
                        types.TextContent(
                            type="text", text=f"Tasks cancelled: {result}"
                        )
                    ]

                elif name == "get-keys":
                    keys = self.meili_client.keys.get_keys(arguments)
                    return [types.TextContent(type="text", text=f"API keys: {keys}")]

                elif name == "create-key":
                    key = self.meili_client.keys.create_key(
                        {
                            "description": arguments.get("description"),
                            "actions": arguments["actions"],
                            "indexes": arguments["indexes"],
                            "expiresAt": arguments.get("expiresAt"),
                        }
                    )
                    return [
                        types.TextContent(type="text", text=f"Created API key: {key}")
                    ]

                elif name == "delete-key":
                    self.meili_client.keys.delete_key(arguments["key"])
                    return [
                        types.TextContent(
                            type="text",
                            text=f"Successfully deleted API key: {arguments['key']}",
                        )
                    ]

                elif name == "get-health-status":
                    status = self.meili_client.monitoring.get_health_status()
                    self.logger.info("Health status checked", status=status.__dict__)
                    return [
                        types.TextContent(
                            type="text",
                            text=f"Health status: {json.dumps(status.__dict__, default=json_serializer)}",
                        )
                    ]

                elif name == "get-index-metrics":
                    metrics = self.meili_client.monitoring.get_index_metrics(
                        arguments["indexUid"]
                    )
                    self.logger.info(
                        "Index metrics retrieved",
                        index=arguments["indexUid"],
                        metrics=metrics.__dict__,
                    )
                    return [
                        types.TextContent(
                            type="text",
                            text=f"Index metrics: {json.dumps(metrics.__dict__, default=json_serializer)}",
                        )
                    ]

                elif name == "get-system-info":
                    info = self.meili_client.monitoring.get_system_information()
                    self.logger.info("System information retrieved", info=info)
                    return [
                        types.TextContent(
                            type="text", text=f"System information: {info}"
                        )
                    ]

                raise ValueError(f"Unknown tool: {name}")

            except Exception as e:
                self.logger.error(
                    f"Error executing tool {name}",
                    error=str(e),
                    tool=name,
                    arguments=arguments,
                )
                return [types.TextContent(type="text", text=f"Error: {str(e)}")]

    async def run(self):
        """Run the MCP server"""
        logger.info("Starting Meilisearch MCP server...")

        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="meilisearch",
                    server_version="0.1.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )

    def cleanup(self):
        """Clean shutdown"""
        self.logger.info("Shutting down MCP server")
        self.logger.shutdown()


def main():
    """Main entry point"""
    url = os.getenv("MEILI_HTTP_ADDR", "http://localhost:7700")
    api_key = os.getenv("MEILI_MASTER_KEY")

    server = create_server(url, api_key)
    asyncio.run(server.run())


if __name__ == "__main__":
    main()
