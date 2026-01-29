"""
Data models for the Burki SDK.
"""

from burki.models.assistant import (
    Assistant,
    AssistantCreate,
    AssistantUpdate,
    AssistantList,
    LLMProviderConfig,
    LLMSettings,
    TTSSettings,
    STTSettings,
    STTEndpointingSettings,
    FluxConfig,
    RAGSettings,
    ToolsSettings,
    EndCallTool,
    TransferCallTool,
    DtmfSolverTool,
    InterruptionSettings,
    BackgroundSoundSettings,
    Keyword,
    LLMFallbackSettings,
    LLMFallbackProvider,
)

from burki.models.call import (
    Call,
    CallCreate,
    CallUpdate,
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

from burki.models.phone_number import (
    PhoneNumber,
    AvailablePhoneNumber,
    SearchPhoneNumbersResponse,
    PurchasePhoneNumberResponse,
    ReleasePhoneNumberResponse,
    CountryCode,
    CountryCodesResponse,
    WebhookConfig,
    UpdateWebhookResponse,
)

from burki.models.document import (
    Document,
    DocumentCreate,
    DocumentUpdate,
    DocumentList,
    DocumentChunk,
)

from burki.models.tool import (
    Tool,
    ToolCreate,
    ToolUpdate,
    ToolList,
    ToolParameter,
    ToolExecution,
)

from burki.models.sms import (
    SMS,
    SMSConversation,
    SMSMessage,
    SendSMSResponse,
    SMSStatusResponse,
    SMSQueueStats,
    SMSCancelResponse,
)

from burki.models.campaign import (
    Campaign,
    CampaignCreate,
    CampaignUpdate,
    CampaignList,
    CampaignContact,
    CampaignStats,
    CampaignProgress,
)

from burki.models.realtime import (
    TranscriptEvent,
    TranscriptSegment,
    CampaignProgressEvent,
    ConnectionStatus,
)

__all__ = [
    # Assistant models
    "Assistant",
    "AssistantCreate",
    "AssistantUpdate",
    "AssistantList",
    "LLMProviderConfig",
    "LLMSettings",
    "TTSSettings",
    "STTSettings",
    "STTEndpointingSettings",
    "FluxConfig",
    "RAGSettings",
    "ToolsSettings",
    "EndCallTool",
    "TransferCallTool",
    "DtmfSolverTool",
    "InterruptionSettings",
    "BackgroundSoundSettings",
    "Keyword",
    "LLMFallbackSettings",
    "LLMFallbackProvider",
    # Call models
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
    # Phone number models
    "PhoneNumber",
    "AvailablePhoneNumber",
    "SearchPhoneNumbersResponse",
    "PurchasePhoneNumberResponse",
    "ReleasePhoneNumberResponse",
    "CountryCode",
    "CountryCodesResponse",
    "WebhookConfig",
    "UpdateWebhookResponse",
    # Document models
    "Document",
    "DocumentCreate",
    "DocumentUpdate",
    "DocumentList",
    "DocumentChunk",
    # Tool models
    "Tool",
    "ToolCreate",
    "ToolUpdate",
    "ToolList",
    "ToolParameter",
    "ToolExecution",
    # SMS models
    "SMS",
    "SMSConversation",
    "SMSMessage",
    "SendSMSResponse",
    "SMSStatusResponse",
    "SMSQueueStats",
    "SMSCancelResponse",
    # Campaign models
    "Campaign",
    "CampaignCreate",
    "CampaignUpdate",
    "CampaignList",
    "CampaignContact",
    "CampaignStats",
    "CampaignProgress",
    # Realtime models
    "TranscriptEvent",
    "TranscriptSegment",
    "CampaignProgressEvent",
    "ConnectionStatus",
]
