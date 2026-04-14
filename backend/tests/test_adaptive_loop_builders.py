from datetime import datetime

from app.schemas.adaptive import (
    MistakeResolutionSignal,
    MistakeVocabularyBacklink,
    VocabularyHub,
    VocabularyLoopSummary,
    VocabularyReviewItem,
)
from app.schemas.journey import DailyLoopPlan, DailyLoopStep
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
