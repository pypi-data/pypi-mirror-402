"""
Base resource class for Burki SDK.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from burki.http_client import HTTPClient


class BaseResource:
    """Base class for all resource classes."""

    def __init__(self, http_client: "HTTPClient") -> None:
        """
        Initialize the resource.

        Args:
            http_client: The HTTP client instance.
        """
        self._http = http_client
