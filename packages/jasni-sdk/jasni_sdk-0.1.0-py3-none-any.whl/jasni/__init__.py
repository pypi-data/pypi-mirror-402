"""
Jasni Python SDK

Official Python SDK for the Jasni AI Email API.
Build AI-powered email automation, agents, and integrations.

Example:
    >>> from jasni import Jasni
    >>> jasni = Jasni("jsk_your_api_key")
    >>> accounts = jasni.accounts.list()
"""

from jasni.client import AsyncJasni, Jasni
from jasni.errors import (
    AuthenticationError,
    ConflictError,
    JasniError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
)
from jasni.types import (
    Account,
    Attachment,
    CreateAccountResponse,
    CreateDraftResponse,
    CreateLabelResponse,
    CreateWebhookResponse,
    DeleteAccountResponse,
    UpdateAccountResponse,
    Draft,
    Email,
    EmailLabel,
    EmailPreview,
    ForwardResponse,
    Label,
    ListAccountsResponse,
    ListDraftsResponse,
    ListEmailsResponse,
    ListLabelsResponse,
    ListWebhooksResponse,
    ReplyResponse,
    SendEmailResponse,
    UpdateDraftResponse,
    UpdateWebhookResponse,
    Webhook,
    WebhookEvent,
    # Thread types
    ThreadPreview,
    ListThreadsResponse,
    GetThreadResponse,
)

__version__ = "0.1.0"
__all__ = [
    # Main clients
    "Jasni",
    "AsyncJasni",
    # Errors
    "JasniError",
    "AuthenticationError",
    "NotFoundError",
    "ValidationError",
    "RateLimitError",
    "ConflictError",
    "ServerError",
    # Types
    "Account",
    "Attachment",
    "CreateAccountResponse",
    "CreateDraftResponse",
    "CreateLabelResponse",
    "CreateWebhookResponse",
    "DeleteAccountResponse",
    "UpdateAccountResponse",
    "Draft",
    "Email",
    "EmailLabel",
    "EmailPreview",
    "ForwardResponse",
    "Label",
    "ListAccountsResponse",
    "ListDraftsResponse",
    "ListEmailsResponse",
    "ListLabelsResponse",
    "ListWebhooksResponse",
    "ReplyResponse",
    "SendEmailResponse",
    "UpdateDraftResponse",
    "UpdateWebhookResponse",
    "Webhook",
    "WebhookEvent",
    # Thread types
    "ThreadPreview",
    "ListThreadsResponse",
    "GetThreadResponse",
]
