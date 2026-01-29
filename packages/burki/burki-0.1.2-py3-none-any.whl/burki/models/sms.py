"""
SMS models for the Burki SDK.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class SMS(BaseModel):
    """Represents an SMS message."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    conversation_id: Optional[int] = None
    provider: str = "twilio"  # twilio, telnyx, vonage
    provider_message_id: Optional[str] = None
    from_number: str
    to_number: str
    body: str
    direction: str = "outbound"  # inbound, outbound
    status: str = "queued"  # queued, sending, sent, delivered, failed
    media_urls: Optional[List[str]] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class SMSConversation(BaseModel):
    """Represents an SMS conversation."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: Optional[str] = None
    assistant_id: int
    assistant_name: Optional[str] = None
    customer_phone_number: str
    assistant_phone_number: Optional[str] = None
    status: str = "active"  # active, completed
    message_count: int = 0
    started_at: Optional[str] = None
    last_activity: Optional[str] = None
    ended_at: Optional[str] = None
    channel: str = "sms"


class SMSMessage(BaseModel):
    """Represents a message within an SMS conversation."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    conversation_id: str
    role: str  # user, assistant, system
    content: str
    timestamp: Optional[str] = None
    message_index: Optional[int] = None
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None


class SendSMSResponse(BaseModel):
    """Response from sending an SMS."""

    model_config = ConfigDict(from_attributes=True)

    success: bool
    message: str
    message_id: Optional[str] = None
    provider: Optional[str] = None
    status: Optional[str] = None
    queued: bool = False
    queue_position: Optional[int] = None
    estimated_send_time: Optional[str] = None


class SMSStatusResponse(BaseModel):
    """Response from getting SMS status."""

    model_config = ConfigDict(from_attributes=True)

    success: bool
    message_id: str
    status: str
    provider: Optional[str] = None
    provider_status: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    sent_at: Optional[str] = None
    delivered_at: Optional[str] = None


class SMSQueueStats(BaseModel):
    """SMS queue statistics."""

    model_config = ConfigDict(from_attributes=True)

    total_queued: int = 0
    by_provider: Optional[Dict[str, int]] = None
    pending: int = 0
    processing: int = 0
    completed_last_hour: int = 0
    failed_last_hour: int = 0
    average_send_time_ms: Optional[float] = None


class SMSCancelResponse(BaseModel):
    """Response from canceling an SMS."""

    model_config = ConfigDict(from_attributes=True)

    success: bool
    message: str
    message_id: str
    status: str


# Re-export all models
__all__ = [
    "SMS",
    "SMSConversation",
    "SMSMessage",
    "SendSMSResponse",
    "SMSStatusResponse",
    "SMSQueueStats",
    "SMSCancelResponse",
]
