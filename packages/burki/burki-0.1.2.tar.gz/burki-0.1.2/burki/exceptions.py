"""
Burki SDK Exceptions.

This module defines the exception hierarchy for the Burki SDK.
"""

from typing import Any, Optional


class BurkiError(Exception):
    """Base exception for all Burki SDK errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_body: Optional[Any] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_body = response_body

    def __str__(self) -> str:
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message


class AuthenticationError(BurkiError):
    """Raised when authentication fails (401)."""

    def __init__(
        self,
        message: str = "Authentication failed. Check your API key.",
        response_body: Optional[Any] = None,
    ) -> None:
        super().__init__(message, status_code=401, response_body=response_body)


class NotFoundError(BurkiError):
    """Raised when a resource is not found (404)."""

    def __init__(
        self,
        message: str = "Resource not found.",
        response_body: Optional[Any] = None,
    ) -> None:
        super().__init__(message, status_code=404, response_body=response_body)


class ValidationError(BurkiError):
    """Raised when request validation fails (400, 422)."""

    def __init__(
        self,
        message: str = "Request validation failed.",
        status_code: int = 400,
        response_body: Optional[Any] = None,
    ) -> None:
        super().__init__(message, status_code=status_code, response_body=response_body)


class RateLimitError(BurkiError):
    """Raised when rate limit is exceeded (429)."""

    def __init__(
        self,
        message: str = "Rate limit exceeded. Please slow down.",
        response_body: Optional[Any] = None,
        retry_after: Optional[int] = None,
    ) -> None:
        super().__init__(message, status_code=429, response_body=response_body)
        self.retry_after = retry_after


class ServerError(BurkiError):
    """Raised when the server returns an error (5xx)."""

    def __init__(
        self,
        message: str = "Server error occurred.",
        status_code: int = 500,
        response_body: Optional[Any] = None,
    ) -> None:
        super().__init__(message, status_code=status_code, response_body=response_body)


class WebSocketError(BurkiError):
    """Raised when a WebSocket error occurs."""

    def __init__(
        self,
        message: str = "WebSocket error occurred.",
        response_body: Optional[Any] = None,
    ) -> None:
        super().__init__(message, response_body=response_body)
