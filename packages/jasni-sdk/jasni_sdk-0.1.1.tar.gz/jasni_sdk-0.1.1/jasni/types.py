"""
Jasni SDK Type Definitions

Pydantic models for all API request and response types.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


# ============================================================================
# Enums
# ============================================================================

class WebhookEvent(str, Enum):
    """Webhook event types."""
    EMAIL_RECEIVED = "email.received"
    EMAIL_SENT = "email.sent"
    EMAIL_DELIVERED = "email.delivered"
    EMAIL_BOUNCED = "email.bounced"
    EMAIL_SPAM = "email.spam"
    EMAIL_REJECTED = "email.rejected"
    EMAIL_DELETED = "email.deleted"
    DOMAIN_VERIFIED = "domain.verified"


# ============================================================================
# Account Types
# ============================================================================

class Account(BaseModel):
    """Email account."""
    id: str
    email: str
    name: str
    created_at: str


class ListAccountsResponse(BaseModel):
    """Response from listing accounts."""
    accounts: List[Account]
    total: int


class CreateAccountResponse(BaseModel):
    """Response from creating an account."""
    account: Account
    message: str


class DeleteAccountResponse(BaseModel):
    """Response from deleting an account."""
    deleted_email: str
    message: str


class UpdateAccountResponse(BaseModel):
    """Response from updating an account."""
    account: Account
    message: str


# ============================================================================
# Email Types
# ============================================================================

class EmailAddress(BaseModel):
    """Email address with optional name."""
    address: str
    name: Optional[str] = None


class Attachment(BaseModel):
    """Email attachment metadata."""
    filename: str
    content_type: str = Field(alias="contentType")
    size: int

    class Config:
        populate_by_name = True


class EmailPreview(BaseModel):
    """Email preview (list view)."""
    uid: int
    message_id: str = Field(alias="messageId")
    subject: str
    from_: Union[EmailAddress, str] = Field(alias="from")
    to: List[Union[EmailAddress, str]]
    date: str
    seen: bool
    has_attachments: bool = Field(alias="hasAttachments")
    snippet: Optional[str] = None

    class Config:
        populate_by_name = True


class Email(EmailPreview):
    """Full email with body content."""
    text: Optional[str] = None
    html: Optional[str] = None
    cc: Optional[List[Union[EmailAddress, str]]] = None
    bcc: Optional[List[Union[EmailAddress, str]]] = None
    reply_to: Optional[str] = Field(default=None, alias="replyTo")
    attachments: Optional[List[Attachment]] = None
    in_reply_to: Optional[str] = Field(default=None, alias="inReplyTo")
    references: Optional[str] = None


class ListEmailsResponse(BaseModel):
    """Response from listing emails."""
    emails: List[EmailPreview]
    folder: str
    total: int
    account: str


class GetEmailResponse(BaseModel):
    """Response from getting a single email."""
    email: Email


class SendEmailResponse(BaseModel):
    """Response from sending an email."""
    message_id: str = Field(alias="messageId")
    from_: str = Field(alias="from")
    to: List[str]
    subject: str
    saved_to_sent: bool = Field(alias="savedToSent")

    class Config:
        populate_by_name = True


class ReplyResponse(BaseModel):
    """Response from replying to an email."""
    message_id: str = Field(alias="messageId")
    from_: str = Field(alias="from")
    to: List[str]
    cc: Optional[List[str]] = None
    subject: str
    in_reply_to: str = Field(alias="inReplyTo")
    references: str
    saved_to_sent: bool = Field(alias="savedToSent")

    class Config:
        populate_by_name = True


class ForwardedFrom(BaseModel):
    """Original email info when forwarding."""
    uid: int
    from_: Union[EmailAddress, str] = Field(alias="from")
    subject: str
    date: str

    class Config:
        populate_by_name = True


class ForwardResponse(BaseModel):
    """Response from forwarding an email."""
    message_id: str = Field(alias="messageId")
    from_: str = Field(alias="from")
    to: List[str]
    cc: Optional[List[str]] = None
    subject: str
    saved_to_sent: bool = Field(alias="savedToSent")
    forwarded_from: ForwardedFrom = Field(alias="forwardedFrom")

    class Config:
        populate_by_name = True


class AttachmentData(BaseModel):
    """Email attachment with content."""
    filename: str
    content_type: str = Field(alias="contentType")
    size: int
    content: str  # Base64 encoded content

    class Config:
        populate_by_name = True


class GetAttachmentsResponse(BaseModel):
    """Response from getting all attachments."""
    attachments: List[AttachmentData]
    uid: int
    account: str


class GetAttachmentResponse(BaseModel):
    """Response from getting a single attachment."""
    attachment: AttachmentData
    uid: int
    account: str


class GetRawResponse(BaseModel):
    """Response from getting raw email."""
    raw: str  # RFC 822 format
    uid: int
    account: str


# ============================================================================
# Thread Types
# ============================================================================

class ThreadPreview(BaseModel):
    """Thread/conversation preview."""
    thread_id: str = Field(alias="threadId")
    subject: str
    message_count: int = Field(alias="messageCount")
    unread_count: int = Field(alias="unreadCount")
    last_message_date: str = Field(alias="lastMessageDate")
    participants: List[EmailAddress]
    snippet: Optional[str] = None
    email_uids: List[int] = Field(alias="emailUids")

    class Config:
        populate_by_name = True


class ListThreadsResponse(BaseModel):
    """Response from listing threads."""
    threads: List[ThreadPreview]
    folder: str
    total_threads: int = Field(alias="totalThreads")
    total_emails: int = Field(alias="totalEmails")

    class Config:
        populate_by_name = True


class GetThreadResponse(BaseModel):
    """Response from getting a single thread."""
    thread_id: str = Field(alias="threadId")
    subject: str
    participants: List[EmailAddress]
    message_count: int = Field(alias="messageCount")
    unread_count: int = Field(alias="unreadCount")
    emails: List[Email]

    class Config:
        populate_by_name = True


# ============================================================================
# Draft Types
# ============================================================================

class Draft(EmailPreview):
    """Draft email."""
    text: Optional[str] = None
    html: Optional[str] = None


class ListDraftsResponse(BaseModel):
    """Response from listing drafts."""
    drafts: List[Draft]
    total: int
    account: str


class CreateDraftResponse(BaseModel):
    """Response from creating a draft."""
    uid: int
    account: str
    message: str


class UpdateDraftResponse(BaseModel):
    """Response from updating a draft."""
    uid: int
    account: str
    message: str


class GetDraftResponse(BaseModel):
    """Response from getting a single draft."""
    email: Email


class SendDraftResponse(BaseModel):
    """Response from sending a draft."""
    message_id: str = Field(alias="messageId")
    from_: str = Field(alias="from")
    to: List[str]
    subject: str
    saved_to_sent: bool = Field(alias="savedToSent")

    class Config:
        populate_by_name = True


# ============================================================================
# Label Types
# ============================================================================

class Label(BaseModel):
    """Email label."""
    id: str
    name: str
    color: str
    description: Optional[str] = None
    created_at: str
    email_count: Optional[int] = None


class EmailLabel(Label):
    """Label with assignment metadata."""
    applied_by: str
    applied_at: str
    metadata: Optional[Dict[str, Any]] = None


class ListLabelsResponse(BaseModel):
    """Response from listing labels."""
    labels: List[Label]
    total: int


class CreateLabelResponse(BaseModel):
    """Response from creating a label."""
    label: Label
    message: str


class DeleteLabelResponse(BaseModel):
    """Response from deleting a label."""
    deleted_id: str
    deleted_name: str
    message: str


class CreatedLabel(BaseModel):
    """Newly created label (partial info)."""
    id: str
    name: str
    color: str


class GetEmailLabelsResponse(BaseModel):
    """Response from getting email labels."""
    labels: List[EmailLabel]
    message_id: str
    account: str


class AssignLabelsResponse(BaseModel):
    """Response from assigning labels to an email."""
    labels: List[EmailLabel]
    created_labels: List[CreatedLabel]
    message_id: str
    account: str
    message: str


class RemoveLabelsResponse(BaseModel):
    """Response from removing labels from an email."""
    removed_count: int
    message_id: str
    message: str


# ============================================================================
# Webhook Types
# ============================================================================

class Webhook(BaseModel):
    """Webhook configuration."""
    id: str
    url: str
    events: List[WebhookEvent]
    active: bool
    description: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None
    secret: Optional[str] = None  # Only returned on creation


class ListWebhooksResponse(BaseModel):
    """Response from listing webhooks."""
    webhooks: List[Webhook]


class GetWebhookResponse(BaseModel):
    """Response from getting a webhook."""
    webhook: Webhook


class CreateWebhookResponse(BaseModel):
    """Response from creating a webhook."""
    webhook: Webhook


class UpdateWebhookResponse(BaseModel):
    """Response from updating a webhook."""
    webhook: Webhook


# ============================================================================
# API Response Types
# ============================================================================

class ApiSuccessResponse(BaseModel):
    """Successful API response wrapper."""
    success: bool = True
    data: Any
    message: Optional[str] = None


class ApiErrorResponse(BaseModel):
    """Error API response."""
    success: bool = False
    error: str
