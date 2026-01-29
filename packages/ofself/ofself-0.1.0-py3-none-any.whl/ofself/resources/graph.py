"""
Graph Resource

Get graph snapshots for visualization.
"""

from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from ofself.client import OfSelfClient


class GraphResource:
    """
    Access graph data for visualization.
    
    Usage:
        # Get full graph snapshot
        graph = client.graph.snapshot(user_id="user-123")
        
        # Graph contains nodes and edges for visualization
        print(f"Nodes: {len(graph['nodes'])}")
        print(f"Edges: {len(graph['edges'])}")
    """

    def __init__(self, client: "OfSelfClient") -> None:
        self._client = client

    def snapshot(
        self,
        user_id: str,
        include_metadata: bool = False,
        node_types: Optional[list[str]] = None,
        tag_ids: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """
        Get a snapshot of the user's graph.
        
        Returns nodes and edges formatted for visualization libraries
        like D3.js, vis.js, or react-force-graph.
        
        Args:
            user_id: ID of the user
            include_metadata: Include full node metadata
            node_types: Filter by node types
            tag_ids: Filter by tags
            
        Returns:
            Graph data with nodes and edges:
            {
                "nodes": [
                    {"id": "...", "title": "...", "type": "...", ...}
                ],
                "edges": [
                    {"source": "...", "target": "...", "type": "...", ...}
                ]
            }
        """
        params: dict[str, Any] = {
            "include_metadata": include_metadata,
        }
        
        if node_types:
            params["node_types"] = ",".join(node_types)
        if tag_ids:
            params["tag_ids"] = ",".join(tag_ids)
        
        return self._client._request(
            "GET",
            "/graph/snapshot",
            user_id=user_id,
            params=params,
        )


