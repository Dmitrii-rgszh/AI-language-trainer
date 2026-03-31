from .base import ApiModel


class ListeningAttempt(ApiModel):
    id: str
    lesson_run_id: str
    lesson_title: str
    block_title: str
    prompt_label: str | None = None
    answer_summary: str
    score: int
    used_transcript_support: bool
    completed_at: str


class ListeningTrendPoint(ApiModel):
    label: str
    occurrences: int


class ListeningTrend(ApiModel):
    average_score: int
    recent_attempts: int
    transcript_support_rate: int
    weakest_prompts: list[ListeningTrendPoint]
