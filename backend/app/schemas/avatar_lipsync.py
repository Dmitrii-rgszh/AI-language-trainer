from typing import Literal

from pydantic import Field

from .base import ApiModel


class WelcomeTutorClipRequest(ApiModel):
    text: str = Field(min_length=1, max_length=1200)
    language: Literal["ru", "en"] = "ru"
    avatar_key: str = Field(default="verba_tutor", min_length=1, max_length=80)


class WelcomeTutorStatusResponse(ApiModel):
    available: bool
    mode: Literal["musetalk", "fallback"]
    details: str
