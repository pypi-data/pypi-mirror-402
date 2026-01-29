from __future__ import annotations

"""
Relationships Resource

Manage relationships between nodes in the user's graph.
"""

from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from ofself.client import OfSelfClient


class RelationshipsResource:
    """
    Manage relationships between nodes.
    
    Usage:
        # Create a relationship
        rel = client.relationships.create(
            user_id="user-123",
            source_node_id="node-a",
            target_node_id="node-b",
            relationship_type="references"
        )
        
        # List relationships
        rels = client.relationships.list(user_id="user-123")
    """

    def __init__(self, client: "OfSelfClient") -> None:
        self._client = client

    def create(
        self,
        user_id: str,
        from_node_id: str,
        to_node_id: str,
        relationship_type: str,
        strength: Optional[float] = None,
        confidence: Optional[float] = None,
        context: Optional[str] = None,
        bidirectional: Optional[bool] = None,
        view: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Create a relationship between two nodes.
        
        Args:
            user_id: ID of the user
            source_node_id: ID of the source node
            target_node_id: ID of the target node
            relationship_type: Type of relationship (e.g., "references", "parent_of")
            weight: Relationship strength (0-1)
            metadata: Additional metadata
            
        Returns:
            Created relationship data
        """
        payload: dict[str, Any] = {
            "from_node_id": from_node_id,
            "to_node_id": to_node_id,
            "relationship_type": relationship_type,
        }
        if strength is not None:
            payload["strength"] = strength
        if confidence is not None:
            payload["confidence"] = confidence
        if context is not None:
            payload["context"] = context
        if bidirectional is not None:
            payload["bidirectional"] = bidirectional
        if view is not None:
            payload["view"] = view
        
        return self._client._request(
            "POST",
            "/relationships",
            user_id=user_id,
            json=payload,
        )

    def list(
        self,
        user_id: str,
        from_node_id: Optional[str] = None,
        to_node_id: Optional[str] = None,
        relationship_type: Optional[str] = None,
        view: Optional[str] = None,
        include_nodes: bool = False,
    ) -> dict[str, Any]:
        """
        List relationships.
        
        Args:
            user_id: ID of the user
            node_id: Filter by node ID (returns all relationships involving this node)
            relationship_type: Filter by relationship type
            page: Page number
            per_page: Items per page
            
        Returns:
            Paginated list of relationships
        """
        params: dict[str, Any] = {}

        if from_node_id:
            params["from_node_id"] = from_node_id
        if to_node_id:
            params["to_node_id"] = to_node_id
        if relationship_type:
            params["relationship_type"] = relationship_type
        if view:
            params["view"] = view
        if include_nodes:
            params["include_nodes"] = "true"
        
        return self._client._request(
            "GET",
            "/relationships",
            user_id=user_id,
            params=params,
        )

    def get(self, user_id: str, relationship_id: str) -> dict[str, Any]:
        """
        Get a single relationship.
        
        Args:
            user_id: ID of the user
            relationship_id: ID of the relationship
            
        Returns:
            Relationship data
        """
        return self._client._request(
            "GET",
            f"/relationships/{relationship_id}",
            user_id=user_id,
        )

    def update(
        self,
        user_id: str,
        relationship_id: str,
        relationship_type: Optional[str] = None,
        strength: Optional[float] = None,
        confidence: Optional[float] = None,
        context: Optional[str] = None,
        bidirectional: Optional[bool] = None,
    ) -> dict[str, Any]:
        """
        Update a relationship.
        
        Args:
            user_id: ID of the user
            relationship_id: ID of the relationship
            relationship_type: New relationship type
            weight: New weight
            metadata: New metadata
            
        Returns:
            Updated relationship data
        """
        payload: dict[str, Any] = {}
        
        if relationship_type is not None:
            payload["relationship_type"] = relationship_type
        if strength is not None:
            payload["strength"] = strength
        if confidence is not None:
            payload["confidence"] = confidence
        if context is not None:
            payload["context"] = context
        if bidirectional is not None:
            payload["bidirectional"] = bidirectional
        
        return self._client._request(
            "PUT",
            f"/relationships/{relationship_id}",
            user_id=user_id,
            json=payload,
        )

    def delete(self, user_id: str, relationship_id: str) -> None:
        """
        Delete a relationship.
        
        Args:
            user_id: ID of the user
            relationship_id: ID of the relationship
        """
        self._client._request(
            "DELETE",
            f"/relationships/{relationship_id}",
            user_id=user_id,
        )


