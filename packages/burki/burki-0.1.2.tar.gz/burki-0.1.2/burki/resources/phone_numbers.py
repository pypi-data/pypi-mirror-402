"""
Phone Numbers resource for the Burki SDK.
"""

from typing import Any, Dict, List, Optional

from burki.resources.base import BaseResource
from burki.models.phone_number import (
    PhoneNumber,
    AvailablePhoneNumber,
    SearchPhoneNumbersResponse,
    PurchasePhoneNumberResponse,
    ReleasePhoneNumberResponse,
    CountryCodesResponse,
    WebhookConfig,
)


class PhoneNumbersResource(BaseResource):
    """
    Resource for managing phone numbers.

    Example:
        ```python
        # Search for available phone numbers
        results = client.phone_numbers.search(
            country_code="US",
            area_code="415",
            provider="twilio"
        )

        # Purchase a phone number
        response = client.phone_numbers.purchase(
            phone_number="+14155551234",
            provider="twilio",
            friendly_name="Main Support Line"
        )

        # Release a phone number
        client.phone_numbers.release(phone_number="+14155551234")

        # Update webhooks
        client.phone_numbers.update_webhooks(
            phone_number="+14155551234",
            voice_webhook_url="https://example.com/voice"
        )
        ```
    """

    def search(
        self,
        provider: str,
        country_code: str = "US",
        area_code: Optional[str] = None,
        contains: Optional[str] = None,
        locality: Optional[str] = None,
        region: Optional[str] = None,
        limit: int = 20,
    ) -> SearchPhoneNumbersResponse:
        """
        Search for available phone numbers to purchase.

        Args:
            provider: Provider to search (twilio, telnyx, vonage, byo-sip-trunk).
            country_code: Country code (e.g., "US", "GB", "CA").
            area_code: Filter by area code (e.g., "415").
            contains: Filter for numbers containing a specific pattern.
            locality: Filter by city/locality.
            region: Filter by region/state.
            limit: Maximum number of results.

        Returns:
            SearchPhoneNumbersResponse with available numbers.
        """
        data: Dict[str, Any] = {
            "provider": provider,
            "country_code": country_code,
            "limit": limit,
        }

        if area_code:
            data["area_code"] = area_code
        if contains:
            data["contains"] = contains
        if locality:
            data["locality"] = locality
        if region:
            data["region"] = region

        response = self._http.post("/api/v1/phone-numbers/search", json=data)
        return SearchPhoneNumbersResponse.model_validate(response)

    async def search_async(
        self,
        provider: str,
        country_code: str = "US",
        area_code: Optional[str] = None,
        contains: Optional[str] = None,
        locality: Optional[str] = None,
        region: Optional[str] = None,
        limit: int = 20,
    ) -> SearchPhoneNumbersResponse:
        """
        Async version of search().
        """
        data: Dict[str, Any] = {
            "provider": provider,
            "country_code": country_code,
            "limit": limit,
        }

        if area_code:
            data["area_code"] = area_code
        if contains:
            data["contains"] = contains
        if locality:
            data["locality"] = locality
        if region:
            data["region"] = region

        response = await self._http.post_async("/api/v1/phone-numbers/search", json=data)
        return SearchPhoneNumbersResponse.model_validate(response)

    def purchase(
        self,
        phone_number: str,
        provider: str,
        friendly_name: Optional[str] = None,
        assistant_id: Optional[int] = None,
        country_code: Optional[str] = None,
    ) -> PurchasePhoneNumberResponse:
        """
        Purchase a phone number.

        Args:
            phone_number: The phone number to purchase (E.164 format).
            provider: Provider to purchase from (twilio, telnyx, vonage, byo-sip-trunk).
            friendly_name: Optional friendly name for the number.
            assistant_id: Optional assistant to assign the number to.
            country_code: Country code (required for some providers).

        Returns:
            PurchasePhoneNumberResponse with purchase details.
        """
        data: Dict[str, Any] = {
            "phone_number": phone_number,
            "provider": provider,
        }

        if friendly_name:
            data["friendly_name"] = friendly_name
        if assistant_id:
            data["assistant_id"] = assistant_id
        if country_code:
            data["country_code"] = country_code

        response = self._http.post("/api/v1/phone-numbers/purchase", json=data)
        return PurchasePhoneNumberResponse.model_validate(response)

    async def purchase_async(
        self,
        phone_number: str,
        provider: str,
        friendly_name: Optional[str] = None,
        assistant_id: Optional[int] = None,
        country_code: Optional[str] = None,
    ) -> PurchasePhoneNumberResponse:
        """
        Async version of purchase().
        """
        data: Dict[str, Any] = {
            "phone_number": phone_number,
            "provider": provider,
        }

        if friendly_name:
            data["friendly_name"] = friendly_name
        if assistant_id:
            data["assistant_id"] = assistant_id
        if country_code:
            data["country_code"] = country_code

        response = await self._http.post_async("/api/v1/phone-numbers/purchase", json=data)
        return PurchasePhoneNumberResponse.model_validate(response)

    def release(
        self,
        phone_number: str,
        provider: Optional[str] = None,
    ) -> ReleasePhoneNumberResponse:
        """
        Release a phone number.

        Args:
            phone_number: The phone number to release (E.164 format).
            provider: Provider (auto-detected if not specified).

        Returns:
            ReleasePhoneNumberResponse confirming release.
        """
        data: Dict[str, Any] = {
            "phone_number": phone_number,
        }

        if provider:
            data["provider"] = provider

        response = self._http.post("/api/v1/phone-numbers/release", json=data)
        return ReleasePhoneNumberResponse.model_validate(response)

    async def release_async(
        self,
        phone_number: str,
        provider: Optional[str] = None,
    ) -> ReleasePhoneNumberResponse:
        """
        Async version of release().
        """
        data: Dict[str, Any] = {
            "phone_number": phone_number,
        }

        if provider:
            data["provider"] = provider

        response = await self._http.post_async("/api/v1/phone-numbers/release", json=data)
        return ReleasePhoneNumberResponse.model_validate(response)

    def get_countries(self, provider: str = "telnyx") -> CountryCodesResponse:
        """
        Get available country codes for phone number search.

        Args:
            provider: Provider to get country codes from (twilio or telnyx).

        Returns:
            CountryCodesResponse with available country codes.
        """
        response = self._http.get(
            "/api/v1/phone-numbers/countries",
            params={"provider": provider}
        )
        return CountryCodesResponse.model_validate(response)

    async def get_countries_async(self, provider: str = "telnyx") -> CountryCodesResponse:
        """
        Async version of get_countries().
        """
        response = await self._http.get_async(
            "/api/v1/phone-numbers/countries",
            params={"provider": provider}
        )
        return CountryCodesResponse.model_validate(response)

    def diagnose(self, phone_number: str) -> Dict[str, Any]:
        """
        Diagnose the connection status of a phone number (Telnyx).

        Args:
            phone_number: The phone number to diagnose (E.164 format).

        Returns:
            Diagnostic information about the phone number.
        """
        response = self._http.get(f"/api/v1/phone-numbers/{phone_number}/diagnose")
        return response

    async def diagnose_async(self, phone_number: str) -> Dict[str, Any]:
        """
        Async version of diagnose().
        """
        response = await self._http.get_async(f"/api/v1/phone-numbers/{phone_number}/diagnose")
        return response

    def get_webhooks(
        self,
        phone_number: str,
        provider: Optional[str] = None,
    ) -> WebhookConfig:
        """
        Get current webhook configuration for a phone number.

        Args:
            phone_number: The phone number (E.164 format).
            provider: Provider (auto-detected if not specified).

        Returns:
            WebhookConfig with current webhook URLs.
        """
        params: Dict[str, Any] = {}
        if provider:
            params["provider"] = provider

        response = self._http.get(
            f"/api/v1/phone-numbers/{phone_number}/webhooks",
            params=params
        )
        return WebhookConfig.model_validate(response)

    async def get_webhooks_async(
        self,
        phone_number: str,
        provider: Optional[str] = None,
    ) -> WebhookConfig:
        """
        Async version of get_webhooks().
        """
        params: Dict[str, Any] = {}
        if provider:
            params["provider"] = provider

        response = await self._http.get_async(
            f"/api/v1/phone-numbers/{phone_number}/webhooks",
            params=params
        )
        return WebhookConfig.model_validate(response)

    def update_webhooks(
        self,
        phone_number: str,
        voice_webhook_url: Optional[str] = None,
        disable_sms: bool = False,
        enable_sms: bool = False,
        provider: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update voice webhook URL and/or SMS settings for a phone number.

        Args:
            phone_number: The phone number (E.164 format).
            voice_webhook_url: New voice webhook URL.
            disable_sms: Set to True to disable SMS webhooks.
            enable_sms: Set to True to enable SMS webhooks.
            provider: Provider (auto-detected if not specified).

        Returns:
            Response confirming the update.
        """
        data: Dict[str, Any] = {
            "phone_number": phone_number,
        }

        if voice_webhook_url:
            data["voice_webhook_url"] = voice_webhook_url
        if disable_sms:
            data["disable_sms"] = disable_sms
        if enable_sms:
            data["enable_sms"] = enable_sms
        if provider:
            data["provider"] = provider

        response = self._http.put("/api/v1/phone-numbers/webhooks", json=data)
        return response

    async def update_webhooks_async(
        self,
        phone_number: str,
        voice_webhook_url: Optional[str] = None,
        disable_sms: bool = False,
        enable_sms: bool = False,
        provider: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Async version of update_webhooks().
        """
        data: Dict[str, Any] = {
            "phone_number": phone_number,
        }

        if voice_webhook_url:
            data["voice_webhook_url"] = voice_webhook_url
        if disable_sms:
            data["disable_sms"] = disable_sms
        if enable_sms:
            data["enable_sms"] = enable_sms
        if provider:
            data["provider"] = provider

        response = await self._http.put_async("/api/v1/phone-numbers/webhooks", json=data)
        return response

    def sync_verified_caller_ids(self) -> Dict[str, Any]:
        """
        Sync verified caller IDs from Twilio for your organization.

        Returns:
            Response with sync results.
        """
        response = self._http.post("/api/v1/phone-numbers/organization/sync-verified-caller-ids")
        return response

    async def sync_verified_caller_ids_async(self) -> Dict[str, Any]:
        """
        Async version of sync_verified_caller_ids().
        """
        response = await self._http.post_async(
            "/api/v1/phone-numbers/organization/sync-verified-caller-ids"
        )
        return response

    def add_verified_caller_id(
        self,
        phone_number: str,
        friendly_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Add a new verified caller ID (for outbound calls with unowned numbers).

        Args:
            phone_number: The phone number to verify (E.164 format).
            friendly_name: Optional friendly name for the caller ID.

        Returns:
            Response with verification details.
        """
        # This endpoint uses form data
        data = {"phone_number": phone_number}
        if friendly_name:
            data["friendly_name"] = friendly_name

        response = self._http.post(
            "/api/v1/phone-numbers/organization/add-verified-caller-id",
            data=data  # Form data, not JSON
        )
        return response

    async def add_verified_caller_id_async(
        self,
        phone_number: str,
        friendly_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Async version of add_verified_caller_id().
        """
        data = {"phone_number": phone_number}
        if friendly_name:
            data["friendly_name"] = friendly_name

        response = await self._http.post_async(
            "/api/v1/phone-numbers/organization/add-verified-caller-id",
            data=data
        )
        return response
