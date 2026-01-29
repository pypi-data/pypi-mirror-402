from __future__ import annotations

"""
Third-Party Apps Resource

Covers endpoints in `backend/app/routes/third_party.py`.
Most endpoints are JWT-only developer/admin flows.
"""

from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from ofself.client import OfSelfClient


class ThirdPartyResource:
    def __init__(self, client: "OfSelfClient") -> None:
        self._client = client

    def register(self, user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self._client._request("POST", "/third-party/register", user_id=user_id, json=payload)

    def me(self, user_id: str) -> dict[str, Any]:
        return self._client._request("GET", "/third-party/me", user_id=user_id)

    def my_apps(self, user_id: str) -> dict[str, Any]:
        return self._client._request("GET", "/third-party/my-apps", user_id=user_id)

    def info(self, user_id: str) -> dict[str, Any]:
        return self._client._request("GET", "/third-party/info", user_id=user_id)

    def update(self, user_id: str, third_party_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self._client._request("PUT", f"/third-party/{third_party_id}", user_id=user_id, json=payload)

    def create_tags(self, user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self._client._request("POST", "/third-party/tags", user_id=user_id, json=payload)

    # Admin/native-dev endpoints
    def list_apps(self, user_id: str) -> dict[str, Any]:
        return self._client._request("GET", "/apps", user_id=user_id)

    def list_pending_apps(self, user_id: str) -> dict[str, Any]:
        return self._client._request("GET", "/apps/pending", user_id=user_id)

    def verify_app(self, user_id: str, app_id: str) -> dict[str, Any]:
        return self._client._request("POST", f"/apps/{app_id}/verify", user_id=user_id)

    def unverify_app(self, user_id: str, app_id: str) -> dict[str, Any]:
        return self._client._request("POST", f"/apps/{app_id}/unverify", user_id=user_id)

    def delete_app(self, user_id: str, app_id: str) -> dict[str, Any]:
        return self._client._request("DELETE", f"/apps/{app_id}", user_id=user_id)

    def metrics(
        self,
        user_id: str,
        third_party_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        return self._client._request(
            "GET",
            f"/third-party/{third_party_id}/metrics",
            user_id=user_id,
            params=params,
        )


