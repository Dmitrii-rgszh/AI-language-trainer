from typing import Literal

from pydantic import Field

from .base import ApiModel


class LiveAvatarIceServer(ApiModel):
    urls: list[str] = Field(default_factory=list)
    username: str | None = None
    credential: str | None = None


class LiveAvatarConfigResponse(ApiModel):
    enabled: bool
    signaling_path: str
    signaling_url: str
    default_avatar_key: str
    default_voice_profile_id: str
    fallback_mode_available: bool
    ice_servers: list[LiveAvatarIceServer] = Field(default_factory=list)
    details: str


class LiveAvatarStatusResponse(ApiModel):
    enabled: bool
    ready: bool
    mode: Literal["live", "fallback", "disabled"]
    details: str


class LiveAvatarFallbackRequest(ApiModel):
    user_text: str = Field(min_length=1, max_length=1600)
    language: Literal["ru", "en"] = "ru"
    avatar_key: str = Field(default="verba_tutor", min_length=1, max_length=80)


class LiveAvatarFallbackResponse(ApiModel):
    transcript: str
    assistant_text: str
    clip_id: str
    clip_url: str
