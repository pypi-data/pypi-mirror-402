from __future__ import annotations

"""
Files Resource

Manage user file uploads.
"""

from pathlib import Path
from typing import TYPE_CHECKING, Any, BinaryIO, Optional, Union

if TYPE_CHECKING:
    from ofself.client import OfSelfClient


class FilesResource:
    """
    Manage file uploads.
    
    Usage:
        # Upload a file
        file = client.files.upload(
            user_id="user-123",
            file_path="/path/to/document.pdf",
            tag_ids=["tag-work"]
        )
        
        # List files
        files = client.files.list(user_id="user-123")
        
        # Download a file
        content = client.files.download(user_id="user-123", file_id="file-456")
    """

    def __init__(self, client: "OfSelfClient") -> None:
        self._client = client

    def upload(
        self,
        user_id: str,
        file: Union[str, Path, BinaryIO],
        filename: Optional[str] = None,
        content_type: Optional[str] = None,
        tag_ids: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Upload a file.
        
        Args:
            user_id: ID of the user
            file: File path, Path object, or file-like object
            filename: Override filename (optional)
            content_type: Override content type (optional)
            tag_ids: Tags to apply to the file
            metadata: Additional metadata
            
        Returns:
            Uploaded file data
        """
        # Handle different file input types
        if isinstance(file, (str, Path)):
            path = Path(file)
            file_obj = open(path, "rb")
            fname = filename or path.name
            should_close = True
        else:
            file_obj = file
            fname = filename or getattr(file, "name", "upload")
            should_close = False
        
        try:
            files = {"file": (fname, file_obj, content_type or "application/octet-stream")}
            
            data: dict[str, Any] = {}
            if tag_ids:
                data["tag_ids"] = ",".join(tag_ids)
            if metadata:
                import json
                data["metadata"] = json.dumps(metadata)
            
            return self._client._request(
                "POST",
                "/raw-files",
                user_id=user_id,
                files=files,
                data=data if data else None,
            )
        finally:
            if should_close:
                file_obj.close()

    def list(
        self,
        user_id: str,
        tag_ids: Optional[list[str]] = None,
        content_type: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        per_page: int = 50,
    ) -> dict[str, Any]:
        """
        List files with optional filters.
        
        Args:
            user_id: ID of the user
            tag_ids: Filter by tag IDs
            content_type: Filter by content type
            search: Search in filename
            page: Page number
            per_page: Items per page
            
        Returns:
            Paginated list of files
        """
        params: dict[str, Any] = {
            "page": page,
            "per_page": per_page,
        }
        
        if tag_ids:
            params["tag_ids"] = ",".join(tag_ids)
        if content_type:
            params["content_type"] = content_type
        if search:
            params["search"] = search
        
        return self._client._request(
            "GET",
            "/raw-files",
            user_id=user_id,
            params=params,
        )

    def get(self, user_id: str, file_id: str) -> dict[str, Any]:
        """
        Get file metadata.
        
        Args:
            user_id: ID of the user
            file_id: ID of the file
            
        Returns:
            File metadata
        """
        return self._client._request(
            "GET",
            f"/raw-files/{file_id}",
            user_id=user_id,
        )

    def download(self, user_id: str, file_id: str) -> bytes:
        """
        Download file content.
        
        Args:
            user_id: ID of the user
            file_id: ID of the file
            
        Returns:
            File content as bytes
        """
        return self._client._request(
            "GET",
            f"/raw-files/{file_id}/download",
            user_id=user_id,
        )

    def update(
        self,
        user_id: str,
        file_id: str,
        filename: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Update file metadata.
        
        Args:
            user_id: ID of the user
            file_id: ID of the file
            filename: New filename (optional)
            metadata: New metadata (optional)
            
        Returns:
            Updated file data
        """
        payload: dict[str, Any] = {}
        
        if filename is not None:
            payload["filename"] = filename
        if metadata is not None:
            payload["metadata"] = metadata
        
        return self._client._request(
            "PUT",
            f"/raw-files/{file_id}",
            user_id=user_id,
            json=payload,
        )

    def delete(self, user_id: str, file_id: str) -> None:
        """
        Delete a file.
        
        Args:
            user_id: ID of the user
            file_id: ID of the file
        """
        self._client._request(
            "DELETE",
            f"/raw-files/{file_id}",
            user_id=user_id,
        )

    def add_tag(self, user_id: str, file_id: str, tag_id: str) -> dict[str, Any]:
        """
        Add a tag to a file.
        
        Args:
            user_id: ID of the user
            file_id: ID of the file
            tag_id: ID of the tag
            
        Returns:
            Updated file data
        """
        return self._client._request(
            "POST",
            f"/raw-files/{file_id}/tags",
            user_id=user_id,
            json={"tag_id": tag_id},
        )

    def remove_tag(self, user_id: str, file_id: str, tag_id: str) -> dict[str, Any]:
        """
        Remove a tag from a file.
        
        Args:
            user_id: ID of the user
            file_id: ID of the file
            tag_id: ID of the tag
            
        Returns:
            Updated file data
        """
        return self._client._request(
            "DELETE",
            f"/raw-files/{file_id}/tags/{tag_id}",
            user_id=user_id,
        )


