from enum import Enum
from typing import Any

from pydantic import Field

from .base import ApiModel


class ProviderType(str, Enum):
    LLM = "llm"
    STT = "stt"
    TTS = "tts"
    SCORING = "scoring"


class ProviderAvailability(str, Enum):
    READY = "ready"
    MOCK = "mock"
    OFFLINE = "offline"


class ProviderStatus(ApiModel):
    key: str
    name: str
    type: ProviderType
    status: ProviderAvailability
    details: str


class ProviderPreference(ApiModel):
    provider_type: ProviderType
    selected_provider: str
    enabled: bool = True
    settings: dict[str, Any] = Field(default_factory=dict)


class ProviderPreferenceUpdateRequest(ApiModel):
    selected_provider: str
    enabled: bool = True
    settings: dict[str, Any] = Field(default_factory=dict)
