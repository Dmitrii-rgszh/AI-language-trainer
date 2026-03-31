from datetime import datetime

from .base import ApiModel


class PronunciationWordAssessment(ApiModel):
    target_word: str
    heard_word: str | None = None
    score: int
    status: str
    note: str


class PronunciationFocusAssessment(ApiModel):
    focus: str
    status: str
    note: str


class PronunciationAttempt(ApiModel):
    id: str
    drill_id: str | None = None
    drill_title: str | None = None
    target_text: str
    sound_focus: str | None = None
    transcript: str
    score: int
    feedback: str
    weakest_words: list[str]
    focus_issues: list[str]
    created_at: datetime


class TrendPoint(ApiModel):
    label: str
    occurrences: int


class PronunciationTrend(ApiModel):
    average_score: int
    recent_attempts: int
    weakest_words: list[TrendPoint]
    weakest_sounds: list[TrendPoint]


class PronunciationAssessment(ApiModel):
    target_text: str
    transcript: str
    score: int
    matched_tokens: list[str]
    missed_tokens: list[str]
    feedback: str
    weakest_words: list[str]
    word_assessments: list[PronunciationWordAssessment]
    focus_assessments: list[PronunciationFocusAssessment]
