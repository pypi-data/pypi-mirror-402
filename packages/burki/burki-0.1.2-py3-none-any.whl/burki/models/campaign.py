"""
Campaign models for the Burki SDK.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class CampaignContact(BaseModel):
    """A contact in a campaign."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: Optional[int] = None
    campaign_id: Optional[int] = None
    
    phone_number: str
    name: Optional[str] = None
    email: Optional[str] = None
    
    # Custom variables for templates
    variables: Dict[str, Any] = Field(default_factory=dict)
    
    status: str = "pending"  # pending, in_progress, completed, failed, skipped
    
    # Call information
    call_sid: Optional[str] = None
    call_duration: Optional[int] = None
    call_status: Optional[str] = None
    
    attempts: int = 0
    last_attempt_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    error_message: Optional[str] = None


class CampaignSchedule(BaseModel):
    """Schedule settings for a campaign."""
    
    schedule_type: str = "immediate"  # immediate, once, recurring
    scheduled_at: Optional[datetime] = None
    timezone: str = "UTC"
    
    # Recurring settings
    days_of_week: List[int] = Field(default_factory=list)  # 0=Monday, 6=Sunday
    start_time: Optional[str] = None  # HH:MM format
    end_time: Optional[str] = None  # HH:MM format


class CampaignSettings(BaseModel):
    """Execution settings for a campaign."""
    
    max_concurrent_calls: int = 5
    calls_per_minute: int = 10
    max_attempts: int = 3
    retry_delay_minutes: int = 30
    
    # Voicemail handling
    leave_voicemail: bool = False
    voicemail_message: Optional[str] = None
    
    # Templates (Jinja2)
    welcome_template: Optional[str] = None
    agenda_template: Optional[str] = None


class Campaign(BaseModel):
    """Represents a campaign in Burki."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    organization_id: int
    assistant_id: int
    
    name: str
    description: Optional[str] = None
    campaign_type: str = "call"  # call, sms
    
    status: str = "draft"  # draft, scheduled, running, paused, completed, cancelled
    
    # Contacts
    total_contacts: int = 0
    completed_contacts: int = 0
    failed_contacts: int = 0
    
    # Schedule
    schedule: CampaignSchedule = Field(default_factory=CampaignSchedule)
    
    # Settings
    settings: CampaignSettings = Field(default_factory=CampaignSettings)
    
    # Phone number to call from
    phone_number_id: Optional[int] = None
    from_phone_number: Optional[str] = None
    
    # Timestamps
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class CampaignCreate(BaseModel):
    """Request model for creating a campaign."""
    
    name: str
    description: Optional[str] = None
    assistant_id: int
    campaign_type: str = "call"
    
    contacts: List[CampaignContact] = Field(default_factory=list)
    
    phone_number_id: Optional[int] = None
    
    schedule: Optional[CampaignSchedule] = None
    settings: Optional[CampaignSettings] = None


class CampaignUpdate(BaseModel):
    """Request model for updating a campaign."""
    
    name: Optional[str] = None
    description: Optional[str] = None
    
    schedule: Optional[CampaignSchedule] = None
    settings: Optional[CampaignSettings] = None


class CampaignProgress(BaseModel):
    """Progress information for a campaign."""
    
    campaign_id: int
    status: str
    
    total_contacts: int = 0
    completed_contacts: int = 0
    failed_contacts: int = 0
    pending_contacts: int = 0
    in_progress_contacts: int = 0
    
    completion_percentage: float = 0.0
    success_rate: float = 0.0
    
    # Cost tracking
    total_cost: float = 0.0
    
    # Timing
    started_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None


class CampaignList(BaseModel):
    """Response model for listing campaigns."""
    
    items: List[Campaign]
    total: int


class CampaignContactList(BaseModel):
    """Response model for listing campaign contacts."""
    
    items: List[CampaignContact]
    total: int
    skip: int
    limit: int


class CampaignStats(BaseModel):
    """Statistics for a campaign."""
    
    model_config = ConfigDict(from_attributes=True)
    
    campaign_id: int
    status: str
    total_contacts: int = 0
    completed_contacts: int = 0
    failed_contacts: int = 0
    pending_contacts: int = 0
    in_progress_contacts: int = 0
    
    completion_percentage: float = 0.0
    success_rate: float = 0.0
    average_call_duration: Optional[float] = None
    total_call_duration: Optional[int] = None
    total_cost: Optional[float] = None
    
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None


# Re-export all models
__all__ = [
    "Campaign",
    "CampaignCreate",
    "CampaignUpdate",
    "CampaignList",
    "CampaignContact",
    "CampaignContactList",
    "CampaignSchedule",
    "CampaignSettings",
    "CampaignProgress",
    "CampaignStats",
]
