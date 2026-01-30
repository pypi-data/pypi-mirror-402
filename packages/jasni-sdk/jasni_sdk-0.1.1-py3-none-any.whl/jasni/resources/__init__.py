"""
Jasni SDK Resources

Resource classes for interacting with different API endpoints.
"""

from jasni.resources.accounts import AccountsResource, AsyncAccountsResource
from jasni.resources.drafts import AsyncDraftsResource, DraftsResource
from jasni.resources.emails import AsyncEmailsResource, EmailsResource
from jasni.resources.labels import AsyncLabelsResource, LabelsResource
from jasni.resources.webhooks import AsyncWebhooksResource, WebhooksResource

__all__ = [
    "AccountsResource",
    "AsyncAccountsResource",
    "DraftsResource",
    "AsyncDraftsResource",
    "EmailsResource",
    "AsyncEmailsResource",
    "LabelsResource",
    "AsyncLabelsResource",
    "WebhooksResource",
    "AsyncWebhooksResource",
]
