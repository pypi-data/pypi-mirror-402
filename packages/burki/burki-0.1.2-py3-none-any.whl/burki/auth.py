"""
Authentication module for Burki SDK.

Handles API key authentication and token management.
"""

from typing import Dict


class BurkiAuth:
    """Authentication handler for Burki API."""

    def __init__(self, api_key: str) -> None:
        """
        Initialize authentication with API key.

        Args:
            api_key: Your Burki API key from the dashboard.
        """
        if not api_key:
            raise ValueError("API key is required")
        self._api_key = api_key

    @property
    def headers(self) -> Dict[str, str]:
        """Get authentication headers for API requests."""
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    def get_websocket_token(self) -> str:
        """Get the token for WebSocket authentication."""
        return self._api_key
