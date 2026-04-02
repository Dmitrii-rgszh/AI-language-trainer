from typing import Literal

from pydantic import Field

from .base import ApiModel


class SynthesizeSpeechRequest(ApiModel):
    text: str = Field(min_length=1, max_length=1200)
    language: str = Field(default="en", min_length=2, max_length=10)
    speaker: str | None = Field(default=None, max_length=120)
    style: Literal["coach", "warm", "neutral"] = "coach"


class TranscribeSpeechResponse(ApiModel):
    transcript: str = Field(min_length=1, max_length=4000)
