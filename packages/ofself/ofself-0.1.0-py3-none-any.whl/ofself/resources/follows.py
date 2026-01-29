from __future__ import annotations

"""
Follows Resource

Manage follow relationships (social layer built on top of sharing).
JWT-only endpoints.
"""

from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from ofself.client import OfSelfClient


class FollowsResource:
    def __init__(self, client: "OfSelfClient") -> None:
        self._client = client

    def create(self, target_user_id: str, message: Optional[str] = None) -> dict[str, Any]:
        payload: dict[str, Any] = {"target_user_id": target_user_id}
        if message:
            payload["message"] = message
        return self._client._request("POST", "/follows", json=payload)

    def list_incoming(
        self,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status
        return self._client._request("GET", "/follows/incoming", params=params)

    def list_outgoing(
        self,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status
        return self._client._request("GET", "/follows/outgoing", params=params)

    def respond(
        self,
        follow_id: str,
        action: str,
        share: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"action": action}
        if share is not None:
            payload["share"] = share
        return self._client._request("PUT", f"/follows/{follow_id}/respond", json=payload)

    def revoke(self, follow_id: str) -> dict[str, Any]:
        return self._client._request("DELETE", f"/follows/{follow_id}")


