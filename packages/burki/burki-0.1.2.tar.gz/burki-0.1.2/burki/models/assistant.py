"""
Assistant models for the Burki SDK.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class Keyword(BaseModel):
    """A keyword to be detected in STT, with an optional intensifier."""

    keyword: str
    intensifier: float = 1.0


class BackgroundSoundSettings(BaseModel):
    """Settings for background sounds during calls."""

    enabled: bool = False
    storage_key: Optional[str] = None
    sound_url: Optional[str] = None
    volume: float = Field(default=0.3, ge=0.0, le=1.0)
    loop: bool = True


class LLMProviderConfig(BaseModel):
    """Configuration for the LLM provider."""

    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = "gpt-4o-mini"
    custom_config: Optional[Dict[str, Any]] = Field(default_factory=dict)


class LLMSettings(BaseModel):
    """Settings for the Large Language Model."""

    temperature: float = 0.5
    max_tokens: int = 1000
    system_prompt: str = "You are a helpful assistant."
    welcome_message: Optional[str] = None
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop_sequences: List[str] = Field(default_factory=list)


class InterruptionSettings(BaseModel):
    """Settings for call interruption behavior."""

    interruption_threshold: int = 3
    min_speaking_time: float = 0.5
    interruption_cooldown: float = 2.0


class TTSSettings(BaseModel):
    """Settings for Text-to-Speech service."""

    model_config = ConfigDict(protected_namespaces=(), populate_by_name=True)

    provider: str = "elevenlabs"
    voice_id: str = "rachel"
    model_id: Optional[str] = Field(default="turbo", alias="tts_model_id")
    latency: int = 1
    stability: float = 0.5
    similarity_boost: float = 0.75
    style: float = 0.0
    use_speaker_boost: bool = True
    provider_config: Optional[Dict[str, Any]] = Field(default_factory=dict)
    background_sound: BackgroundSoundSettings = Field(default_factory=BackgroundSoundSettings)


class STTEndpointingSettings(BaseModel):
    """Endpointing settings for Speech-to-Text."""

    silence_threshold: int = 500
    min_silence_duration: int = 500


class FluxConfig(BaseModel):
    """Configuration for Deepgram Flux models (AI-powered turn detection)."""

    eot_timeout_ms: Optional[int] = Field(default=None, ge=10, le=10000)
    eager_eot_threshold: Optional[float] = Field(default=None, ge=0.3, le=0.9)
    eot_threshold: Optional[float] = Field(default=None, ge=0.5, le=0.9)
    tag: Optional[str] = None
    mip_opt_out: Optional[bool] = False


class STTSettings(BaseModel):
    """Settings for Speech-to-Text service."""

    provider: Optional[str] = "deepgram"
    model: str = "nova-2"
    language: str = "en-US"
    punctuate: bool = True
    interim_results: bool = True
    endpointing: STTEndpointingSettings = Field(default_factory=STTEndpointingSettings)
    utterance_end_ms: int = Field(default=1000, ge=100, le=10000)
    vad_turnoff: int = 500
    smart_format: bool = True
    keywords: List[Keyword] = Field(default_factory=list)
    keyterms: List[str] = Field(default_factory=list)
    audio_denoising: bool = False
    flux_config: Optional[FluxConfig] = None
    provider_config: Optional[Dict[str, Any]] = Field(default_factory=dict)


class EndCallTool(BaseModel):
    """Configuration for the 'end call' tool."""

    enabled: bool = False
    scenarios: List[str] = Field(default_factory=list)
    custom_message: Optional[str] = None


class TransferCallTool(BaseModel):
    """Configuration for the 'transfer call' tool."""

    enabled: bool = False
    scenarios: List[str] = Field(default_factory=list)
    transfer_numbers: List[str] = Field(default_factory=list)
    custom_message: Optional[str] = None


class DtmfSolverTool(BaseModel):
    """Configuration for the 'DTMF solver' tool - allows AI to send DTMF tones."""

    enabled: bool = False
    scenarios: List[str] = Field(default_factory=list)


class ToolsSettings(BaseModel):
    """Settings for integrated tools."""

    enabled_tools: List[str] = Field(default_factory=list)
    end_call: EndCallTool = Field(default_factory=EndCallTool)
    transfer_call: TransferCallTool = Field(default_factory=TransferCallTool)
    dtmf_solver: DtmfSolverTool = Field(default_factory=DtmfSolverTool)
    custom_tools: List[Dict[str, Any]] = Field(default_factory=list)


class RAGSettings(BaseModel):
    """Settings for Retrieval-Augmented Generation."""

    enabled: bool = False
    search_limit: int = 3
    similarity_threshold: float = 0.7
    embedding_model: str = "text-embedding-3-small"
    chunking_strategy: str = "recursive"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    auto_process: bool = True
    include_metadata: bool = True
    context_window_tokens: int = 4000


class LLMFallbackProvider(BaseModel):
    """Configuration for a single LLM fallback provider."""

    provider: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None


class LLMFallbackSettings(BaseModel):
    """Settings for LLM fallback providers."""

    enabled: bool = False
    fallbacks: List[LLMFallbackProvider] = Field(default_factory=list)


class Assistant(BaseModel):
    """Represents an assistant in the Burki system."""

    id: int
    organization_id: Optional[int] = None
    name: str
    description: Optional[str] = None

    # LLM Provider Configuration
    llm_provider: Optional[str] = "openai"
    llm_provider_config: Optional[LLMProviderConfig] = Field(default_factory=LLMProviderConfig)

    # LLM Settings
    llm_settings: Optional[LLMSettings] = Field(default_factory=LLMSettings)

    # Webhook settings
    webhook_url: Optional[str] = None
    webhook_headers: Optional[Dict[str, str]] = None
    sms_webhook_url: Optional[str] = None
    messaging_service_sid: Optional[str] = None

    # Interruption Settings
    interruption_settings: Optional[InterruptionSettings] = Field(default_factory=InterruptionSettings)

    # TTS Settings
    tts_settings: Optional[TTSSettings] = Field(default_factory=TTSSettings)

    # STT Settings
    stt_settings: Optional[STTSettings] = Field(default_factory=STTSettings)

    # Call control settings
    end_call_message: Optional[str] = None
    transfer_call_message: Optional[str] = None
    idle_message: Optional[str] = "Are you still there? I'm here to help if you need anything."
    max_idle_messages: Optional[int] = None
    idle_timeout: Optional[int] = None
    max_call_length: Optional[int] = None

    # Conversation continuity settings
    conversation_continuity_enabled: Optional[bool] = True

    # Tools configuration
    tools_settings: Optional[ToolsSettings] = Field(default_factory=ToolsSettings)

    # RAG settings
    rag_settings: Optional[RAGSettings] = Field(default_factory=RAGSettings)

    # Fallback providers configuration
    llm_fallback_providers: Optional[LLMFallbackSettings] = Field(default_factory=LLMFallbackSettings)

    # Additional settings
    custom_settings: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = True

    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Computed fields (from API responses)
    call_count: Optional[int] = None
    total_duration: Optional[int] = None
    phone_numbers: Optional[List[str]] = None

    model_config = ConfigDict(from_attributes=True)


class AssistantCreate(BaseModel):
    """Model for creating a new assistant."""

    name: str
    description: Optional[str] = None
    llm_provider: str = "openai"
    llm_provider_config: Optional[LLMProviderConfig] = None
    llm_settings: Optional[LLMSettings] = None
    webhook_url: Optional[str] = None
    webhook_headers: Optional[Dict[str, str]] = None
    sms_webhook_url: Optional[str] = None
    messaging_service_sid: Optional[str] = None
    interruption_settings: Optional[InterruptionSettings] = None
    tts_settings: Optional[TTSSettings] = None
    stt_settings: Optional[STTSettings] = None
    end_call_message: Optional[str] = None
    transfer_call_message: Optional[str] = None
    idle_message: Optional[str] = None
    max_idle_messages: Optional[int] = None
    idle_timeout: Optional[int] = None
    max_call_length: Optional[int] = None
    conversation_continuity_enabled: Optional[bool] = True
    tools_settings: Optional[ToolsSettings] = None
    rag_settings: Optional[RAGSettings] = None
    llm_fallback_providers: Optional[LLMFallbackSettings] = None
    custom_settings: Optional[Dict[str, Any]] = None
    is_active: bool = True


class AssistantUpdate(BaseModel):
    """Model for updating an assistant (partial update)."""

    name: Optional[str] = None
    description: Optional[str] = None
    llm_provider: Optional[str] = None
    llm_provider_config: Optional[LLMProviderConfig] = None
    llm_settings: Optional[LLMSettings] = None
    webhook_url: Optional[str] = None
    webhook_headers: Optional[Dict[str, str]] = None
    sms_webhook_url: Optional[str] = None
    messaging_service_sid: Optional[str] = None
    interruption_settings: Optional[InterruptionSettings] = None
    tts_settings: Optional[TTSSettings] = None
    stt_settings: Optional[STTSettings] = None
    end_call_message: Optional[str] = None
    transfer_call_message: Optional[str] = None
    idle_message: Optional[str] = None
    max_idle_messages: Optional[int] = None
    idle_timeout: Optional[int] = None
    max_call_length: Optional[int] = None
    conversation_continuity_enabled: Optional[bool] = None
    tools_settings: Optional[ToolsSettings] = None
    rag_settings: Optional[RAGSettings] = None
    llm_fallback_providers: Optional[LLMFallbackSettings] = None
    custom_settings: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class AssistantList(BaseModel):
    """Paginated list of assistants."""

    items: List[Assistant]
    total: int
    skip: int
    limit: int


# Re-export all models
__all__ = [
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
]
