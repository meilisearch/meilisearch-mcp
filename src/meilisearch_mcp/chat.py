import logging
from typing import Any, Dict, Iterator, List, Optional

from meilisearch import Client
from meilisearch.errors import MeilisearchApiError

logger = logging.getLogger(__name__)


class ChatManager:
    def __init__(self, client: Client):
        self.client = client

    async def create_chat_completion(
        self,
        workspace_uid: str,
        messages: List[Dict[str, str]],
        model: str = "gpt-3.5-turbo",
        stream: bool = True,
    ) -> str:
        try:
            logger.info(f"Creating chat completion for workspace: {workspace_uid}")

            # The SDK returns an iterator for streaming responses
            response_chunks = []
            for chunk in self.client.create_chat_completion(
                workspace_uid=workspace_uid,
                messages=messages,
                model=model,
                stream=stream,
            ):
                response_chunks.append(chunk)

            # Combine all chunks into a complete response
            full_response = self._combine_chunks(response_chunks)
            logger.info(
                f"Chat completion created successfully for workspace: {workspace_uid}"
            )
            return full_response

        except MeilisearchApiError as e:
            logger.error(f"Meilisearch API error in create_chat_completion: {e}")
            raise
        except Exception as e:
            logger.error(f"Error in create_chat_completion: {e}")
            raise

    def _combine_chunks(self, chunks: List[Dict[str, Any]]) -> str:
        """Combine streaming chunks into a single response message."""
        content_parts = []
        for chunk in chunks:
            if "choices" in chunk and chunk["choices"]:
                choice = chunk["choices"][0]
                if "delta" in choice and "content" in choice["delta"]:
                    content_parts.append(choice["delta"]["content"])
        return "".join(content_parts)

    async def get_chat_workspaces(
        self, offset: Optional[int] = None, limit: Optional[int] = None
    ) -> Dict[str, Any]:
        try:
            logger.info(f"Getting chat workspaces (offset={offset}, limit={limit})")
            workspaces = self.client.get_chat_workspaces(offset=offset, limit=limit)
            logger.info(
                f"Retrieved {len(workspaces.get('results', []))} chat workspaces"
            )
            return workspaces
        except MeilisearchApiError as e:
            logger.error(f"Meilisearch API error in get_chat_workspaces: {e}")
            raise
        except Exception as e:
            logger.error(f"Error in get_chat_workspaces: {e}")
            raise

    async def get_chat_workspace_settings(self, workspace_uid: str) -> Dict[str, Any]:
        try:
            logger.info(f"Getting settings for chat workspace: {workspace_uid}")
            settings = self.client.get_chat_workspace_settings(workspace_uid)
            logger.info(f"Retrieved settings for workspace: {workspace_uid}")
            return settings
        except MeilisearchApiError as e:
            logger.error(f"Meilisearch API error in get_chat_workspace_settings: {e}")
            raise
        except Exception as e:
            logger.error(f"Error in get_chat_workspace_settings: {e}")
            raise

    async def update_chat_workspace_settings(
        self, workspace_uid: str, settings: Dict[str, Any]
    ) -> Dict[str, Any]:
        try:
            logger.info(f"Updating settings for chat workspace: {workspace_uid}")
            updated_settings = self.client.update_chat_workspace_settings(
                workspace_uid, settings
            )
            logger.info(f"Updated settings for workspace: {workspace_uid}")
            return updated_settings
        except MeilisearchApiError as e:
            logger.error(
                f"Meilisearch API error in update_chat_workspace_settings: {e}"
            )
            raise
        except Exception as e:
            logger.error(f"Error in update_chat_workspace_settings: {e}")
            raise
