"""
Assistants resource for the Burki SDK.
"""

from typing import Any, Dict, List, Optional, Union

from burki.resources.base import BaseResource
from burki.models.assistant import (
    Assistant,
    AssistantCreate,
    AssistantUpdate,
    AssistantList,
    LLMSettings,
    TTSSettings,
    STTSettings,
    RAGSettings,
)


class AssistantsResource(BaseResource):
    """
    Resource for managing assistants.

    Example:
        ```python
        # List all assistants
        assistants = client.assistants.list()

        # Create an assistant
        assistant = client.assistants.create(
            name="Support Bot",
            llm_settings={"model": "gpt-4o-mini"}
        )

        # Update an assistant
        assistant = client.assistants.update(
            assistant_id=123,
            name="Updated Bot"
        )

        # Delete an assistant
        client.assistants.delete(assistant_id=123)
        ```
    """

    def list(
        self,
        skip: int = 0,
        limit: int = 100,
        active_only: Optional[bool] = None,
        my_assistants_only: bool = False,
        include_stats: bool = False,
    ) -> List[Assistant]:
        """
        List all assistants in your organization.

        Args:
            skip: Number of items to skip.
            limit: Maximum number of items to return.
            active_only: Filter by active status.
            my_assistants_only: Only return assistants created by you.
            include_stats: Include call statistics for each assistant.

        Returns:
            List of Assistant objects.
        """
        params: Dict[str, Any] = {"skip": skip, "limit": limit}
        if active_only is not None:
            params["active_only"] = active_only
        if my_assistants_only:
            params["my_assistants_only"] = my_assistants_only
        if include_stats:
            params["include_stats"] = include_stats

        response = self._http.get("/api/v1/assistants", params=params)
        
        # Handle both list and paginated responses
        if isinstance(response, list):
            return [Assistant.model_validate(item) for item in response]
        elif isinstance(response, dict) and "items" in response:
            return [Assistant.model_validate(item) for item in response["items"]]
        return []

    async def list_async(
        self,
        skip: int = 0,
        limit: int = 100,
        active_only: Optional[bool] = None,
        my_assistants_only: bool = False,
        include_stats: bool = False,
    ) -> List[Assistant]:
        """
        Async version of list().
        """
        params: Dict[str, Any] = {"skip": skip, "limit": limit}
        if active_only is not None:
            params["active_only"] = active_only
        if my_assistants_only:
            params["my_assistants_only"] = my_assistants_only
        if include_stats:
            params["include_stats"] = include_stats

        response = await self._http.get_async("/api/v1/assistants", params=params)
        
        if isinstance(response, list):
            return [Assistant.model_validate(item) for item in response]
        elif isinstance(response, dict) and "items" in response:
            return [Assistant.model_validate(item) for item in response["items"]]
        return []

    def get(self, assistant_id: int) -> Assistant:
        """
        Get a specific assistant by ID.

        Args:
            assistant_id: The ID of the assistant.

        Returns:
            The Assistant object.
        """
        response = self._http.get(f"/api/v1/assistants/{assistant_id}")
        return Assistant.model_validate(response)

    async def get_async(self, assistant_id: int) -> Assistant:
        """
        Async version of get().
        """
        response = await self._http.get_async(f"/api/v1/assistants/{assistant_id}")
        return Assistant.model_validate(response)

    def get_by_phone(self, phone_number: str) -> Assistant:
        """
        Get an assistant by its assigned phone number.

        Args:
            phone_number: The phone number (E.164 format).

        Returns:
            The Assistant object.
        """
        response = self._http.get(f"/api/v1/assistants/by-phone/{phone_number}")
        return Assistant.model_validate(response)

    async def get_by_phone_async(self, phone_number: str) -> Assistant:
        """
        Async version of get_by_phone().
        """
        response = await self._http.get_async(f"/api/v1/assistants/by-phone/{phone_number}")
        return Assistant.model_validate(response)

    def create(
        self,
        name: str,
        description: Optional[str] = None,
        llm_provider: str = "openai",
        llm_settings: Optional[Union[LLMSettings, Dict[str, Any]]] = None,
        tts_settings: Optional[Union[TTSSettings, Dict[str, Any]]] = None,
        stt_settings: Optional[Union[STTSettings, Dict[str, Any]]] = None,
        rag_settings: Optional[Union[RAGSettings, Dict[str, Any]]] = None,
        webhook_url: Optional[str] = None,
        webhook_headers: Optional[Dict[str, str]] = None,
        sms_webhook_url: Optional[str] = None,
        messaging_service_sid: Optional[str] = None,
        **kwargs: Any,
    ) -> Assistant:
        """
        Create a new assistant.

        Args:
            name: Name of the assistant.
            description: Optional description.
            llm_provider: LLM provider (openai, anthropic, etc.).
            llm_settings: LLM configuration settings.
            tts_settings: Text-to-speech settings.
            stt_settings: Speech-to-text settings.
            rag_settings: RAG (knowledge base) settings.
            webhook_url: Webhook URL for call events.
            webhook_headers: Custom headers for webhooks.
            sms_webhook_url: Webhook URL for SMS events.
            messaging_service_sid: Twilio Messaging Service SID.
            **kwargs: Additional settings.

        Returns:
            The created Assistant object.
        """
        data: Dict[str, Any] = {
            "name": name,
            "llm_provider": llm_provider,
        }

        if description:
            data["description"] = description
        if llm_settings:
            data["llm_settings"] = (
                llm_settings.model_dump() if hasattr(llm_settings, 'model_dump') else llm_settings
            )
        if tts_settings:
            data["tts_settings"] = (
                tts_settings.model_dump() if hasattr(tts_settings, 'model_dump') else tts_settings
            )
        if stt_settings:
            data["stt_settings"] = (
                stt_settings.model_dump() if hasattr(stt_settings, 'model_dump') else stt_settings
            )
        if rag_settings:
            data["rag_settings"] = (
                rag_settings.model_dump() if hasattr(rag_settings, 'model_dump') else rag_settings
            )
        if webhook_url:
            data["webhook_url"] = webhook_url
        if webhook_headers:
            data["webhook_headers"] = webhook_headers
        if sms_webhook_url:
            data["sms_webhook_url"] = sms_webhook_url
        if messaging_service_sid:
            data["messaging_service_sid"] = messaging_service_sid

        # Add any additional kwargs
        data.update(kwargs)

        response = self._http.post("/api/v1/assistants", json=data)
        return Assistant.model_validate(response)

    async def create_async(
        self,
        name: str,
        description: Optional[str] = None,
        llm_provider: str = "openai",
        llm_settings: Optional[Union[LLMSettings, Dict[str, Any]]] = None,
        tts_settings: Optional[Union[TTSSettings, Dict[str, Any]]] = None,
        stt_settings: Optional[Union[STTSettings, Dict[str, Any]]] = None,
        rag_settings: Optional[Union[RAGSettings, Dict[str, Any]]] = None,
        webhook_url: Optional[str] = None,
        webhook_headers: Optional[Dict[str, str]] = None,
        sms_webhook_url: Optional[str] = None,
        messaging_service_sid: Optional[str] = None,
        **kwargs: Any,
    ) -> Assistant:
        """
        Async version of create().
        """
        data: Dict[str, Any] = {
            "name": name,
            "llm_provider": llm_provider,
        }

        if description:
            data["description"] = description
        if llm_settings:
            data["llm_settings"] = (
                llm_settings.model_dump() if hasattr(llm_settings, 'model_dump') else llm_settings
            )
        if tts_settings:
            data["tts_settings"] = (
                tts_settings.model_dump() if hasattr(tts_settings, 'model_dump') else tts_settings
            )
        if stt_settings:
            data["stt_settings"] = (
                stt_settings.model_dump() if hasattr(stt_settings, 'model_dump') else stt_settings
            )
        if rag_settings:
            data["rag_settings"] = (
                rag_settings.model_dump() if hasattr(rag_settings, 'model_dump') else rag_settings
            )
        if webhook_url:
            data["webhook_url"] = webhook_url
        if webhook_headers:
            data["webhook_headers"] = webhook_headers
        if sms_webhook_url:
            data["sms_webhook_url"] = sms_webhook_url
        if messaging_service_sid:
            data["messaging_service_sid"] = messaging_service_sid

        data.update(kwargs)

        response = await self._http.post_async("/api/v1/assistants", json=data)
        return Assistant.model_validate(response)

    def update(
        self,
        assistant_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        is_active: Optional[bool] = None,
        llm_settings: Optional[Union[LLMSettings, Dict[str, Any]]] = None,
        tts_settings: Optional[Union[TTSSettings, Dict[str, Any]]] = None,
        stt_settings: Optional[Union[STTSettings, Dict[str, Any]]] = None,
        rag_settings: Optional[Union[RAGSettings, Dict[str, Any]]] = None,
        webhook_url: Optional[str] = None,
        webhook_headers: Optional[Dict[str, str]] = None,
        sms_webhook_url: Optional[str] = None,
        messaging_service_sid: Optional[str] = None,
        **kwargs: Any,
    ) -> Assistant:
        """
        Update an existing assistant (PATCH - partial update with merge).

        Args:
            assistant_id: The ID of the assistant to update.
            name: New name for the assistant.
            description: New description.
            is_active: Whether the assistant is active.
            llm_settings: Updated LLM settings (merged with existing).
            tts_settings: Updated TTS settings (merged with existing).
            stt_settings: Updated STT settings (merged with existing).
            rag_settings: Updated RAG settings (merged with existing).
            webhook_url: Updated webhook URL.
            webhook_headers: Updated webhook headers.
            sms_webhook_url: Updated SMS webhook URL.
            messaging_service_sid: Updated Twilio Messaging Service SID.
            **kwargs: Additional settings.

        Returns:
            The updated Assistant object.
        """
        data: Dict[str, Any] = {}

        if name is not None:
            data["name"] = name
        if description is not None:
            data["description"] = description
        if is_active is not None:
            data["is_active"] = is_active
        if llm_settings is not None:
            data["llm_settings"] = (
                llm_settings.model_dump() if hasattr(llm_settings, 'model_dump') else llm_settings
            )
        if tts_settings is not None:
            data["tts_settings"] = (
                tts_settings.model_dump() if hasattr(tts_settings, 'model_dump') else tts_settings
            )
        if stt_settings is not None:
            data["stt_settings"] = (
                stt_settings.model_dump() if hasattr(stt_settings, 'model_dump') else stt_settings
            )
        if rag_settings is not None:
            data["rag_settings"] = (
                rag_settings.model_dump() if hasattr(rag_settings, 'model_dump') else rag_settings
            )
        if webhook_url is not None:
            data["webhook_url"] = webhook_url
        if webhook_headers is not None:
            data["webhook_headers"] = webhook_headers
        if sms_webhook_url is not None:
            data["sms_webhook_url"] = sms_webhook_url
        if messaging_service_sid is not None:
            data["messaging_service_sid"] = messaging_service_sid

        data.update(kwargs)

        response = self._http.patch(f"/api/v1/assistants/{assistant_id}", json=data)
        return Assistant.model_validate(response)

    async def update_async(
        self,
        assistant_id: int,
        **kwargs: Any,
    ) -> Assistant:
        """
        Async version of update().
        """
        response = await self._http.patch_async(
            f"/api/v1/assistants/{assistant_id}", json=kwargs
        )
        return Assistant.model_validate(response)

    def update_status(self, assistant_id: int, is_active: bool) -> Assistant:
        """
        Quick method to update just the active status of an assistant.

        Args:
            assistant_id: The ID of the assistant.
            is_active: Whether the assistant should be active.

        Returns:
            The updated Assistant object.
        """
        response = self._http.patch(
            f"/api/v1/assistants/{assistant_id}/status",
            params={"is_active": is_active}
        )
        return Assistant.model_validate(response)

    async def update_status_async(self, assistant_id: int, is_active: bool) -> Assistant:
        """
        Async version of update_status().
        """
        response = await self._http.patch_async(
            f"/api/v1/assistants/{assistant_id}/status",
            params={"is_active": is_active}
        )
        return Assistant.model_validate(response)

    def delete(self, assistant_id: int) -> bool:
        """
        Delete an assistant.

        Args:
            assistant_id: The ID of the assistant to delete.

        Returns:
            True if deleted successfully.
        """
        self._http.delete(f"/api/v1/assistants/{assistant_id}")
        return True

    async def delete_async(self, assistant_id: int) -> bool:
        """
        Async version of delete().
        """
        await self._http.delete_async(f"/api/v1/assistants/{assistant_id}")
        return True

    def get_count(self, active_only: bool = False) -> int:
        """
        Get the total count of assistants.

        Args:
            active_only: Only count active assistants.

        Returns:
            The total number of assistants.
        """
        params = {"active_only": active_only} if active_only else {}
        response = self._http.get("/api/v1/assistants/count", params=params)
        return response.get("count", 0) if isinstance(response, dict) else 0

    async def get_count_async(self, active_only: bool = False) -> int:
        """
        Async version of get_count().
        """
        params = {"active_only": active_only} if active_only else {}
        response = await self._http.get_async("/api/v1/assistants/count", params=params)
        return response.get("count", 0) if isinstance(response, dict) else 0

    def export(
        self,
        format: str = "csv",
        assistant_ids: Optional[List[int]] = None,
        search: Optional[str] = None,
        status: Optional[str] = None,
    ) -> bytes:
        """
        Export assistants data in CSV or JSON format.

        Args:
            format: Export format (csv or json).
            assistant_ids: Specific assistant IDs to export (selection mode).
            search: Search filter for assistants (fallback mode).
            status: Status filter (active, inactive, or all).

        Returns:
            The exported data as bytes.
        """
        params: Dict[str, Any] = {"format": format}
        if assistant_ids:
            params["assistant_ids"] = ",".join(str(id) for id in assistant_ids)
        if search:
            params["search"] = search
        if status:
            params["status"] = status

        response = self._http.get("/api/v1/assistants/export", params=params)
        return response

    async def export_async(
        self,
        format: str = "csv",
        assistant_ids: Optional[List[int]] = None,
        search: Optional[str] = None,
        status: Optional[str] = None,
    ) -> bytes:
        """
        Async version of export().
        """
        params: Dict[str, Any] = {"format": format}
        if assistant_ids:
            params["assistant_ids"] = ",".join(str(id) for id in assistant_ids)
        if search:
            params["search"] = search
        if status:
            params["status"] = status

        response = await self._http.get_async("/api/v1/assistants/export", params=params)
        return response

    def get_cloned_voices(
        self,
        status: Optional[str] = None,
        provider: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        List cloned voices for your organization.

        Args:
            status: Filter by voice status.
            provider: Filter by provider (elevenlabs, resemble).

        Returns:
            List of cloned voice dictionaries.
        """
        params: Dict[str, Any] = {}
        if status:
            params["status"] = status
        if provider:
            params["provider"] = provider

        response = self._http.get("/api/v1/assistants/cloned-voices", params=params)
        
        if isinstance(response, dict) and "cloned_voices" in response:
            return response["cloned_voices"]
        return []

    async def get_cloned_voices_async(
        self,
        status: Optional[str] = None,
        provider: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Async version of get_cloned_voices().
        """
        params: Dict[str, Any] = {}
        if status:
            params["status"] = status
        if provider:
            params["provider"] = provider

        response = await self._http.get_async("/api/v1/assistants/cloned-voices", params=params)
        
        if isinstance(response, dict) and "cloned_voices" in response:
            return response["cloned_voices"]
        return []

    def get_providers(self) -> Dict[str, Any]:
        """
        Get list of supported LLM providers.

        Returns:
            Dictionary of available providers and their configurations.
        """
        response = self._http.get("/api/v1/assistants/providers")
        return response.get("providers", {}) if isinstance(response, dict) else {}

    async def get_providers_async(self) -> Dict[str, Any]:
        """
        Async version of get_providers().
        """
        response = await self._http.get_async("/api/v1/assistants/providers")
        return response.get("providers", {}) if isinstance(response, dict) else {}

    def get_organization_info(self) -> Dict[str, Any]:
        """
        Get information about your organization.

        Returns:
            Dictionary with organization details.
        """
        response = self._http.get("/api/v1/assistants/me/organization")
        return response if isinstance(response, dict) else {}

    async def get_organization_info_async(self) -> Dict[str, Any]:
        """
        Async version of get_organization_info().
        """
        response = await self._http.get_async("/api/v1/assistants/me/organization")
        return response if isinstance(response, dict) else {}
