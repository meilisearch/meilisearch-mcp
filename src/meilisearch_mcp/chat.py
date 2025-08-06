from typing import Dict, Any, List, Optional, AsyncIterator
from meilisearch import Client
import httpx
import json


class ChatManager:
    """Manage Meilisearch chat completions and workspaces"""

    def __init__(self, client: Client):
        self.client = client
        self.base_url = client.config.url.rstrip("/")
        self.headers = {
            "Authorization": (
                f"Bearer {client.config.api_key}" if client.config.api_key else None
            ),
            "Content-Type": "application/json",
        }
        # Remove None values from headers
        self.headers = {k: v for k, v in self.headers.items() if v is not None}

    async def chat_completion_stream(
        self,
        query: str,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        index_uids: Optional[List[str]] = None,
        workspace_uid: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """
        Stream chat completion responses from Meilisearch.

        Args:
            query: The user's query/prompt
            model: The model to use for chat completion (e.g., "gpt-4", "gpt-3.5-turbo")
            temperature: Controls randomness (0-1)
            max_tokens: Maximum tokens in response
            index_uids: List of index UIDs to search for context
            workspace_uid: Chat workspace UID to use

        Yields:
            Streaming response chunks
        """
        endpoint = f"{self.base_url}/chat/completions"

        payload = {"query": query, "stream": True}

        if model:
            payload["model"] = model
        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens:
            payload["maxTokens"] = max_tokens
        if index_uids:
            payload["indexUids"] = index_uids
        if workspace_uid:
            payload["workspaceUid"] = workspace_uid

        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST", endpoint, headers=self.headers, json=payload, timeout=60.0
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]  # Remove "data: " prefix
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            if "choices" in chunk and chunk["choices"]:
                                content = (
                                    chunk["choices"][0]
                                    .get("delta", {})
                                    .get("content", "")
                                )
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue

    def chat_completion(
        self,
        query: str,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        index_uids: Optional[List[str]] = None,
        workspace_uid: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get a non-streaming chat completion response.

        Args:
            query: The user's query/prompt
            model: The model to use for chat completion
            temperature: Controls randomness (0-1)
            max_tokens: Maximum tokens in response
            index_uids: List of index UIDs to search for context
            workspace_uid: Chat workspace UID to use

        Returns:
            Chat completion response
        """
        endpoint = f"{self.base_url}/chat/completions"

        payload = {"query": query, "stream": False}

        if model:
            payload["model"] = model
        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens:
            payload["maxTokens"] = max_tokens
        if index_uids:
            payload["indexUids"] = index_uids
        if workspace_uid:
            payload["workspaceUid"] = workspace_uid

        with httpx.Client() as client:
            response = client.post(
                endpoint, headers=self.headers, json=payload, timeout=60.0
            )
            response.raise_for_status()
            return response.json()

    def create_chat_workspace(
        self,
        uid: str,
        name: str,
        description: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        index_uids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new chat workspace.

        Args:
            uid: Unique identifier for the workspace
            name: Name of the workspace
            description: Description of the workspace
            model: Default model for this workspace
            temperature: Default temperature for this workspace
            max_tokens: Default max tokens for this workspace
            index_uids: Default index UIDs for this workspace

        Returns:
            Created workspace information
        """
        endpoint = f"{self.base_url}/chat/workspaces"

        payload = {"uid": uid, "name": name}

        if description:
            payload["description"] = description
        if model:
            payload["model"] = model
        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens:
            payload["maxTokens"] = max_tokens
        if index_uids:
            payload["indexUids"] = index_uids

        with httpx.Client() as client:
            response = client.post(endpoint, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()

    def update_chat_workspace(
        self,
        uid: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        index_uids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Update an existing chat workspace.

        Args:
            uid: Unique identifier of the workspace to update
            name: New name for the workspace
            description: New description for the workspace
            model: New default model for this workspace
            temperature: New default temperature for this workspace
            max_tokens: New default max tokens for this workspace
            index_uids: New default index UIDs for this workspace

        Returns:
            Updated workspace information
        """
        endpoint = f"{self.base_url}/chat/workspaces/{uid}"

        payload = {}

        if name:
            payload["name"] = name
        if description:
            payload["description"] = description
        if model:
            payload["model"] = model
        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens:
            payload["maxTokens"] = max_tokens
        if index_uids:
            payload["indexUids"] = index_uids

        with httpx.Client() as client:
            response = client.patch(endpoint, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()

    def list_chat_workspaces(
        self, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        List all chat workspaces.

        Args:
            limit: Maximum number of workspaces to return
            offset: Number of workspaces to skip

        Returns:
            List of chat workspaces
        """
        endpoint = f"{self.base_url}/chat/workspaces"

        params = {}
        if limit:
            params["limit"] = limit
        if offset:
            params["offset"] = offset

        with httpx.Client() as client:
            response = client.get(endpoint, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()

    def get_chat_workspace(self, uid: str) -> Dict[str, Any]:
        """
        Get details of a specific chat workspace.

        Args:
            uid: Unique identifier of the workspace

        Returns:
            Workspace details
        """
        endpoint = f"{self.base_url}/chat/workspaces/{uid}"

        with httpx.Client() as client:
            response = client.get(endpoint, headers=self.headers)
            response.raise_for_status()
            return response.json()

    def delete_chat_workspace(self, uid: str) -> Dict[str, Any]:
        """
        Delete a chat workspace.

        Args:
            uid: Unique identifier of the workspace to delete

        Returns:
            Deletion confirmation
        """
        endpoint = f"{self.base_url}/chat/workspaces/{uid}"

        with httpx.Client() as client:
            response = client.delete(endpoint, headers=self.headers)
            response.raise_for_status()
            return response.json()
