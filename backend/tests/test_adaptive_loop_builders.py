from datetime import datetime

from app.schemas.adaptive import (
    MistakeResolutionSignal,
    MistakeVocabularyBacklink,
    SkillTrajectoryMemory,
    SkillTrajectorySignal,
    VocabularyHub,
    VocabularyLoopSummary,
    VocabularyReviewItem,
)
from app.schemas.journey import DailyLoopPlan, DailyLoopStep, LearnerJourneyState
from app.schemas.lesson import LessonRecommendation
from app.schemas.mistake import Mistake, WeakSpot
from app.schemas.profile import OnboardingAnswers, UserProfile
from app.schemas.progress import LessonHistoryItem, ProgressSnapshot
from app.services.adaptive_study_service.loop_builder import (
    build_adaptive_study_loop,
    derive_generation_rationale,
)
from app.services.adaptive_study_service.loop_heuristics import detect_progress_focus
from app.services.adaptive_study_service.loop_heuristics import build_progress_trajectory
from app.services.adaptive_study_service.loop_heuristics import build_strategy_memory
from app.services.recommendation_service.engine import build_next_recommendation
from app.services.adaptive_study_service.service import AdaptiveStudyService
from app.services.adaptive_study_service.vocabulary_hub_builder import build_vocabulary_hub


def _build_profile() -> UserProfile:
    return UserProfile(
        id="user-1",
        name="Nina",
        native_language="ru",
        current_level="A2",
        target_level="B2",
        profession_track="trainer_skills",
        preferred_ui_language="ru",
        preferred_explanation_language="ru",
        lesson_duration=20,
        speaking_priority=7,
        grammar_priority=6,
        profession_priority=8,
        onboarding_answers=OnboardingAnswers(),
    )


def _build_progress() -> ProgressSnapshot:
    return ProgressSnapshot(
        id="snapshot-1",
        grammar_score=52,
        speaking_score=58,
        listening_score=49,
        pronunciation_score=46,
        writing_score=54,
        profession_score=61,
        regulation_score=0,
        streak=3,
        daily_goal_minutes=20,
        minutes_completed_today=12,
        history=[],
    )


class _StubLessonRepository:
    def get_recommendation(self, profession_track: str) -> LessonRecommendation:
        return LessonRecommendation(
            id="lesson-stub",
            title="Main route",
            lesson_type="mixed",
            goal="Keep the route moving.",
            duration=20,
            focus_area="speaking",
        )

    def list_recent_completed_lessons(self, user_id: str, limit: int = 1) -> list[LessonHistoryItem]:
        return []


class _StubMistakeRepository:
    def list_weak_spots(self, user_id: str, limit: int = 2) -> list[WeakSpot]:
        return []

    def list_mistakes(self, user_id: str) -> list[Mistake]:
        return []


class _StubVocabularyRepository:
    def list_due_items(self, user_id: str, limit: int = 3) -> list[VocabularyReviewItem]:
        return []

    def list_mistake_backlinks(self, user_id: str, limit: int = 6) -> list[MistakeVocabularyBacklink]:
        return []


class _StubProgressRepository:
    def __init__(self, latest: ProgressSnapshot, recent: list[ProgressSnapshot]) -> None:
        self._latest = latest
        self._recent = recent

    def get_latest_snapshot(self, user_id: str) -> ProgressSnapshot:
        return self._latest

    def list_recent_snapshots(self, user_id: str, limit: int = 3) -> list[ProgressSnapshot]:
        return self._recent[:limit]


class _StubJourneyRepository:
    def __init__(self, journey_state: LearnerJourneyState | None) -> None:
        self._journey_state = journey_state

    def get_journey_state(self, user_id: str) -> LearnerJourneyState | None:
        return self._journey_state


def test_build_adaptive_study_loop_returns_consistent_loop() -> None:
    loop = build_adaptive_study_loop(
        profile=_build_profile(),
        recommendation=LessonRecommendation(
            id="lesson-1",
            title="Recovery lesson",
            lesson_type="recovery",
            goal="Fix recurring mistakes.",
            duration=20,
            focus_area="grammar",
        ),
        weak_spots=[
            WeakSpot(
                id="weak-1",
                title="Present Perfect vs Past Simple",
                category="grammar",
                recommendation="Review tense contrast.",
            )
        ],
        mistakes=[
            Mistake(
                id="mistake-1",
                category="grammar",
                subtype="tense-choice",
                source_module="speaking",
                original_text="I work here since 2022.",
                corrected_text="I have worked here since 2022.",
                explanation="Use Present Perfect.",
                repetition_count=2,
                last_seen_at=datetime.utcnow(),
            )
        ],
        progress=_build_progress(),
        recent_lessons=[
            LessonHistoryItem(
                id="history-1",
                title="Warmup",
                lesson_type="mixed",
                completed_at="2026-04-01",
                score=76,
            )
        ],
        due_vocabulary=[
            VocabularyReviewItem(
                id="vocab-1",
                word="have worked",
                translation="pattern",
                context="I have worked here since 2022.",
                category="mistake_tense_patterns",
                source_module="speaking",
                review_reason="reason",
                linked_mistake_subtype="tense-choice",
                linked_mistake_title="Present Perfect vs Past Simple",
                learned_status="active",
                repetition_stage=2,
                due_now=True,
            )
        ],
        vocabulary_summary=VocabularyLoopSummary(
            due_count=1,
            new_count=0,
            active_count=3,
            mastered_count=1,
            weakest_category="grammar",
        ),
        vocabulary_backlinks=[
            MistakeVocabularyBacklink(
                weak_spot_title="Present Perfect vs Past Simple",
                weak_spot_category="grammar",
                due_count=1,
                active_count=1,
                example_words=["have worked"],
                source_modules=["speaking"],
            )
        ],
    )

    assert loop.focus_area == "grammar"
    assert loop.recommendation.lesson_type == "recovery"
    assert loop.vocabulary_summary.due_count == 1
    assert loop.module_rotation
    assert loop.next_steps


def test_build_vocabulary_hub_wraps_sections_without_changes() -> None:
    hub = build_vocabulary_hub(
        summary=VocabularyLoopSummary(
            due_count=1,
            new_count=0,
            active_count=2,
            mastered_count=1,
            weakest_category="grammar",
        ),
        due_items=[],
        recent_items=[],
        mistake_backlinks=[],
    )

    assert isinstance(hub, VocabularyHub)
    assert hub.summary.due_count == 1


def test_derive_generation_rationale_proxies_loop_copy_logic() -> None:
    rationale = derive_generation_rationale(
        recommendation_lesson_type="lesson",
        weak_spots=[
            WeakSpot(
                id="weak-1",
                title="Present Perfect vs Past Simple",
                category="grammar",
                recommendation="Review tense contrast.",
            )
        ],
        vocabulary_summary=VocabularyLoopSummary(
            due_count=2,
            new_count=0,
            active_count=4,
            mastered_count=1,
            weakest_category="grammar",
        ),
        listening_focus="audio_comprehension",
        mistake_resolution=[
            MistakeResolutionSignal(
                weak_spot_title="Present Perfect vs Past Simple",
                weak_spot_category="grammar",
                status="recovering",
                repetition_count=2,
                last_seen_days_ago=2,
                linked_vocabulary_count=1,
                resolution_hint="Pattern is easing.",
            )
        ],
    )

    assert rationale


def test_detect_progress_focus_prefers_weakest_measured_skill() -> None:
    progress = _build_progress()

    focus = detect_progress_focus(progress, ["speaking", "grammar"])

    assert focus == "pronunciation"


def test_build_progress_trajectory_prefers_slipping_skill_across_recent_snapshots() -> None:
    latest = _build_progress()
    older = latest.model_copy(
        update={
            "id": "snapshot-0",
            "grammar_score": 50,
            "speaking_score": 60,
            "listening_score": 52,
            "pronunciation_score": 50,
            "writing_score": 54,
            "profession_score": 61,
        }
    )
    oldest = latest.model_copy(
        update={
            "id": "snapshot--1",
            "grammar_score": 49,
            "speaking_score": 61,
            "listening_score": 55,
            "pronunciation_score": 53,
            "writing_score": 56,
            "profession_score": 62,
        }
    )

    trajectory = build_progress_trajectory([latest, older, oldest], ["speaking", "grammar"])

    assert trajectory is not None
    assert trajectory.focus_skill == "pronunciation"
    assert trajectory.direction == "slipping"
    assert trajectory.observed_snapshots == 3
    assert trajectory.signals[0].skill == "pronunciation"


def test_build_strategy_memory_prefers_persistent_longer_term_signal() -> None:
    latest = _build_progress().model_copy(
        update={
            "grammar_score": 55,
            "speaking_score": 63,
            "listening_score": 60,
            "pronunciation_score": 58,
            "writing_score": 61,
            "profession_score": 66,
        }
    )
    older_a = latest.model_copy(update={"id": "snapshot-0", "grammar_score": 54, "pronunciation_score": 57})
    older_b = latest.model_copy(update={"id": "snapshot--1", "grammar_score": 53, "pronunciation_score": 56})
    older_c = latest.model_copy(update={"id": "snapshot--2", "grammar_score": 56, "pronunciation_score": 61})
    older_d = latest.model_copy(update={"id": "snapshot--3", "grammar_score": 52, "pronunciation_score": 62})

    strategy_memory = build_strategy_memory(
        [latest, older_a, older_b, older_c, older_d],
        ["grammar", "speaking"],
    )

    assert strategy_memory is not None
    assert strategy_memory.focus_skill == "grammar"
    assert strategy_memory.persistence_level == "persistent"
    assert strategy_memory.observed_snapshots == 5
    assert strategy_memory.signals[0].skill == "grammar"


def test_build_next_recommendation_uses_task_driven_transfer_signal() -> None:
    profile = _build_profile().model_copy(
        update={
            "onboarding_answers": _build_profile().onboarding_answers.model_copy(
                update={"preferred_mode": "text_first", "active_skill_focus": ["reading", "writing"]}
            )
        }
    )
    latest = _build_progress()
    journey_state = LearnerJourneyState(
        id="journey-1",
        user_id=profile.id,
        stage="daily_loop_completed",
        source="proof_lesson",
        preferred_mode="text_first",
        diagnostic_readiness="soft_start",
        time_budget_minutes=20,
        current_focus_area="writing",
        current_strategy_summary="The route should protect the writing response lane.",
        next_best_action="Return for one more connected writing pass.",
        proof_lesson_handoff=None,
        strategy_snapshot={
            "sessionSummary": {
                "taskDrivenTransferEvaluation": {
                    "inputRoute": "/reading",
                    "inputLabel": "reading input",
                    "responseRoute": "/writing",
                    "responseLabel": "writing response",
                    "transferOutcome": "fragile",
                    "summary": "The move into writing response is still fragile.",
                }
            }
        },
        onboarding_completed_at=datetime.utcnow().isoformat(),
        last_daily_plan_id=None,
        created_at=datetime.utcnow().isoformat(),
        updated_at=datetime.utcnow().isoformat(),
    )

    recommendation = build_next_recommendation(
        profile,
        _StubLessonRepository(),
        _StubMistakeRepository(),
        _StubVocabularyRepository(),
        _StubProgressRepository(latest, [latest]),
        _StubJourneyRepository(journey_state),
    )

    assert recommendation is not None
    assert recommendation.focus_area == "writing"
    assert "writing response" in recommendation.goal.lower()


def test_build_next_recommendation_can_widen_after_strong_task_transfer_pass() -> None:
    profile = _build_profile().model_copy(
        update={
            "onboarding_answers": _build_profile().onboarding_answers.model_copy(
                update={"preferred_mode": "text_first", "active_skill_focus": ["reading", "writing"]}
            )
        }
    )
    latest = _build_progress()
    journey_state = LearnerJourneyState(
        id="journey-1",
        user_id=profile.id,
        stage="daily_loop_completed",
        source="proof_lesson",
        preferred_mode="text_first",
        diagnostic_readiness="soft_start",
        time_budget_minutes=20,
        current_focus_area="writing",
        current_strategy_summary="The response lane is ready to widen again.",
        next_best_action="Let the broader route lead again.",
        proof_lesson_handoff=None,
        strategy_snapshot={
            "sessionSummary": {
                "taskDrivenTransferEvaluation": {
                    "inputRoute": "/reading",
                    "inputLabel": "reading input",
                    "responseRoute": "/writing",
                    "responseLabel": "writing response",
                    "transferOutcome": "held",
                    "summary": "The transfer held cleanly in the protected response pass.",
                    "currentWindowStage": "protect_response",
                    "nextWindowStage": "ready_to_widen",
                    "windowAction": "advance_to_widen",
                }
            }
        },
        onboarding_completed_at=datetime.utcnow().isoformat(),
        last_daily_plan_id=None,
        created_at=datetime.utcnow().isoformat(),
        updated_at=datetime.utcnow().isoformat(),
    )

    recommendation = build_next_recommendation(
        profile,
        _StubLessonRepository(),
        _StubMistakeRepository(),
        _StubVocabularyRepository(),
        _StubProgressRepository(latest, [latest]),
        _StubJourneyRepository(journey_state),
    )

    assert recommendation is not None
    assert "start widening again" in recommendation.goal.lower() or "broader route lead again" in recommendation.goal.lower()


def test_build_next_recommendation_can_stop_forcing_response_focus_after_transfer_window_closes() -> None:
    profile = _build_profile().model_copy(
        update={
            "onboarding_answers": _build_profile().onboarding_answers.model_copy(
                update={"preferred_mode": "text_first", "active_skill_focus": ["reading", "writing"]}
            )
        }
    )
    latest = _build_progress()
    journey_state = LearnerJourneyState(
        id="journey-1",
        user_id=profile.id,
        stage="daily_loop_completed",
        source="proof_lesson",
        preferred_mode="text_first",
        diagnostic_readiness="soft_start",
        time_budget_minutes=20,
        current_focus_area="writing",
        current_strategy_summary="The protected transfer window can close now.",
        next_best_action="Return to the broader route.",
        proof_lesson_handoff=None,
        strategy_snapshot={
            "sessionSummary": {
                "taskDrivenTransferEvaluation": {
                    "inputRoute": "/reading",
                    "inputLabel": "reading input",
                    "responseRoute": "/writing",
                    "responseLabel": "writing response",
                    "transferOutcome": "held",
                    "summary": "The widening pass kept the transfer alive cleanly.",
                    "currentWindowStage": "ready_to_widen",
                    "nextWindowStage": "close_window",
                    "windowAction": "close_window",
                }
            }
        },
        onboarding_completed_at=datetime.utcnow().isoformat(),
        last_daily_plan_id=None,
        created_at=datetime.utcnow().isoformat(),
        updated_at=datetime.utcnow().isoformat(),
    )

    recommendation = build_next_recommendation(
        profile,
        _StubLessonRepository(),
        _StubMistakeRepository(),
        _StubVocabularyRepository(),
        _StubProgressRepository(latest, [latest]),
        _StubJourneyRepository(journey_state),
    )

    assert recommendation is not None
    assert "broader route lead again" in recommendation.goal.lower() or "transfer window has already done its job" in recommendation.goal.lower()
    assert recommendation.focus_area != "writing"


def test_build_next_recommendation_does_not_force_ritual_focus_after_ready_to_carry() -> None:
    profile = _build_profile()
    latest = _build_progress()
    journey_state = LearnerJourneyState(
        id="journey-1",
        user_id=profile.id,
        stage="daily_loop_completed",
        source="proof_lesson",
        preferred_mode="mixed",
        diagnostic_readiness="soft_start",
        time_budget_minutes=20,
        current_focus_area="vocabulary",
        current_strategy_summary="The captured phrase is ready to ride inside the broader route.",
        next_best_action="Let the broader route lead again.",
        proof_lesson_handoff=None,
        strategy_snapshot={
            "ritualSignalMemory": {
                "activeSignalType": "word_journal",
                "activeLabel": "keep it light",
                "recommendedFocus": "vocabulary",
                "summary": "The word journal signal is ready to carry forward inside the broader route.",
                "windowStage": "ready_to_carry",
            }
        },
        onboarding_completed_at=datetime.utcnow().isoformat(),
        last_daily_plan_id=None,
        created_at=datetime.utcnow().isoformat(),
        updated_at=datetime.utcnow().isoformat(),
    )

    recommendation = build_next_recommendation(
        profile,
        _StubLessonRepository(),
        _StubMistakeRepository(),
        _StubVocabularyRepository(),
        _StubProgressRepository(latest, [latest]),
        _StubJourneyRepository(journey_state),
    )

    assert recommendation is not None
    assert "does not need to restart from capture" in recommendation.goal.lower() or "carry forward inside the broader route" in recommendation.goal.lower()
    assert recommendation.focus_area != "vocabulary"


def test_build_next_recommendation_uses_skill_trajectory_when_live_focus_is_balanced() -> None:
    profile = _build_profile().model_copy(
        update={
            "onboarding_answers": _build_profile().onboarding_answers.model_copy(
                update={"active_skill_focus": ["grammar", "speaking"]}
            )
        }
    )
    latest = _build_progress().model_copy(
        update={
            "grammar_score": 56,
            "speaking_score": 57,
            "listening_score": 56,
            "pronunciation_score": 57,
            "writing_score": 56,
            "profession_score": 58,
        }
    )
    older = latest.model_copy(
        update={
            "id": "snapshot-0",
            "grammar_score": 59,
            "speaking_score": 58,
            "listening_score": 57,
            "pronunciation_score": 58,
            "writing_score": 57,
            "profession_score": 58,
        }
    )
    oldest = latest.model_copy(
        update={
            "id": "snapshot--1",
            "grammar_score": 63,
            "speaking_score": 59,
            "listening_score": 58,
            "pronunciation_score": 59,
            "writing_score": 58,
            "profession_score": 59,
        }
    )

    recommendation = build_next_recommendation(
        profile=profile,
        lesson_repository=_StubLessonRepository(),
        mistake_repository=_StubMistakeRepository(),
        vocabulary_repository=_StubVocabularyRepository(),
        progress_repository=_StubProgressRepository(latest, [latest, older, oldest]),
    )

    assert recommendation is not None
    assert recommendation.focus_area == "grammar"
    assert "multi-day learner memory" in recommendation.goal.lower()


def test_build_next_recommendation_can_fall_back_to_strategy_memory() -> None:
    profile = _build_profile().model_copy(
        update={
            "onboarding_answers": _build_profile().onboarding_answers.model_copy(
                update={"active_skill_focus": ["grammar", "speaking"]}
            )
        }
    )
    latest = _build_progress().model_copy(
        update={
            "grammar_score": 66,
            "speaking_score": 67,
            "listening_score": 66,
            "pronunciation_score": 67,
            "writing_score": 66,
            "profession_score": 68,
        }
    )
    older_a = latest.model_copy(update={"id": "snapshot-0", "grammar_score": 60, "speaking_score": 66})
    older_b = latest.model_copy(update={"id": "snapshot--1", "grammar_score": 57, "speaking_score": 66})
    older_c = latest.model_copy(update={"id": "snapshot--2", "grammar_score": 55, "speaking_score": 67})
    older_d = latest.model_copy(update={"id": "snapshot--3", "grammar_score": 54, "speaking_score": 67})

    recommendation = build_next_recommendation(
        profile=profile,
        lesson_repository=_StubLessonRepository(),
        mistake_repository=_StubMistakeRepository(),
        vocabulary_repository=_StubVocabularyRepository(),
        progress_repository=_StubProgressRepository(latest, [latest, older_a, older_b, older_c, older_d]),
    )

    assert recommendation is not None
    assert recommendation.focus_area == "grammar"
    assert "longer learner memory" in recommendation.goal.lower()


def test_build_next_recommendation_prefers_connected_return_when_recovery_arc_is_protected() -> None:
    profile = _build_profile()
    journey_state = LearnerJourneyState.model_validate(
        {
            "userId": "user-1",
            "stage": "daily_loop_ready",
            "source": "proof_lesson",
            "preferredMode": "mixed",
            "diagnosticReadiness": "soft_start",
            "timeBudgetMinutes": 20,
            "currentFocusArea": "grammar",
            "currentStrategySummary": "The route should reopen calmly.",
            "nextBestAction": "Start with a protected return.",
            "strategySnapshot": {
                "routeRecoveryMemory": {
                    "phase": "protected_return",
                    "horizonDays": 2,
                    "focusSkill": "grammar",
                    "supportPracticeTitle": "Speaking refresh",
                    "sessionShape": "protected_mix",
                    "summary": "The route is back in motion, but the next 2 sessions should still protect grammar before opening fully.",
                    "actionHint": "Use a protected return for the next 2 routes and let the calmer support lane carry some of the load.",
                    "nextPhaseHint": "If the return rhythm holds, the route can widen again after these protected sessions.",
                }
            },
            "createdAt": "2026-04-15T10:00:00",
            "updatedAt": "2026-04-15T10:00:00",
        }
    )

    class _RecoveryPressureMistakeRepository(_StubMistakeRepository):
        def list_weak_spots(self, user_id: str, limit: int = 2) -> list[WeakSpot]:
            return [
                WeakSpot(
                    id="weak-1",
                    title="Present Perfect vs Past Simple",
                    category="grammar",
                    recommendation="Review tense contrast.",
                )
            ]

    recommendation = build_next_recommendation(
        profile=profile,
        lesson_repository=_StubLessonRepository(),
        mistake_repository=_RecoveryPressureMistakeRepository(),
        vocabulary_repository=_StubVocabularyRepository(),
        progress_repository=_StubProgressRepository(_build_progress(), [_build_progress()]),
        journey_repository=_StubJourneyRepository(journey_state),
    )

    assert recommendation is not None
    assert recommendation.lesson_type == "mixed"
    assert recommendation.focus_area == "grammar"
    assert "protected_return" in recommendation.goal.lower()


def test_build_next_recommendation_uses_active_reentry_route_when_sequence_is_in_progress() -> None:
    profile = _build_profile()
    journey_state = LearnerJourneyState.model_validate(
        {
            "userId": "user-1",
            "stage": "daily_loop_ready",
            "source": "proof_lesson",
            "preferredMode": "mixed",
            "diagnosticReadiness": "soft_start",
            "timeBudgetMinutes": 20,
            "currentFocusArea": "grammar",
            "currentStrategySummary": "The route is still in a grammar repair cycle.",
            "nextBestAction": "Open writing support next.",
            "strategySnapshot": {
                "routeRecoveryMemory": {
                    "phase": "skill_repair_cycle",
                    "horizonDays": 3,
                    "focusSkill": "grammar",
                    "supportPracticeTitle": "Grammar support",
                    "sessionShape": "focused_support",
                    "summary": "Grammar needs a short repair cycle across the next routes before the wider path opens again.",
                    "actionHint": "Keep the route narrow and reopen support steps in order.",
                    "nextPhaseHint": "If grammar holds, the route can widen after the repair cycle.",
                },
                "routeReentryProgress": {
                    "sequenceKey": "route-reentry:user-1:plan-1:skill_repair_cycle:grammar",
                    "phase": "skill_repair_cycle",
                    "focusSkill": "grammar",
                    "orderedRoutes": ["/grammar", "/writing", "/speaking", "/vocabulary", "/pronunciation"],
                    "completedRoutes": ["/grammar"],
                    "nextRoute": "/writing",
                    "status": "active",
                },
            },
            "createdAt": "2026-04-15T10:00:00",
            "updatedAt": "2026-04-15T10:00:00",
        }
    )

    recommendation = build_next_recommendation(
        profile=profile,
        lesson_repository=_StubLessonRepository(),
        mistake_repository=_StubMistakeRepository(),
        vocabulary_repository=_StubVocabularyRepository(),
        progress_repository=_StubProgressRepository(_build_progress(), [_build_progress()]),
        journey_repository=_StubJourneyRepository(journey_state),
    )

    assert recommendation is not None
    assert recommendation.lesson_type == "mixed"
    assert recommendation.focus_area == "writing"
    assert "writing support" in recommendation.goal.lower()
    assert "sequenced recovery progression" in recommendation.goal.lower()


def test_build_next_recommendation_resets_to_main_route_after_repeated_reentry_surface() -> None:
    profile = _build_profile()
    journey_state = LearnerJourneyState.model_validate(
        {
            "userId": "user-1",
            "stage": "daily_loop_ready",
            "source": "proof_lesson",
            "preferredMode": "mixed",
            "diagnosticReadiness": "soft_start",
            "timeBudgetMinutes": 20,
            "currentFocusArea": "grammar",
            "currentStrategySummary": "The route should stop reopening the same support surface.",
            "nextBestAction": "Reset through the calmer main route first.",
            "strategySnapshot": {
                "routeRecoveryMemory": {
                    "phase": "skill_repair_cycle",
                    "horizonDays": 3,
                    "focusSkill": "grammar",
                    "supportPracticeTitle": "Grammar support",
                    "sessionShape": "focused_support",
                    "summary": "Grammar still needs a short repair cycle before the wider path opens again.",
                    "actionHint": "Reopen support steps in order, but do not get stuck on one surface.",
                    "nextPhaseHint": "If grammar holds, the route can widen after the repair cycle.",
                },
                "routeReentryProgress": {
                    "sequenceKey": "route-reentry:user-1:plan-1:skill_repair_cycle:grammar",
                    "phase": "skill_repair_cycle",
                    "focusSkill": "grammar",
                    "orderedRoutes": ["/grammar", "/writing", "/speaking", "/vocabulary", "/pronunciation"],
                    "completedRoutes": ["/grammar"],
                    "nextRoute": "/writing",
                    "status": "active",
                },
                "routeEntryMemory": {
                    "recentEntries": [
                        {
                            "route": "/writing",
                            "source": "smart_reentry",
                            "enteredAt": "2026-04-15T10:00:00",
                            "stage": "daily_loop_ready",
                            "recoveryPhase": "skill_repair_cycle",
                            "sessionShape": "focused_support",
                            "nextRoute": "/writing",
                        },
                        {
                            "route": "/writing",
                            "source": "surface_visit",
                            "enteredAt": "2026-04-15T10:10:00",
                            "stage": "daily_loop_ready",
                            "recoveryPhase": "skill_repair_cycle",
                            "sessionShape": "focused_support",
                            "nextRoute": "/writing",
                        },
                    ],
                    "lastRoute": "/writing",
                    "lastSource": "surface_visit",
                    "repeatedRouteCount": 2,
                    "activeNextRoute": "/writing",
                    "activeNextRouteVisits": 2,
                },
            },
            "createdAt": "2026-04-15T10:00:00",
            "updatedAt": "2026-04-15T10:10:00",
        }
    )

    recommendation = build_next_recommendation(
        profile=profile,
        lesson_repository=_StubLessonRepository(),
        mistake_repository=_StubMistakeRepository(),
        vocabulary_repository=_StubVocabularyRepository(),
        progress_repository=_StubProgressRepository(_build_progress(), [_build_progress()]),
        journey_repository=_StubJourneyRepository(journey_state),
    )

    assert recommendation is not None
    assert recommendation.lesson_type == "mixed"
    assert recommendation.focus_area == "grammar"
    assert "writing support has already reopened 2 times" in recommendation.goal.lower()
    assert "calmer main path" in recommendation.goal.lower()


def test_strategy_alignment_turns_repeated_reentry_into_multi_day_reset() -> None:
    alignment = AdaptiveStudyService._build_strategy_alignment(
        recommendation=LessonRecommendation(
            id="lesson-1",
            title="Main route",
            lesson_type="mixed",
            goal="Keep the route moving.",
            duration=20,
            focus_area="grammar",
        ),
        weak_spots=[],
        due_vocabulary=[],
        progress=_build_progress(),
        recent_progress=[_build_progress()],
        journey_state=LearnerJourneyState.model_validate(
            {
                "userId": "user-1",
                "stage": "daily_loop_ready",
                "source": "proof_lesson",
                "preferredMode": "mixed",
                "diagnosticReadiness": "soft_start",
                "timeBudgetMinutes": 20,
                "currentFocusArea": "grammar",
                "currentStrategySummary": "Reset through the calmer main route first.",
                "nextBestAction": "Use the calmer main route before reopening writing support again.",
                "strategySnapshot": {
                    "routeRecoveryMemory": {
                        "phase": "skill_repair_cycle",
                        "horizonDays": 3,
                        "focusSkill": "grammar",
                        "supportPracticeTitle": "Grammar support",
                        "sessionShape": "focused_support",
                        "summary": "Grammar still needs a short repair cycle before the wider path opens again.",
                        "actionHint": "Keep the route narrow and reopen support steps in order.",
                        "nextPhaseHint": "If grammar holds, the route can widen after the repair cycle.",
                    },
                    "routeReentryProgress": {
                        "sequenceKey": "route-reentry:user-1:plan-1:skill_repair_cycle:grammar",
                        "phase": "skill_repair_cycle",
                        "focusSkill": "grammar",
                        "orderedRoutes": ["/grammar", "/writing", "/speaking", "/vocabulary", "/pronunciation"],
                        "completedRoutes": ["/grammar"],
                        "nextRoute": "/writing",
                        "status": "active",
                    },
                    "routeEntryMemory": {
                        "recentEntries": [
                            {
                                "route": "/writing",
                                "source": "smart_reentry",
                                "enteredAt": "2026-04-15T10:00:00",
                                "stage": "daily_loop_ready",
                                "recoveryPhase": "skill_repair_cycle",
                                "sessionShape": "focused_support",
                                "nextRoute": "/writing",
                            },
                            {
                                "route": "/writing",
                                "source": "surface_visit",
                                "enteredAt": "2026-04-15T10:10:00",
                                "stage": "daily_loop_ready",
                                "recoveryPhase": "skill_repair_cycle",
                                "sessionShape": "focused_support",
                                "nextRoute": "/writing",
                            },
                        ],
                        "lastRoute": "/writing",
                        "lastSource": "surface_visit",
                        "repeatedRouteCount": 2,
                        "activeNextRoute": "/writing",
                        "activeNextRouteVisits": 2,
                    },
                },
                "createdAt": "2026-04-15T10:00:00",
                "updatedAt": "2026-04-15T10:10:00",
            }
        ),
        daily_loop_plan=DailyLoopPlan(
            id="plan-1",
            plan_date_key="2026-04-15",
            status="ready",
            stage="daily_loop_ready",
            session_kind="recommended",
            focus_area="grammar",
            headline="Today's route resets through the calmer main path before reopening writing support again.",
            summary="Writing support has already reopened 2 times in recent returns, so today's route resets through the calmer main path first.",
            why_this_now="Use the calmer main route first so the sequence regains momentum before writing support returns.",
            next_step_hint="Use the calmer main route first, then reopen writing support after the route settles again.",
            preferred_mode="mixed",
            time_budget_minutes=20,
            estimated_minutes=20,
            recommended_lesson_type="mixed",
            recommended_lesson_title="Calmer reset route",
            lesson_run_id=None,
            completed_at=None,
            steps=[],
        ),
        profile=_build_profile(),
    )

    assert alignment is not None
    assert alignment.route_recovery_memory is not None
    assert alignment.route_recovery_memory.phase == "protected_return"
    assert "calmer main path before reopening writing support again" in alignment.route_recovery_memory.summary.lower()
    assert alignment.route_reentry_focus is None
    assert alignment.route_reentry_next_label is None
    assert alignment.recommended_module_key == "lesson"
    assert "connected reset passes" in (alignment.recommended_module_reason or "").lower()


def test_build_adaptive_study_loop_can_fall_back_to_trajectory_focus() -> None:
    profile = _build_profile()
    latest = _build_progress().model_copy(
        update={
            "grammar_score": 56,
            "speaking_score": 57,
            "listening_score": 56,
            "pronunciation_score": 57,
            "writing_score": 56,
            "profession_score": 58,
        }
    )

    loop = build_adaptive_study_loop(
        profile=profile,
        recommendation=LessonRecommendation(
            id="lesson-trajectory",
            title="Main route",
            lesson_type="mixed",
            goal="Keep the route moving.",
            duration=20,
            focus_area="speaking",
        ),
        weak_spots=[],
        mistakes=[],
        progress=latest,
        recent_lessons=[],
        due_vocabulary=[],
        vocabulary_summary=VocabularyLoopSummary(
            due_count=0,
            new_count=0,
            active_count=0,
            mastered_count=0,
            weakest_category=None,
        ),
        vocabulary_backlinks=[],
        strategy_alignment=AdaptiveStudyService._build_strategy_alignment(
            recommendation=LessonRecommendation(
                id="lesson-trajectory",
                title="Main route",
                lesson_type="mixed",
                goal="Keep the route moving.",
                duration=20,
                focus_area="speaking",
            ),
            weak_spots=[],
            due_vocabulary=[],
            progress=latest,
            recent_progress=[
                latest,
                latest.model_copy(update={"id": "snapshot-0", "grammar_score": 59}),
                latest.model_copy(update={"id": "snapshot--1", "grammar_score": 63}),
            ],
            journey_state=None,
            daily_loop_plan=DailyLoopPlan(
                id="plan-1",
                plan_date_key="2026-04-15",
                status="ready",
                stage="daily_loop_ready",
                session_kind="recommended",
                focus_area="grammar",
                headline="Trajectory route",
                summary="Protect the slipping signal.",
                why_this_now="Grammar has been slipping across recent sessions.",
                next_step_hint="Start the route and stabilize grammar first.",
                preferred_mode="mixed",
                time_budget_minutes=20,
                estimated_minutes=20,
                recommended_lesson_type="mixed",
                recommended_lesson_title="Trajectory route",
                lesson_run_id=None,
                completed_at=None,
                steps=[],
            ),
            profile=profile,
        ),
    )

    assert loop.focus_area == "grammar"


def test_build_adaptive_study_loop_softens_rotation_for_route_rescue() -> None:
    profile = _build_profile()
    progress = _build_progress()

    loop = build_adaptive_study_loop(
        profile=profile,
        recommendation=LessonRecommendation(
            id="lesson-route-rescue",
            title="Main route",
            lesson_type="mixed",
            goal="Keep the route moving.",
            duration=20,
            focus_area="speaking",
        ),
        weak_spots=[],
        mistakes=[],
        progress=progress,
        recent_lessons=[],
        due_vocabulary=[
            VocabularyReviewItem(
                id="vocab-1",
                word="restart",
                translation="restart",
                context="Restart the route gently.",
                category="general",
                source_module="lesson",
                review_reason="reason",
                linked_mistake_subtype=None,
                linked_mistake_title=None,
                learned_status="active",
                repetition_stage=2,
                due_now=True,
            )
        ],
        vocabulary_summary=VocabularyLoopSummary(
            due_count=1,
            new_count=0,
            active_count=1,
            mastered_count=0,
            weakest_category=None,
        ),
        vocabulary_backlinks=[],
        strategy_alignment=AdaptiveStudyService._build_strategy_alignment(
            recommendation=LessonRecommendation(
                id="lesson-route-rescue",
                title="Main route",
                lesson_type="mixed",
                goal="Keep the route moving.",
                duration=20,
                focus_area="speaking",
            ),
            weak_spots=[],
            due_vocabulary=[
                VocabularyReviewItem(
                    id="vocab-1",
                    word="restart",
                    translation="restart",
                    context="Restart the route gently.",
                    category="general",
                    source_module="lesson",
                    review_reason="reason",
                    linked_mistake_subtype=None,
                    linked_mistake_title=None,
                    learned_status="active",
                    repetition_stage=2,
                    due_now=True,
                )
            ],
            progress=progress,
            recent_progress=[progress],
            journey_state=LearnerJourneyState.model_validate(
                {
                    "userId": "user-1",
                    "stage": "daily_loop_ready",
                    "source": "proof_lesson",
                    "preferredMode": "mixed",
                    "diagnosticReadiness": "soft_start",
                    "timeBudgetMinutes": 20,
                    "currentFocusArea": "speaking",
                    "currentStrategySummary": "Reopen the route gently.",
                    "nextBestAction": "Start with a gentler route restart.",
                    "strategySnapshot": {
                        "routeCadenceMemory": {
                            "status": "route_rescue",
                            "observedPlans": 4,
                            "completedPlans": 1,
                            "missedPlans": 2,
                            "idleDays": 4,
                            "summary": "Recent route rhythm has slipped, so the route should restart gently.",
                            "actionHint": "Start with a short warm re-entry before wider pressure returns.",
                        },
                        "routeRecoveryMemory": {
                            "phase": "route_rebuild",
                            "horizonDays": 3,
                            "focusSkill": "grammar",
                            "supportPracticeTitle": "Vocabulary repetition",
                            "sessionShape": "gentle_restart",
                            "summary": "The route should rebuild over the next 3 sessions while it protects grammar.",
                            "actionHint": "Keep the next 3 routes short and finishable before the route widens again.",
                            "nextPhaseHint": "Once the rhythm returns, widen back into fuller mixed practice.",
                        }
                    },
                    "createdAt": "2026-04-15T10:00:00",
                    "updatedAt": "2026-04-15T10:00:00",
                }
            ),
            daily_loop_plan=DailyLoopPlan(
                id="plan-route-rescue",
                plan_date_key="2026-04-15",
                status="ready",
                stage="daily_loop_ready",
                session_kind="recommended",
                focus_area="speaking",
                headline="Route rescue",
                summary="Reopen the route gently.",
                why_this_now="Cadence says the learner needs a calmer restart.",
                next_step_hint="Start with a short warm re-entry.",
                preferred_mode="mixed",
                time_budget_minutes=20,
                estimated_minutes=20,
                recommended_lesson_type="mixed",
                recommended_lesson_title="Route rescue",
                lesson_run_id=None,
                completed_at=None,
                steps=[],
            ),
            profile=profile,
        ),
    )

    assert loop.focus_area == "vocabulary"
    assert loop.module_rotation[0].module_key in {"lesson", "vocabulary"}
    assert "reopening after a break" in loop.summary.lower()
    assert "route_rebuild" in loop.generation_rationale[0].lower()
    assert "route cadence" in loop.generation_rationale[1].lower()


def test_strategy_alignment_exposes_live_progress_signal() -> None:
    alignment = AdaptiveStudyService._build_strategy_alignment(
        recommendation=LessonRecommendation(
            id="lesson-1",
            title="Main route",
            lesson_type="mixed",
            goal="Keep the route moving.",
            duration=20,
            focus_area="grammar",
        ),
        weak_spots=[],
        due_vocabulary=[],
        progress=_build_progress(),
        recent_progress=[
            _build_progress(),
            _build_progress().model_copy(
                update={
                    "id": "snapshot-0",
                    "grammar_score": 50,
                    "speaking_score": 60,
                    "listening_score": 52,
                    "pronunciation_score": 50,
                    "writing_score": 54,
                    "profession_score": 61,
                }
            ),
            _build_progress().model_copy(
                update={
                    "id": "snapshot--1",
                    "grammar_score": 49,
                    "speaking_score": 61,
                    "listening_score": 55,
                    "pronunciation_score": 53,
                    "writing_score": 56,
                    "profession_score": 62,
                }
            ),
        ],
        journey_state=None,
        daily_loop_plan=DailyLoopPlan(
            id="plan-1",
            plan_date_key="2026-04-14",
            status="ready",
            stage="daily_loop_ready",
            session_kind="recommended",
            focus_area="pronunciation",
            headline="Today's route leans toward pronunciation.",
            summary="Use the weakest live skill as the next stabilizing signal.",
            why_this_now="Fresh progress says pronunciation needs support before the route widens.",
            next_step_hint="Start the route and support pronunciation first.",
            preferred_mode="mixed",
            time_budget_minutes=20,
            estimated_minutes=20,
            recommended_lesson_type="mixed",
            recommended_lesson_title="Pronunciation route",
            lesson_run_id=None,
            completed_at=None,
            steps=[
                DailyLoopStep(
                    id="step-1",
                    skill="pronunciation",
                    title="Support pronunciation",
                    description="Stabilize the weakest live skill first.",
                    duration_minutes=4,
                )
            ],
        ),
        profile=_build_profile(),
    )

    assert alignment is not None
    assert alignment.live_progress_focus == "pronunciation"
    assert alignment.live_progress_score == 46
    assert alignment.live_progress_reason
    assert alignment.skill_trajectory is not None
    assert alignment.skill_trajectory.focus_skill == "pronunciation"
    assert alignment.strategy_memory is not None
    assert alignment.strategy_memory.focus_skill == "grammar"
    assert alignment.strategy_memory.persistence_level in {"persistent", "recurring"}


def test_strategy_alignment_exposes_route_cadence_memory_from_journey_state() -> None:
    alignment = AdaptiveStudyService._build_strategy_alignment(
        recommendation=LessonRecommendation(
            id="lesson-1",
            title="Main route",
            lesson_type="mixed",
            goal="Keep the route moving.",
            duration=20,
            focus_area="grammar",
        ),
        weak_spots=[],
        due_vocabulary=[],
        progress=_build_progress(),
        recent_progress=[_build_progress()],
        journey_state=LearnerJourneyState.model_validate(
            {
                "userId": "user-1",
                "stage": "daily_loop_ready",
                "source": "proof_lesson",
                "preferredMode": "mixed",
                "diagnosticReadiness": "soft_start",
                "timeBudgetMinutes": 20,
                "currentFocusArea": "grammar",
                "currentStrategySummary": "Reopen the route gently.",
                "nextBestAction": "Start with a gentler route restart.",
                "strategySnapshot": {
                    "routeCadenceMemory": {
                        "status": "gentle_reentry",
                        "observedPlans": 5,
                        "completedPlans": 3,
                        "missedPlans": 1,
                        "idleDays": 2,
                        "summary": "The learner is returning after a short break, so the route should reopen calmly.",
                        "actionHint": "Use a calmer restart and let the route earn momentum again.",
                    },
                    "routeRecoveryMemory": {
                        "phase": "protected_return",
                        "horizonDays": 2,
                        "focusSkill": "grammar",
                        "supportPracticeTitle": "Speaking refresh",
                        "sessionShape": "protected_mix",
                        "summary": "The route is back in motion, but the next 2 sessions should still protect grammar before opening fully.",
                        "actionHint": "Use a protected return for the next 2 routes and let the calmer support lane carry some of the load.",
                        "nextPhaseHint": "If the return rhythm holds, the route can widen again after these protected sessions.",
                    }
                },
                "createdAt": "2026-04-15T10:00:00",
                "updatedAt": "2026-04-15T10:00:00",
            }
        ),
        daily_loop_plan=DailyLoopPlan(
            id="plan-1",
            plan_date_key="2026-04-15",
            status="ready",
            stage="daily_loop_ready",
            session_kind="recommended",
            focus_area="grammar",
            headline="Today's route reopens gently.",
            summary="Use a calmer restart.",
            why_this_now="Cadence says the learner is returning after a short break.",
            next_step_hint="Start with a calmer restart.",
            preferred_mode="mixed",
            time_budget_minutes=20,
            estimated_minutes=20,
            recommended_lesson_type="mixed",
            recommended_lesson_title="Gentle route",
            lesson_run_id=None,
            completed_at=None,
            steps=[],
        ),
        profile=_build_profile(),
    )

    assert alignment is not None
    assert alignment.route_cadence_memory is not None
    assert alignment.route_cadence_memory.status == "gentle_reentry"
    assert alignment.route_recovery_memory is not None
    assert alignment.route_recovery_memory.phase == "protected_return"
    assert "calmer restart" in alignment.recommended_module_reason.lower()


def test_strategy_alignment_exposes_active_reentry_step() -> None:
    alignment = AdaptiveStudyService._build_strategy_alignment(
        recommendation=LessonRecommendation(
            id="lesson-1",
            title="Main route",
            lesson_type="mixed",
            goal="Keep the route moving.",
            duration=20,
            focus_area="grammar",
        ),
        weak_spots=[],
        due_vocabulary=[],
        progress=_build_progress(),
        recent_progress=[_build_progress()],
        journey_state=LearnerJourneyState.model_validate(
            {
                "userId": "user-1",
                "stage": "daily_loop_ready",
                "source": "proof_lesson",
                "preferredMode": "mixed",
                "diagnosticReadiness": "soft_start",
                "timeBudgetMinutes": 20,
                "currentFocusArea": "grammar",
                "currentStrategySummary": "Keep the repair route narrow.",
                "nextBestAction": "Open writing support next.",
                "strategySnapshot": {
                    "routeRecoveryMemory": {
                        "phase": "skill_repair_cycle",
                        "horizonDays": 3,
                        "focusSkill": "grammar",
                        "supportPracticeTitle": "Grammar support",
                        "sessionShape": "focused_support",
                        "summary": "Grammar still needs a short repair cycle before the wider path opens again.",
                        "actionHint": "Reopen support steps in order.",
                        "nextPhaseHint": "If grammar holds, the route can widen after the repair cycle.",
                    },
                    "routeReentryProgress": {
                        "sequenceKey": "route-reentry:user-1:plan-1:skill_repair_cycle:grammar",
                        "phase": "skill_repair_cycle",
                        "focusSkill": "grammar",
                        "orderedRoutes": ["/grammar", "/writing", "/speaking", "/vocabulary", "/pronunciation"],
                        "completedRoutes": ["/grammar"],
                        "nextRoute": "/writing",
                        "status": "active",
                    },
                },
                "createdAt": "2026-04-15T10:00:00",
                "updatedAt": "2026-04-15T10:00:00",
            }
        ),
        daily_loop_plan=DailyLoopPlan(
            id="plan-1",
            plan_date_key="2026-04-15",
            status="ready",
            stage="daily_loop_ready",
            session_kind="recommended",
            focus_area="writing",
            headline="Writing re-entry route",
            summary="Reopen the route through writing support.",
            why_this_now="The sequence says writing support should reopen next.",
            next_step_hint="Open writing support next.",
            preferred_mode="mixed",
            time_budget_minutes=20,
            estimated_minutes=20,
            recommended_lesson_type="mixed",
            recommended_lesson_title="Writing re-entry route",
            lesson_run_id=None,
            completed_at=None,
            steps=[],
        ),
        profile=_build_profile(),
    )

    assert alignment is not None
    assert alignment.route_reentry_focus == "writing"
    assert alignment.route_reentry_next_route == "/writing"
    assert alignment.route_reentry_next_label == "writing support"
    assert alignment.route_reentry_completed_steps == 1
    assert alignment.route_reentry_total_steps == 5
    assert alignment.recommended_module_key == "writing"
    assert "writing support" in (alignment.recommended_module_reason or "").lower()


def test_build_adaptive_study_loop_prioritizes_active_reentry_step() -> None:
    profile = _build_profile()
    progress = _build_progress()

    alignment = AdaptiveStudyService._build_strategy_alignment(
        recommendation=LessonRecommendation(
            id="lesson-reentry",
            title="Main route",
            lesson_type="mixed",
            goal="Keep the route moving.",
            duration=20,
            focus_area="grammar",
        ),
        weak_spots=[],
        due_vocabulary=[],
        progress=progress,
        recent_progress=[progress],
        journey_state=LearnerJourneyState.model_validate(
            {
                "userId": "user-1",
                "stage": "daily_loop_ready",
                "source": "proof_lesson",
                "preferredMode": "mixed",
                "diagnosticReadiness": "soft_start",
                "timeBudgetMinutes": 20,
                "currentFocusArea": "grammar",
                "currentStrategySummary": "Keep the repair route narrow.",
                "nextBestAction": "Open writing support next.",
                "strategySnapshot": {
                    "routeRecoveryMemory": {
                        "phase": "skill_repair_cycle",
                        "horizonDays": 3,
                        "focusSkill": "grammar",
                        "supportPracticeTitle": "Grammar support",
                        "sessionShape": "focused_support",
                        "summary": "Grammar still needs a short repair cycle before the wider path opens again.",
                        "actionHint": "Reopen support steps in order.",
                        "nextPhaseHint": "If grammar holds, the route can widen after the repair cycle.",
                    },
                    "routeReentryProgress": {
                        "sequenceKey": "route-reentry:user-1:plan-1:skill_repair_cycle:grammar",
                        "phase": "skill_repair_cycle",
                        "focusSkill": "grammar",
                        "orderedRoutes": ["/grammar", "/writing", "/speaking", "/vocabulary", "/pronunciation"],
                        "completedRoutes": ["/grammar"],
                        "nextRoute": "/writing",
                        "status": "active",
                    },
                },
                "createdAt": "2026-04-15T10:00:00",
                "updatedAt": "2026-04-15T10:00:00",
            }
        ),
        daily_loop_plan=DailyLoopPlan(
            id="plan-reentry",
            plan_date_key="2026-04-15",
            status="ready",
            stage="daily_loop_ready",
            session_kind="recommended",
            focus_area="writing",
            headline="Writing re-entry route",
            summary="Reopen the route through writing support.",
            why_this_now="The sequence says writing support should reopen next.",
            next_step_hint="Open writing support next.",
            preferred_mode="mixed",
            time_budget_minutes=20,
            estimated_minutes=20,
            recommended_lesson_type="mixed",
            recommended_lesson_title="Writing re-entry route",
            lesson_run_id=None,
            completed_at=None,
            steps=[],
        ),
        profile=profile,
    )
    assert alignment is not None

    loop = build_adaptive_study_loop(
        profile=profile,
        recommendation=LessonRecommendation(
            id="lesson-reentry",
            title="Main route",
            lesson_type="mixed",
            goal="Keep the route moving.",
            duration=20,
            focus_area="grammar",
        ),
        weak_spots=[],
        mistakes=[],
        progress=progress,
        recent_lessons=[],
        due_vocabulary=[],
        vocabulary_summary=VocabularyLoopSummary(
            due_count=0,
            new_count=0,
            active_count=0,
            mastered_count=0,
            weakest_category=None,
        ),
        vocabulary_backlinks=[],
        strategy_alignment=alignment,
    )

    assert loop.focus_area == "writing"
    assert loop.module_rotation[0].module_key == "writing"
    assert "writing support" in loop.summary.lower()
    assert "writing support" in loop.generation_rationale[0].lower()
    assert loop.next_steps[0].step_type == "writing"


def test_strategy_alignment_exposes_support_reopen_arc_after_connected_reset() -> None:
    alignment = AdaptiveStudyService._build_strategy_alignment(
        recommendation=LessonRecommendation(
            id="lesson-1",
            title="Main route",
            lesson_type="mixed",
            goal="Keep the route moving.",
            duration=20,
            focus_area="grammar",
        ),
        weak_spots=[],
        due_vocabulary=[],
        progress=_build_progress(),
        recent_progress=[_build_progress()],
        journey_state=LearnerJourneyState.model_validate(
            {
                "userId": "user-1",
                "stage": "daily_loop_ready",
                "source": "proof_lesson",
                "preferredMode": "mixed",
                "diagnosticReadiness": "soft_start",
                "timeBudgetMinutes": 20,
                "currentFocusArea": "grammar",
                "currentStrategySummary": "The calmer reset has landed, so writing support can reopen again.",
                "nextBestAction": "Open writing support next.",
                "strategySnapshot": {
                    "routeRecoveryMemory": {
                        "phase": "protected_return",
                        "horizonDays": 3,
                        "focusSkill": "grammar",
                        "supportPracticeTitle": "Grammar support",
                        "sessionShape": "protected_mix",
                        "summary": "The route is reconnecting through the calmer main path before writing support reopens again.",
                        "actionHint": "Use connected reset passes before reopening writing support again.",
                        "nextPhaseHint": "If the calmer reset holds, writing support can reopen again without trapping the learner.",
                    },
                    "routeReentryProgress": {
                        "sequenceKey": "route-reentry:user-1:plan-1:skill_repair_cycle:grammar",
                        "phase": "skill_repair_cycle",
                        "focusSkill": "grammar",
                        "orderedRoutes": ["/grammar", "/writing", "/speaking"],
                        "completedRoutes": ["/grammar"],
                        "nextRoute": "/writing",
                        "status": "active",
                    },
                    "routeEntryMemory": {
                        "activeNextRoute": "/writing",
                        "activeNextRouteVisits": 2,
                        "connectedResetVisits": 2,
                        "readyToReopenActiveNextRoute": True,
                    },
                },
                "createdAt": "2026-04-15T10:00:00",
                "updatedAt": "2026-04-15T10:00:00",
            }
        ),
        daily_loop_plan=DailyLoopPlan(
            id="plan-1",
            plan_date_key="2026-04-15",
            status="ready",
            stage="daily_loop_ready",
            session_kind="recommended",
            focus_area="writing",
            headline="Writing reopen route",
            summary="Bring writing support back into the connected route.",
            why_this_now="The calmer reset has landed, so writing support can return early.",
            next_step_hint="Open writing support next.",
            preferred_mode="mixed",
            time_budget_minutes=20,
            estimated_minutes=20,
            recommended_lesson_type="mixed",
            recommended_lesson_title="Writing reopen route",
            lesson_run_id=None,
            completed_at=None,
            steps=[],
        ),
        profile=_build_profile(),
    )

    assert alignment is not None
    assert alignment.route_recovery_memory is not None
    assert alignment.route_recovery_memory.phase == "support_reopen_arc"
    assert alignment.route_reentry_focus == "writing"
    assert alignment.recommended_module_key == "writing"
    assert "writing support" in (alignment.recommended_module_reason or "").lower()


def test_strategy_alignment_widens_when_support_reopen_arc_is_ready_to_expand() -> None:
    alignment = AdaptiveStudyService._build_strategy_alignment(
        recommendation=LessonRecommendation(
            id="lesson-1",
            title="Main route",
            lesson_type="mixed",
            goal="Keep the route moving.",
            duration=20,
            focus_area="grammar",
        ),
        weak_spots=[],
        due_vocabulary=[],
        progress=_build_progress(),
        recent_progress=[_build_progress()],
        journey_state=LearnerJourneyState.model_validate(
            {
                "userId": "user-1",
                "stage": "daily_loop_ready",
                "source": "proof_lesson",
                "preferredMode": "mixed",
                "diagnosticReadiness": "soft_start",
                "timeBudgetMinutes": 20,
                "currentFocusArea": "writing",
                "currentStrategySummary": "Writing support has landed and the route can widen again.",
                "nextBestAction": "Return to the broader daily route while keeping writing support available.",
                "strategySnapshot": {
                    "routeRecoveryMemory": {
                        "phase": "support_reopen_arc",
                        "horizonDays": 3,
                        "focusSkill": "writing",
                        "supportPracticeTitle": "writing support",
                        "sessionShape": "guided_balance",
                        "summary": "Writing support has already landed across two connected reopen passes, so the next route can widen again without dropping it.",
                        "actionHint": "Let the next route widen through the daily route, but keep writing support available inside the broader mix.",
                        "nextPhaseHint": "If writing support stays stable in this wider pass, the route can leave the reopen arc and extend forward again.",
                        "reopenStage": "ready_to_expand",
                        "expansionReady": True,
                        "followUpCompletionCount": 2,
                    },
                    "routeReentryProgress": {
                        "sequenceKey": "route-reentry:user-1:plan-1:skill_repair_cycle:grammar",
                        "phase": "skill_repair_cycle",
                        "focusSkill": "grammar",
                        "orderedRoutes": ["/grammar", "/writing", "/speaking"],
                        "completedRoutes": ["/grammar"],
                        "nextRoute": "/writing",
                        "status": "active",
                    },
                },
                "createdAt": "2026-04-15T10:00:00",
                "updatedAt": "2026-04-15T10:00:00",
            }
        ),
        daily_loop_plan=DailyLoopPlan(
            id="plan-1",
            plan_date_key="2026-04-15",
            status="ready",
            stage="daily_loop_ready",
            session_kind="recommended",
            focus_area="grammar",
            headline="Return to the wider route",
            summary="The reopened support can stay available, but the broader daily route should lead again.",
            why_this_now="The reopen arc is ready to widen, so the broader route can lead again.",
            next_step_hint="Return to the broader daily route while keeping writing support available.",
            preferred_mode="mixed",
            time_budget_minutes=20,
            estimated_minutes=20,
            recommended_lesson_type="mixed",
            recommended_lesson_title="Return to the wider route",
            lesson_run_id=None,
            completed_at=None,
            steps=[],
        ),
        profile=_build_profile(),
    )

    assert alignment is not None
    assert alignment.route_recovery_memory is not None
    assert alignment.route_recovery_memory.reopen_stage == "ready_to_expand"
    assert alignment.recommended_module_key == "lesson"
    assert "wider" in (alignment.recommended_module_reason or "").lower() or "widen" in (alignment.recommended_module_reason or "").lower()
