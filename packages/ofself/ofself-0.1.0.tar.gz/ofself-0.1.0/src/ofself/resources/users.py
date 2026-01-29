"""
Users Resource

User profile and API key management.
"""

from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from ofself.client import OfSelfClient


class UsersResource:
    """
    Manage user profiles and API keys.
    
    Usage:
        # Get user profile
        user = client.users.get(user_id="user-123")
        
        # Update profile
        client.users.update(user_id="user-123", username="newname")
        
        # Manage API keys
        keys = client.users.list_api_keys(user_id="user-123")
        new_key = client.users.create_api_key(user_id="user-123", name="My App")
    """

    def __init__(self, client: "OfSelfClient") -> None:
        self._client = client

    def get(self, user_id: str) -> dict[str, Any]:
        """
        Get user profile.
        
        Args:
            user_id: ID of the user
            
        Returns:
            User profile data
        """
        return self._client._request("GET", f"/users/{user_id}")

    def update(
        self,
        user_id: str,
        username: Optional[str] = None,
        email: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Update user profile.
        
        Args:
            user_id: ID of the user
            username: New username
            email: New email
            metadata: Additional profile data
            
        Returns:
            Updated user data
        """
        payload: dict[str, Any] = {}
        if username:
            payload["username"] = username
        if email:
            payload["email"] = email
        if metadata:
            payload["metadata"] = metadata
        
        return self._client._request("PUT", f"/users/{user_id}", json=payload)

    def change_password(
        self,
        user_id: str,
        current_password: str,
        new_password: str,
    ) -> dict[str, Any]:
        """
        Change user's password.
        
        Args:
            user_id: ID of the user
            current_password: Current password
            new_password: New password
            
        Returns:
            Success confirmation
        """
        return self._client._request(
            "PUT",
            "/users/me/password",
            user_id=user_id,
            json={
                "current_password": current_password,
                "new_password": new_password,
            },
        )

    def search(
        self,
        query: str,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        """
        Search for users.
        
        Args:
            query: Search query (email or username)
            page: Page number
            per_page: Results per page
            
        Returns:
            List of matching users
        """
        return self._client._request(
            "GET",
            "/users/search",
            params={"q": query, "page": page, "per_page": per_page},
        )

    # API Key Management

    def list_api_keys(self, user_id: str) -> list[dict[str, Any]]:
        """
        List user's API keys.
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of API keys (without secrets)
        """
        return self._client._request("GET", "/users/me/api-keys", user_id=user_id)

    def create_api_key(
        self,
        user_id: str,
        name: str,
        scopes: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """
        Create a new API key.
        
        Args:
            user_id: ID of the user
            name: Name for the API key
            scopes: Optional permission scopes
            
        Returns:
            Created API key (including secret - shown only once!)
        """
        payload: dict[str, Any] = {"name": name}
        if scopes:
            payload["scopes"] = scopes
        
        return self._client._request(
            "POST",
            "/users/me/api-keys",
            user_id=user_id,
            json=payload,
        )

    def delete_api_key(self, user_id: str, api_key_id: str) -> None:
        """
        Delete an API key.
        
        Args:
            user_id: ID of the user
            api_key_id: ID of the API key to delete
        """
        self._client._request(
            "DELETE",
            f"/users/me/api-keys/{api_key_id}",
            user_id=user_id,
        )


