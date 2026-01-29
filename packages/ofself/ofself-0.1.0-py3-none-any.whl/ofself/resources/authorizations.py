"""
Authorizations Resource

Manage third-party app authorizations.
"""

from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from ofself.client import OfSelfClient


class AuthorizationsResource:
    """
    Manage authorized third-party apps.
    
    Users can view and revoke access granted to third-party apps.
    
    Usage:
        # List authorized apps
        auths = client.authorizations.list(user_id="user-123")
        
        # Revoke access
        client.authorizations.revoke(user_id="user-123", auth_id="auth-456")
    """

    def __init__(self, client: "OfSelfClient") -> None:
        self._client = client

    def list(
        self,
        user_id: str,
        page: int = 1,
        per_page: int = 50,
    ) -> dict[str, Any]:
        """
        List authorized third-party apps.
        
        Args:
            user_id: ID of the user
            page: Page number
            per_page: Items per page
            
        Returns:
            List of authorized apps with their permissions
        """
        return self._client._request(
            "GET",
            "/authorizations",
            user_id=user_id,
            params={"page": page, "per_page": per_page},
        )

    def get(self, user_id: str, authorization_id: str) -> dict[str, Any]:
        """
        Get authorization details.
        
        Args:
            user_id: ID of the user
            authorization_id: ID of the authorization
            
        Returns:
            Authorization details including app info and permissions
        """
        return self._client._request(
            "GET",
            f"/authorizations/{authorization_id}",
            user_id=user_id,
        )

    def update(
        self,
        user_id: str,
        authorization_id: str,
        exposure_profile_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Update authorization (change exposure profile).
        
        Args:
            user_id: ID of the user
            authorization_id: ID of the authorization
            exposure_profile_id: New exposure profile to use
            
        Returns:
            Updated authorization
        """
        payload: dict[str, Any] = {}
        if exposure_profile_id:
            payload["exposure_profile_id"] = exposure_profile_id
        
        return self._client._request(
            "PUT",
            f"/authorizations/{authorization_id}",
            user_id=user_id,
            json=payload,
        )

    def revoke(self, user_id: str, authorization_id: str) -> None:
        """
        Revoke authorization (remove app access).
        
        Args:
            user_id: ID of the user
            authorization_id: ID of the authorization to revoke
        """
        self._client._request(
            "DELETE",
            f"/authorizations/{authorization_id}",
            user_id=user_id,
        )


