from datetime import datetime
from typing import Literal

from .base import ApiModel

MistakeCategory = Literal[
    "grammar",
    "pronunciation",
    "vocabulary",
    "speaking",
    "writing",
    "profession",
]


class Mistake(ApiModel):
    id: str
    category: MistakeCategory
    subtype: str
    source_module: str
    original_text: str
    corrected_text: str
    explanation: str
    repetition_count: int
    last_seen_at: datetime


class WeakSpot(ApiModel):
    id: str
    title: str
    category: MistakeCategory
    recommendation: str
