"""
Campaigns resource for the Burki SDK.
"""

from typing import Any, Dict, List, Optional, Union

from burki.resources.base import BaseResource
from burki.models.campaign import (
    Campaign,
    CampaignCreate,
    CampaignContact,
    CampaignProgress,
    CampaignSchedule,
    CampaignSettings,
)


class CampaignsResource(BaseResource):
    """
    Resource for managing campaigns.

    Example:
        ```python
        # Create a campaign
        campaign = client.campaigns.create(
            name="Outreach Campaign",
            assistant_id=123,
            contacts=[
                {"phone_number": "+14155551234", "name": "John"},
                {"phone_number": "+14155555678", "name": "Jane"}
            ]
        )

        # Start the campaign
        client.campaigns.start(campaign_id=456)

        # Get progress
        progress = client.campaigns.get_progress(campaign_id=456)
        ```
    """

    def list(
        self,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Campaign]:
        """
        List campaigns.

        Args:
            status: Filter by status (draft, scheduled, running, paused, completed).
            skip: Number of items to skip.
            limit: Maximum number of items to return.

        Returns:
            List of Campaign objects.
        """
        params: Dict[str, Any] = {"skip": skip, "limit": limit}

        if status:
            params["status"] = status

        response = self._http.get("/api/v1/campaigns", params=params)

        if isinstance(response, list):
            return [Campaign.model_validate(item) for item in response]
        elif isinstance(response, dict) and "items" in response:
            return [Campaign.model_validate(item) for item in response["items"]]
        return []

    async def list_async(
        self,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Campaign]:
        """
        Async version of list().
        """
        params: Dict[str, Any] = {"skip": skip, "limit": limit}

        if status:
            params["status"] = status

        response = await self._http.get_async("/api/v1/campaigns", params=params)

        if isinstance(response, list):
            return [Campaign.model_validate(item) for item in response]
        elif isinstance(response, dict) and "items" in response:
            return [Campaign.model_validate(item) for item in response["items"]]
        return []

    def get(self, campaign_id: int) -> Campaign:
        """
        Get a specific campaign by ID.

        Args:
            campaign_id: The ID of the campaign.

        Returns:
            The Campaign object.
        """
        response = self._http.get(f"/api/v1/campaigns/{campaign_id}")
        return Campaign.model_validate(response)

    async def get_async(self, campaign_id: int) -> Campaign:
        """
        Async version of get().
        """
        response = await self._http.get_async(f"/api/v1/campaigns/{campaign_id}")
        return Campaign.model_validate(response)

    def create(
        self,
        name: str,
        assistant_id: int,
        contacts: List[Union[CampaignContact, Dict[str, Any]]],
        description: Optional[str] = None,
        campaign_type: str = "call",
        phone_number_id: Optional[int] = None,
        schedule: Optional[Union[CampaignSchedule, Dict[str, Any]]] = None,
        settings: Optional[Union[CampaignSettings, Dict[str, Any]]] = None,
    ) -> Campaign:
        """
        Create a new campaign.

        Args:
            name: Name of the campaign.
            assistant_id: The ID of the assistant to use.
            contacts: List of contacts to call.
            description: Optional description.
            campaign_type: Type of campaign (call or sms).
            phone_number_id: Optional phone number to call from.
            schedule: Schedule settings.
            settings: Execution settings.

        Returns:
            The created Campaign object.
        """
        data: Dict[str, Any] = {
            "name": name,
            "assistant_id": assistant_id,
            "campaign_type": campaign_type,
            "contacts": [
                c.model_dump() if isinstance(c, CampaignContact) else c
                for c in contacts
            ],
        }

        if description:
            data["description"] = description
        if phone_number_id:
            data["phone_number_id"] = phone_number_id
        if schedule:
            data["schedule"] = (
                schedule.model_dump()
                if isinstance(schedule, CampaignSchedule)
                else schedule
            )
        if settings:
            data["settings"] = (
                settings.model_dump()
                if isinstance(settings, CampaignSettings)
                else settings
            )

        response = self._http.post("/api/v1/campaigns", json=data)
        return Campaign.model_validate(response)

    async def create_async(
        self,
        name: str,
        assistant_id: int,
        contacts: List[Union[CampaignContact, Dict[str, Any]]],
        description: Optional[str] = None,
        campaign_type: str = "call",
        phone_number_id: Optional[int] = None,
        schedule: Optional[Union[CampaignSchedule, Dict[str, Any]]] = None,
        settings: Optional[Union[CampaignSettings, Dict[str, Any]]] = None,
    ) -> Campaign:
        """
        Async version of create().
        """
        data: Dict[str, Any] = {
            "name": name,
            "assistant_id": assistant_id,
            "campaign_type": campaign_type,
            "contacts": [
                c.model_dump() if isinstance(c, CampaignContact) else c
                for c in contacts
            ],
        }

        if description:
            data["description"] = description
        if phone_number_id:
            data["phone_number_id"] = phone_number_id
        if schedule:
            data["schedule"] = (
                schedule.model_dump()
                if isinstance(schedule, CampaignSchedule)
                else schedule
            )
        if settings:
            data["settings"] = (
                settings.model_dump()
                if isinstance(settings, CampaignSettings)
                else settings
            )

        response = await self._http.post_async("/api/v1/campaigns", json=data)
        return Campaign.model_validate(response)

    def update(
        self,
        campaign_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        schedule: Optional[Union[CampaignSchedule, Dict[str, Any]]] = None,
        settings: Optional[Union[CampaignSettings, Dict[str, Any]]] = None,
    ) -> Campaign:
        """
        Update a campaign.

        Args:
            campaign_id: The ID of the campaign.
            name: New name for the campaign.
            description: New description.
            schedule: Updated schedule settings.
            settings: Updated execution settings.

        Returns:
            The updated Campaign object.
        """
        data: Dict[str, Any] = {}

        if name is not None:
            data["name"] = name
        if description is not None:
            data["description"] = description
        if schedule is not None:
            data["schedule"] = (
                schedule.model_dump()
                if isinstance(schedule, CampaignSchedule)
                else schedule
            )
        if settings is not None:
            data["settings"] = (
                settings.model_dump()
                if isinstance(settings, CampaignSettings)
                else settings
            )

        response = self._http.patch(f"/api/v1/campaigns/{campaign_id}", json=data)
        return Campaign.model_validate(response)

    async def update_async(
        self,
        campaign_id: int,
        **kwargs: Any,
    ) -> Campaign:
        """
        Async version of update().
        """
        response = await self._http.patch_async(
            f"/api/v1/campaigns/{campaign_id}", json=kwargs
        )
        return Campaign.model_validate(response)

    def delete(self, campaign_id: int) -> bool:
        """
        Delete a campaign.

        Args:
            campaign_id: The ID of the campaign.

        Returns:
            True if deleted successfully.
        """
        self._http.delete(f"/api/v1/campaigns/{campaign_id}")
        return True

    async def delete_async(self, campaign_id: int) -> bool:
        """
        Async version of delete().
        """
        await self._http.delete_async(f"/api/v1/campaigns/{campaign_id}")
        return True

    def start(self, campaign_id: int) -> Campaign:
        """
        Start a campaign.

        Args:
            campaign_id: The ID of the campaign.

        Returns:
            The updated Campaign object.
        """
        response = self._http.post(f"/api/v1/campaigns/{campaign_id}/start")
        return Campaign.model_validate(response)

    async def start_async(self, campaign_id: int) -> Campaign:
        """
        Async version of start().
        """
        response = await self._http.post_async(f"/api/v1/campaigns/{campaign_id}/start")
        return Campaign.model_validate(response)

    def pause(self, campaign_id: int) -> Campaign:
        """
        Pause a running campaign.

        Args:
            campaign_id: The ID of the campaign.

        Returns:
            The updated Campaign object.
        """
        response = self._http.post(f"/api/v1/campaigns/{campaign_id}/pause")
        return Campaign.model_validate(response)

    async def pause_async(self, campaign_id: int) -> Campaign:
        """
        Async version of pause().
        """
        response = await self._http.post_async(f"/api/v1/campaigns/{campaign_id}/pause")
        return Campaign.model_validate(response)

    def resume(self, campaign_id: int) -> Campaign:
        """
        Resume a paused campaign.

        Args:
            campaign_id: The ID of the campaign.

        Returns:
            The updated Campaign object.
        """
        response = self._http.post(f"/api/v1/campaigns/{campaign_id}/resume")
        return Campaign.model_validate(response)

    async def resume_async(self, campaign_id: int) -> Campaign:
        """
        Async version of resume().
        """
        response = await self._http.post_async(
            f"/api/v1/campaigns/{campaign_id}/resume"
        )
        return Campaign.model_validate(response)

    def cancel(self, campaign_id: int) -> Campaign:
        """
        Cancel a campaign.

        Args:
            campaign_id: The ID of the campaign.

        Returns:
            The updated Campaign object.
        """
        response = self._http.post(f"/api/v1/campaigns/{campaign_id}/cancel")
        return Campaign.model_validate(response)

    async def cancel_async(self, campaign_id: int) -> Campaign:
        """
        Async version of cancel().
        """
        response = await self._http.post_async(
            f"/api/v1/campaigns/{campaign_id}/cancel"
        )
        return Campaign.model_validate(response)

    def get_progress(self, campaign_id: int) -> CampaignProgress:
        """
        Get the progress of a campaign.

        Args:
            campaign_id: The ID of the campaign.

        Returns:
            The CampaignProgress object.
        """
        response = self._http.get(f"/api/v1/campaigns/{campaign_id}/progress")
        return CampaignProgress.model_validate(response)

    async def get_progress_async(self, campaign_id: int) -> CampaignProgress:
        """
        Async version of get_progress().
        """
        response = await self._http.get_async(
            f"/api/v1/campaigns/{campaign_id}/progress"
        )
        return CampaignProgress.model_validate(response)

    def get_contacts(
        self,
        campaign_id: int,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[CampaignContact]:
        """
        Get contacts in a campaign.

        Args:
            campaign_id: The ID of the campaign.
            status: Filter by contact status.
            skip: Number of items to skip.
            limit: Maximum number of items to return.

        Returns:
            List of CampaignContact objects.
        """
        params: Dict[str, Any] = {"skip": skip, "limit": limit}

        if status:
            params["status"] = status

        response = self._http.get(
            f"/api/v1/campaigns/{campaign_id}/contacts", params=params
        )

        if isinstance(response, list):
            return [CampaignContact.model_validate(item) for item in response]
        elif isinstance(response, dict) and "items" in response:
            return [CampaignContact.model_validate(item) for item in response["items"]]
        return []

    async def get_contacts_async(
        self,
        campaign_id: int,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[CampaignContact]:
        """
        Async version of get_contacts().
        """
        params: Dict[str, Any] = {"skip": skip, "limit": limit}

        if status:
            params["status"] = status

        response = await self._http.get_async(
            f"/api/v1/campaigns/{campaign_id}/contacts", params=params
        )

        if isinstance(response, list):
            return [CampaignContact.model_validate(item) for item in response]
        elif isinstance(response, dict) and "items" in response:
            return [CampaignContact.model_validate(item) for item in response["items"]]
        return []

    def add_contacts(
        self,
        campaign_id: int,
        contacts: List[Union[CampaignContact, Dict[str, Any]]],
    ) -> Dict[str, Any]:
        """
        Add contacts to a campaign.

        Args:
            campaign_id: The ID of the campaign.
            contacts: List of contacts to add.

        Returns:
            Response indicating success.
        """
        data = {
            "contacts": [
                c.model_dump() if isinstance(c, CampaignContact) else c
                for c in contacts
            ]
        }

        response = self._http.post(
            f"/api/v1/campaigns/{campaign_id}/contacts", json=data
        )
        return response

    async def add_contacts_async(
        self,
        campaign_id: int,
        contacts: List[Union[CampaignContact, Dict[str, Any]]],
    ) -> Dict[str, Any]:
        """
        Async version of add_contacts().
        """
        data = {
            "contacts": [
                c.model_dump() if isinstance(c, CampaignContact) else c
                for c in contacts
            ]
        }

        response = await self._http.post_async(
            f"/api/v1/campaigns/{campaign_id}/contacts", json=data
        )
        return response
