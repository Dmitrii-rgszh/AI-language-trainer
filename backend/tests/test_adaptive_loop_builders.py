from datetime import datetime

from app.schemas.adaptive import (
    MistakeResolutionSignal,
    MistakeVocabularyBacklink,
    VocabularyHub,
    VocabularyLoopSummary,
    VocabularyReviewItem,
)
from app.schemas.lesson import LessonRecommendation
from app.schemas.mistake import Mistake, WeakSpot
from app.schemas.profile import OnboardingAnswers, UserProfile
from app.schemas.progress import LessonHistoryItem, ProgressSnapshot
from app.services.adaptive_study_service.loop_builder import (
    build_adaptive_study_loop,
    derive_generation_rationale,
)
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
