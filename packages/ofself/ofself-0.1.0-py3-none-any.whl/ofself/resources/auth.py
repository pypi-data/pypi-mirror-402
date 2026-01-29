"""
Auth Resource

User authentication endpoints (for user-facing apps, not third-party API access).
"""

from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from ofself.client import OfSelfClient


class AuthResource:
    """
    User authentication.
    
    Note: Most SDK users will use API keys, not user auth.
    This is for building user-facing applications.
    
    Usage:
        # Register a new user
        user = client.auth.register(
            email="user@example.com",
            password="secure-password",
            username="johndoe"
        )
        
        # Login
        tokens = client.auth.login(
            email="user@example.com",
            password="secure-password"
        )
        
        # Get current user
        me = client.auth.me(access_token=tokens["access_token"])
    """

    def __init__(self, client: "OfSelfClient") -> None:
        self._client = client

    def register(
        self,
        email: str,
        password: str,
        username: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Register a new user.
        
        Args:
            email: User's email
            password: User's password
            username: Optional username
            
        Returns:
            Created user data with tokens
        """
        payload: dict[str, Any] = {
            "email": email,
            "password": password,
        }
        if username:
            payload["username"] = username
        
        return self._client._request("POST", "/auth/register", json=payload)

    def login(self, email: str, password: str) -> dict[str, Any]:
        """
        Login with email and password.
        
        Args:
            email: User's email
            password: User's password
            
        Returns:
            Access token, refresh token, and user data
        """
        return self._client._request(
            "POST",
            "/auth/login",
            json={"email": email, "password": password},
        )

    def refresh(self, refresh_token: str) -> dict[str, Any]:
        """
        Refresh an access token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            New access token and refresh token
        """
        return self._client._request(
            "POST",
            "/auth/refresh",
            json={"refresh_token": refresh_token},
        )

    def me(self, access_token: Optional[str] = None) -> dict[str, Any]:
        """
        Get current authenticated user.
        
        Args:
            access_token: JWT access token (uses API key if not provided)
            
        Returns:
            Current user data
        """
        # Note: This would need special handling for JWT vs API key auth
        return self._client._request("GET", "/auth/me")

    def logout(self) -> None:
        """Logout current user (invalidate tokens)."""
        self._client._request("POST", "/auth/logout")


