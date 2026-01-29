"""
Webhooks Resource

Manage webhook subscriptions for real-time events.
"""

from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from ofself.client import OfSelfClient


class WebhooksResource:
    """
    Manage webhook subscriptions.
    
    Webhooks allow your app to receive real-time notifications
    when user data changes.
    
    Usage:
        # Subscribe to events
        sub = client.webhooks.subscribe(
            url="https://myapp.com/webhooks",
            events=["node.created", "node.updated"]
        )
        
        # Get current subscription
        sub = client.webhooks.get_subscription()
        
        # Unsubscribe
        client.webhooks.unsubscribe()
    """

    def __init__(self, client: "OfSelfClient") -> None:
        self._client = client

    def subscribe(
        self,
        url: str,
        events: list[str],
        secret: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Subscribe to webhook events.
        
        Args:
            url: URL to receive webhook POST requests
            events: List of events to subscribe to:
                - node.created
                - node.updated
                - node.deleted
                - tag.created
                - tag.updated
                - tag.deleted
                - file.uploaded
                - file.deleted
                - relationship.created
                - relationship.deleted
            secret: Optional shared secret for HMAC verification
            
        Returns:
            Subscription details including generated secret if not provided
        """
        payload: dict[str, Any] = {
            "url": url,
            "events": events,
        }
        
        if secret:
            payload["secret"] = secret
        
        return self._client._request("POST", "/subscribe", json=payload)

    def get_subscription(self) -> dict[str, Any]:
        """
        Get current webhook subscription.
        
        Returns:
            Current subscription details or empty if not subscribed
        """
        return self._client._request("GET", "/subscription")

    def unsubscribe(self) -> None:
        """Unsubscribe from webhook events."""
        self._client._request("DELETE", "/subscription")


