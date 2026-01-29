"""
Phone number models for the Burki SDK.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class PhoneNumber(BaseModel):
    """Represents a phone number in the Burki system."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: Optional[int] = None
    assistant_id: Optional[int] = None
    phone_number: str
    friendly_name: Optional[str] = None
    provider: str = "twilio"  # twilio, telnyx, vonage, byo-sip-trunk
    provider_phone_id: Optional[str] = None
    capabilities: Optional[Dict[str, bool]] = None
    phone_metadata: Optional[Dict[str, Any]] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Joined fields
    assistant_name: Optional[str] = None


class AvailablePhoneNumber(BaseModel):
    """Represents an available phone number for purchase."""

    model_config = ConfigDict(from_attributes=True)

    phone_number: str
    friendly_name: Optional[str] = None
    region: Optional[str] = None
    locality: Optional[str] = None
    iso_country: Optional[str] = None
    capabilities: Optional[Dict[str, bool]] = None
    monthly_cost: Optional[float] = None
    setup_cost: Optional[float] = None
    provider: Optional[str] = None


class SearchPhoneNumbersResponse(BaseModel):
    """Response from searching for available phone numbers."""

    model_config = ConfigDict(from_attributes=True)

    success: bool
    numbers: List[AvailablePhoneNumber] = Field(default_factory=list)
    total_found: int = 0
    provider: str


class PurchasePhoneNumberResponse(BaseModel):
    """Response from purchasing a phone number."""

    model_config = ConfigDict(from_attributes=True)

    success: bool
    phone_number: str
    provider: str
    purchase_details: Optional[Dict[str, Any]] = None
    message: str


class ReleasePhoneNumberResponse(BaseModel):
    """Response from releasing a phone number."""

    model_config = ConfigDict(from_attributes=True)

    success: bool
    phone_number: str
    provider: str
    message: str


class CountryCode(BaseModel):
    """Represents a country code."""

    code: str
    name: str
    phone_code: Optional[str] = None


class CountryCodesResponse(BaseModel):
    """Response from listing available country codes."""

    model_config = ConfigDict(from_attributes=True)

    success: bool
    country_codes: List[Dict[str, Any]] = Field(default_factory=list)
    provider: str


class WebhookConfig(BaseModel):
    """Webhook configuration for a phone number."""

    model_config = ConfigDict(from_attributes=True)

    success: bool
    phone_number: str
    provider: str
    voice_webhook_url: Optional[str] = None
    sms_webhook_url: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None


class UpdateWebhookResponse(BaseModel):
    """Response from updating phone number webhooks."""

    model_config = ConfigDict(from_attributes=True)

    success: bool
    phone_number: str
    provider: str
    updated_webhooks: Dict[str, str] = Field(default_factory=dict)
    message: str


# Re-export all models
__all__ = [
    "PhoneNumber",
    "AvailablePhoneNumber",
    "SearchPhoneNumbersResponse",
    "PurchasePhoneNumberResponse",
    "ReleasePhoneNumberResponse",
    "CountryCode",
    "CountryCodesResponse",
    "WebhookConfig",
    "UpdateWebhookResponse",
]
