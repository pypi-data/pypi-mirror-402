"""
OfSelf SDK Exceptions

All exceptions raised by the SDK inherit from OfSelfError.
"""

from typing import Any, Optional


class OfSelfError(Exception):
    """Base exception for all OfSelf SDK errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_body: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_body = response_body or {}

    def __str__(self) -> str:
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message


class AuthenticationError(OfSelfError):
    """
    Raised when authentication fails.
    
    This usually means:
    - Invalid or expired API key
    - Missing API key
    - Invalid OAuth token
    """
    pass


class PermissionDenied(OfSelfError):
    """
    Raised when the authenticated user doesn't have permission.
    
    This usually means:
    - User hasn't granted access to the requested resource
    - Exposure profile doesn't include the requested data
    - Third-party app not authorized
    """
    pass


class NotFoundError(OfSelfError):
    """
    Raised when a requested resource doesn't exist.
    
    This could mean:
    - Invalid ID
    - Resource was deleted
    - Resource belongs to a different user
    """
    pass


class ValidationError(OfSelfError):
    """
    Raised when request validation fails.
    
    Check the response_body for field-specific errors.
    """
    
    @property
    def errors(self) -> dict[str, Any]:
        """Get field-specific validation errors."""
        return self.response_body.get("errors", {})


class RateLimitError(OfSelfError):
    """
    Raised when rate limit is exceeded.
    
    Check retry_after for when to retry.
    """
    
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_body: Optional[dict[str, Any]] = None,
        retry_after: Optional[int] = None,
    ) -> None:
        super().__init__(message, status_code, response_body)
        self.retry_after = retry_after


class ServerError(OfSelfError):
    """
    Raised when the API returns a 5xx error.
    
    This indicates a problem on the server side.
    Consider retrying after a brief delay.
    """
    pass


class ConnectionError(OfSelfError):
    """
    Raised when unable to connect to the API.
    
    This could mean:
    - Network issues
    - API is down
    - Invalid base URL
    """
    pass


