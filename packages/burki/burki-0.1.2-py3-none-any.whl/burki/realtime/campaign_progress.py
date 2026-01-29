"""
Campaign progress WebSocket stream.
"""

import asyncio
import json
from datetime import datetime
from typing import TYPE_CHECKING, Any, AsyncIterator, Optional, Union

import websockets

from burki.models.realtime import (
    CampaignProgressEvent,
    CampaignContactEvent,
    CampaignCompletedEvent,
)
from burki.exceptions import WebSocketError

if TYPE_CHECKING:
    from websockets.asyncio.client import ClientConnection


CampaignEvent = Union[CampaignProgressEvent, CampaignContactEvent, CampaignCompletedEvent]


class CampaignProgressStream:
    """
    WebSocket stream for campaign progress updates.

    Usage:
        ```python
        async with client.realtime.campaign_progress(campaign_id) as stream:
            async for event in stream:
                if isinstance(event, CampaignProgressEvent):
                    print(f"Progress: {event.completed_contacts}/{event.total_contacts}")
                elif isinstance(event, CampaignCompletedEvent):
                    print(f"Campaign completed! Success rate: {event.success_rate}%")
        ```
    """

    def __init__(self, ws_url: str, token: str) -> None:
        """
        Initialize the campaign progress stream.

        Args:
            ws_url: WebSocket URL for the campaign progress stream.
            token: Authentication token.
        """
        self._ws_url = ws_url
        self._token = token
        self._websocket: Optional[Any] = None  # websockets connection
        self._running = False

    async def __aenter__(self) -> "CampaignProgressStream":
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.disconnect()

    async def connect(self) -> None:
        """Connect to the WebSocket."""
        try:
            # Add token as query parameter
            url = f"{self._ws_url}?token={self._token}"
            self._websocket = await websockets.connect(url)
            self._running = True
        except Exception as e:
            raise WebSocketError(f"Failed to connect to campaign progress stream: {e}")

    async def disconnect(self) -> None:
        """Disconnect from the WebSocket."""
        self._running = False
        if self._websocket:
            await self._websocket.close()
            self._websocket = None

    async def __aiter__(self) -> AsyncIterator[CampaignEvent]:
        """Iterate over incoming events."""
        if not self._websocket:
            raise WebSocketError("Not connected. Use 'async with' or call connect() first.")

        while self._running:
            try:
                message = await asyncio.wait_for(
                    self._websocket.recv(),
                    timeout=60.0  # 1 minute timeout for keepalive
                )

                try:
                    data = json.loads(message)
                    event = self._parse_event(data)
                    if event:
                        yield event
                except json.JSONDecodeError:
                    continue

            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                try:
                    pong = await self._websocket.ping()
                    await asyncio.wait_for(pong, timeout=10)
                except Exception:
                    break
            except websockets.exceptions.ConnectionClosed:
                break
            except Exception as e:
                raise WebSocketError(f"Error receiving campaign progress: {e}")

    def _parse_event(self, data: dict) -> Optional[CampaignEvent]:
        """Parse a WebSocket message into an event object."""
        event_type = data.get("type")

        timestamp = datetime.fromisoformat(
            data.get("timestamp", datetime.utcnow().isoformat())
        )
        campaign_id = data.get("campaign_id", 0)

        if event_type == "progress":
            return CampaignProgressEvent(
                type="progress",
                campaign_id=campaign_id,
                timestamp=timestamp,
                total_contacts=data.get("total_contacts", 0),
                completed_contacts=data.get("completed_contacts", 0),
                failed_contacts=data.get("failed_contacts", 0),
                pending_contacts=data.get("pending_contacts", 0),
                in_progress_contacts=data.get("in_progress_contacts", 0),
                completion_percentage=data.get("completion_percentage", 0.0),
                contact_id=data.get("contact_id"),
                contact_phone=data.get("contact_phone"),
                contact_status=data.get("contact_status"),
                contact_error=data.get("contact_error"),
            )
        elif event_type == "contact_update":
            return CampaignContactEvent(
                type="contact_update",
                campaign_id=campaign_id,
                timestamp=timestamp,
                contact_id=data.get("contact_id", 0),
                phone_number=data.get("phone_number", ""),
                status=data.get("status", ""),
                call_sid=data.get("call_sid"),
                call_duration=data.get("call_duration"),
                error_message=data.get("error_message"),
            )
        elif event_type == "campaign_completed":
            return CampaignCompletedEvent(
                type="campaign_completed",
                campaign_id=campaign_id,
                timestamp=timestamp,
                total_contacts=data.get("total_contacts", 0),
                completed_contacts=data.get("completed_contacts", 0),
                failed_contacts=data.get("failed_contacts", 0),
                success_rate=data.get("success_rate", 0.0),
                total_duration=data.get("total_duration", 0),
                total_cost=data.get("total_cost", 0.0),
            )

        return None

    async def send_ping(self) -> None:
        """Send a ping message to keep the connection alive."""
        if self._websocket:
            await self._websocket.send(json.dumps({"type": "ping"}))

    @property
    def connected(self) -> bool:
        """Check if the WebSocket is connected."""
        return self._websocket is not None and self._running
