from __future__ import annotations

"""
History & Analytics Resource

Covers endpoints in `backend/app/routes/history.py`.
"""

from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from ofself.client import OfSelfClient


class HistoryResource:
    def __init__(self, client: "OfSelfClient") -> None:
        self._client = client

    # ----------------------------
    # Node history
    # ----------------------------

    def get_node_history(
        self,
        user_id: str,
        node_id: str,
        limit: int = 100,
        offset: int = 0,
        include_snapshots: bool = False,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "limit": limit,
            "offset": offset,
            "include_snapshots": str(include_snapshots).lower(),
        }
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        return self._client._request(
            "GET",
            f"/nodes/{node_id}/history",
            user_id=user_id,
            params=params,
        )

    def get_node_version(self, user_id: str, node_id: str, version: int) -> dict[str, Any]:
        return self._client._request("GET", f"/nodes/{node_id}/history/{version}", user_id=user_id)

    def get_node_at_time(self, user_id: str, node_id: str, timestamp: str) -> dict[str, Any]:
        return self._client._request(
            "GET",
            f"/nodes/{node_id}/history/at-time",
            user_id=user_id,
            params={"timestamp": timestamp},
        )

    def get_node_ledger(self, user_id: str, node_id: str) -> dict[str, Any]:
        return self._client._request("GET", f"/nodes/{node_id}/ledger", user_id=user_id)

    def get_node_contributions(
        self,
        user_id: str,
        node_id: str,
        status: Optional[str] = None,
        contributor_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status
        if contributor_type:
            params["contributor_type"] = contributor_type
        return self._client._request(
            "GET",
            f"/nodes/{node_id}/contributions",
            user_id=user_id,
            params=params,
        )

    def get_agent_contributions(
        self,
        user_id: str,
        agent_id: str,
        status: str = "active",
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        return self._client._request(
            "GET",
            f"/agents/{agent_id}/contributions",
            user_id=user_id,
            params={"status": status, "limit": limit, "offset": offset},
        )

    # ----------------------------
    # Parsing sessions
    # ----------------------------

    def list_sessions(
        self,
        user_id: str,
        status: str = "all",
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        return self._client._request(
            "GET",
            "/sessions",
            user_id=user_id,
            params={"status": status, "limit": limit, "offset": offset},
        )

    def get_session(self, user_id: str, session_id: str) -> dict[str, Any]:
        return self._client._request("GET", f"/sessions/{session_id}", user_id=user_id)

    # ----------------------------
    # Analytics
    # ----------------------------

    def get_agent_stats(self, user_id: str) -> dict[str, Any]:
        return self._client._request("GET", "/analytics/agent-stats", user_id=user_id)

    def get_history_stats(self, user_id: str) -> dict[str, Any]:
        return self._client._request("GET", "/analytics/history-stats", user_id=user_id)


