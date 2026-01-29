"""
Exposure Profiles Resource

Manage exposure profiles that control what data is shared.
"""

from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from ofself.client import OfSelfClient


class ExposureProfilesResource:
    """
    Manage exposure profiles.
    
    Exposure profiles define what data a user shares with third-party apps.
    They can specify:
    - Which node types are accessible
    - Which tags are accessible
    - Read/write permissions
    - Time-based access
    
    Usage:
        # Create an exposure profile
        profile = client.exposure_profiles.create(
            user_id="user-123",
            name="Work Data",
            scope={
                "node_types": ["note", "document"],
                "tag_ids": ["tag-work"],
                "permissions": ["read"]
            }
        )
        
        # List profiles
        profiles = client.exposure_profiles.list(user_id="user-123")
    """

    def __init__(self, client: "OfSelfClient") -> None:
        self._client = client

    def create(
        self,
        user_id: str,
        name: str,
        scope: dict[str, Any],
        description: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Create an exposure profile.
        
        Args:
            user_id: ID of the user
            name: Profile name
            scope: What data is exposed (node_types, tag_ids, permissions, etc.)
            description: Human-readable description
            
        Returns:
            Created exposure profile data
            
        Example scope:
            {
                "node_types": ["note", "document"],
                "tag_ids": ["tag-work", "tag-public"],
                "permissions": ["read"],  # read, write, delete
                "exclude_tag_ids": ["tag-private"]
            }
        """
        payload: dict[str, Any] = {
            "name": name,
            "scope": scope,
        }
        
        if description:
            payload["description"] = description
        
        return self._client._request(
            "POST",
            "/exposure-profiles",
            user_id=user_id,
            json=payload,
        )

    def list(
        self,
        user_id: str,
        page: int = 1,
        per_page: int = 50,
    ) -> dict[str, Any]:
        """
        List exposure profiles.
        
        Args:
            user_id: ID of the user
            page: Page number
            per_page: Items per page
            
        Returns:
            Paginated list of exposure profiles
        """
        return self._client._request(
            "GET",
            "/exposure-profiles",
            user_id=user_id,
            params={"page": page, "per_page": per_page},
        )

    def get(self, user_id: str, profile_id: str) -> dict[str, Any]:
        """
        Get an exposure profile.
        
        Args:
            user_id: ID of the user
            profile_id: ID of the profile
            
        Returns:
            Exposure profile data
        """
        return self._client._request(
            "GET",
            f"/exposure-profiles/{profile_id}",
            user_id=user_id,
        )

    def update(
        self,
        user_id: str,
        profile_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        scope: Optional[dict[str, Any]] = None,
        is_default: Optional[bool] = None,
    ) -> dict[str, Any]:
        """
        Update an exposure profile.
        
        Args:
            user_id: ID of the user
            profile_id: ID of the profile
            name: New name
            description: New description
            scope: New scope
            is_default: Set as default profile
            
        Returns:
            Updated exposure profile data
        """
        payload: dict[str, Any] = {}
        
        if name is not None:
            payload["name"] = name
        if description is not None:
            payload["description"] = description
        if scope is not None:
            payload["scope"] = scope
        if is_default is not None:
            payload["is_default"] = is_default
        
        return self._client._request(
            "PUT",
            f"/exposure-profiles/{profile_id}",
            user_id=user_id,
            json=payload,
        )

    def delete(self, user_id: str, profile_id: str) -> None:
        """
        Delete an exposure profile.
        
        Args:
            user_id: ID of the user
            profile_id: ID of the profile
        """
        self._client._request(
            "DELETE",
            f"/exposure-profiles/{profile_id}",
            user_id=user_id,
        )


