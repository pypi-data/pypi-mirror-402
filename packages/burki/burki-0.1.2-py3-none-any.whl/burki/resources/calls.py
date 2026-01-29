"""
Calls resource for the Burki SDK.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from burki.resources.base import BaseResource
from burki.models.call import (
    Call,
    PaginatedCalls,
    CallTranscript,
    CallRecording,
    CallMetrics,
    CallAnalytics,
    CallStats,
    ChatMessage,
    WebhookLog,
    InitiateCallResponse,
)


class CallsResource(BaseResource):
    """
    Resource for managing calls.

    Example:
        ```python
        # Initiate an outbound call
        response = client.calls.initiate(
            from_phone_number="+14155559999",
            to_phone_number="+14155551234",
            welcome_message="Hello! This is a follow-up call."
        )

        # List calls
        calls = client.calls.list(status="completed")

        # Get call details
        call = client.calls.get(call_id=123)

        # Get transcripts
        transcripts = client.calls.get_transcripts(call_id=123)

        # Terminate a call
        client.calls.terminate(call_sid="CA123...")
        ```
    """

    def initiate(
        self,
        from_phone_number: str,
        to_phone_number: str,
        welcome_message: Optional[str] = None,
        agenda: Optional[str] = None,
        assistant_id: Optional[int] = None,
        variables: Optional[Dict[str, Any]] = None,
    ) -> InitiateCallResponse:
        """
        Initiate an outbound call from an assistant.

        Args:
            from_phone_number: The phone number to call from (E.164 format).
            to_phone_number: The phone number to call (E.164 format).
            welcome_message: Optional custom welcome message.
            agenda: Optional call agenda/context for the assistant.
            assistant_id: Optional assistant ID override (uses phone number's assigned assistant by default).
            variables: Optional variables to pass to the assistant.

        Returns:
            InitiateCallResponse with call details.
        """
        data: Dict[str, Any] = {
            "from_phone_number": from_phone_number,
            "to_phone_number": to_phone_number,
        }

        if welcome_message:
            data["welcome_message"] = welcome_message
        if agenda:
            data["agenda"] = agenda
        if assistant_id:
            data["assistant_id"] = assistant_id
        if variables:
            data["variables"] = variables

        response = self._http.post("/calls/initiate", json=data)
        return InitiateCallResponse.model_validate(response)

    async def initiate_async(
        self,
        from_phone_number: str,
        to_phone_number: str,
        welcome_message: Optional[str] = None,
        agenda: Optional[str] = None,
        assistant_id: Optional[int] = None,
        variables: Optional[Dict[str, Any]] = None,
    ) -> InitiateCallResponse:
        """
        Async version of initiate().
        """
        data: Dict[str, Any] = {
            "from_phone_number": from_phone_number,
            "to_phone_number": to_phone_number,
        }

        if welcome_message:
            data["welcome_message"] = welcome_message
        if agenda:
            data["agenda"] = agenda
        if assistant_id:
            data["assistant_id"] = assistant_id
        if variables:
            data["variables"] = variables

        response = await self._http.post_async("/calls/initiate", json=data)
        return InitiateCallResponse.model_validate(response)

    def list(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        assistant_id: Optional[int] = None,
        customer_phone: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        min_duration: Optional[int] = None,
        max_duration: Optional[int] = None,
    ) -> List[Call]:
        """
        List calls with filtering options.

        Args:
            skip: Number of items to skip.
            limit: Maximum number of items to return.
            status: Filter by call status (ongoing, completed, failed).
            assistant_id: Filter by assistant ID.
            customer_phone: Filter by customer phone number.
            date_from: Filter calls from this date.
            date_to: Filter calls to this date.
            min_duration: Minimum call duration in seconds.
            max_duration: Maximum call duration in seconds.

        Returns:
            List of Call objects.
        """
        params: Dict[str, Any] = {"skip": skip, "limit": limit}

        if status:
            params["status"] = status
        if assistant_id:
            params["assistant_id"] = assistant_id
        if customer_phone:
            params["customer_phone"] = customer_phone
        if date_from:
            params["date_from"] = date_from.isoformat()
        if date_to:
            params["date_to"] = date_to.isoformat()
        if min_duration is not None:
            params["min_duration"] = min_duration
        if max_duration is not None:
            params["max_duration"] = max_duration

        response = self._http.get("/api/v1/calls", params=params)

        if isinstance(response, dict) and "items" in response:
            return [Call.model_validate(item) for item in response["items"]]
        elif isinstance(response, list):
            return [Call.model_validate(item) for item in response]
        return []

    async def list_async(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        assistant_id: Optional[int] = None,
        customer_phone: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        min_duration: Optional[int] = None,
        max_duration: Optional[int] = None,
    ) -> List[Call]:
        """
        Async version of list().
        """
        params: Dict[str, Any] = {"skip": skip, "limit": limit}

        if status:
            params["status"] = status
        if assistant_id:
            params["assistant_id"] = assistant_id
        if customer_phone:
            params["customer_phone"] = customer_phone
        if date_from:
            params["date_from"] = date_from.isoformat()
        if date_to:
            params["date_to"] = date_to.isoformat()
        if min_duration is not None:
            params["min_duration"] = min_duration
        if max_duration is not None:
            params["max_duration"] = max_duration

        response = await self._http.get_async("/api/v1/calls", params=params)

        if isinstance(response, dict) and "items" in response:
            return [Call.model_validate(item) for item in response["items"]]
        elif isinstance(response, list):
            return [Call.model_validate(item) for item in response]
        return []

    def get(self, call_id: int) -> Call:
        """
        Get a specific call by ID.

        Args:
            call_id: The ID of the call.

        Returns:
            The Call object.
        """
        response = self._http.get(f"/api/v1/calls/{call_id}")
        return Call.model_validate(response)

    async def get_async(self, call_id: int) -> Call:
        """
        Async version of get().
        """
        response = await self._http.get_async(f"/api/v1/calls/{call_id}")
        return Call.model_validate(response)

    def get_by_sid(self, call_sid: str) -> Call:
        """
        Get a specific call by Twilio/Telnyx call SID.

        Args:
            call_sid: The call SID.

        Returns:
            The Call object.
        """
        response = self._http.get(f"/api/v1/calls/sid/{call_sid}")
        return Call.model_validate(response)

    async def get_by_sid_async(self, call_sid: str) -> Call:
        """
        Async version of get_by_sid().
        """
        response = await self._http.get_async(f"/api/v1/calls/sid/{call_sid}")
        return Call.model_validate(response)

    def update_metadata(self, call_id: int, metadata: Dict[str, Any]) -> Call:
        """
        Update the metadata for a specific call.

        Args:
            call_id: The ID of the call.
            metadata: Dictionary of metadata to merge with existing metadata.

        Returns:
            The updated Call object.
        """
        data = {"metadata": metadata}
        response = self._http.patch(f"/api/v1/calls/{call_id}/metadata", json=data)
        return Call.model_validate(response)

    async def update_metadata_async(self, call_id: int, metadata: Dict[str, Any]) -> Call:
        """
        Async version of update_metadata().
        """
        data = {"metadata": metadata}
        response = await self._http.patch_async(f"/api/v1/calls/{call_id}/metadata", json=data)
        return Call.model_validate(response)

    def get_transcripts(
        self,
        call_id: int,
        speaker: Optional[str] = None,
        include_interim: bool = False,
    ) -> List[CallTranscript]:
        """
        Get transcripts for a call.

        Args:
            call_id: The ID of the call.
            speaker: Filter by speaker (user or assistant).
            include_interim: Include interim (non-final) transcripts.

        Returns:
            List of CallTranscript objects.
        """
        params: Dict[str, Any] = {"include_interim": include_interim}
        if speaker:
            params["speaker"] = speaker

        response = self._http.get(f"/api/v1/calls/{call_id}/transcripts", params=params)
        return [CallTranscript.model_validate(item) for item in response]

    async def get_transcripts_async(
        self,
        call_id: int,
        speaker: Optional[str] = None,
        include_interim: bool = False,
    ) -> List[CallTranscript]:
        """
        Async version of get_transcripts().
        """
        params: Dict[str, Any] = {"include_interim": include_interim}
        if speaker:
            params["speaker"] = speaker

        response = await self._http.get_async(
            f"/api/v1/calls/{call_id}/transcripts", params=params
        )
        return [CallTranscript.model_validate(item) for item in response]

    def get_transcripts_by_sid(
        self,
        call_sid: str,
        speaker: Optional[str] = None,
        include_interim: bool = False,
    ) -> List[CallTranscript]:
        """
        Get transcripts for a call by SID.

        Args:
            call_sid: The call SID.
            speaker: Filter by speaker (user or assistant).
            include_interim: Include interim (non-final) transcripts.

        Returns:
            List of CallTranscript objects.
        """
        params: Dict[str, Any] = {"include_interim": include_interim}
        if speaker:
            params["speaker"] = speaker

        response = self._http.get(f"/api/v1/calls/sid/{call_sid}/transcripts", params=params)
        return [CallTranscript.model_validate(item) for item in response]

    async def get_transcripts_by_sid_async(
        self,
        call_sid: str,
        speaker: Optional[str] = None,
        include_interim: bool = False,
    ) -> List[CallTranscript]:
        """
        Async version of get_transcripts_by_sid().
        """
        params: Dict[str, Any] = {"include_interim": include_interim}
        if speaker:
            params["speaker"] = speaker

        response = await self._http.get_async(
            f"/api/v1/calls/sid/{call_sid}/transcripts", params=params
        )
        return [CallTranscript.model_validate(item) for item in response]

    def export_transcripts(
        self,
        call_id: int,
        format: str = "txt",
        speaker: Optional[str] = None,
    ) -> bytes:
        """
        Export call transcripts in various formats.

        Args:
            call_id: The ID of the call.
            format: Export format (txt, json, or csv).
            speaker: Filter by speaker.

        Returns:
            The exported data as bytes.
        """
        params: Dict[str, Any] = {"format": format}
        if speaker:
            params["speaker"] = speaker

        response = self._http.get(f"/api/v1/calls/{call_id}/transcripts/export", params=params)
        return response

    async def export_transcripts_async(
        self,
        call_id: int,
        format: str = "txt",
        speaker: Optional[str] = None,
    ) -> bytes:
        """
        Async version of export_transcripts().
        """
        params: Dict[str, Any] = {"format": format}
        if speaker:
            params["speaker"] = speaker

        response = await self._http.get_async(
            f"/api/v1/calls/{call_id}/transcripts/export", params=params
        )
        return response

    def get_recordings(
        self,
        call_id: int,
        recording_type: Optional[str] = None,
    ) -> List[CallRecording]:
        """
        Get recordings for a call.

        Args:
            call_id: The ID of the call.
            recording_type: Filter by recording type (user, assistant, mixed).

        Returns:
            List of CallRecording objects.
        """
        params: Dict[str, Any] = {}
        if recording_type:
            params["recording_type"] = recording_type

        response = self._http.get(f"/api/v1/calls/{call_id}/recordings", params=params)
        return [CallRecording.model_validate(item) for item in response]

    async def get_recordings_async(
        self,
        call_id: int,
        recording_type: Optional[str] = None,
    ) -> List[CallRecording]:
        """
        Async version of get_recordings().
        """
        params: Dict[str, Any] = {}
        if recording_type:
            params["recording_type"] = recording_type

        response = await self._http.get_async(
            f"/api/v1/calls/{call_id}/recordings", params=params
        )
        return [CallRecording.model_validate(item) for item in response]

    def get_recordings_by_sid(
        self,
        call_sid: str,
        recording_type: Optional[str] = None,
    ) -> List[CallRecording]:
        """
        Get recordings for a call by SID.

        Args:
            call_sid: The call SID.
            recording_type: Filter by recording type.

        Returns:
            List of CallRecording objects.
        """
        params: Dict[str, Any] = {}
        if recording_type:
            params["recording_type"] = recording_type

        response = self._http.get(f"/api/v1/calls/sid/{call_sid}/recordings", params=params)
        return [CallRecording.model_validate(item) for item in response]

    async def get_recordings_by_sid_async(
        self,
        call_sid: str,
        recording_type: Optional[str] = None,
    ) -> List[CallRecording]:
        """
        Async version of get_recordings_by_sid().
        """
        params: Dict[str, Any] = {}
        if recording_type:
            params["recording_type"] = recording_type

        response = await self._http.get_async(
            f"/api/v1/calls/sid/{call_sid}/recordings", params=params
        )
        return [CallRecording.model_validate(item) for item in response]

    def get_recording_url(self, call_id: int, recording_id: int) -> str:
        """
        Get the streaming URL for a recording.

        Args:
            call_id: The ID of the call.
            recording_id: The ID of the recording.

        Returns:
            The URL to stream/play the recording.
        """
        # This endpoint returns audio data, but for URL purposes we return the endpoint
        return f"{self._http._base_url}/api/v1/calls/{call_id}/recording/{recording_id}/play"

    def get_metrics(self, call_id: int) -> CallMetrics:
        """
        Get calculated metrics for a call.

        Args:
            call_id: The ID of the call.

        Returns:
            The CallMetrics object.
        """
        response = self._http.get(f"/api/v1/calls/{call_id}/metrics")
        return CallMetrics.model_validate(response)

    async def get_metrics_async(self, call_id: int) -> CallMetrics:
        """
        Async version of get_metrics().
        """
        response = await self._http.get_async(f"/api/v1/calls/{call_id}/metrics")
        return CallMetrics.model_validate(response)

    def get_messages(
        self,
        call_id: int,
        role: Optional[str] = None,
    ) -> List[ChatMessage]:
        """
        Get chat messages (LLM conversation) for a call.

        Args:
            call_id: The ID of the call.
            role: Filter by role (system, user, assistant).

        Returns:
            List of ChatMessage objects.
        """
        params: Dict[str, Any] = {}
        if role:
            params["role"] = role

        response = self._http.get(f"/api/v1/calls/{call_id}/messages", params=params)
        return [ChatMessage.model_validate(item) for item in response]

    async def get_messages_async(
        self,
        call_id: int,
        role: Optional[str] = None,
    ) -> List[ChatMessage]:
        """
        Async version of get_messages().
        """
        params: Dict[str, Any] = {}
        if role:
            params["role"] = role

        response = await self._http.get_async(
            f"/api/v1/calls/{call_id}/messages", params=params
        )
        return [ChatMessage.model_validate(item) for item in response]

    def get_webhook_logs(
        self,
        call_id: int,
        webhook_type: Optional[str] = None,
    ) -> List[WebhookLog]:
        """
        Get webhook logs for a call.

        Args:
            call_id: The ID of the call.
            webhook_type: Filter by webhook type.

        Returns:
            List of WebhookLog objects.
        """
        params: Dict[str, Any] = {}
        if webhook_type:
            params["webhook_type"] = webhook_type

        response = self._http.get(f"/api/v1/calls/{call_id}/webhook-logs", params=params)
        return [WebhookLog.model_validate(item) for item in response]

    async def get_webhook_logs_async(
        self,
        call_id: int,
        webhook_type: Optional[str] = None,
    ) -> List[WebhookLog]:
        """
        Async version of get_webhook_logs().
        """
        params: Dict[str, Any] = {}
        if webhook_type:
            params["webhook_type"] = webhook_type

        response = await self._http.get_async(
            f"/api/v1/calls/{call_id}/webhook-logs", params=params
        )
        return [WebhookLog.model_validate(item) for item in response]

    def terminate(self, call_sid: str) -> Dict[str, Any]:
        """
        Terminate an ongoing call.

        Args:
            call_sid: The call SID to terminate.

        Returns:
            Response indicating success.
        """
        response = self._http.post(f"/api/v1/calls/{call_sid}/terminate")
        return response

    async def terminate_async(self, call_sid: str) -> Dict[str, Any]:
        """
        Async version of terminate().
        """
        response = await self._http.post_async(f"/api/v1/calls/{call_sid}/terminate")
        return response

    def get_analytics(self, period: str = "7d") -> CallAnalytics:
        """
        Get call analytics for your organization.

        Args:
            period: Analysis period (1d, 7d, 30d, 90d).

        Returns:
            The CallAnalytics object.
        """
        response = self._http.get("/api/v1/calls/analytics", params={"period": period})
        return CallAnalytics.model_validate(response)

    async def get_analytics_async(self, period: str = "7d") -> CallAnalytics:
        """
        Async version of get_analytics().
        """
        response = await self._http.get_async(
            "/api/v1/calls/analytics", params={"period": period}
        )
        return CallAnalytics.model_validate(response)

    def get_stats(self) -> CallStats:
        """
        Get basic call statistics.

        Returns:
            The CallStats object.
        """
        response = self._http.get("/api/v1/calls/stats")
        return CallStats.model_validate(response)

    async def get_stats_async(self) -> CallStats:
        """
        Async version of get_stats().
        """
        response = await self._http.get_async("/api/v1/calls/stats")
        return CallStats.model_validate(response)

    def get_count(
        self,
        status: Optional[str] = None,
        assistant_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> int:
        """
        Get the count of calls with optional filters.

        Args:
            status: Filter by call status.
            assistant_id: Filter by assistant ID.
            date_from: Filter calls from this date.
            date_to: Filter calls to this date.

        Returns:
            The count of calls.
        """
        params: Dict[str, Any] = {}
        if status:
            params["status"] = status
        if assistant_id:
            params["assistant_id"] = assistant_id
        if date_from:
            params["date_from"] = date_from.isoformat()
        if date_to:
            params["date_to"] = date_to.isoformat()

        response = self._http.get("/api/v1/calls/count", params=params)
        return response.get("count", 0) if isinstance(response, dict) else 0

    async def get_count_async(
        self,
        status: Optional[str] = None,
        assistant_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> int:
        """
        Async version of get_count().
        """
        params: Dict[str, Any] = {}
        if status:
            params["status"] = status
        if assistant_id:
            params["assistant_id"] = assistant_id
        if date_from:
            params["date_from"] = date_from.isoformat()
        if date_to:
            params["date_to"] = date_to.isoformat()

        response = await self._http.get_async("/api/v1/calls/count", params=params)
        return response.get("count", 0) if isinstance(response, dict) else 0

    def search(
        self,
        query: str,
        limit: int = 50,
    ) -> List[Call]:
        """
        Search calls by various criteria.

        Args:
            query: Search query (minimum 3 characters).
            limit: Maximum number of results.

        Returns:
            List of matching Call objects.
        """
        params = {"q": query, "limit": limit}
        response = self._http.get("/api/v1/calls/search", params=params)
        return [Call.model_validate(item) for item in response]

    async def search_async(
        self,
        query: str,
        limit: int = 50,
    ) -> List[Call]:
        """
        Async version of search().
        """
        params = {"q": query, "limit": limit}
        response = await self._http.get_async("/api/v1/calls/search", params=params)
        return [Call.model_validate(item) for item in response]

    def export(
        self,
        format: str = "csv",
        status: Optional[str] = None,
        assistant_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> bytes:
        """
        Export calls data.

        Args:
            format: Export format (csv or json).
            status: Filter by call status.
            assistant_id: Filter by assistant ID.
            date_from: Filter calls from this date.
            date_to: Filter calls to this date.

        Returns:
            The exported data as bytes.
        """
        params: Dict[str, Any] = {"format": format}
        if status:
            params["status"] = status
        if assistant_id:
            params["assistant_id"] = assistant_id
        if date_from:
            params["date_from"] = date_from.isoformat()
        if date_to:
            params["date_to"] = date_to.isoformat()

        response = self._http.get("/api/v1/calls/export", params=params)
        return response

    async def export_async(
        self,
        format: str = "csv",
        status: Optional[str] = None,
        assistant_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> bytes:
        """
        Async version of export().
        """
        params: Dict[str, Any] = {"format": format}
        if status:
            params["status"] = status
        if assistant_id:
            params["assistant_id"] = assistant_id
        if date_from:
            params["date_from"] = date_from.isoformat()
        if date_to:
            params["date_to"] = date_to.isoformat()

        response = await self._http.get_async("/api/v1/calls/export", params=params)
        return response
