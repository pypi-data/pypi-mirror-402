"""
Realtime event models for the Burki SDK.
"""

from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel


class TranscriptEvent(BaseModel):
    """A real-time transcript event from a call."""
    
    type: str = "transcript"
    call_sid: str
    timestamp: datetime
    
    # Transcript data
    content: str
    speaker: str  # user or assistant
    is_final: bool = True
    confidence: Optional[float] = None
    segment_start: Optional[float] = None
    segment_end: Optional[float] = None


class CallStatusEvent(BaseModel):
    """A real-time call status event."""
    
    type: str = "call_status"
    call_sid: str
    timestamp: datetime
    
    status: str  # in-progress, completed, failed
    metadata: Dict[str, Any] = {}


class CampaignProgressEvent(BaseModel):
    """A real-time campaign progress event."""
    
    type: str = "progress"
    campaign_id: int
    timestamp: datetime
    
    # Progress data
    total_contacts: int = 0
    completed_contacts: int = 0
    failed_contacts: int = 0
    pending_contacts: int = 0
    in_progress_contacts: int = 0
    
    completion_percentage: float = 0.0
    
    # Latest contact update
    contact_id: Optional[int] = None
    contact_phone: Optional[str] = None
    contact_status: Optional[str] = None
    contact_error: Optional[str] = None


class CampaignContactEvent(BaseModel):
    """A real-time campaign contact status event."""
    
    type: str = "contact_update"
    campaign_id: int
    timestamp: datetime
    
    contact_id: int
    phone_number: str
    status: str  # pending, in_progress, completed, failed, skipped
    
    call_sid: Optional[str] = None
    call_duration: Optional[int] = None
    error_message: Optional[str] = None


class CampaignCompletedEvent(BaseModel):
    """Event when a campaign completes."""
    
    type: str = "campaign_completed"
    campaign_id: int
    timestamp: datetime
    
    total_contacts: int
    completed_contacts: int
    failed_contacts: int
    success_rate: float
    total_duration: int = 0
    total_cost: float = 0.0


class WebSocketMessage(BaseModel):
    """Generic WebSocket message wrapper."""
    
    type: str
    timestamp: datetime
    data: Dict[str, Any] = {}


class TranscriptSegment(BaseModel):
    """A segment within a transcript."""
    
    content: str
    speaker: str  # user or assistant
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    confidence: Optional[float] = None
    is_final: bool = True


class ConnectionStatus(BaseModel):
    """WebSocket connection status."""
    
    connected: bool = False
    connection_id: Optional[str] = None
    subscribed_calls: list = []
    subscribed_campaigns: list = []
    last_ping: Optional[datetime] = None


# Re-export all models
__all__ = [
    "TranscriptEvent",
    "TranscriptSegment",
    "CallStatusEvent",
    "CampaignProgressEvent",
    "CampaignContactEvent",
    "CampaignCompletedEvent",
    "WebSocketMessage",
    "ConnectionStatus",
]
