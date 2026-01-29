from __future__ import annotations

"""
Proposals Resource

Manage proposals for data changes.

Third-party apps can propose changes to user data. Users then approve or reject.
"""

from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from ofself.client import OfSelfClient


class ProposalsResource:
    """
    Manage proposals for data changes.
    
    The proposal flow:
    1. Third-party app creates a proposal (e.g., "create this node")
    2. User reviews the proposal in their dashboard
    3. User approves or rejects
    4. If approved, changes are applied to user's data
    
    Usage:
        # Create a proposal to add a node
        proposal = client.proposals.create(
            user_id="user-123",
            title="Extract Entities",
            type="CREATE_NODE",
            canonical_data={
                "entities": [{
                    "title": "Meeting Notes",
                    "value": "Discussed project timeline...",
                    "node_type": "note"
                }]
            }
        )
        
        # List pending proposals
        proposals = client.proposals.list(user_id="user-123", status="pending")
    """

    def __init__(self, client: "OfSelfClient") -> None:
        self._client = client

    def create(
        self,
        user_id: str,
        title: str,
        type: str,
        canonical_data: dict[str, Any],
        description: Optional[str] = None,
        graph_view: Optional[str] = None,
        raw_data: Optional[dict[str, Any]] = None,
        tags: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """
        Create a proposal.
        
        Args:
            user_id: ID of the user to propose changes to
            proposal_type: Type of proposal:
                - "create_node": Create new nodes
                - "update_node": Update existing nodes
                - "delete_node": Delete nodes
                - "merge_nodes": Merge multiple nodes into one
                - "create_relationship": Create relationships
                - "create_tag": Create tags
            canonical_data: Structured data for the proposal
            raw_data: Optional raw/source data for reference
            
        Returns:
            Created proposal data
            
        Example canonical_data for create_node:
            {
                "entities": [
                    {
                        "title": "Note Title",
                        "value": "Note content",
                        "node_type": "note",
                        "tags": ["work", "meeting"]
                    }
                ]
            }
        """
        payload: dict[str, Any] = {
            "title": title,
            "type": type,
            "description": description,
            "graph_view": graph_view,
            "canonical_data": canonical_data,
            "tags": tags,
        }
        
        if raw_data:
            payload["raw_data"] = raw_data
        
        return self._client._request(
            "POST",
            "/proposals",
            user_id=user_id,
            json=payload,
        )

    def list(
        self,
        user_id: str,
        status: Optional[str] = None,
        page: int = 1,
        per_page: int = 50,
        graph_view: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        List proposals.
        
        Args:
            user_id: ID of the user
            status: Filter by status (pending, approved, rejected)
            proposal_type: Filter by proposal type
            page: Page number
            per_page: Items per page
            
        Returns:
            Paginated list of proposals
        """
        if page < 1:
            page = 1
        if per_page < 1:
            per_page = 50

        params: dict[str, Any] = {
            "page": page,
            "per_page": per_page,
        }
        
        if status:
            params["status"] = status
        if graph_view:
            params["graph_view"] = graph_view
        
        return self._client._request(
            "GET",
            "/proposals",
            user_id=user_id,
            params=params,
        )

    def get(self, user_id: str, proposal_id: str) -> dict[str, Any]:
        """
        Get a proposal.
        
        Args:
            user_id: ID of the user
            proposal_id: ID of the proposal
            
        Returns:
            Proposal data
        """
        return self._client._request(
            "GET",
            f"/proposals/{proposal_id}",
            user_id=user_id,
        )

    def update(self, user_id: str, proposal_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Update/enrich a proposal (Proposals V2 PATCH).
        """
        return self._client._request(
            "PATCH",
            f"/proposals/{proposal_id}",
            user_id=user_id,
            json=payload,
        )

    def approve(
        self,
        user_id: str,
        proposal_id: str,
        modifications: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Approve a proposal.
        
        Args:
            user_id: ID of the user
            proposal_id: ID of the proposal
            modifications: Optional modifications to apply before approving
            
        Returns:
            Updated proposal data with applied results
        """
        payload: dict[str, Any] = {}
        
        if modifications:
            payload["modifications"] = modifications
        
        return self._client._request(
            "POST",
            f"/proposals/{proposal_id}/approve",
            user_id=user_id,
            json=payload if payload else None,
        )

    def reject(
        self,
        user_id: str,
        proposal_id: str,
        reason: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Reject a proposal.
        
        Args:
            user_id: ID of the user
            proposal_id: ID of the proposal
            reason: Optional rejection reason
            
        Returns:
            Updated proposal data
        """
        payload: dict[str, Any] = {}
        
        if reason:
            payload["reason"] = reason
        
        return self._client._request(
            "POST",
            f"/proposals/{proposal_id}/reject",
            user_id=user_id,
            json=payload if payload else None,
        )

    def apply(self, user_id: str, proposal_id: str) -> dict[str, Any]:
        """
        Apply an approved proposal (Proposals V2).
        """
        return self._client._request("POST", f"/proposals/{proposal_id}/apply", user_id=user_id)

    def delete(self, user_id: str, proposal_id: str) -> dict[str, Any]:
        """
        Delete a proposal (Proposals V2).
        """
        return self._client._request("DELETE", f"/proposals/{proposal_id}", user_id=user_id)

    def subscribe(
        self,
        user_id: str,
        event_types: list[str],
        webhook_url: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Subscribe to proposal events (Proposals V2).
        """
        payload: dict[str, Any] = {"event_types": event_types}
        if webhook_url:
            payload["webhook_url"] = webhook_url
        return self._client._request(
            "POST",
            "/proposals/subscribe",
            user_id=user_id,
            json=payload,
        )

    def get_events(
        self,
        user_id: str,
        since: Optional[str] = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        """
        Poll proposal events (Proposals V2).
        """
        params: dict[str, Any] = {"limit": limit}
        if since:
            params["since"] = since
        return self._client._request(
            "GET",
            "/proposals/events",
            user_id=user_id,
            params=params,
        )


