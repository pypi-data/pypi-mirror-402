"""
OfSelf Client

Main client class for interacting with the OfSelf API.
"""

from typing import Any, Optional
import httpx

from ofself.exceptions import (
    OfSelfError,
    AuthenticationError,
    PermissionDenied,
    NotFoundError,
    ValidationError,
    RateLimitError,
    ServerError,
    ConnectionError,
)
from ofself.resources.auth import AuthResource
from ofself.resources.users import UsersResource
from ofself.resources.nodes import NodesResource
from ofself.resources.tags import TagsResource
from ofself.resources.files import FilesResource
from ofself.resources.relationships import RelationshipsResource
from ofself.resources.embeddings import EmbeddingsResource
from ofself.resources.graph import GraphResource
from ofself.resources.exposure_profiles import ExposureProfilesResource
from ofself.resources.sharing import SharingResource
from ofself.resources.authorizations import AuthorizationsResource
from ofself.resources.proposals import ProposalsResource
from ofself.resources.audit import AuditResource
from ofself.resources.webhooks import WebhooksResource
from ofself.resources.follows import FollowsResource
from ofself.resources.history import HistoryResource
from ofself.resources.third_party import ThirdPartyResource


DEFAULT_BASE_URL = "https://api.ofself.ai/api/v1"
DEFAULT_TIMEOUT = 30.0


class OfSelfClient:
    """
    Main client for the OfSelf API.
    
    Args:
        api_key: Your API key from the developer dashboard
        base_url: API base URL (default: https://api.ofself.ai/api/v1)
        timeout: Request timeout in seconds (default: 30)
        
    Usage:
        client = OfSelfClient(api_key="your-api-key")
        
        # Create a node
        node = client.nodes.create(
            user_id="user-123",
            title="My Note",
            value="Hello world!"
        )
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        access_token: Optional[str] = None,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        if not api_key and not access_token:
            raise ValueError("Either api_key or access_token is required")

        self.api_key = api_key
        self.access_token = access_token
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        
        # Initialize HTTP client
        base_headers: dict[str, str] = {
            "Accept": "application/json",
            "User-Agent": "ofself-python/0.1.0",
        }
        if access_token:
            base_headers["Authorization"] = f"Bearer {access_token}"
        elif api_key:
            base_headers["X-API-Key"] = api_key
            base_headers["Content-Type"] = "application/json"

        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
            headers=base_headers,
        )
        
        # Initialize resource namespaces
        self.auth = AuthResource(self)
        self.users = UsersResource(self)
        self.nodes = NodesResource(self)
        self.tags = TagsResource(self)
        self.files = FilesResource(self)
        self.relationships = RelationshipsResource(self)
        self.embeddings = EmbeddingsResource(self)
        self.graph = GraphResource(self)
        self.exposure_profiles = ExposureProfilesResource(self)
        self.sharing = SharingResource(self)
        self.authorizations = AuthorizationsResource(self)
        self.proposals = ProposalsResource(self)
        self.audit = AuditResource(self)
        self.webhooks = WebhooksResource(self)
        self.follows = FollowsResource(self)
        self.history = HistoryResource(self)
        self.third_party = ThirdPartyResource(self)

    def _request(
        self,
        method: str,
        path: str,
        user_id: Optional[str] = None,
        params: Optional[dict[str, Any]] = None,
        json: Optional[dict[str, Any]] = None,
        data: Optional[dict[str, Any]] = None,
        files: Optional[dict[str, Any]] = None,
    ) -> Any:
        """
        Make an HTTP request to the API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE, PATCH)
            path: API path (e.g., "/nodes")
            user_id: User ID to act on behalf of
            params: Query parameters
            json: JSON request body
            data: Form data
            files: File uploads
            
        Returns:
            Parsed JSON response
            
        Raises:
            OfSelfError: On API errors
        """
        headers: dict[str, str] = {}

        # Add user ID header if provided (only needed for API key auth)
        if user_id and self.api_key and not self.access_token:
            headers["X-User-ID"] = user_id
        
        # Don't send Content-Type for file uploads (httpx handles it)
        if files:
            headers["Content-Type"] = ""
        
        try:
            response = self._client.request(
                method=method,
                url=path,
                params=params,
                json=json,
                data=data,
                files=files,
                headers=headers,
            )
        except httpx.ConnectError as e:
            raise ConnectionError(f"Failed to connect to API: {e}") from e
        except httpx.TimeoutException as e:
            raise ConnectionError(f"Request timed out: {e}") from e
        
        return self._handle_response(response)

    def _handle_response(self, response: httpx.Response) -> Any:
        """
        Handle API response and raise appropriate exceptions.
        """
        # Success responses
        if response.status_code in (200, 201):
            if response.headers.get("content-type", "").startswith("application/json"):
                return response.json()
            return response.content
        
        # No content (successful delete)
        if response.status_code == 204:
            return None
        
        # Parse error response
        try:
            error_body = response.json()
            err = error_body.get("error")
            message = (
                error_body.get("message")
                or (err.get("message") if isinstance(err, dict) else err)
                or "Unknown error"
            )
        except Exception:
            error_body = {}
            message = response.text or f"HTTP {response.status_code}"
        
        # Map status codes to exceptions
        status = response.status_code
        
        if status == 401:
            raise AuthenticationError(message, status, error_body)
        
        if status == 403:
            raise PermissionDenied(message, status, error_body)
        
        if status == 404:
            raise NotFoundError(message, status, error_body)
        
        if status == 422 or status == 400:
            raise ValidationError(message, status, error_body)
        
        if status == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(
                message,
                status,
                error_body,
                retry_after=int(retry_after) if retry_after else None,
            )
        
        if status >= 500:
            raise ServerError(message, status, error_body)
        
        raise OfSelfError(message, status, error_body)

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self) -> "OfSelfClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()


class AsyncOfSelfClient:
    """
    Async client for the OfSelf API.
    
    Usage:
        async with AsyncOfSelfClient(api_key="your-api-key") as client:
            node = await client.nodes.create(...)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        access_token: Optional[str] = None,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        if not api_key and not access_token:
            raise ValueError("Either api_key or access_token is required")
        
        self.api_key = api_key
        self.access_token = access_token
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        
        base_headers: dict[str, str] = {
            "Accept": "application/json",
            "User-Agent": "ofself-python/0.1.0",
        }
        if access_token:
            base_headers["Authorization"] = f"Bearer {access_token}"
        elif api_key:
            base_headers["X-API-Key"] = api_key
            base_headers["Content-Type"] = "application/json"

        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
            headers=base_headers,
        )
        
        # Note: Async resources would need to be implemented separately
        # For now, we'll keep sync resources and async _request

    async def _request(
        self,
        method: str,
        path: str,
        user_id: Optional[str] = None,
        params: Optional[dict[str, Any]] = None,
        json: Optional[dict[str, Any]] = None,
    ) -> Any:
        """Make an async HTTP request."""
        headers: dict[str, str] = {}
        if user_id and self.api_key and not self.access_token:
            headers["X-User-ID"] = user_id
        
        try:
            response = await self._client.request(
                method=method,
                url=path,
                params=params,
                json=json,
                headers=headers,
            )
        except httpx.ConnectError as e:
            raise ConnectionError(f"Failed to connect to API: {e}") from e
        except httpx.TimeoutException as e:
            raise ConnectionError(f"Request timed out: {e}") from e
        
        return self._handle_response(response)

    def _handle_response(self, response: httpx.Response) -> Any:
        """Handle API response (same logic as sync client)."""
        # Reuse the same logic from OfSelfClient
        if response.status_code in (200, 201):
            if response.headers.get("content-type", "").startswith("application/json"):
                return response.json()
            return response.content
        
        if response.status_code == 204:
            return None
        
        try:
            error_body = response.json()
            err = error_body.get("error")
            message = (
                error_body.get("message")
                or (err.get("message") if isinstance(err, dict) else err)
                or "Unknown error"
            )
        except Exception:
            error_body = {}
            message = response.text or f"HTTP {response.status_code}"
        
        status = response.status_code
        
        if status == 401:
            raise AuthenticationError(message, status, error_body)
        if status == 403:
            raise PermissionDenied(message, status, error_body)
        if status == 404:
            raise NotFoundError(message, status, error_body)
        if status == 422 or status == 400:
            raise ValidationError(message, status, error_body)
        if status == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(
                message, status, error_body,
                retry_after=int(retry_after) if retry_after else None,
            )
        if status >= 500:
            raise ServerError(message, status, error_body)
        
        raise OfSelfError(message, status, error_body)

    async def close(self) -> None:
        """Close the async HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> "AsyncOfSelfClient":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

