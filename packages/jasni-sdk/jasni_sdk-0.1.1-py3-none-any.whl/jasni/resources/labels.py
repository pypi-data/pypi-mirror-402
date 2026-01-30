"""
Labels Resource

Resource for managing labels.
"""

from typing import TYPE_CHECKING, Optional

from jasni.types import CreateLabelResponse, DeleteLabelResponse, ListLabelsResponse

if TYPE_CHECKING:
    from jasni.http import AsyncHttpClient, HttpClient


class LabelsResource:
    """
    Resource for managing labels (synchronous).
    
    Example:
        >>> labels = jasni.labels.list(include_count=True)
        >>> for label in labels.labels:
        ...     print(f"- {label.name}: {label.email_count} emails")
    """
    
    def __init__(self, http: "HttpClient") -> None:
        self._http = http
    
    def list(
        self,
        *,
        include_count: bool = False
    ) -> ListLabelsResponse:
        """
        List all labels for the authenticated user.
        
        Args:
            include_count: Include email count per label. Default: False
        
        Returns:
            ListLabelsResponse with labels
        
        Example:
            >>> # List labels
            >>> labels = jasni.labels.list()
            
            >>> # List labels with email counts
            >>> labels = jasni.labels.list(include_count=True)
        """
        data = self._http.get("/api/v1/labels", query={
            "include_count": include_count,
        })
        return ListLabelsResponse(**data)
    
    def create(
        self,
        *,
        name: str,
        color: Optional[str] = None,
        description: Optional[str] = None
    ) -> CreateLabelResponse:
        """
        Create a new label.
        
        Args:
            name: Label name
            color: Hex color code (e.g., #ff0000). Auto-generated if not provided.
            description: Label description
        
        Returns:
            CreateLabelResponse with the created label
        
        Example:
            >>> label = jasni.labels.create(
            ...     name="Important",
            ...     color="#ff0000",
            ...     description="Important emails"
            ... )
            >>> print(f"Created label: {label.label.id}")
        """
        data = self._http.post("/api/v1/labels", body={
            "name": name,
            "color": color,
            "description": description,
        })
        return CreateLabelResponse(**data)
    
    def delete(self, id: str) -> DeleteLabelResponse:
        """
        Delete a label by ID.
        
        This also removes all email-label associations for this label.
        
        Args:
            id: The label ID to delete
        
        Returns:
            DeleteLabelResponse with confirmation
        
        Example:
            >>> result = jasni.labels.delete("label-id-123")
            >>> print(result.message)  # "Label deleted successfully"
        """
        data = self._http.delete("/api/v1/labels", query={"id": id})
        return DeleteLabelResponse(**data)


class AsyncLabelsResource:
    """
    Resource for managing labels (asynchronous).
    """
    
    def __init__(self, http: "AsyncHttpClient") -> None:
        self._http = http
    
    async def list(
        self,
        *,
        include_count: bool = False
    ) -> ListLabelsResponse:
        """List all labels for the authenticated user."""
        data = await self._http.get("/api/v1/labels", query={
            "include_count": include_count,
        })
        return ListLabelsResponse(**data)
    
    async def create(
        self,
        *,
        name: str,
        color: Optional[str] = None,
        description: Optional[str] = None
    ) -> CreateLabelResponse:
        """Create a new label."""
        data = await self._http.post("/api/v1/labels", body={
            "name": name,
            "color": color,
            "description": description,
        })
        return CreateLabelResponse(**data)
    
    async def delete(self, id: str) -> DeleteLabelResponse:
        """
        Delete a label by ID.
        
        This also removes all email-label associations for this label.
        """
        data = await self._http.delete("/api/v1/labels", query={"id": id})
        return DeleteLabelResponse(**data)
