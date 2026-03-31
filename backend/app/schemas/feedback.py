from datetime import datetime
from typing import Literal

from pydantic import Field

from .base import ApiModel


class SpeakingFeedbackRequest(ApiModel):
    scenario_id: str
    transcript: str = Field(min_length=1, max_length=4000)
    feedback_language: Literal["ru", "en"] = "ru"


class WritingReviewRequest(ApiModel):
    task_id: str
    draft: str = Field(min_length=1, max_length=5000)
    feedback_language: Literal["ru", "en"] = "ru"


class AITextFeedback(ApiModel):
    source: Literal["ai", "mock"]
    summary: str
    voice_text: str
    voice_language: Literal["ru", "en"]


class SpeakingVoiceFeedback(ApiModel):
    transcript: str
    feedback: AITextFeedback


class SpeakingAttempt(ApiModel):
    id: str
    scenario_id: str
    scenario_title: str
    input_mode: Literal["text", "voice"]
    transcript: str
    feedback_summary: str
    feedback_source: Literal["ai", "mock"]
    voice_text: str
    voice_language: Literal["ru", "en"]
    created_at: datetime


class WritingAttempt(ApiModel):
    id: str
    task_id: str
    task_title: str
    draft: str
    feedback_summary: str
    feedback_source: Literal["ai", "mock"]
    voice_text: str
    voice_language: Literal["ru", "en"]
    created_at: datetime
