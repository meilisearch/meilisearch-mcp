from typing import Dict, Any, List, Optional, Union
from meilisearch import Client
import json
from datetime import datetime


def json_serializer(obj: Any) -> str:
    """Custom JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    return str(obj)


class DocumentManager:
    """Manage documents within Meilisearch indexes"""

    def __init__(self, client: Client):
        self.client = client

    async def get_documents(
        self,
        index_uid: str,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
        fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Get documents from an index"""
        try:
            index = self.client.index(index_uid)
            documents = index.get_documents(
                {"offset": offset, "limit": limit, "fields": fields}
            )
            # Convert to JSON-serializable format
            return json.loads(json.dumps(documents, default=json_serializer))
        except Exception as e:
            raise Exception(f"Failed to get documents: {str(e)}")

    async def get_document(
        self, index_uid: str, document_id: Union[str, int]
    ) -> Dict[str, Any]:
        """Get a single document"""
        try:
            index = self.client.index(index_uid)
            document = index.get_document(document_id)
            # Convert to JSON-serializable format
            return json.loads(json.dumps(document, default=json_serializer))
        except Exception as e:
            raise Exception(f"Failed to get document: {str(e)}")

    async def add_documents(
        self,
        index_uid: str,
        documents: List[Dict[str, Any]],
        primary_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Add documents to an index"""
        try:
            index = self.client.index(index_uid)
            result = index.add_documents(documents, primary_key)
            # Convert to JSON-serializable format
            return json.loads(json.dumps(result, default=json_serializer))
        except Exception as e:
            raise Exception(f"Failed to add documents: {str(e)}")

    async def update_documents(
        self, index_uid: str, documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Update documents in an index"""
        try:
            index = self.client.index(index_uid)
            result = index.update_documents(documents)
            # Convert to JSON-serializable format
            return json.loads(json.dumps(result, default=json_serializer))
        except Exception as e:
            raise Exception(f"Failed to update documents: {str(e)}")

    async def delete_document(
        self, index_uid: str, document_id: Union[str, int]
    ) -> Dict[str, Any]:
        """Delete a single document"""
        try:
            index = self.client.index(index_uid)
            result = index.delete_document(document_id)
            # Convert to JSON-serializable format
            return json.loads(json.dumps(result, default=json_serializer))
        except Exception as e:
            raise Exception(f"Failed to delete document: {str(e)}")

    async def delete_documents(
        self, index_uid: str, document_ids: List[Union[str, int]]
    ) -> Dict[str, Any]:
        """Delete multiple documents by ID"""
        try:
            index = self.client.index(index_uid)
            result = index.delete_documents(document_ids)
            # Convert to JSON-serializable format
            return json.loads(json.dumps(result, default=json_serializer))
        except Exception as e:
            raise Exception(f"Failed to delete documents: {str(e)}")

    async def delete_all_documents(self, index_uid: str) -> Dict[str, Any]:
        """Delete all documents in an index"""
        try:
            index = self.client.index(index_uid)
            result = index.delete_all_documents()
            # Convert to JSON-serializable format
            return json.loads(json.dumps(result, default=json_serializer))
        except Exception as e:
            raise Exception(f"Failed to delete all documents: {str(e)}")
