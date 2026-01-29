from __future__ import annotations

"""
Nodes Resource

Manage user nodes (notes, documents, entities, etc.)
"""

from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from ofself.client import OfSelfClient


class NodesResource:
    """
    Manage nodes in a user's graph.
    
    Usage:
        # Create a node
        node = client.nodes.create(
            user_id="user-123",
            title="My Note",
            value="Hello world!",
            node_type="note"
        )
        
        # List nodes
        nodes = client.nodes.list(user_id="user-123", node_type="note")
        
        # Get a specific node
        node = client.nodes.get(user_id="user-123", node_id="node-456")
        
        # Update a node
        node = client.nodes.update(
            user_id="user-123",
            node_id="node-456",
            title="Updated Title"
        )
        
        # Delete a node
        client.nodes.delete(user_id="user-123", node_id="node-456")
    """

    def __init__(self, client: "OfSelfClient") -> None:
        self._client = client

    def create(
        self,
        user_id: str,
        title: str,
        value: Optional[str] = None,
        node_type: str = "note",
        meaning_level: Optional[str] = None,
        graph_view: Optional[str] = None,
        importance_score: Optional[float] = None,
        metadata: Optional[dict[str, Any]] = None,
        node_metadata: Optional[dict[str, Any]] = None,  # backward compat
        tags: Optional[list[str]] = None,  # tag IDs or names
        tag_ids: Optional[list[str]] = None,  # backward compat
        agent_metadata: Optional[dict[str, Any]] = None,
        last_modified_by_agent_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Create a new node.
        
        Args:
            user_id: ID of the user who owns the node
            title: Node title
            value: Node content/value
            node_type: Type of node (note, document, entity, etc.)
            node_metadata: Additional metadata as key-value pairs
            tag_ids: List of tag IDs to associate with the node
            
        Returns:
            Created node data
        """
        payload: dict[str, Any] = {"title": title, "node_type": node_type}
        
        if value is not None:
            payload["value"] = value
        if meaning_level is not None:
            payload["meaning_level"] = meaning_level
        if graph_view is not None:
            payload["graph_view"] = graph_view
        if importance_score is not None:
            payload["importance_score"] = importance_score

        if metadata is not None:
            payload["metadata"] = metadata
        elif node_metadata is not None:
            payload["metadata"] = node_metadata

        # Backend accepts tag UUIDs OR tag names; keep backward compat with tag_ids
        if tags is not None:
            payload["tags"] = tags
        elif tag_ids is not None:
            payload["tags"] = tag_ids

        if agent_metadata is not None:
            payload["agent_metadata"] = agent_metadata
        if last_modified_by_agent_id is not None:
            payload["last_modified_by_agent_id"] = last_modified_by_agent_id
        
        return self._client._request(
            "POST",
            "/nodes",
            user_id=user_id,
            json=payload,
        )

    def list(
        self,
        user_id: str,
        node_type: Optional[str] = None,
        tag_ids: Optional[list[str]] = None,
        search: Optional[str] = None,
        page: int = 1,
        per_page: int = 50,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        access: Optional[str] = None,
        view: Optional[str] = None,
        include_tags: Optional[bool] = None,
        include_owner: Optional[bool] = None,
    ) -> dict[str, Any]:
        """
        List nodes with optional filters.
        
        Args:
            user_id: ID of the user
            node_type: Filter by node type
            tag_ids: Filter by tag IDs
            search: Search in title and value
            page: Page number (1-indexed)
            per_page: Items per page (max 100)
            sort_by: Field to sort by
            sort_order: Sort direction (asc or desc)
            
        Returns:
            Paginated list of nodes
        """
        if page < 1:
            page = 1
        if per_page < 1:
            per_page = 50

        limit = per_page
        offset = (page - 1) * per_page

        params: dict[str, Any] = {
            "limit": limit,
            "offset": offset,
            "sort": sort_by,
            "order": sort_order,
        }
        
        if node_type:
            params["node_type"] = node_type
        if tag_ids:
            # Backend supports `tag_id` (single). Use first for now.
            params["tag_id"] = tag_ids[0]
        if search:
            params["search"] = search
        if access:
            params["access"] = access
        if view:
            params["view"] = view
        if include_tags is not None:
            params["include_tags"] = str(include_tags).lower()
        if include_owner is not None:
            params["include_owner"] = str(include_owner).lower()
        
        return self._client._request(
            "GET",
            "/nodes",
            user_id=user_id,
            params=params,
        )

    def get(self, user_id: str, node_id: str) -> dict[str, Any]:
        """
        Get a single node by ID.
        
        Args:
            user_id: ID of the user
            node_id: ID of the node
            
        Returns:
            Node data
            
        Raises:
            NotFoundError: If node doesn't exist
            PermissionDenied: If user doesn't have access
        """
        return self._client._request(
            "GET",
            f"/nodes/{node_id}",
            user_id=user_id,
        )

    def update(
        self,
        user_id: str,
        node_id: str,
        title: Optional[str] = None,
        value: Optional[str] = None,
        node_type: Optional[str] = None,
        meaning_level: Optional[str] = None,
        graph_view: Optional[str] = None,
        importance_score: Optional[float] = None,
        metadata: Optional[dict[str, Any]] = None,
        node_metadata: Optional[dict[str, Any]] = None,  # backward compat
        tags: Optional[list[str]] = None,
        tag_ids: Optional[list[str]] = None,  # backward compat
        agent_metadata: Optional[dict[str, Any]] = None,
        last_modified_by_agent_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Update a node.
        
        Args:
            user_id: ID of the user
            node_id: ID of the node to update
            title: New title (optional)
            value: New value (optional)
            node_type: New node type (optional)
            node_metadata: New metadata (optional)
            
        Returns:
            Updated node data
        """
        payload: dict[str, Any] = {}
        
        if title is not None:
            payload["title"] = title
        if value is not None:
            payload["value"] = value
        if node_type is not None:
            payload["node_type"] = node_type
        if meaning_level is not None:
            payload["meaning_level"] = meaning_level
        if graph_view is not None:
            payload["graph_view"] = graph_view
        if importance_score is not None:
            payload["importance_score"] = importance_score
        if metadata is not None:
            payload["metadata"] = metadata
        elif node_metadata is not None:
            payload["node_metadata"] = node_metadata

        if tags is not None:
            payload["tags"] = tags
        elif tag_ids is not None:
            payload["tag_ids"] = tag_ids

        if agent_metadata is not None:
            payload["agent_metadata"] = agent_metadata
        if last_modified_by_agent_id is not None:
            payload["last_modified_by_agent_id"] = last_modified_by_agent_id
        
        return self._client._request(
            "PUT",
            f"/nodes/{node_id}",
            user_id=user_id,
            json=payload,
        )

    def delete(self, user_id: str, node_id: str) -> None:
        """
        Delete a node.
        
        Args:
            user_id: ID of the user
            node_id: ID of the node to delete
        """
        self._client._request(
            "DELETE",
            f"/nodes/{node_id}",
            user_id=user_id,
        )

    def add_tag(self, user_id: str, node_id: str, tag_id: str) -> dict[str, Any]:
        """
        Add a tag to a node.
        
        Args:
            user_id: ID of the user
            node_id: ID of the node
            tag_id: ID of the tag to add
            
        Returns:
            Updated node data
        """
        return self._client._request(
            "POST",
            f"/nodes/{node_id}/tags",
            user_id=user_id,
            json={"tag_id": tag_id},
        )

    def remove_tag(self, user_id: str, node_id: str, tag_id: str) -> dict[str, Any]:
        """
        Remove a tag from a node.
        
        Args:
            user_id: ID of the user
            node_id: ID of the node
            tag_id: ID of the tag to remove
            
        Returns:
            Updated node data
        """
        return self._client._request(
            "DELETE",
            f"/nodes/{node_id}/tags/{tag_id}",
            user_id=user_id,
        )

    def get_relationships(self, user_id: str, node_id: str) -> list[dict[str, Any]]:
        """
        Get all relationships for a node.
        
        Args:
            user_id: ID of the user
            node_id: ID of the node
            
        Returns:
            List of relationships
        """
        return self._client._request(
            "GET",
            f"/nodes/{node_id}/relationships",
            user_id=user_id,
        )

    def vector_search(
        self,
        user_id: str,
        embedding: list[float],
        limit: int = 10,
        min_score: Optional[float] = None,
        graph_view: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """
        Search nodes using semantic/vector similarity.
        
        Args:
            user_id: ID of the user
            query: Search query text
            limit: Maximum results to return
            node_type: Filter by node type
            tag_ids: Filter by tags
            
        Returns:
            List of nodes ranked by similarity
        """
        payload: dict[str, Any] = {"embedding": embedding, "limit": limit}
        if min_score is not None:
            payload["min_score"] = min_score
        if graph_view is not None:
            payload["graph_view"] = graph_view
        
        return self._client._request(
            "POST",
            "/nodes/search/vector",
            user_id=user_id,
            json=payload,
        )

    def get_history(
        self,
        user_id: str,
        node_id: Optional[str] = None,
        page: int = 1,
        per_page: int = 50,
    ) -> dict[str, Any]:
        """
        Get node change history.
        
        Args:
            user_id: ID of the user
            node_id: Filter by specific node (optional)
            page: Page number
            per_page: Items per page
            
        Returns:
            Paginated history of node changes
        """
        if page < 1:
            page = 1
        if per_page < 1:
            per_page = 50
        limit = per_page
        offset = (page - 1) * per_page

        # Prefer per-node endpoint when node_id is provided
        if node_id:
            return self._client._request(
                "GET",
                f"/nodes/{node_id}/history",
                user_id=user_id,
                params={"limit": limit, "offset": offset},
            )

        return self._client._request(
            "GET",
            "/nodes/history",
            user_id=user_id,
            params={"limit": limit, "offset": offset},
        )

    def update_embedding(
        self,
        user_id: str,
        node_id: str,
        embedding: list[float],
    ) -> dict[str, Any]:
        """
        Update a node's embedding vector.
        
        Args:
            user_id: ID of the user
            node_id: ID of the node
            embedding: Embedding vector (list of floats)
            
        Returns:
            Updated node data
        """
        return self._client._request(
            "PUT",
            f"/nodes/{node_id}/embedding",
            user_id=user_id,
            json={"embedding": embedding},
        )

    def batch_update_embeddings(
        self,
        user_id: str,
        updates: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Update embeddings for multiple nodes.
        
        Args:
            user_id: ID of the user
            updates: List of {"node_id": "...", "embedding": [...]}
            
        Returns:
            Summary of updates
        """
        return self._client._request(
            "PUT",
            "/nodes/batch/embeddings",
            user_id=user_id,
            json={"embeddings": updates},
        )

