"""
OfSelf Python SDK

Official Python SDK for the OfSelf API - Personal data sovereignty platform.

Usage:
    from ofself import OfSelfClient
    
    client = OfSelfClient(api_key="your-api-key")
    
    # Create a node
    node = client.nodes.create(
        user_id="user-123",
        title="My Note",
        value="Hello world!"
    )
    
    # List nodes
    nodes = client.nodes.list(user_id="user-123")
"""

from ofself.client import OfSelfClient
from ofself.exceptions import (
    OfSelfError,
    AuthenticationError,
    PermissionDenied,
    NotFoundError,
    ValidationError,
    RateLimitError,
    ServerError,
)

__version__ = "0.1.0"
__all__ = [
    "OfSelfClient",
    "OfSelfError",
    "AuthenticationError",
    "PermissionDenied",
    "NotFoundError",
    "ValidationError",
    "RateLimitError",
    "ServerError",
]


