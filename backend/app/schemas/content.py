from typing import Literal

from .adaptive import AdaptiveStudyLoop
from .base import ApiModel
from .journey import DailyLoopPlan, LearnerJourneyState
from .lesson import LessonRecommendation
from .mistake import WeakSpot
from .profile import UserProfile
from .progress import ProgressSnapshot


class QuickAction(ApiModel):
    id: str
    title: str
    description: str
    route: str


class ResumeLessonCard(ApiModel):
    run_id: str
    title: str
    current_block_title: str
    completed_blocks: int
    total_blocks: int
    route: str


class DashboardData(ApiModel):
    profile: UserProfile
    progress: ProgressSnapshot
    weak_spots: list[WeakSpot]
    recommendation: LessonRecommendation
    study_loop: AdaptiveStudyLoop | None = None
    daily_loop_plan: DailyLoopPlan | None = None
    journey_state: LearnerJourneyState | None = None
    quick_actions: list[QuickAction]
    resume_lesson: ResumeLessonCard | None = None


class GrammarTopic(ApiModel):
    id: str
    title: str
    level: str
    mastery: int
    explanation: str
    checkpoints: list[str]


class SpeakingScenario(ApiModel):
    id: str
    title: str
    mode: Literal["guided", "free", "roleplay"]
    goal: str
    prompt: str
    feedback_hint: str


class PronunciationDrill(ApiModel):
    id: str
    title: str
    sound: str
    focus: str
    phrases: list[str]
    difficulty: str


class WritingTask(ApiModel):
    id: str
    title: str
    brief: str
    tone: str
    checklist: list[str]
    improved_version_preview: str


class ProfessionTrackCard(ApiModel):
    id: str
    title: str
    domain: str
    summary: str
    lesson_focus: list[str]
