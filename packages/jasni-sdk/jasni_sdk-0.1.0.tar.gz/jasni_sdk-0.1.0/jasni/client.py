"""
Jasni Client

Main client classes for interacting with the Jasni API.
Provides both synchronous and asynchronous interfaces.
"""

import warnings
from typing import Optional

from jasni.http import AsyncHttpClient, HttpClient
from jasni.resources.accounts import AccountsResource, AsyncAccountsResource
from jasni.resources.drafts import AsyncDraftsResource, DraftsResource
from jasni.resources.emails import AsyncEmailsResource, EmailsResource
from jasni.resources.labels import AsyncLabelsResource, LabelsResource
from jasni.resources.webhooks import AsyncWebhooksResource, WebhooksResource

DEFAULT_BASE_URL = "https://api.jasni.ai"


class Jasni:
    """
    Main Jasni SDK client (synchronous).
    
    Provides access to all Jasni API resources including accounts,
    emails, drafts, labels, and webhooks.
    
    Example:
        >>> from jasni import Jasni
        >>>
        >>> jasni = Jasni("jsk_your_api_key")
        >>>
        >>> # List accounts
        >>> accounts = jasni.accounts.list()
        >>>
        >>> # Send an email
        >>> jasni.emails.send(
        ...     from_="me@mail.jasni.ai",
        ...     to="recipient@example.com",
        ...     subject="Hello!",
        ...     text="Hello from Jasni SDK"
        ... )
    
    Args:
        api_key: Your Jasni API key (starts with 'jsk_')
        base_url: Base URL for the API. Defaults to https://api.jasni.ai
        timeout: Request timeout in seconds. Default: 30.0
    """
    
    def __init__(
        self,
        api_key: str,
        *,
        base_url: Optional[str] = None,
        timeout: float = 30.0
    ) -> None:
        if not api_key:
            raise ValueError("API key is required")
        
        if not api_key.startswith("jsk_"):
            warnings.warn(
                'Warning: Jasni API keys should start with "jsk_"',
                UserWarning,
                stacklevel=2
            )
        
        self._base_url = base_url or DEFAULT_BASE_URL
        self._http = HttpClient(
            base_url=self._base_url,
            api_key=api_key,
            timeout=timeout
        )
        
        # Initialize resources
        self.accounts = AccountsResource(self._http)
        self.emails = EmailsResource(self._http)
        self.drafts = DraftsResource(self._http)
        self.labels = LabelsResource(self._http)
        self.webhooks = WebhooksResource(self._http)
    
    def close(self) -> None:
        """Close the HTTP client and release resources."""
        self._http.close()
    
    def __enter__(self) -> "Jasni":
        return self
    
    def __exit__(self, *args) -> None:
        self.close()


class AsyncJasni:
    """
    Main Jasni SDK client (asynchronous).
    
    Provides access to all Jasni API resources with async/await support.
    
    Example:
        >>> import asyncio
        >>> from jasni import AsyncJasni
        >>>
        >>> async def main():
        ...     jasni = AsyncJasni("jsk_your_api_key")
        ...
        ...     # List emails
        ...     emails = await jasni.emails.list(account="me@mail.jasni.ai")
        ...     for email in emails.emails:
        ...         print(f"- {email.subject}")
        ...
        ...     await jasni.close()
        >>>
        >>> asyncio.run(main())
    
    Args:
        api_key: Your Jasni API key (starts with 'jsk_')
        base_url: Base URL for the API. Defaults to https://api.jasni.ai
        timeout: Request timeout in seconds. Default: 30.0
    """
    
    def __init__(
        self,
        api_key: str,
        *,
        base_url: Optional[str] = None,
        timeout: float = 30.0
    ) -> None:
        if not api_key:
            raise ValueError("API key is required")
        
        if not api_key.startswith("jsk_"):
            warnings.warn(
                'Warning: Jasni API keys should start with "jsk_"',
                UserWarning,
                stacklevel=2
            )
        
        self._base_url = base_url or DEFAULT_BASE_URL
        self._http = AsyncHttpClient(
            base_url=self._base_url,
            api_key=api_key,
            timeout=timeout
        )
        
        # Initialize resources
        self.accounts = AsyncAccountsResource(self._http)
        self.emails = AsyncEmailsResource(self._http)
        self.drafts = AsyncDraftsResource(self._http)
        self.labels = AsyncLabelsResource(self._http)
        self.webhooks = AsyncWebhooksResource(self._http)
    
    async def close(self) -> None:
        """Close the HTTP client and release resources."""
        await self._http.aclose()
    
    async def __aenter__(self) -> "AsyncJasni":
        return self
    
    async def __aexit__(self, *args) -> None:
        await self.close()
