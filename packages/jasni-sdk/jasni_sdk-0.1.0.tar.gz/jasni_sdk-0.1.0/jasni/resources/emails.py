"""
Emails Resource

Resource for managing emails, including sending, replying, forwarding,
and managing email labels.
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from jasni.types import (
    AssignLabelsResponse,
    ForwardResponse,
    GetEmailLabelsResponse,
    GetEmailResponse,
    ListEmailsResponse,
    RemoveLabelsResponse,
    ReplyResponse,
    SendEmailResponse,
    GetAttachmentsResponse,
    GetAttachmentResponse,
    GetRawResponse,
    ListThreadsResponse,
    GetThreadResponse,
)

if TYPE_CHECKING:
    from jasni.http import AsyncHttpClient, HttpClient


class EmailLabelsResource:
    """
    Resource for managing email labels (synchronous).
    
    Example:
        >>> labels = jasni.emails.labels.list(123, account="me@mail.jasni.ai")
    """
    
    def __init__(self, http: "HttpClient") -> None:
        self._http = http
    
    def list(
        self,
        uid: Union[int, str],
        *,
        account: str,
        folder: Optional[str] = None
    ) -> GetEmailLabelsResponse:
        """
        Get all labels assigned to an email.
        
        Args:
            uid: Email UID (number) or message_id (string)
            account: Email account
            folder: Folder where the email is located. Default: INBOX
        
        Returns:
            GetEmailLabelsResponse with the email's labels
        
        Example:
            >>> labels = jasni.emails.labels.list(
            ...     123,
            ...     account="me@mail.jasni.ai"
            ... )
            >>> for label in labels.labels:
            ...     print(f"- {label.name}: {label.color}")
        """
        data = self._http.get(f"/api/v1/emails/{uid}/labels", query={
            "account": account,
            "folder": folder,
        })
        return GetEmailLabelsResponse(**data)
    
    def assign(
        self,
        uid: Union[int, str],
        *,
        account: str,
        folder: Optional[str] = None,
        label_ids: Optional[List[str]] = None,
        labels: Optional[List[str]] = None,
        agent_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AssignLabelsResponse:
        """
        Assign labels to an email.
        Can create new labels automatically if they don't exist.
        
        Args:
            uid: Email UID (number) or message_id (string)
            account: Email account
            folder: Folder where the email is located. Default: INBOX
            label_ids: Array of existing label IDs to assign
            labels: Array of label names (creates if not exists)
            agent_name: Name of the agent applying the labels
            metadata: Additional context about the categorization
        
        Returns:
            AssignLabelsResponse with assigned and created labels
        
        Example:
            >>> # Assign by label names (creates if not exists)
            >>> result = jasni.emails.labels.assign(
            ...     123,
            ...     account="me@mail.jasni.ai",
            ...     labels=["Important", "Work"],
            ...     agent_name="my-classifier"
            ... )
            
            >>> # Assign by label IDs
            >>> result = jasni.emails.labels.assign(
            ...     123,
            ...     account="me@mail.jasni.ai",
            ...     label_ids=["label-id-1", "label-id-2"]
            ... )
        """
        data = self._http.post(
            f"/api/v1/emails/{uid}/labels",
            body={
                "label_ids": label_ids,
                "labels": labels,
                "agent_name": agent_name,
                "metadata": metadata,
            },
            query={
                "account": account,
                "folder": folder,
            }
        )
        return AssignLabelsResponse(**data)
    
    def remove(
        self,
        uid: Union[int, str],
        *,
        account: str,
        label_ids: List[str],
        folder: Optional[str] = None
    ) -> RemoveLabelsResponse:
        """
        Remove labels from an email.
        
        Args:
            uid: Email UID (number) or message_id (string)
            account: Email account
            label_ids: Label IDs to remove
            folder: Folder where the email is located. Default: INBOX
        
        Returns:
            RemoveLabelsResponse with count of removed labels
        
        Example:
            >>> jasni.emails.labels.remove(
            ...     123,
            ...     account="me@mail.jasni.ai",
            ...     label_ids=["label-id-1"]
            ... )
        """
        data = self._http.delete(f"/api/v1/emails/{uid}/labels", query={
            "account": account,
            "folder": folder,
            "label_ids": ",".join(label_ids),
        })
        return RemoveLabelsResponse(**data)


class AsyncEmailLabelsResource:
    """
    Resource for managing email labels (asynchronous).
    """
    
    def __init__(self, http: "AsyncHttpClient") -> None:
        self._http = http
    
    async def list(
        self,
        uid: Union[int, str],
        *,
        account: str,
        folder: Optional[str] = None
    ) -> GetEmailLabelsResponse:
        """Get all labels assigned to an email."""
        data = await self._http.get(f"/api/v1/emails/{uid}/labels", query={
            "account": account,
            "folder": folder,
        })
        return GetEmailLabelsResponse(**data)
    
    async def assign(
        self,
        uid: Union[int, str],
        *,
        account: str,
        folder: Optional[str] = None,
        label_ids: Optional[List[str]] = None,
        labels: Optional[List[str]] = None,
        agent_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AssignLabelsResponse:
        """Assign labels to an email."""
        data = await self._http.post(
            f"/api/v1/emails/{uid}/labels",
            body={
                "label_ids": label_ids,
                "labels": labels,
                "agent_name": agent_name,
                "metadata": metadata,
            },
            query={
                "account": account,
                "folder": folder,
            }
        )
        return AssignLabelsResponse(**data)
    
    async def remove(
        self,
        uid: Union[int, str],
        *,
        account: str,
        label_ids: List[str],
        folder: Optional[str] = None
    ) -> RemoveLabelsResponse:
        """Remove labels from an email."""
        data = await self._http.delete(f"/api/v1/emails/{uid}/labels", query={
            "account": account,
            "folder": folder,
            "label_ids": ",".join(label_ids),
        })
        return RemoveLabelsResponse(**data)


class EmailsResource:
    """
    Resource for managing emails (synchronous).
    
    Example:
        >>> emails = jasni.emails.list(account="me@mail.jasni.ai")
        >>> for email in emails.emails:
        ...     print(f"- {email.subject}")
    """
    
    def __init__(self, http: "HttpClient") -> None:
        self._http = http
        self.labels = EmailLabelsResource(http)
    
    def list(
        self,
        *,
        account: str,
        folder: Optional[str] = None,
        limit: Optional[int] = None,
        label_ids: Optional[List[str]] = None,
        labels: Optional[List[str]] = None
    ) -> ListEmailsResponse:
        """
        List emails for an email account.
        
        Args:
            account: Email account to fetch from
            folder: Folder to fetch from. Default: INBOX
            limit: Number of emails to fetch. Default: 50, max: 100
            label_ids: Filter by label IDs (emails must have ALL specified labels)
            labels: Filter by label names (emails must have ALL specified labels)
        
        Returns:
            ListEmailsResponse with email previews
        
        Example:
            >>> # List all emails
            >>> emails = jasni.emails.list(
            ...     account="me@mail.jasni.ai",
            ...     folder="INBOX",
            ...     limit=20
            ... )
            
            >>> # Filter by labels
            >>> emails = jasni.emails.list(
            ...     account="me@mail.jasni.ai",
            ...     labels=["Important", "Work"]
            ... )
            
            >>> # Filter by label IDs
            >>> emails = jasni.emails.list(
            ...     account="me@mail.jasni.ai",
            ...     label_ids=["label-id-1", "label-id-2"]
            ... )
        """
        data = self._http.get("/api/v1/emails", query={
            "account": account,
            "folder": folder,
            "limit": limit,
            "label_ids": ",".join(label_ids) if label_ids else None,
            "labels": ",".join(labels) if labels else None,
        })
        return ListEmailsResponse(**data)
    
    def get(
        self,
        uid: int,
        *,
        account: str,
        folder: Optional[str] = None
    ) -> GetEmailResponse:
        """
        Get a specific email by UID.
        
        Args:
            uid: Email UID
            account: Email account
            folder: Folder where the email is located. Default: INBOX
        
        Returns:
            GetEmailResponse with full email details
        
        Example:
            >>> email = jasni.emails.get(123, account="me@mail.jasni.ai")
            >>> print(email.email.subject)
        """
        data = self._http.get(f"/api/v1/emails/{uid}", query={
            "account": account,
            "folder": folder,
        })
        return GetEmailResponse(**data)
    
    def delete(
        self,
        uid: int,
        *,
        account: str,
        folder: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Delete a specific email.
        
        Args:
            uid: Email UID
            account: Email account
            folder: Folder where the email is located. Default: INBOX
        
        Returns:
            Dict with success message
        
        Example:
            >>> jasni.emails.delete(123, account="me@mail.jasni.ai")
        """
        return self._http.delete(f"/api/v1/emails/{uid}", query={
            "account": account,
            "folder": folder,
        })
    
    def mark_as_read(
        self,
        uid: int,
        *,
        account: str,
        folder: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Mark an email as read.
        
        Args:
            uid: Email UID
            account: Email account
            folder: Folder where the email is located. Default: INBOX
        
        Returns:
            Dict with success message
        
        Example:
            >>> jasni.emails.mark_as_read(123, account="me@mail.jasni.ai")
        """
        return self._http.patch(
            f"/api/v1/emails/{uid}",
            body={"action": "read"},
            query={
                "account": account,
                "folder": folder,
            }
        )
    
    def mark_as_unread(
        self,
        uid: int,
        *,
        account: str,
        folder: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Mark an email as unread.
        
        Args:
            uid: Email UID
            account: Email account
            folder: Folder where the email is located. Default: INBOX
        
        Returns:
            Dict with success message
        
        Example:
            >>> jasni.emails.mark_as_unread(123, account="me@mail.jasni.ai")
        """
        return self._http.patch(
            f"/api/v1/emails/{uid}",
            body={"action": "unread"},
            query={
                "account": account,
                "folder": folder,
            }
        )
    
    def send(
        self,
        *,
        from_: str,
        to: Union[str, List[str]],
        subject: str,
        text: Optional[str] = None,
        html: Optional[str] = None,
        cc: Optional[Union[str, List[str]]] = None,
        bcc: Optional[Union[str, List[str]]] = None,
        reply_to: Optional[str] = None
    ) -> SendEmailResponse:
        """
        Send a new email.
        
        Args:
            from_: Sender email address (must be an account you own)
            to: Recipient email address(es)
            subject: Email subject
            text: Plain text body
            html: HTML body
            cc: CC recipients
            bcc: BCC recipients
            reply_to: Reply-to address
        
        Returns:
            SendEmailResponse with message ID
        
        Example:
            >>> result = jasni.emails.send(
            ...     from_="me@mail.jasni.ai",
            ...     to="recipient@example.com",
            ...     subject="Hello!",
            ...     text="Plain text body",
            ...     html="<p>HTML body</p>"
            ... )
            >>> print(f"Sent with ID: {result.message_id}")
        """
        data = self._http.post("/api/v1/emails/send", body={
            "from": from_,
            "to": to,
            "subject": subject,
            "text": text,
            "html": html,
            "cc": cc,
            "bcc": bcc,
            "replyTo": reply_to,
        })
        return SendEmailResponse(**data)
    
    def reply(
        self,
        uid: int,
        *,
        account: str,
        text: Optional[str] = None,
        html: Optional[str] = None,
        reply_all: bool = False,
        include_original: bool = True,
        folder: Optional[str] = None
    ) -> ReplyResponse:
        """
        Reply to an email.
        
        Args:
            uid: Email UID to reply to
            account: Email account
            text: Plain text reply body
            html: HTML reply body
            reply_all: Reply to all recipients. Default: False
            include_original: Include original message in reply. Default: True
            folder: Folder where the original email is. Default: INBOX
        
        Returns:
            ReplyResponse with message ID and threading info
        
        Example:
            >>> result = jasni.emails.reply(
            ...     123,
            ...     account="me@mail.jasni.ai",
            ...     text="Thanks for your email!",
            ...     reply_all=False
            ... )
        """
        data = self._http.post(
            f"/api/v1/emails/{uid}/reply",
            body={
                "text": text,
                "html": html,
                "replyAll": reply_all,
                "includeOriginal": include_original,
            },
            query={
                "account": account,
                "folder": folder,
            }
        )
        return ReplyResponse(**data)
    
    def forward(
        self,
        uid: int,
        *,
        account: str,
        to: Union[str, List[str]],
        text: Optional[str] = None,
        html: Optional[str] = None,
        cc: Optional[Union[str, List[str]]] = None,
        bcc: Optional[Union[str, List[str]]] = None,
        include_original: bool = True,
        folder: Optional[str] = None
    ) -> ForwardResponse:
        """
        Forward an email to new recipients.
        
        Args:
            uid: Email UID to forward
            account: Email account
            to: Recipient(s) to forward to
            text: Optional message to include before forwarded content
            html: Optional HTML message
            cc: CC recipients
            bcc: BCC recipients
            include_original: Include original message. Default: True
            folder: Folder where the original email is. Default: INBOX
        
        Returns:
            ForwardResponse with message ID and original email info
        
        Example:
            >>> result = jasni.emails.forward(
            ...     123,
            ...     account="me@mail.jasni.ai",
            ...     to="colleague@example.com",
            ...     text="FYI - see the email below"
            ... )
        """
        data = self._http.post(
            f"/api/v1/emails/{uid}/forward",
            body={
                "to": to,
                "cc": cc,
                "bcc": bcc,
                "text": text,
                "html": html,
                "includeOriginal": include_original,
            },
            query={
                "account": account,
                "folder": folder,
            }
        )
        return ForwardResponse(**data)
    
    def get_attachments(
        self,
        uid: int,
        *,
        account: str,
        folder: Optional[str] = None
    ) -> GetAttachmentsResponse:
        """
        Get all attachments from an email with their content.
        
        Args:
            uid: Email UID
            account: Email account
            folder: Folder where the email is located. Default: INBOX
        
        Returns:
            GetAttachmentsResponse with all attachments (base64 encoded content)
        
        Example:
            >>> attachments = jasni.emails.get_attachments(
            ...     123,
            ...     account="me@mail.jasni.ai"
            ... )
            >>> for att in attachments.attachments:
            ...     print(f"{att.filename}: {att.size} bytes")
        """
        data = self._http.get(f"/api/v1/emails/{uid}/attachments", query={
            "account": account,
            "folder": folder,
        })
        return GetAttachmentsResponse(**data)
    
    def get_attachment(
        self,
        uid: int,
        *,
        account: str,
        attachment: Union[str, int],
        folder: Optional[str] = None
    ) -> GetAttachmentResponse:
        """
        Get a specific attachment from an email.
        
        Args:
            uid: Email UID
            account: Email account
            attachment: Attachment filename or index (0-based)
            folder: Folder where the email is located. Default: INBOX
        
        Returns:
            GetAttachmentResponse with attachment (base64 encoded content)
        
        Example:
            >>> # Get by filename
            >>> att = jasni.emails.get_attachment(
            ...     123,
            ...     account="me@mail.jasni.ai",
            ...     attachment="document.pdf"
            ... )
            
            >>> # Get by index
            >>> att = jasni.emails.get_attachment(
            ...     123,
            ...     account="me@mail.jasni.ai",
            ...     attachment=0  # first attachment
            ... )
        """
        data = self._http.get(f"/api/v1/emails/{uid}/attachments/{attachment}", query={
            "account": account,
            "folder": folder,
        })
        return GetAttachmentResponse(**data)
    
    def get_raw(
        self,
        uid: int,
        *,
        account: str,
        folder: Optional[str] = None
    ) -> GetRawResponse:
        """
        Get the raw email message in RFC 822 format.
        
        Args:
            uid: Email UID
            account: Email account
            folder: Folder where the email is located. Default: INBOX
        
        Returns:
            GetRawResponse with raw email string
        
        Example:
            >>> raw = jasni.emails.get_raw(123, account="me@mail.jasni.ai")
            >>> print(raw.raw)  # Full RFC 822 message
        """
        data = self._http.get(f"/api/v1/emails/{uid}/raw", query={
            "account": account,
            "folder": folder,
        })
        return GetRawResponse(**data)
    
    def list_threads(
        self,
        *,
        account: str,
        folder: Optional[str] = None,
        limit: Optional[int] = None
    ) -> ListThreadsResponse:
        """
        List email threads (conversations) for an email account.
        Emails are grouped by Message-ID, In-Reply-To, and References headers.
        
        Args:
            account: Email account to fetch from
            folder: Folder to fetch from. Default: INBOX
            limit: Maximum number of emails to fetch before grouping. Default: 100
        
        Returns:
            ListThreadsResponse with thread previews
        
        Example:
            >>> threads = jasni.emails.list_threads(
            ...     account="me@mail.jasni.ai",
            ...     folder="INBOX",
            ...     limit=100
            ... )
            >>> for thread in threads.threads:
            ...     print(f"{thread.subject} ({thread.message_count} messages)")
        """
        data = self._http.get("/api/v1/emails/threads", query={
            "account": account,
            "folder": folder,
            "limit": limit,
        })
        return ListThreadsResponse(**data)
    
    def get_thread(
        self,
        thread_id: str,
        *,
        account: str,
        folder: Optional[str] = None
    ) -> GetThreadResponse:
        """
        Get all emails in a specific thread/conversation.
        
        Args:
            thread_id: Thread ID (the root message's Message-ID)
            account: Email account
            folder: Folder where the emails are located. Default: INBOX
        
        Returns:
            GetThreadResponse with all emails in the thread
        
        Example:
            >>> thread = jasni.emails.get_thread(
            ...     "<message-id@example.com>",
            ...     account="me@mail.jasni.ai"
            ... )
            >>> print(f"Thread: {thread.subject}")
            >>> for email in thread.emails:
            ...     print(f"- {email.from_.address}: {email.subject}")
        """
        from urllib.parse import quote
        encoded_thread_id = quote(thread_id, safe='')
        data = self._http.get(f"/api/v1/emails/threads/{encoded_thread_id}", query={
            "account": account,
            "folder": folder,
        })
        return GetThreadResponse(**data)


class AsyncEmailsResource:
    """
    Resource for managing emails (asynchronous).
    """
    
    def __init__(self, http: "AsyncHttpClient") -> None:
        self._http = http
        self.labels = AsyncEmailLabelsResource(http)
    
    async def list(
        self,
        *,
        account: str,
        folder: Optional[str] = None,
        limit: Optional[int] = None,
        label_ids: Optional[List[str]] = None,
        labels: Optional[List[str]] = None
    ) -> ListEmailsResponse:
        """
        List emails for an email account.
        
        Args:
            account: Email account to fetch from
            folder: Folder to fetch from. Default: INBOX
            limit: Number of emails to fetch. Default: 50, max: 100
            label_ids: Filter by label IDs (emails must have ALL specified labels)
            labels: Filter by label names (emails must have ALL specified labels)
        """
        data = await self._http.get("/api/v1/emails", query={
            "account": account,
            "folder": folder,
            "limit": limit,
            "label_ids": ",".join(label_ids) if label_ids else None,
            "labels": ",".join(labels) if labels else None,
        })
        return ListEmailsResponse(**data)
    
    async def get(
        self,
        uid: int,
        *,
        account: str,
        folder: Optional[str] = None
    ) -> GetEmailResponse:
        """Get a specific email by UID."""
        data = await self._http.get(f"/api/v1/emails/{uid}", query={
            "account": account,
            "folder": folder,
        })
        return GetEmailResponse(**data)
    
    async def delete(
        self,
        uid: int,
        *,
        account: str,
        folder: Optional[str] = None
    ) -> Dict[str, str]:
        """Delete a specific email."""
        return await self._http.delete(f"/api/v1/emails/{uid}", query={
            "account": account,
            "folder": folder,
        })
    
    async def mark_as_read(
        self,
        uid: int,
        *,
        account: str,
        folder: Optional[str] = None
    ) -> Dict[str, str]:
        """Mark an email as read."""
        return await self._http.patch(
            f"/api/v1/emails/{uid}",
            body={"action": "read"},
            query={
                "account": account,
                "folder": folder,
            }
        )
    
    async def mark_as_unread(
        self,
        uid: int,
        *,
        account: str,
        folder: Optional[str] = None
    ) -> Dict[str, str]:
        """Mark an email as unread."""
        return await self._http.patch(
            f"/api/v1/emails/{uid}",
            body={"action": "unread"},
            query={
                "account": account,
                "folder": folder,
            }
        )
    
    async def send(
        self,
        *,
        from_: str,
        to: Union[str, List[str]],
        subject: str,
        text: Optional[str] = None,
        html: Optional[str] = None,
        cc: Optional[Union[str, List[str]]] = None,
        bcc: Optional[Union[str, List[str]]] = None,
        reply_to: Optional[str] = None
    ) -> SendEmailResponse:
        """Send a new email."""
        data = await self._http.post("/api/v1/emails/send", body={
            "from": from_,
            "to": to,
            "subject": subject,
            "text": text,
            "html": html,
            "cc": cc,
            "bcc": bcc,
            "replyTo": reply_to,
        })
        return SendEmailResponse(**data)
    
    async def reply(
        self,
        uid: int,
        *,
        account: str,
        text: Optional[str] = None,
        html: Optional[str] = None,
        reply_all: bool = False,
        include_original: bool = True,
        folder: Optional[str] = None
    ) -> ReplyResponse:
        """Reply to an email."""
        data = await self._http.post(
            f"/api/v1/emails/{uid}/reply",
            body={
                "text": text,
                "html": html,
                "replyAll": reply_all,
                "includeOriginal": include_original,
            },
            query={
                "account": account,
                "folder": folder,
            }
        )
        return ReplyResponse(**data)
    
    async def forward(
        self,
        uid: int,
        *,
        account: str,
        to: Union[str, List[str]],
        text: Optional[str] = None,
        html: Optional[str] = None,
        cc: Optional[Union[str, List[str]]] = None,
        bcc: Optional[Union[str, List[str]]] = None,
        include_original: bool = True,
        folder: Optional[str] = None
    ) -> ForwardResponse:
        """Forward an email to new recipients."""
        data = await self._http.post(
            f"/api/v1/emails/{uid}/forward",
            body={
                "to": to,
                "cc": cc,
                "bcc": bcc,
                "text": text,
                "html": html,
                "includeOriginal": include_original,
            },
            query={
                "account": account,
                "folder": folder,
            }
        )
        return ForwardResponse(**data)
    
    async def get_attachments(
        self,
        uid: int,
        *,
        account: str,
        folder: Optional[str] = None
    ) -> GetAttachmentsResponse:
        """Get all attachments from an email with their content."""
        data = await self._http.get(f"/api/v1/emails/{uid}/attachments", query={
            "account": account,
            "folder": folder,
        })
        return GetAttachmentsResponse(**data)
    
    async def get_attachment(
        self,
        uid: int,
        *,
        account: str,
        attachment: Union[str, int],
        folder: Optional[str] = None
    ) -> GetAttachmentResponse:
        """Get a specific attachment from an email."""
        data = await self._http.get(f"/api/v1/emails/{uid}/attachments/{attachment}", query={
            "account": account,
            "folder": folder,
        })
        return GetAttachmentResponse(**data)
    
    async def get_raw(
        self,
        uid: int,
        *,
        account: str,
        folder: Optional[str] = None
    ) -> GetRawResponse:
        """Get the raw email message in RFC 822 format."""
        data = await self._http.get(f"/api/v1/emails/{uid}/raw", query={
            "account": account,
            "folder": folder,
        })
        return GetRawResponse(**data)
    
    async def list_threads(
        self,
        *,
        account: str,
        folder: Optional[str] = None,
        limit: Optional[int] = None
    ) -> ListThreadsResponse:
        """
        List email threads (conversations) for an email account.
        Emails are grouped by Message-ID, In-Reply-To, and References headers.
        """
        data = await self._http.get("/api/v1/emails/threads", query={
            "account": account,
            "folder": folder,
            "limit": limit,
        })
        return ListThreadsResponse(**data)
    
    async def get_thread(
        self,
        thread_id: str,
        *,
        account: str,
        folder: Optional[str] = None
    ) -> GetThreadResponse:
        """Get all emails in a specific thread/conversation."""
        from urllib.parse import quote
        encoded_thread_id = quote(thread_id, safe='')
        data = await self._http.get(f"/api/v1/emails/threads/{encoded_thread_id}", query={
            "account": account,
            "folder": folder,
        })
        return GetThreadResponse(**data)
