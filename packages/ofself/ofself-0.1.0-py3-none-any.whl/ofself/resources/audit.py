"""
Audit Resource

Access audit logs for user data changes.
"""

from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from ofself.client import OfSelfClient


class AuditResource:
    """
    Access audit logs.
    
    Audit logs track all changes to user data, including:
    - Who made the change
    - What was changed
    - When it happened
    - Previous and new values
    
    Usage:
        # List recent audit logs
        logs = client.audit.list(user_id="user-123")
        
        # Get specific log entry
        log = client.audit.get(user_id="user-123", log_id="log-456")
    """

    def __init__(self, client: "OfSelfClient") -> None:
        self._client = client

    def list(
        self,
        user_id: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        action: Optional[str] = None,
        page: int = 1,
        per_page: int = 50,
    ) -> dict[str, Any]:
        """
        List audit logs.
        
        Args:
            user_id: ID of the user
            resource_type: Filter by resource type (node, tag, file, etc.)
            resource_id: Filter by specific resource ID
            action: Filter by action (create, update, delete)
            page: Page number
            per_page: Items per page
            
        Returns:
            Paginated list of audit logs
        """
        params: dict[str, Any] = {
            "page": page,
            "per_page": per_page,
        }
        
        if resource_type:
            params["resource_type"] = resource_type
        if resource_id:
            params["resource_id"] = resource_id
        if action:
            params["action"] = action
        
        return self._client._request(
            "GET",
            "/audit-logs",
            user_id=user_id,
            params=params,
        )

    def get(self, user_id: str, log_id: str) -> dict[str, Any]:
        """
        Get a specific audit log entry.
        
        Args:
            user_id: ID of the user
            log_id: ID of the audit log
            
        Returns:
            Audit log with full details
        """
        return self._client._request(
            "GET",
            f"/audit-logs/{log_id}",
            user_id=user_id,
        )


