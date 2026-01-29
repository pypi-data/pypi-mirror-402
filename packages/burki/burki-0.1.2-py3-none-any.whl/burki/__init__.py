"""
Burki Python SDK - Official SDK for the Burki Voice AI Platform.

Example usage:
    from burki import BurkiClient

    client = BurkiClient(api_key="your-api-key")
    assistants = client.assistants.list()
"""

from burki.client import BurkiClient
from burki.exceptions import (
    BurkiError,
    AuthenticationError,
    NotFoundError,
    ValidationError,
    RateLimitError,
    ServerError,
)

__version__ = "0.1.0"
__all__ = [
    "BurkiClient",
    "BurkiError",
    "AuthenticationError",
    "NotFoundError",
    "ValidationError",
    "RateLimitError",
    "ServerError",
]
