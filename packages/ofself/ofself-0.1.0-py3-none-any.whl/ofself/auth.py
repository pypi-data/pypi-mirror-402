"""
OfSelf OAuth Helpers

Utilities for implementing OAuth 2.0 authorization flow.
"""

from typing import Optional
from urllib.parse import urlencode


class OAuthHelper:
    """
    Helper class for OAuth 2.0 authorization with OfSelf.
    
    Usage:
        oauth = OAuthHelper(
            client_id="your-client-id",
            client_secret="your-client-secret",
            redirect_uri="https://yourapp.com/callback"
        )
        
        # Step 1: Get authorization URL
        auth_url = oauth.get_authorization_url(
            scopes=["nodes:read", "tags:read"],
            state="random-state-string"
        )
        # Redirect user to auth_url
        
        # Step 2: Handle callback and exchange code for tokens
        tokens = oauth.exchange_code(code="authorization-code-from-callback")
        
        # Step 3: Use the access token
        client = OfSelfClient(api_key=tokens["access_token"])
    """

    BASE_URL = "https://api.ofself.ai"

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        base_url: Optional[str] = None,
    ) -> None:
        """
        Initialize OAuth helper.
        
        Args:
            client_id: Your app's client ID
            client_secret: Your app's client secret
            redirect_uri: URL to redirect after authorization
            base_url: Custom API base URL (optional)
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.base_url = (base_url or self.BASE_URL).rstrip("/")

    def get_authorization_url(
        self,
        scopes: list[str],
        state: Optional[str] = None,
    ) -> str:
        """
        Get the URL to redirect users to for authorization.
        
        Args:
            scopes: List of scopes to request (e.g., ["nodes:read", "tags:read"])
            state: Random string to prevent CSRF attacks
            
        Returns:
            Authorization URL to redirect users to
            
        Available scopes:
            - nodes:read - Read nodes
            - nodes:write - Create/update/delete nodes
            - tags:read - Read tags
            - tags:write - Create/update/delete tags
            - files:read - Read files
            - files:write - Upload/update/delete files
            - relationships:read - Read relationships
            - relationships:write - Create/update/delete relationships
            - proposals:write - Create proposals
        """
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(scopes),
        }
        
        if state:
            params["state"] = state
        
        return f"{self.base_url}/oauth/authorize?{urlencode(params)}"

    def exchange_code(self, code: str) -> dict:
        """
        Exchange authorization code for access and refresh tokens.
        
        Args:
            code: Authorization code from callback
            
        Returns:
            Dictionary with access_token, refresh_token, expires_in, token_type
        """
        import httpx
        
        response = httpx.post(
            f"{self.base_url}/oauth/token",
            data={
                "grant_type": "authorization_code",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uri": self.redirect_uri,
                "code": code,
            },
        )
        response.raise_for_status()
        return response.json()

    def refresh_tokens(self, refresh_token: str) -> dict:
        """
        Refresh an expired access token.
        
        Args:
            refresh_token: Refresh token from previous authorization
            
        Returns:
            Dictionary with new access_token, refresh_token, expires_in
        """
        import httpx
        
        response = httpx.post(
            f"{self.base_url}/oauth/token",
            data={
                "grant_type": "refresh_token",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": refresh_token,
            },
        )
        response.raise_for_status()
        return response.json()


# Available OAuth scopes
SCOPES = {
    "nodes:read": "Read user nodes",
    "nodes:write": "Create, update, and delete nodes",
    "tags:read": "Read user tags",
    "tags:write": "Create, update, and delete tags",
    "files:read": "Read user files",
    "files:write": "Upload, update, and delete files",
    "relationships:read": "Read node relationships",
    "relationships:write": "Create, update, and delete relationships",
    "proposals:write": "Create proposals for data changes",
    "exposure_profiles:read": "Read exposure profiles",
    "exposure_profiles:write": "Create and manage exposure profiles",
    "sharing:read": "View sharing settings",
    "sharing:write": "Create and revoke shares",
}


