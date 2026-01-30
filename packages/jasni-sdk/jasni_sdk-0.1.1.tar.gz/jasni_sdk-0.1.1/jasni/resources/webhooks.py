"""
Webhooks Resource

Resource for managing webhooks.
"""

from typing import TYPE_CHECKING, Dict, List, Optional

from jasni.types import (
    CreateWebhookResponse,
    GetWebhookResponse,
    ListWebhooksResponse,
    UpdateWebhookResponse,
    WebhookEvent,
)

if TYPE_CHECKING:
    from jasni.http import AsyncHttpClient, HttpClient


class WebhooksResource:
    """
    Resource for managing webhooks (synchronous).
    
    Example:
        >>> webhooks = jasni.webhooks.list()
        >>> for webhook in webhooks.webhooks:
        ...     print(f"- {webhook.url}: {webhook.events}")
    """
    
    def __init__(self, http: "HttpClient") -> None:
        self._http = http
    
    def list(self) -> ListWebhooksResponse:
        """
        List all webhooks for the authenticated user.
        
        Returns:
            ListWebhooksResponse with webhooks
        
        Example:
            >>> webhooks = jasni.webhooks.list()
        """
        data = self._http.get("/api/v1/webhooks")
        return ListWebhooksResponse(**data)
    
    def get(self, id: str) -> GetWebhookResponse:
        """
        Get a specific webhook by ID.
        
        Args:
            id: Webhook ID
        
        Returns:
            GetWebhookResponse with the webhook
        
        Example:
            >>> webhook = jasni.webhooks.get("webhook-id")
            >>> print(f"URL: {webhook.webhook.url}")
        """
        data = self._http.get(f"/api/v1/webhooks/{id}")
        return GetWebhookResponse(**data)
    
    def create(
        self,
        *,
        url: str,
        events: List[WebhookEvent],
        description: Optional[str] = None
    ) -> CreateWebhookResponse:
        """
        Create a new webhook.
        
        Args:
            url: Webhook URL (must be HTTP or HTTPS)
            events: Events to subscribe to
            description: Optional description
        
        Returns:
            CreateWebhookResponse with the created webhook (including secret)
        
        Example:
            >>> webhook = jasni.webhooks.create(
            ...     url="https://my-server.com/webhook",
            ...     events=["email.received", "email.sent"],
            ...     description="My email webhook"
            ... )
            >>> # Save the secret! It's only returned on creation
            >>> print(f"Webhook secret: {webhook.webhook.secret}")
        """
        # Convert enum values to strings if needed
        event_strings = [
            e.value if isinstance(e, WebhookEvent) else e 
            for e in events
        ]
        
        data = self._http.post("/api/v1/webhooks", body={
            "url": url,
            "events": event_strings,
            "description": description,
        })
        return CreateWebhookResponse(**data)
    
    def update(
        self,
        *,
        id: str,
        url: Optional[str] = None,
        events: Optional[List[WebhookEvent]] = None,
        active: Optional[bool] = None,
        description: Optional[str] = None
    ) -> UpdateWebhookResponse:
        """
        Update an existing webhook.
        
        Args:
            id: Webhook ID
            url: New webhook URL
            events: New events to subscribe to
            active: Enable or disable the webhook
            description: New description
        
        Returns:
            UpdateWebhookResponse with the updated webhook
        
        Example:
            >>> # Update URL and events
            >>> jasni.webhooks.update(
            ...     id="webhook-id",
            ...     url="https://new-url.com/webhook",
            ...     events=["email.received"]
            ... )
            
            >>> # Disable a webhook
            >>> jasni.webhooks.update(
            ...     id="webhook-id",
            ...     active=False
            ... )
        """
        # Convert enum values to strings if needed
        event_strings = None
        if events is not None:
            event_strings = [
                e.value if isinstance(e, WebhookEvent) else e 
                for e in events
            ]
        
        data = self._http.patch("/api/v1/webhooks", body={
            "id": id,
            "url": url,
            "events": event_strings,
            "active": active,
            "description": description,
        })
        return UpdateWebhookResponse(**data)
    
    def delete(self, id: str) -> Dict[str, str]:
        """
        Delete a webhook.
        
        Args:
            id: The webhook ID to delete
        
        Returns:
            Dict with success message
        
        Example:
            >>> jasni.webhooks.delete("webhook-id")
        """
        return self._http.delete("/api/v1/webhooks", query={"id": id})


class AsyncWebhooksResource:
    """
    Resource for managing webhooks (asynchronous).
    """
    
    def __init__(self, http: "AsyncHttpClient") -> None:
        self._http = http
    
    async def list(self) -> ListWebhooksResponse:
        """List all webhooks for the authenticated user."""
        data = await self._http.get("/api/v1/webhooks")
        return ListWebhooksResponse(**data)
    
    async def get(self, id: str) -> GetWebhookResponse:
        """Get a specific webhook by ID."""
        data = await self._http.get(f"/api/v1/webhooks/{id}")
        return GetWebhookResponse(**data)
    
    async def create(
        self,
        *,
        url: str,
        events: List[WebhookEvent],
        description: Optional[str] = None
    ) -> CreateWebhookResponse:
        """Create a new webhook."""
        event_strings = [
            e.value if isinstance(e, WebhookEvent) else e 
            for e in events
        ]
        
        data = await self._http.post("/api/v1/webhooks", body={
            "url": url,
            "events": event_strings,
            "description": description,
        })
        return CreateWebhookResponse(**data)
    
    async def update(
        self,
        *,
        id: str,
        url: Optional[str] = None,
        events: Optional[List[WebhookEvent]] = None,
        active: Optional[bool] = None,
        description: Optional[str] = None
    ) -> UpdateWebhookResponse:
        """Update an existing webhook."""
        event_strings = None
        if events is not None:
            event_strings = [
                e.value if isinstance(e, WebhookEvent) else e 
                for e in events
            ]
        
        data = await self._http.patch("/api/v1/webhooks", body={
            "id": id,
            "url": url,
            "events": event_strings,
            "active": active,
            "description": description,
        })
        return UpdateWebhookResponse(**data)
    
    async def delete(self, id: str) -> Dict[str, str]:
        """Delete a webhook."""
        return await self._http.delete("/api/v1/webhooks", query={"id": id})
