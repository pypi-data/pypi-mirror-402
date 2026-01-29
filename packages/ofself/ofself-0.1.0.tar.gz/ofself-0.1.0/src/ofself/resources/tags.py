"""
Tags Resource

Manage user tags for organizing nodes and files.
"""

from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from ofself.client import OfSelfClient


class TagsResource:
    """
    Manage tags for organizing data.
    
    Usage:
        # Create a tag
        tag = client.tags.create(
            user_id="user-123",
            name="Work",
            color="#4A90D9"
        )
        
        # List tags
        tags = client.tags.list(user_id="user-123")
        
        # Get nodes with a tag
        nodes = client.tags.get_nodes(user_id="user-123", tag_id="tag-456")
    """

    def __init__(self, client: "OfSelfClient") -> None:
        self._client = client

    def create(
        self,
        user_id: str,
        name: str,
        color: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Create a new tag.
        
        Args:
            user_id: ID of the user
            name: Tag name
            color: Hex color code (e.g., "#4A90D9")
            
        Returns:
            Created tag data
        """
        payload: dict[str, Any] = {"name": name}
        
        if color:
            payload["color"] = color
        
        return self._client._request(
            "POST",
            "/tags",
            user_id=user_id,
            json=payload,
        )

    def list(
        self,
        user_id: str,
        search: Optional[str] = None,
        page: int = 1,
        per_page: int = 50,
    ) -> dict[str, Any]:
        """
        List all tags.
        
        Args:
            user_id: ID of the user
            search: Search in tag names
            page: Page number
            per_page: Items per page
            
        Returns:
            Paginated list of tags
        """
        params: dict[str, Any] = {
            "page": page,
            "per_page": per_page,
        }
        
        if search:
            params["search"] = search
        
        return self._client._request(
            "GET",
            "/tags",
            user_id=user_id,
            params=params,
        )

    def get(self, user_id: str, tag_id: str) -> dict[str, Any]:
        """
        Get a single tag by ID.
        
        Args:
            user_id: ID of the user
            tag_id: ID of the tag
            
        Returns:
            Tag data
        """
        return self._client._request(
            "GET",
            f"/tags/{tag_id}",
            user_id=user_id,
        )

    def update(
        self,
        user_id: str,
        tag_id: str,
        name: Optional[str] = None,
        color: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Update a tag.
        
        Args:
            user_id: ID of the user
            tag_id: ID of the tag
            name: New name (optional)
            color: New color (optional)
            
        Returns:
            Updated tag data
        """
        payload: dict[str, Any] = {}
        
        if name is not None:
            payload["name"] = name
        if color is not None:
            payload["color"] = color
        
        return self._client._request(
            "PUT",
            f"/tags/{tag_id}",
            user_id=user_id,
            json=payload,
        )

    def delete(self, user_id: str, tag_id: str) -> None:
        """
        Delete a tag.
        
        Args:
            user_id: ID of the user
            tag_id: ID of the tag
        """
        self._client._request(
            "DELETE",
            f"/tags/{tag_id}",
            user_id=user_id,
        )

    def get_nodes(
        self,
        user_id: str,
        tag_id: str,
        page: int = 1,
        per_page: int = 50,
    ) -> dict[str, Any]:
        """
        Get all nodes with a specific tag.
        
        Args:
            user_id: ID of the user
            tag_id: ID of the tag
            page: Page number
            per_page: Items per page
            
        Returns:
            Paginated list of nodes
        """
        return self._client._request(
            "GET",
            f"/tags/{tag_id}/nodes",
            user_id=user_id,
            params={"page": page, "per_page": per_page},
        )

    def get_files(
        self,
        user_id: str,
        tag_id: str,
        page: int = 1,
        per_page: int = 50,
    ) -> dict[str, Any]:
        """
        Get all files with a specific tag.
        
        Args:
            user_id: ID of the user
            tag_id: ID of the tag
            page: Page number
            per_page: Items per page
            
        Returns:
            Paginated list of files
        """
        return self._client._request(
            "GET",
            f"/tags/{tag_id}/files",
            user_id=user_id,
            params={"page": page, "per_page": per_page},
        )


