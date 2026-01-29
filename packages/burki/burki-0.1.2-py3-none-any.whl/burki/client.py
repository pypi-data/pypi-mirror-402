"""
Main Burki client module.

This is the entry point for interacting with the Burki API.
"""

from typing import Optional

from burki.auth import BurkiAuth
from burki.http_client import HTTPClient, DEFAULT_BASE_URL, DEFAULT_TIMEOUT
from burki.resources.assistants import AssistantsResource
from burki.resources.calls import CallsResource
from burki.resources.phone_numbers import PhoneNumbersResource
from burki.resources.documents import DocumentsResource
from burki.resources.tools import ToolsResource
from burki.resources.sms import SMSResource
from burki.resources.campaigns import CampaignsResource
from burki.realtime import RealtimeClient


class BurkiClient:
    """
    Main client for interacting with the Burki Voice AI API.

    Example:
        ```python
        from burki import BurkiClient

        client = BurkiClient(api_key="your-api-key")

        # List assistants
        assistants = client.assistants.list()

        # Create an assistant
        assistant = client.assistants.create(
            name="My Bot",
            llm_settings={"model": "gpt-4o-mini"}
        )
        ```
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        """
        Initialize the Burki client.

        Args:
            api_key: Your Burki API key from the dashboard.
            base_url: Base URL for the API. Defaults to https://api.burki.dev
            timeout: Request timeout in seconds. Defaults to 30.
        """
        self._auth = BurkiAuth(api_key)
        self._http_client = HTTPClient(
            auth=self._auth,
            base_url=base_url,
            timeout=timeout,
        )
        self._base_url = base_url

        # Initialize resource clients
        self._assistants: Optional[AssistantsResource] = None
        self._calls: Optional[CallsResource] = None
        self._phone_numbers: Optional[PhoneNumbersResource] = None
        self._documents: Optional[DocumentsResource] = None
        self._tools: Optional[ToolsResource] = None
        self._sms: Optional[SMSResource] = None
        self._campaigns: Optional[CampaignsResource] = None
        self._realtime: Optional[RealtimeClient] = None

    @property
    def assistants(self) -> AssistantsResource:
        """Access the Assistants resource."""
        if self._assistants is None:
            self._assistants = AssistantsResource(self._http_client)
        return self._assistants

    @property
    def calls(self) -> CallsResource:
        """Access the Calls resource."""
        if self._calls is None:
            self._calls = CallsResource(self._http_client)
        return self._calls

    @property
    def phone_numbers(self) -> PhoneNumbersResource:
        """Access the Phone Numbers resource."""
        if self._phone_numbers is None:
            self._phone_numbers = PhoneNumbersResource(self._http_client)
        return self._phone_numbers

    @property
    def documents(self) -> DocumentsResource:
        """Access the Documents resource."""
        if self._documents is None:
            self._documents = DocumentsResource(self._http_client)
        return self._documents

    @property
    def tools(self) -> ToolsResource:
        """Access the Tools resource."""
        if self._tools is None:
            self._tools = ToolsResource(self._http_client)
        return self._tools

    @property
    def sms(self) -> SMSResource:
        """Access the SMS resource."""
        if self._sms is None:
            self._sms = SMSResource(self._http_client)
        return self._sms

    @property
    def campaigns(self) -> CampaignsResource:
        """Access the Campaigns resource."""
        if self._campaigns is None:
            self._campaigns = CampaignsResource(self._http_client)
        return self._campaigns

    @property
    def realtime(self) -> RealtimeClient:
        """Access the Realtime (WebSocket) client."""
        if self._realtime is None:
            self._realtime = RealtimeClient(self._auth, self._base_url)
        return self._realtime

    def close(self) -> None:
        """Close all client connections."""
        self._http_client.close()

    async def close_async(self) -> None:
        """Close all async client connections."""
        await self._http_client.close_async()

    def __enter__(self) -> "BurkiClient":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()

    async def __aenter__(self) -> "BurkiClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close_async()
