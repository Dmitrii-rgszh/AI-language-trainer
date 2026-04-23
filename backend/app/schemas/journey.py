from __future__ import annotations

from typing import Literal

from pydantic import Field

from .base import ApiModel
from .profile import ProfileUpdateRequest, UserProfile


class ProofLessonHandoff(ApiModel):
    locale: str
    scenario_id: str
    before_phrase: str
    after_phrase: str
    clarity_status_label: str
    directions: list[str] = Field(default_factory=list)
    wins: list[str] = Field(default_factory=list)
    created_at: str


class JourneyAccountDraft(ApiModel):
    login: str = ""
    email: str = ""


class StartOnboardingSessionRequest(ApiModel):
    source: Literal["proof_lesson", "direct_onboarding"] = "direct_onboarding"
    proof_lesson_handoff: ProofLessonHandoff | None = None


class SaveOnboardingSessionDraftRequest(ApiModel):
    account_draft: JourneyAccountDraft = Field(default_factory=JourneyAccountDraft)
    profile_draft: ProfileUpdateRequest
    current_step: int = Field(default=0, ge=0, le=12)


class CompleteRouteReentrySupportStepRequest(ApiModel):
    route: str


class CompleteTaskDrivenStepRequest(ApiModel):
    input_route: str
    response_route: str


class RegisterRouteEntryRequest(ApiModel):
    route: str
    source: str = "surface_visit"


class RegisterRitualSignalRequest(ApiModel):
    signal_type: Literal["word_journal", "spontaneous_voice"]
    route: str
    label: str
    summary: str | None = None


class OnboardingSession(ApiModel):
    id: str
    user_id: str | None = None
    status: str
    source: str
    proof_lesson_handoff: ProofLessonHandoff | None = None
    account_draft: JourneyAccountDraft = Field(default_factory=JourneyAccountDraft)
    profile_draft: UserProfile | None = None
    current_step: int = 0
    completed_at: str | None = None
    created_at: str
    updated_at: str


class DailyLoopStep(ApiModel):
    id: str
    skill: str
    title: str
    description: str
    duration_minutes: int = Field(ge=1, le=60)


class DailyRitualStage(ApiModel):
    id: str
    title: str
    summary: str
    emphasis: str
    required: bool = True


class DailyRitual(ApiModel):
    headline: str
    promise: str
    completion_rule: str
    closure_rule: str
    stages: list[DailyRitualStage] = Field(default_factory=list)


class TaskDrivenInput(ApiModel):
    input_route: str
    input_label: str
    response_route: str
    response_label: str
    title: str
    summary: str
    bridge: str
    closure: str


class DailyLoopPlan(ApiModel):
    id: str
    plan_date_key: str
    status: str
    stage: str
    session_kind: str
    focus_area: str
    headline: str
    summary: str
    why_this_now: str
    next_step_hint: str
    preferred_mode: str
    time_budget_minutes: int
    estimated_minutes: int
    recommended_lesson_type: str
    recommended_lesson_title: str
    lesson_run_id: str | None = None
    completed_at: str | None = None
    steps: list[DailyLoopStep] = Field(default_factory=list)
    ritual: DailyRitual | None = None
    task_driven_input: TaskDrivenInput | None = None


class LearnerJourneyState(ApiModel):
    user_id: str
    stage: str
    source: str
    preferred_mode: str
    diagnostic_readiness: str
    time_budget_minutes: int
    current_focus_area: str
    current_strategy_summary: str
    next_best_action: str
    last_daily_plan_id: str | None = None
    proof_lesson_handoff: ProofLessonHandoff | None = None
    strategy_snapshot: dict = Field(default_factory=dict)
    onboarding_completed_at: str | None = None
    created_at: str
    updated_at: str
