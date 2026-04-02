from app.schemas.adaptive import MistakeResolutionSignal, VocabularyLoopSummary, VocabularyReviewItem
from app.schemas.mistake import WeakSpot
from app.services.adaptive_study_service.headline_builder import build_headline
from app.services.adaptive_study_service.loop_copy import (
    build_generation_rationale as facade_build_generation_rationale,
)
from app.services.adaptive_study_service.loop_copy import (
    build_headline as facade_build_headline,
)
from app.services.adaptive_study_service.loop_copy import (
    build_summary as facade_build_summary,
)
from app.services.adaptive_study_service.rationale_builder import build_generation_rationale
from app.services.adaptive_study_service.summary_builder import build_summary


def test_adaptive_copy_facade_reexports_builder_functions() -> None:
    assert facade_build_headline is build_headline
    assert facade_build_summary is build_summary
    assert facade_build_generation_rationale is build_generation_rationale


def test_build_headline_and_summary_return_consistent_copy() -> None:
    headline = build_headline("Nina", "profession_english")
    summary = build_summary(
        weak_spots=[
            WeakSpot(
                id="weak-1",
                title="Present Perfect vs Past Simple",
                category="grammar",
                recommendation="Review tense contrast.",
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
        minutes_completed_today=12,
        listening_focus="audio_comprehension",
        vocabulary_summary=VocabularyLoopSummary(
            due_count=1,
            new_count=0,
            active_count=3,
            mastered_count=1,
            weakest_category="grammar",
        ),
    )

    assert "profession english" in headline
    assert "Present Perfect vs Past Simple" in summary
    assert "Minutes completed today: 12." in summary


def test_build_generation_rationale_mentions_active_signals() -> None:
    rationale = build_generation_rationale(
        recommendation_lesson_type="recovery",
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
    assert any("Present Perfect vs Past Simple" in line for line in rationale)
