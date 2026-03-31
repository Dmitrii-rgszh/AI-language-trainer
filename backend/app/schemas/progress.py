from .base import ApiModel


class LessonHistoryItem(ApiModel):
    id: str
    title: str
    lesson_type: str
    completed_at: str
    score: int


class ProgressSnapshot(ApiModel):
    id: str
    grammar_score: int
    speaking_score: int
    listening_score: int
    pronunciation_score: int
    writing_score: int
    profession_score: int
    regulation_score: int
    streak: int
    daily_goal_minutes: int
    minutes_completed_today: int
    history: list[LessonHistoryItem]

