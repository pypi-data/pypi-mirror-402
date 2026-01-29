"""
SMS resource for the Burki SDK.
"""

from typing import Any, Dict, List, Optional

from burki.resources.base import BaseResource
from burki.models.sms import (
    SMS,
    SMSConversation,
    SMSMessage,
    SendSMSResponse,
    SMSStatusResponse,
    SMSQueueStats,
)


class SMSResource(BaseResource):
    """
    Resource for managing SMS messaging.

    Example:
        ```python
        # Send an SMS message
        response = client.sms.send(
            from_phone_number="+14155559999",
            to_phone_number="+14155551234",
            message="Hello from Burki!"
        )

        # Get SMS conversations
        conversations = client.sms.list_conversations()

        # Get messages in a conversation
        messages = client.sms.get_messages(conversation_id="123")

        # Get queue statistics
        stats = client.sms.get_queue_stats()
        ```
    """

    def send(
        self,
        from_phone_number: str,
        to_phone_number: str,
        message: str,
        media_urls: Optional[List[str]] = None,
        queue: bool = True,
        idempotency_key: Optional[str] = None,
    ) -> SendSMSResponse:
        """
        Send an SMS message through an assistant.

        The system will automatically:
        1. Find the assistant associated with the from_phone_number
        2. Use the assistant's configured telephony provider (Twilio, Telnyx, or Vonage)
        3. Queue the SMS for delivery with per-provider rate limiting (default)
           or send immediately if queue=False
        4. Persist the outbound message to the SMS conversation

        Args:
            from_phone_number: Sender phone number (must be assigned to an assistant).
            to_phone_number: Recipient phone number (E.164 format).
            message: SMS message content (max 1600 chars).
            media_urls: Optional list of media URLs for MMS.
            queue: If True (default), queue with rate limiting. If False, send immediately.
            idempotency_key: Optional key to dedupe retried requests.

        Returns:
            SendSMSResponse with send status and message ID.
        """
        data: Dict[str, Any] = {
            "from_phone_number": from_phone_number,
            "to_phone_number": to_phone_number,
            "message": message,
            "queue": queue,
        }

        if media_urls:
            data["media_urls"] = media_urls
        if idempotency_key:
            data["idempotency_key"] = idempotency_key

        response = self._http.post("/sms/send", json=data)
        return SendSMSResponse.model_validate(response)

    async def send_async(
        self,
        from_phone_number: str,
        to_phone_number: str,
        message: str,
        media_urls: Optional[List[str]] = None,
        queue: bool = True,
        idempotency_key: Optional[str] = None,
    ) -> SendSMSResponse:
        """
        Async version of send().
        """
        data: Dict[str, Any] = {
            "from_phone_number": from_phone_number,
            "to_phone_number": to_phone_number,
            "message": message,
            "queue": queue,
        }

        if media_urls:
            data["media_urls"] = media_urls
        if idempotency_key:
            data["idempotency_key"] = idempotency_key

        response = await self._http.post_async("/sms/send", json=data)
        return SendSMSResponse.model_validate(response)

    def get_status(self, message_id: str) -> SMSStatusResponse:
        """
        Get the status of a sent SMS message.

        Args:
            message_id: The message ID returned from send().

        Returns:
            SMSStatusResponse with delivery status.
        """
        response = self._http.get(f"/sms/status/{message_id}")
        return SMSStatusResponse.model_validate(response)

    async def get_status_async(self, message_id: str) -> SMSStatusResponse:
        """
        Async version of get_status().
        """
        response = await self._http.get_async(f"/sms/status/{message_id}")
        return SMSStatusResponse.model_validate(response)

    def cancel(self, message_id: str) -> Dict[str, Any]:
        """
        Cancel a queued SMS message (before it's sent).

        Args:
            message_id: The message ID to cancel.

        Returns:
            Response indicating cancellation result.
        """
        response = self._http.post(f"/sms/cancel/{message_id}")
        return response

    async def cancel_async(self, message_id: str) -> Dict[str, Any]:
        """
        Async version of cancel().
        """
        response = await self._http.post_async(f"/sms/cancel/{message_id}")
        return response

    def get_queue_stats(self) -> SMSQueueStats:
        """
        Get SMS queue statistics.

        Returns:
            SMSQueueStats with queue information.
        """
        response = self._http.get("/sms/queue/stats")
        return SMSQueueStats.model_validate(response)

    async def get_queue_stats_async(self) -> SMSQueueStats:
        """
        Async version of get_queue_stats().
        """
        response = await self._http.get_async("/sms/queue/stats")
        return SMSQueueStats.model_validate(response)

    # SMS Conversations API

    def list_conversations(
        self,
        skip: int = 0,
        limit: int = 50,
        status: Optional[str] = None,
        assistant_id: Optional[int] = None,
        customer_phone: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> List[SMSConversation]:
        """
        List SMS conversations.

        Args:
            skip: Number of items to skip.
            limit: Maximum number of items to return.
            status: Filter by status (active, completed).
            assistant_id: Filter by assistant ID.
            customer_phone: Filter by customer phone number.
            date_from: Filter conversations from this date (ISO format).
            date_to: Filter conversations to this date (ISO format).

        Returns:
            List of SMSConversation objects.
        """
        params: Dict[str, Any] = {"skip": skip, "limit": limit}

        if status:
            params["status"] = status
        if assistant_id:
            params["assistant_id"] = assistant_id
        if customer_phone:
            params["customer_phone"] = customer_phone
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to

        response = self._http.get("/api/v1/sms-conversations/", params=params)
        return [SMSConversation.model_validate(item) for item in response]

    async def list_conversations_async(
        self,
        skip: int = 0,
        limit: int = 50,
        status: Optional[str] = None,
        assistant_id: Optional[int] = None,
        customer_phone: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> List[SMSConversation]:
        """
        Async version of list_conversations().
        """
        params: Dict[str, Any] = {"skip": skip, "limit": limit}

        if status:
            params["status"] = status
        if assistant_id:
            params["assistant_id"] = assistant_id
        if customer_phone:
            params["customer_phone"] = customer_phone
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to

        response = await self._http.get_async("/api/v1/sms-conversations/", params=params)
        return [SMSConversation.model_validate(item) for item in response]

    def get_conversation(self, conversation_id: str) -> SMSConversation:
        """
        Get a specific SMS conversation by ID.

        Args:
            conversation_id: The conversation ID.

        Returns:
            The SMSConversation object.
        """
        response = self._http.get(f"/api/v1/sms-conversations/{conversation_id}")
        return SMSConversation.model_validate(response)

    async def get_conversation_async(self, conversation_id: str) -> SMSConversation:
        """
        Async version of get_conversation().
        """
        response = await self._http.get_async(f"/api/v1/sms-conversations/{conversation_id}")
        return SMSConversation.model_validate(response)

    def get_messages(self, conversation_id: str) -> List[SMSMessage]:
        """
        Get all messages in an SMS conversation.

        Args:
            conversation_id: The conversation ID.

        Returns:
            List of SMSMessage objects.
        """
        response = self._http.get(f"/api/v1/sms-conversations/{conversation_id}/messages")
        return [SMSMessage.model_validate(item) for item in response]

    async def get_messages_async(self, conversation_id: str) -> List[SMSMessage]:
        """
        Async version of get_messages().
        """
        response = await self._http.get_async(
            f"/api/v1/sms-conversations/{conversation_id}/messages"
        )
        return [SMSMessage.model_validate(item) for item in response]

    def get_related_conversations(self, conversation_id: str) -> List[Dict[str, Any]]:
        """
        Get related calls and SMS conversations that share the same unified session.

        This shows the complete interaction history across voice and SMS channels.

        Args:
            conversation_id: The conversation ID.

        Returns:
            List of related conversation dictionaries.
        """
        response = self._http.get(f"/api/v1/sms-conversations/{conversation_id}/related")
        return response

    async def get_related_conversations_async(self, conversation_id: str) -> List[Dict[str, Any]]:
        """
        Async version of get_related_conversations().
        """
        response = await self._http.get_async(
            f"/api/v1/sms-conversations/{conversation_id}/related"
        )
        return response

    def delete_conversation(self, conversation_id: str) -> Dict[str, Any]:
        """
        Archive an SMS conversation and purge associated data.

        This archives the conversation (makes it invisible in UI) and:
        1. Purges all ChatMessage records
        2. Purges all SMSAuditLog records
        3. Purges all SMSMessageLog records
        4. Clears Redis session keys for fresh conversation start

        Args:
            conversation_id: The conversation ID to delete.

        Returns:
            Response confirming deletion.
        """
        response = self._http.delete(f"/api/v1/sms-conversations/{conversation_id}")
        return response

    async def delete_conversation_async(self, conversation_id: str) -> Dict[str, Any]:
        """
        Async version of delete_conversation().
        """
        response = await self._http.delete_async(f"/api/v1/sms-conversations/{conversation_id}")
        return response

    def export_conversation(
        self,
        conversation_id: str,
        format: str = "txt",
    ) -> bytes:
        """
        Export an SMS conversation in various formats.

        Args:
            conversation_id: The conversation ID.
            format: Export format (txt, csv, json).

        Returns:
            The exported data as bytes.
        """
        response = self._http.get(
            f"/api/v1/sms-conversations/{conversation_id}/export",
            params={"format": format}
        )
        return response

    async def export_conversation_async(
        self,
        conversation_id: str,
        format: str = "txt",
    ) -> bytes:
        """
        Async version of export_conversation().
        """
        response = await self._http.get_async(
            f"/api/v1/sms-conversations/{conversation_id}/export",
            params={"format": format}
        )
        return response
