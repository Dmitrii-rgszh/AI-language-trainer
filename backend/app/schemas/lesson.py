from typing import Any, Literal

from pydantic import Field

from .base import ApiModel
from .mistake import Mistake
from .progress import ProgressSnapshot

LessonType = Literal[
    "core",
    "diagnostic",
    "grammar",
    "speaking",
    "pronunciation",
    "writing",
    "professional",
    "mixed",
    "recovery",
]

LessonBlockType = Literal[
    "intro_block",
    "review_block",
    "grammar_block",
    "vocab_block",
    "speaking_block",
    "pronunciation_block",
    "listening_block",
    "writing_block",
    "profession_block",
    "reflection_block",
    "summary_block",
]


class LessonBlock(ApiModel):
    id: str
    block_type: LessonBlockType
    title: str
    instructions: str
    estimated_minutes: int
    payload: dict[str, Any]


class Lesson(ApiModel):
    id: str
    lesson_type: LessonType
    title: str
    goal: str
    difficulty: str
    duration: int
    modules: list[LessonBlockType]
    blocks: list[LessonBlock]
    completed: bool = False
    score: int | None = None


class LessonRecommendation(ApiModel):
    id: str
    title: str
    lesson_type: LessonType
    goal: str
    duration: int
    focus_area: str


class StartLessonRunRequest(ApiModel):
    template_id: str | None = None


class CompleteLessonRunRequest(ApiModel):
    score: int = Field(default=78, ge=0, le=100)
    minutes_completed: int | None = Field(default=None, ge=1, le=180)
    block_results: list["BlockResultSubmission"] = Field(default_factory=list)


class BlockResultSubmission(ApiModel):
    block_id: str
    user_response_type: Literal["none", "text", "voice", "multiple_choice"] = "text"
    user_response: str | None = None
    transcript: str | None = None
    feedback_summary: str | None = None
    score: int | None = Field(default=None, ge=0, le=100)


class SubmitBlockResultRequest(BlockResultSubmission):
    pass


class LessonBlockRunState(ApiModel):
    id: str
    block_id: str
    status: str
    user_response_type: str
    user_response: str | None = None
    transcript: str | None = None
    feedback_summary: str | None = None
    score: int | None = None


class LessonRunState(ApiModel):
    run_id: str
    status: str
    started_at: str
    completed_at: str | None = None
    score: int | None = None
    lesson: Lesson
    block_runs: list[LessonBlockRunState] = Field(default_factory=list)


class CompleteLessonRunResponse(ApiModel):
    lesson_run: LessonRunState
    progress: ProgressSnapshot
    mistakes: list[Mistake] = Field(default_factory=list)
