"""
Drafts Resource

Resource for managing email drafts.
"""

from typing import TYPE_CHECKING, Dict, List, Optional, Union

from jasni.types import (
    CreateDraftResponse,
    GetDraftResponse,
    ListDraftsResponse,
    SendDraftResponse,
    UpdateDraftResponse,
)

if TYPE_CHECKING:
    from jasni.http import AsyncHttpClient, HttpClient


class DraftsResource:
    """
    Resource for managing email drafts (synchronous).
    
    Example:
        >>> drafts = jasni.drafts.list(account="me@mail.jasni.ai")
        >>> for draft in drafts.drafts:
        ...     print(f"- {draft.subject}")
    """
    
    def __init__(self, http: "HttpClient") -> None:
        self._http = http
    
    def list(
        self,
        *,
        account: str,
        limit: Optional[int] = None
    ) -> ListDraftsResponse:
        """
        List all drafts for an email account.
        
        Args:
            account: Email account
            limit: Maximum number of drafts. Default: 50
        
        Returns:
            ListDraftsResponse with draft emails
        
        Example:
            >>> drafts = jasni.drafts.list(
            ...     account="me@mail.jasni.ai",
            ...     limit=50
            ... )
        """
        data = self._http.get("/api/v1/emails/drafts", query={
            "account": account,
            "limit": limit,
        })
        return ListDraftsResponse(**data)
    
    def create(
        self,
        *,
        account: str,
        to: Optional[Union[str, List[str]]] = None,
        subject: Optional[str] = None,
        text: Optional[str] = None,
        html: Optional[str] = None,
        cc: Optional[Union[str, List[str]]] = None
    ) -> CreateDraftResponse:
        """
        Create a new draft email.
        
        Args:
            account: Email account
            to: Recipient email address(es)
            subject: Email subject
            text: Plain text body
            html: HTML body
            cc: CC recipients
        
        Returns:
            CreateDraftResponse with the UID of the created draft
        
        Example:
            >>> draft = jasni.drafts.create(
            ...     account="me@mail.jasni.ai",
            ...     to="recipient@example.com",
            ...     subject="Draft subject",
            ...     text="Draft body"
            ... )
            >>> print(f"Created draft with UID: {draft.uid}")
        """
        data = self._http.post("/api/v1/emails/drafts", body={
            "account": account,
            "to": to,
            "subject": subject,
            "text": text,
            "html": html,
            "cc": cc,
        })
        return CreateDraftResponse(**data)
    
    def update(
        self,
        *,
        account: str,
        uid: int,
        to: Optional[Union[str, List[str]]] = None,
        subject: Optional[str] = None,
        text: Optional[str] = None,
        html: Optional[str] = None,
        cc: Optional[Union[str, List[str]]] = None
    ) -> UpdateDraftResponse:
        """
        Update an existing draft email.
        This replaces the existing draft with the new content.
        
        Args:
            account: Email account
            uid: UID of the draft to update
            to: Recipient email address(es)
            subject: Email subject
            text: Plain text body
            html: HTML body
            cc: CC recipients
        
        Returns:
            UpdateDraftResponse with the UID of the updated draft
        
        Example:
            >>> draft = jasni.drafts.update(
            ...     account="me@mail.jasni.ai",
            ...     uid=123,
            ...     subject="Updated subject",
            ...     text="Updated body"
            ... )
        """
        data = self._http.put("/api/v1/emails/drafts", body={
            "account": account,
            "uid": uid,
            "to": to,
            "subject": subject,
            "text": text,
            "html": html,
            "cc": cc,
        })
        return UpdateDraftResponse(**data)
    
    def delete(
        self,
        *,
        account: str,
        uid: int
    ) -> Dict[str, str]:
        """
        Delete a draft email.
        
        Args:
            account: Email account
            uid: UID of the draft to delete
        
        Returns:
            Dict with success message
        
        Example:
            >>> jasni.drafts.delete(account="me@mail.jasni.ai", uid=123)
        """
        return self._http.delete("/api/v1/emails/drafts", query={
            "account": account,
            "uid": uid,
        })
    
    def get(
        self,
        uid: int,
        *,
        account: str
    ) -> GetDraftResponse:
        """
        Get a specific draft email by UID.
        
        Args:
            uid: UID of the draft to retrieve
            account: Email account
        
        Returns:
            GetDraftResponse with the full draft email
        
        Example:
            >>> draft = jasni.drafts.get(123, account="me@mail.jasni.ai")
            >>> print(f"Subject: {draft.email.subject}")
        """
        data = self._http.get(f"/api/v1/emails/{uid}", query={
            "account": account,
            "folder": "Drafts",
        })
        return GetDraftResponse(**data)
    
    def send(
        self,
        *,
        account: str,
        uid: int
    ) -> SendDraftResponse:
        """
        Send a draft email and remove it from the Drafts folder.
        
        Args:
            account: Email account
            uid: UID of the draft to send
        
        Returns:
            SendDraftResponse with message ID and send details
        
        Example:
            >>> result = jasni.drafts.send(account="me@mail.jasni.ai", uid=123)
            >>> print(f"Sent with message ID: {result.message_id}")
        """
        data = self._http.post(f"/api/v1/emails/drafts/{uid}/send", body={
            "account": account,
        })
        return SendDraftResponse(**data)


class AsyncDraftsResource:
    """
    Resource for managing email drafts (asynchronous).
    """
    
    def __init__(self, http: "AsyncHttpClient") -> None:
        self._http = http
    
    async def list(
        self,
        *,
        account: str,
        limit: Optional[int] = None
    ) -> ListDraftsResponse:
        """List all drafts for an email account."""
        data = await self._http.get("/api/v1/emails/drafts", query={
            "account": account,
            "limit": limit,
        })
        return ListDraftsResponse(**data)
    
    async def create(
        self,
        *,
        account: str,
        to: Optional[Union[str, List[str]]] = None,
        subject: Optional[str] = None,
        text: Optional[str] = None,
        html: Optional[str] = None,
        cc: Optional[Union[str, List[str]]] = None
    ) -> CreateDraftResponse:
        """Create a new draft email."""
        data = await self._http.post("/api/v1/emails/drafts", body={
            "account": account,
            "to": to,
            "subject": subject,
            "text": text,
            "html": html,
            "cc": cc,
        })
        return CreateDraftResponse(**data)
    
    async def update(
        self,
        *,
        account: str,
        uid: int,
        to: Optional[Union[str, List[str]]] = None,
        subject: Optional[str] = None,
        text: Optional[str] = None,
        html: Optional[str] = None,
        cc: Optional[Union[str, List[str]]] = None
    ) -> UpdateDraftResponse:
        """Update an existing draft email."""
        data = await self._http.put("/api/v1/emails/drafts", body={
            "account": account,
            "uid": uid,
            "to": to,
            "subject": subject,
            "text": text,
            "html": html,
            "cc": cc,
        })
        return UpdateDraftResponse(**data)
    
    async def delete(
        self,
        *,
        account: str,
        uid: int
    ) -> Dict[str, str]:
        """Delete a draft email."""
        return await self._http.delete("/api/v1/emails/drafts", query={
            "account": account,
            "uid": uid,
        })
    
    async def get(
        self,
        uid: int,
        *,
        account: str
    ) -> GetDraftResponse:
        """Get a specific draft email by UID."""
        data = await self._http.get(f"/api/v1/emails/{uid}", query={
            "account": account,
            "folder": "Drafts",
        })
        return GetDraftResponse(**data)
    
    async def send(
        self,
        *,
        account: str,
        uid: int
    ) -> SendDraftResponse:
        """Send a draft email and remove it from the Drafts folder."""
        data = await self._http.post(f"/api/v1/emails/drafts/{uid}/send", body={
            "account": account,
        })
        return SendDraftResponse(**data)
