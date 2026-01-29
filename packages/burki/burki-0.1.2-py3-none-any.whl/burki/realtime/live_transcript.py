"""
Live transcript WebSocket stream.
"""

import asyncio
import json
from datetime import datetime
from typing import TYPE_CHECKING, Any, AsyncIterator, Optional, Union

import websockets

from burki.models.realtime import TranscriptEvent, CallStatusEvent
from burki.exceptions import WebSocketError

if TYPE_CHECKING:
    from websockets.asyncio.client import ClientConnection


class LiveTranscriptStream:
    """
    WebSocket stream for live call transcripts.

    Usage:
        ```python
        async with client.realtime.live_transcript(call_sid) as stream:
            async for event in stream:
                if isinstance(event, TranscriptEvent):
                    print(f"{event.speaker}: {event.content}")
        ```
    """

    def __init__(self, ws_url: str, token: str) -> None:
        """
        Initialize the live transcript stream.

        Args:
            ws_url: WebSocket URL for the transcript stream.
            token: Authentication token.
        """
        self._ws_url = ws_url
        self._token = token
        self._websocket: Optional[Any] = None  # websockets connection
        self._running = False

    async def __aenter__(self) -> "LiveTranscriptStream":
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
            raise WebSocketError(f"Failed to connect to transcript stream: {e}")

    async def disconnect(self) -> None:
        """Disconnect from the WebSocket."""
        self._running = False
        if self._websocket:
            await self._websocket.close()
            self._websocket = None

    async def __aiter__(self) -> AsyncIterator[Union[TranscriptEvent, CallStatusEvent]]:
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
                    await self._websocket.ping()
                except Exception:
                    break
            except websockets.exceptions.ConnectionClosed:
                break
            except Exception as e:
                raise WebSocketError(f"Error receiving transcript: {e}")

    def _parse_event(self, data: dict) -> Optional[Union[TranscriptEvent, CallStatusEvent]]:
        """Parse a WebSocket message into an event object."""
        event_type = data.get("type")

        if event_type == "transcript":
            transcript_data = data.get("data", {})
            return TranscriptEvent(
                type="transcript",
                call_sid=data.get("call_sid", ""),
                timestamp=datetime.fromisoformat(data.get("timestamp", datetime.utcnow().isoformat())),
                content=transcript_data.get("content", ""),
                speaker=transcript_data.get("speaker", "user"),
                is_final=transcript_data.get("is_final", True),
                confidence=transcript_data.get("confidence"),
                segment_start=transcript_data.get("segment_start"),
                segment_end=transcript_data.get("segment_end"),
            )
        elif event_type == "call_status":
            return CallStatusEvent(
                type="call_status",
                call_sid=data.get("call_sid", ""),
                timestamp=datetime.fromisoformat(data.get("timestamp", datetime.utcnow().isoformat())),
                status=data.get("status", ""),
                metadata=data.get("metadata", {}),
            )

        return None

    @property
    def connected(self) -> bool:
        """Check if the WebSocket is connected."""
        return self._websocket is not None and self._running
