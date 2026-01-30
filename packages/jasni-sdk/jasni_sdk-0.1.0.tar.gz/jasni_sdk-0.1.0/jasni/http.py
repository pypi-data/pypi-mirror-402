"""
HTTP Client for Jasni API

Handles all HTTP communication with the Jasni API, including
request building, authentication, and error handling.
"""

from typing import Any, Dict, Optional, TypeVar, Union

import httpx

from jasni.errors import JasniError, create_error_from_response

T = TypeVar("T")

QueryValue = Union[str, int, bool, None]
QueryParams = Dict[str, QueryValue]


class HttpClient:
    """
    Synchronous HTTP client for the Jasni API.
    """
    
    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: float = 30.0
    ) -> None:
        """
        Initialize the HTTP client.
        
        Args:
            base_url: Base URL for the API
            api_key: Jasni API key
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
        )
    
    def _build_params(
        self,
        query: Optional[QueryParams] = None
    ) -> Optional[Dict[str, str]]:
        """Build query parameters, filtering out None values."""
        if not query:
            return None
        
        return {
            k: str(v).lower() if isinstance(v, bool) else str(v)
            for k, v in query.items()
            if v is not None
        }
    
    def _handle_response(self, response: httpx.Response) -> Any:
        """Handle API response and extract data or raise errors."""
        try:
            data = response.json()
        except Exception as exc:
            raise JasniError(
                f"Failed to parse response: {exc}",
                response.status_code,
                "PARSE_ERROR"
            ) from exc
        
        if not response.is_success or data.get("success") is False:
            error_message = data.get("error", "Unknown error")
            retry_after = response.headers.get("Retry-After")
            
            raise create_error_from_response(
                response.status_code,
                error_message,
                int(retry_after) if retry_after else None
            )
        
        # Return the data from successful response
        if "data" in data:
            return data["data"]
        
        # For responses without a data wrapper
        return data
    
    def request(
        self,
        method: str,
        path: str,
        body: Optional[Dict[str, Any]] = None,
        query: Optional[QueryParams] = None
    ) -> Any:
        """
        Make an HTTP request to the API.
        
        Args:
            method: HTTP method
            path: API path
            body: Request body
            query: Query parameters
        
        Returns:
            Parsed response data
        
        Raises:
            JasniError: On API or network errors
        """
        params = self._build_params(query)
        
        # Filter None values from body
        if body:
            body = {k: v for k, v in body.items() if v is not None}
        
        try:
            response = self._client.request(
                method=method,
                url=path,
                json=body if body else None,
                params=params
            )
        except httpx.RequestError as exc:
            raise JasniError(
                f"Network request failed: {exc}",
                0,
                "NETWORK_ERROR"
            ) from exc
        
        return self._handle_response(response)
    
    def get(
        self,
        path: str,
        query: Optional[QueryParams] = None
    ) -> Any:
        """Make a GET request."""
        return self.request("GET", path, query=query)
    
    def post(
        self,
        path: str,
        body: Optional[Dict[str, Any]] = None,
        query: Optional[QueryParams] = None
    ) -> Any:
        """Make a POST request."""
        return self.request("POST", path, body=body, query=query)
    
    def put(
        self,
        path: str,
        body: Optional[Dict[str, Any]] = None,
        query: Optional[QueryParams] = None
    ) -> Any:
        """Make a PUT request."""
        return self.request("PUT", path, body=body, query=query)
    
    def patch(
        self,
        path: str,
        body: Optional[Dict[str, Any]] = None,
        query: Optional[QueryParams] = None
    ) -> Any:
        """Make a PATCH request."""
        return self.request("PATCH", path, body=body, query=query)
    
    def delete(
        self,
        path: str,
        query: Optional[QueryParams] = None
    ) -> Any:
        """Make a DELETE request."""
        return self.request("DELETE", path, query=query)
    
    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()
    
    def __enter__(self) -> "HttpClient":
        return self
    
    def __exit__(self, *args: Any) -> None:
        self.close()


class AsyncHttpClient:
    """
    Asynchronous HTTP client for the Jasni API.
    """
    
    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: float = 30.0
    ) -> None:
        """
        Initialize the async HTTP client.
        
        Args:
            base_url: Base URL for the API
            api_key: Jasni API key
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
        )
    
    def _build_params(
        self,
        query: Optional[QueryParams] = None
    ) -> Optional[Dict[str, str]]:
        """Build query parameters, filtering out None values."""
        if not query:
            return None
        
        return {
            k: str(v).lower() if isinstance(v, bool) else str(v)
            for k, v in query.items()
            if v is not None
        }
    
    def _handle_response(self, response: httpx.Response) -> Any:
        """Handle API response and extract data or raise errors."""
        try:
            data = response.json()
        except Exception as exc:
            raise JasniError(
                f"Failed to parse response: {exc}",
                response.status_code,
                "PARSE_ERROR"
            ) from exc
        
        if not response.is_success or data.get("success") is False:
            error_message = data.get("error", "Unknown error")
            retry_after = response.headers.get("Retry-After")
            
            raise create_error_from_response(
                response.status_code,
                error_message,
                int(retry_after) if retry_after else None
            )
        
        # Return the data from successful response
        if "data" in data:
            return data["data"]
        
        # For responses without a data wrapper
        return data
    
    async def request(
        self,
        method: str,
        path: str,
        body: Optional[Dict[str, Any]] = None,
        query: Optional[QueryParams] = None
    ) -> Any:
        """
        Make an async HTTP request to the API.
        
        Args:
            method: HTTP method
            path: API path
            body: Request body
            query: Query parameters
        
        Returns:
            Parsed response data
        
        Raises:
            JasniError: On API or network errors
        """
        params = self._build_params(query)
        
        # Filter None values from body
        if body:
            body = {k: v for k, v in body.items() if v is not None}
        
        try:
            response = await self._client.request(
                method=method,
                url=path,
                json=body if body else None,
                params=params
            )
        except httpx.RequestError as exc:
            raise JasniError(
                f"Network request failed: {exc}",
                0,
                "NETWORK_ERROR"
            ) from exc
        
        return self._handle_response(response)
    
    async def get(
        self,
        path: str,
        query: Optional[QueryParams] = None
    ) -> Any:
        """Make an async GET request."""
        return await self.request("GET", path, query=query)
    
    async def post(
        self,
        path: str,
        body: Optional[Dict[str, Any]] = None,
        query: Optional[QueryParams] = None
    ) -> Any:
        """Make an async POST request."""
        return await self.request("POST", path, body=body, query=query)
    
    async def put(
        self,
        path: str,
        body: Optional[Dict[str, Any]] = None,
        query: Optional[QueryParams] = None
    ) -> Any:
        """Make an async PUT request."""
        return await self.request("PUT", path, body=body, query=query)
    
    async def patch(
        self,
        path: str,
        body: Optional[Dict[str, Any]] = None,
        query: Optional[QueryParams] = None
    ) -> Any:
        """Make an async PATCH request."""
        return await self.request("PATCH", path, body=body, query=query)
    
    async def delete(
        self,
        path: str,
        query: Optional[QueryParams] = None
    ) -> Any:
        """Make an async DELETE request."""
        return await self.request("DELETE", path, query=query)
    
    async def aclose(self) -> None:
        """Close the async HTTP client."""
        await self._client.aclose()
    
    async def __aenter__(self) -> "AsyncHttpClient":
        return self
    
    async def __aexit__(self, *args: Any) -> None:
        await self.aclose()
