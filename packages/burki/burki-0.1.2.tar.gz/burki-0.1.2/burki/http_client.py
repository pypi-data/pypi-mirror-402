"""
HTTP client module for Burki SDK.

Provides the base HTTP client with retry logic and error handling.
"""

from typing import Any, Dict, Optional, Type, TypeVar, Union
import httpx

from burki.auth import BurkiAuth
from burki.exceptions import (
    AuthenticationError,
    BurkiError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
)

T = TypeVar("T")

DEFAULT_BASE_URL = "https://api.burki.dev"
DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 3


class HTTPClient:
    """Base HTTP client for making API requests."""

    def __init__(
        self,
        auth: BurkiAuth,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ) -> None:
        """
        Initialize the HTTP client.

        Args:
            auth: Authentication handler.
            base_url: Base URL for the API.
            timeout: Request timeout in seconds.
            max_retries: Maximum number of retries for failed requests.
        """
        self._auth = auth
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._max_retries = max_retries
        self._client: Optional[httpx.Client] = None
        self._async_client: Optional[httpx.AsyncClient] = None

    def _get_client(self) -> httpx.Client:
        """Get or create the sync HTTP client."""
        if self._client is None:
            self._client = httpx.Client(
                base_url=self._base_url,
                headers=self._auth.headers,
                timeout=self._timeout,
            )
        return self._client

    def _get_async_client(self) -> httpx.AsyncClient:
        """Get or create the async HTTP client."""
        if self._async_client is None:
            self._async_client = httpx.AsyncClient(
                base_url=self._base_url,
                headers=self._auth.headers,
                timeout=self._timeout,
            )
        return self._async_client

    def _handle_response(self, response: httpx.Response) -> Any:
        """
        Handle API response and raise appropriate exceptions.

        Args:
            response: The HTTP response object.

        Returns:
            The parsed JSON response data.

        Raises:
            AuthenticationError: If authentication fails.
            NotFoundError: If the resource is not found.
            ValidationError: If request validation fails.
            RateLimitError: If rate limit is exceeded.
            ServerError: If a server error occurs.
            BurkiError: For other errors.
        """
        try:
            data = response.json() if response.content else None
        except Exception:
            data = None

        if response.status_code == 401:
            message = data.get("detail", "Authentication failed") if data else "Authentication failed"
            raise AuthenticationError(message=message, response_body=data)

        if response.status_code == 404:
            message = data.get("detail", "Resource not found") if data else "Resource not found"
            raise NotFoundError(message=message, response_body=data)

        if response.status_code in (400, 422):
            message = data.get("detail", "Validation error") if data else "Validation error"
            raise ValidationError(
                message=message, status_code=response.status_code, response_body=data
            )

        if response.status_code == 429:
            message = data.get("detail", "Rate limit exceeded") if data else "Rate limit exceeded"
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(
                message=message,
                response_body=data,
                retry_after=int(retry_after) if retry_after else None,
            )

        if response.status_code >= 500:
            message = data.get("detail", "Server error") if data else "Server error"
            raise ServerError(
                message=message, status_code=response.status_code, response_body=data
            )

        if not response.is_success:
            message = data.get("detail", f"Request failed with status {response.status_code}") if data else f"Request failed with status {response.status_code}"
            raise BurkiError(
                message=message, status_code=response.status_code, response_body=data
            )

        return data

    def request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        """
        Make a synchronous HTTP request.

        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE).
            path: API endpoint path.
            params: Query parameters.
            json: JSON body data.
            data: Form data.
            files: Files to upload.
            headers: Additional headers.

        Returns:
            The parsed response data.
        """
        client = self._get_client()
        
        # Merge headers
        request_headers = dict(self._auth.headers)
        if headers:
            request_headers.update(headers)
        
        # Remove Content-Type for file uploads
        if files:
            request_headers.pop("Content-Type", None)

        response = client.request(
            method=method,
            url=path,
            params=params,
            json=json,
            data=data,
            files=files,
            headers=request_headers,
        )
        return self._handle_response(response)

    async def request_async(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        """
        Make an asynchronous HTTP request.

        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE).
            path: API endpoint path.
            params: Query parameters.
            json: JSON body data.
            data: Form data.
            files: Files to upload.
            headers: Additional headers.

        Returns:
            The parsed response data.
        """
        client = self._get_async_client()
        
        # Merge headers
        request_headers = dict(self._auth.headers)
        if headers:
            request_headers.update(headers)
        
        # Remove Content-Type for file uploads
        if files:
            request_headers.pop("Content-Type", None)

        response = await client.request(
            method=method,
            url=path,
            params=params,
            json=json,
            data=data,
            files=files,
            headers=request_headers,
        )
        return self._handle_response(response)

    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Make a GET request."""
        return self.request("GET", path, params=params)

    async def get_async(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Make an async GET request."""
        return await self.request_async("GET", path, params=params)

    def post(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Make a POST request."""
        return self.request("POST", path, json=json, data=data, files=files)

    async def post_async(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Make an async POST request."""
        return await self.request_async("POST", path, json=json, data=data, files=files)

    def put(self, path: str, json: Optional[Dict[str, Any]] = None) -> Any:
        """Make a PUT request."""
        return self.request("PUT", path, json=json)

    async def put_async(self, path: str, json: Optional[Dict[str, Any]] = None) -> Any:
        """Make an async PUT request."""
        return await self.request_async("PUT", path, json=json)

    def patch(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Make a PATCH request."""
        return self.request("PATCH", path, json=json, params=params)

    async def patch_async(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Make an async PATCH request."""
        return await self.request_async("PATCH", path, json=json, params=params)

    def delete(self, path: str) -> Any:
        """Make a DELETE request."""
        return self.request("DELETE", path)

    async def delete_async(self, path: str) -> Any:
        """Make an async DELETE request."""
        return await self.request_async("DELETE", path)

    def close(self) -> None:
        """Close the HTTP client connections."""
        if self._client:
            self._client.close()
            self._client = None

    async def close_async(self) -> None:
        """Close the async HTTP client connections."""
        if self._async_client:
            await self._async_client.aclose()
            self._async_client = None
