from __future__ import annotations

"""
Sharing Resource

Manage data sharing between users and third-party apps.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional, Union

if TYPE_CHECKING:
    from ofself.client import OfSelfClient


class SharingResource:
    """
    Manage data sharing.
    
    This is user-to-user sharing (JWT auth), as documented in `ofself-docs`:
    - POST /sharing
    - GET  /sharing/outgoing
    - GET  /sharing/incoming
    - GET  /sharing/:share_id
    - DELETE /sharing/:share_id
    
    Usage:
        # Share with another user
        share = client.sharing.create(
            user_id="user-123",
            shared_with_user_id="user-456",
            scope="specific_tags",
            tag_ids=["tag-uuid-1", "tag-uuid-2"],
        )
        
        # List outgoing shares
        shares = client.sharing.list_outgoing(user_id="user-123")
        
        # Revoke a share
        client.sharing.revoke(user_id="user-123", share_id="share-abc")
    """

    def __init__(self, client: "OfSelfClient") -> None:
        self._client = client

    def create(
        self,
        user_id: str,
        shared_with_user_id: str,
        scope: str,
        tag_ids: Optional[list[str]] = None,
        node_ids: Optional[list[str]] = None,
        can_read: bool = True,
        can_write: bool = False,
        can_delete: bool = False,
        can_share: bool = False,
        expires_at: Optional[Union[datetime, str]] = None,
    ) -> dict[str, Any]:
        """
        Create a new share.
        
        Args:
            user_id: Authenticated user (JWT) initiating the share
            shared_with_user_id: Recipient user id
            scope: all|specific_tags|specific_nodes|graph
            tag_ids: Required if scope=specific_tags
            node_ids: Required if scope=specific_nodes
            can_read/can_write/can_delete/can_share: Permission flags
            expires_at: When the share expires (optional)
            
        Returns:
            Created share data
        """
        payload: dict[str, Any] = {
            "shared_with_user_id": shared_with_user_id,
            "scope": scope,
            "tag_ids": tag_ids,
            "node_ids": node_ids,
            "can_read": can_read,
            "can_write": can_write,
            "can_delete": can_delete,
            "can_share": can_share,
        }

        if expires_at:
            if isinstance(expires_at, datetime):
                payload["expires_at"] = expires_at.isoformat()
            else:
                payload["expires_at"] = expires_at
        
        return self._client._request(
            "POST",
            "/sharing",
            user_id=user_id,
            json=payload,
        )

    def list_outgoing(
        self,
        user_id: str,
        is_active: Optional[bool] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict[str, Any]:
        """
        List shares created by the user (outgoing).
        
        Args:
            user_id: ID of the user
            active_only: Only return active (non-revoked) shares
            page: Page number
            per_page: Items per page
            
        Returns:
            Paginated list of shares
        """
        return self._client._request(
            "GET",
            "/sharing/outgoing",
            user_id=user_id,
            params={
                "is_active": str(is_active).lower() if is_active is not None else None,
                "limit": limit,
                "offset": offset,
            },
        )

    def list_incoming(
        self,
        user_id: str,
        is_active: Optional[bool] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict[str, Any]:
        """
        List shares received by the user (incoming).
        
        Args:
            user_id: ID of the user
            active_only: Only return active (non-revoked) shares
            page: Page number
            per_page: Items per page
            
        Returns:
            Paginated list of shares
        """
        return self._client._request(
            "GET",
            "/sharing/incoming",
            user_id=user_id,
            params={
                "is_active": str(is_active).lower() if is_active is not None else None,
                "limit": limit,
                "offset": offset,
            },
        )

    def get(self, user_id: str, share_id: str) -> dict[str, Any]:
        """
        Get share details.
        
        Args:
            user_id: ID of the user
            share_id: ID of the share
            
        Returns:
            Share data
        """
        return self._client._request(
            "GET",
            f"/sharing/{share_id}",
            user_id=user_id,
        )

    def update(
        self,
        user_id: str,
        share_id: str,
        scope: Optional[str] = None,
        tag_ids: Optional[list[str]] = None,
        node_ids: Optional[list[str]] = None,
        can_read: Optional[bool] = None,
        can_write: Optional[bool] = None,
        can_delete: Optional[bool] = None,
        can_share: Optional[bool] = None,
        expires_at: Optional[Union[datetime, str]] = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if scope is not None:
            payload["scope"] = scope
        if tag_ids is not None:
            payload["tag_ids"] = tag_ids
        if node_ids is not None:
            payload["node_ids"] = node_ids
        if can_read is not None:
            payload["can_read"] = can_read
        if can_write is not None:
            payload["can_write"] = can_write
        if can_delete is not None:
            payload["can_delete"] = can_delete
        if can_share is not None:
            payload["can_share"] = can_share
        if expires_at is not None:
            payload["expires_at"] = expires_at.isoformat() if isinstance(expires_at, datetime) else expires_at

        return self._client._request(
            "PUT",
            f"/sharing/{share_id}",
            user_id=user_id,
            json=payload,
        )

    def revoke(self, user_id: str, share_id: str) -> dict[str, Any]:
        """
        Revoke a share.
        
        Args:
            user_id: ID of the user
            share_id: ID of the share to revoke
            
        Returns:
            Revoked share data
        """
        return self._client._request(
            "DELETE",
            f"/sharing/{share_id}",
            user_id=user_id,
        )


