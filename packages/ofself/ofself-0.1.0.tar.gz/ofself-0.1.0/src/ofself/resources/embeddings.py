"""
Embeddings Resource

Manage vector embeddings for semantic search.
"""

from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from ofself.client import OfSelfClient


class EmbeddingsResource:
    """
    Manage vector embeddings.
    
    Embeddings are vector representations of text used for semantic search.
    
    Usage:
        # Create an embedding
        embedding = client.embeddings.create(
            user_id="user-123",
            text="Meeting notes about project timeline",
            node_id="node-456"
        )
        
        # Search by vector similarity
        results = client.nodes.vector_search(
            user_id="user-123",
            query="project deadlines"
        )
    """

    def __init__(self, client: "OfSelfClient") -> None:
        self._client = client

    def create(
        self,
        user_id: str,
        text: str,
        node_id: Optional[str] = None,
        file_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Create an embedding from text.
        
        Args:
            user_id: ID of the user
            text: Text to create embedding from
            node_id: Associate with a node (optional)
            file_id: Associate with a file (optional)
            metadata: Additional metadata
            
        Returns:
            Created embedding data
        """
        payload: dict[str, Any] = {"text": text}
        
        if node_id:
            payload["node_id"] = node_id
        if file_id:
            payload["file_id"] = file_id
        if metadata:
            payload["metadata"] = metadata
        
        return self._client._request(
            "POST",
            "/embeddings",
            user_id=user_id,
            json=payload,
        )

    def list(
        self,
        user_id: str,
        node_id: Optional[str] = None,
        page: int = 1,
        per_page: int = 50,
    ) -> dict[str, Any]:
        """
        List embeddings.
        
        Args:
            user_id: ID of the user
            node_id: Filter by node ID
            page: Page number
            per_page: Items per page
            
        Returns:
            Paginated list of embeddings
        """
        params: dict[str, Any] = {
            "page": page,
            "per_page": per_page,
        }
        
        if node_id:
            params["node_id"] = node_id
        
        return self._client._request(
            "GET",
            "/embeddings",
            user_id=user_id,
            params=params,
        )

    def get(self, user_id: str, embedding_id: str) -> dict[str, Any]:
        """
        Get an embedding.
        
        Args:
            user_id: ID of the user
            embedding_id: ID of the embedding
            
        Returns:
            Embedding data (optionally with vector)
        """
        return self._client._request(
            "GET",
            f"/embeddings/{embedding_id}",
            user_id=user_id,
        )

    def delete(self, user_id: str, embedding_id: str) -> None:
        """
        Delete an embedding.
        
        Args:
            user_id: ID of the user
            embedding_id: ID of the embedding
        """
        self._client._request(
            "DELETE",
            f"/embeddings/{embedding_id}",
            user_id=user_id,
        )


