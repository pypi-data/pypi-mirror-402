"""
Call-related models for the Burki SDK.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class CallTranscript(BaseModel):
    """Represents a transcript entry from a call."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    call_id: int
    speaker: str  # "user" or "assistant"
    content: str
    timestamp: Optional[datetime] = None
    is_final: bool = True
    confidence: Optional[float] = None
    language: Optional[str] = None
    created_at: Optional[datetime] = None


class CallRecording(BaseModel):
    """Represents a recording from a call."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    call_id: int
    recording_type: str  # "user", "assistant", "mixed"
    url: Optional[str] = None
    duration: Optional[float] = None
    size_bytes: Optional[int] = None
    format: Optional[str] = None
    created_at: Optional[datetime] = None


class CallMetrics(BaseModel):
    """Calculated metrics for a call."""

    model_config = ConfigDict(from_attributes=True)

    call_id: int
    duration_seconds: Optional[int] = None
    talk_time_user: Optional[float] = None
    talk_time_assistant: Optional[float] = None
    silence_time: Optional[float] = None
    interruptions: Optional[int] = None
    average_response_time: Optional[float] = None
    sentiment_score: Optional[float] = None
    emotion_detected: Optional[str] = None
    topics_discussed: Optional[List[str]] = None
    summary: Optional[str] = None
    cost_estimate: Optional[float] = None
    tokens_used: Optional[int] = None


class ChatMessage(BaseModel):
    """Represents a message in the LLM conversation."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    call_id: int
    role: str  # "system", "user", "assistant", "tool"
    content: str
    name: Optional[str] = None  # For tool calls
    tool_call_id: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    timestamp: Optional[datetime] = None
    created_at: Optional[datetime] = None


class WebhookLog(BaseModel):
    """Represents a webhook log entry."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    call_id: int
    webhook_type: str
    url: str
    request_body: Optional[Dict[str, Any]] = None
    response_status: Optional[int] = None
    response_body: Optional[str] = None
    error: Optional[str] = None
    latency_ms: Optional[int] = None
    created_at: Optional[datetime] = None


class Call(BaseModel):
    """Represents a call in the Burki system."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: Optional[int] = None
    assistant_id: Optional[int] = None
    call_sid: Optional[str] = None
    stream_sid: Optional[str] = None
    status: str = "pending"  # pending, ongoing, completed, failed, transferred
    direction: str = "inbound"  # inbound, outbound
    customer_phone: Optional[str] = None
    twilio_phone: Optional[str] = None  # Also used for Telnyx/Vonage phone
    telephony_provider: Optional[str] = None  # twilio, telnyx, vonage
    duration: Optional[int] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Additional fields
    welcome_message: Optional[str] = None
    agenda: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    end_reason: Optional[str] = None
    transferred_to: Optional[str] = None

    # Computed/joined fields
    assistant_name: Optional[str] = None
    transcript_count: Optional[int] = None
    recording_count: Optional[int] = None

    # Cost tracking
    cost: Optional[float] = None
    cost_breakdown: Optional[Dict[str, float]] = None


class CallCreate(BaseModel):
    """Model for creating a new call (used internally)."""

    assistant_id: int
    customer_phone: str
    twilio_phone: Optional[str] = None
    direction: str = "outbound"
    welcome_message: Optional[str] = None
    agenda: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class CallUpdate(BaseModel):
    """Model for updating a call."""

    status: Optional[str] = None
    duration: Optional[int] = None
    ended_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    end_reason: Optional[str] = None


class PaginatedCalls(BaseModel):
    """Paginated list of calls."""

    items: List[Call]
    total: int
    skip: int
    limit: int


class CallAnalytics(BaseModel):
    """Call analytics data."""

    model_config = ConfigDict(from_attributes=True)

    period: str
    total_calls: int
    completed_calls: int
    failed_calls: int
    average_duration: Optional[float] = None
    total_duration: Optional[int] = None
    total_cost: Optional[float] = None
    calls_by_day: Optional[List[Dict[str, Any]]] = None
    calls_by_assistant: Optional[List[Dict[str, Any]]] = None
    calls_by_status: Optional[Dict[str, int]] = None
    sentiment_distribution: Optional[Dict[str, int]] = None
    average_sentiment: Optional[float] = None
    top_topics: Optional[List[Dict[str, Any]]] = None
    peak_hours: Optional[List[Dict[str, Any]]] = None


class CallStats(BaseModel):
    """Basic call statistics."""

    model_config = ConfigDict(from_attributes=True)

    total_calls: int = 0
    ongoing_calls: int = 0
    completed_calls: int = 0
    failed_calls: int = 0
    average_duration: Optional[float] = None
    total_duration: Optional[int] = None


class InitiateCallResponse(BaseModel):
    """Response from initiating an outbound call."""

    model_config = ConfigDict(from_attributes=True)

    success: bool
    message: str
    call_sid: Optional[str] = None
    call_id: Optional[int] = None
    status: Optional[str] = None
    from_number: Optional[str] = None
    to_number: Optional[str] = None


# Re-export all models
__all__ = [
    "Call",
    "CallCreate",
    "CallUpdate",
    "PaginatedCalls",
    "CallTranscript",
    "CallRecording",
    "CallMetrics",
    "CallAnalytics",
    "CallStats",
    "ChatMessage",
    "WebhookLog",
    "InitiateCallResponse",
]
