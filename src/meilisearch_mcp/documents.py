from typing import Dict, Any, List, Optional, Union
from meilisearch import Client


class DocumentManager:
    """Manage documents within Meilisearch indexes"""

    def __init__(self, client: Client):
        self.client = client

    def get_documents(
        self,
        index_uid: str,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
        fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Get documents from an index"""
        try:
            index = self.client.index(index_uid)
            # Build parameters dict, excluding None values to avoid API errors
            params = {}
            if offset is not None:
                params["offset"] = offset
            if limit is not None:
                params["limit"] = limit
            if fields is not None:
                params["fields"] = fields

            result = index.get_documents(params if params else {})

            # Convert meilisearch model objects to JSON-serializable format
            if hasattr(result, "__dict__"):
                result_dict = result.__dict__.copy()
                # Convert individual document objects in results if they exist
                if "results" in result_dict and isinstance(
                    result_dict["results"], list
                ):
                    serialized_results = []
                    for doc in result_dict["results"]:
                        if hasattr(doc, "__dict__"):
                            # Extract the actual document data
                            doc_dict = doc.__dict__.copy()
                            # Look for private attributes that might contain the actual data
                            for key, value in doc_dict.items():
                                if key.startswith("_") and isinstance(value, dict):
                                    # Use the dict content instead of the wrapper
                                    serialized_results.append(value)
                                    break
                            else:
                                # If no private dict found, use the object dict directly
                                serialized_results.append(doc_dict)
                        else:
                            serialized_results.append(doc)
                    result_dict["results"] = serialized_results
                return result_dict
            else:
                return result
        except Exception as e:
            raise Exception(f"Failed to get documents: {str(e)}")

    def get_document(
        self, index_uid: str, document_id: Union[str, int]
    ) -> Dict[str, Any]:
        """Get a single document"""
        try:
            index = self.client.index(index_uid)
            return index.get_document(document_id)
        except Exception as e:
            raise Exception(f"Failed to get document: {str(e)}")

    def add_documents(
        self,
        index_uid: str,
        documents: List[Dict[str, Any]],
        primary_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Add documents to an index"""
        try:
            index = self.client.index(index_uid)
            return index.add_documents(documents, primary_key)
        except Exception as e:
            raise Exception(f"Failed to add documents: {str(e)}")

    def update_documents(
        self, index_uid: str, documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Update documents in an index"""
        try:
            index = self.client.index(index_uid)
            return index.update_documents(documents)
        except Exception as e:
            raise Exception(f"Failed to update documents: {str(e)}")

    def delete_document(
        self, index_uid: str, document_id: Union[str, int]
    ) -> Dict[str, Any]:
        """Delete a single document"""
        try:
            index = self.client.index(index_uid)
            return index.delete_document(document_id)
        except Exception as e:
            raise Exception(f"Failed to delete document: {str(e)}")

    def delete_documents(
        self, index_uid: str, document_ids: List[Union[str, int]]
    ) -> Dict[str, Any]:
        """Delete multiple documents by ID"""
        try:
            index = self.client.index(index_uid)
            return index.delete_documents(document_ids)
        except Exception as e:
            raise Exception(f"Failed to delete documents: {str(e)}")

    def delete_all_documents(self, index_uid: str) -> Dict[str, Any]:
        """Delete all documents in an index"""
        try:
            index = self.client.index(index_uid)
            return index.delete_all_documents()
        except Exception as e:
            raise Exception(f"Failed to delete all documents: {str(e)}")
