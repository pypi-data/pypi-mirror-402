"""
Realtime client for WebSocket connections.
"""

from typing import TYPE_CHECKING

from burki.realtime.live_transcript import LiveTranscriptStream
from burki.realtime.campaign_progress import CampaignProgressStream

if TYPE_CHECKING:
    from burki.auth import BurkiAuth


class RealtimeClient:
    """
    Client for real-time WebSocket connections.

    Example:
        ```python
        # Stream live transcripts during a call
        async with client.realtime.live_transcript(call_sid) as stream:
            async for event in stream:
                print(f"{event.speaker}: {event.content}")

        # Stream campaign progress updates
        async with client.realtime.campaign_progress(campaign_id) as stream:
            async for update in stream:
                print(f"Progress: {update.completed}/{update.total}")
        ```
    """

    def __init__(self, auth: "BurkiAuth", base_url: str) -> None:
        """
        Initialize the realtime client.

        Args:
            auth: Authentication handler.
            base_url: Base URL for the API (will be converted to WebSocket URL).
        """
        self._auth = auth
        
        # Convert HTTP URL to WebSocket URL
        ws_url = base_url.replace("https://", "wss://").replace("http://", "ws://")
        self._ws_base_url = ws_url.rstrip("/")

    def live_transcript(self, call_sid: str) -> LiveTranscriptStream:
        """
        Create a live transcript stream for a call.

        Args:
            call_sid: The call SID to stream transcripts for.

        Returns:
            A LiveTranscriptStream context manager.
        """
        return LiveTranscriptStream(
            ws_url=f"{self._ws_base_url}/live-transcript/{call_sid}",
            token=self._auth.get_websocket_token(),
        )

    def campaign_progress(self, campaign_id: int) -> CampaignProgressStream:
        """
        Create a campaign progress stream.

        Args:
            campaign_id: The ID of the campaign to monitor.

        Returns:
            A CampaignProgressStream context manager.
        """
        return CampaignProgressStream(
            ws_url=f"{self._ws_base_url}/ws/campaigns/{campaign_id}/progress",
            token=self._auth.get_websocket_token(),
        )
