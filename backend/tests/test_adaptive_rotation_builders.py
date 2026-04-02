from app.schemas.adaptive import MistakeResolutionSignal, VocabularyReviewItem
from app.schemas.progress import LessonHistoryItem
from app.services.adaptive_study_service.loop_rotation import (
    build_module_rotation as facade_build_module_rotation,
)
from app.services.adaptive_study_service.loop_rotation import (
    build_next_steps as facade_build_next_steps,
)
from app.services.adaptive_study_service.next_steps_builder import build_next_steps
from app.services.adaptive_study_service.rotation_builder import build_module_rotation


def _build_due_vocabulary() -> list[VocabularyReviewItem]:
    return [
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
    ]


def test_adaptive_rotation_facade_reexports_builder_functions() -> None:
    assert facade_build_module_rotation is build_module_rotation
    assert facade_build_next_steps is build_next_steps


def test_build_module_rotation_prioritizes_recovery_and_due_vocabulary() -> None:
    rotation = build_module_rotation(
        recommendation_lesson_type="recovery",
        recommendation_focus_area="grammar",
        recent_lessons=[
            LessonHistoryItem(
                id="history-1",
                title="Warmup",
                lesson_type="recovery",
                completed_at="2026-04-01",
                score=74,
            )
        ],
        due_vocabulary=_build_due_vocabulary(),
        listening_focus="audio_comprehension",
        mistake_resolution=[
            MistakeResolutionSignal(
                weak_spot_title="Present Perfect vs Past Simple",
                weak_spot_category="grammar",
                status="recovering",
                repetition_count=2,
                last_seen_days_ago=3,
                linked_vocabulary_count=1,
                resolution_hint="Pattern is easing.",
            )
        ],
    )

    assert rotation
    assert rotation[0].module_key == "recovery"
    assert any(item.module_key == "vocabulary" for item in rotation)


def test_build_next_steps_uses_rotation_for_non_recovery_mode() -> None:
    steps = build_next_steps(
        recommendation_lesson_type="lesson",
        focus_area="grammar",
        due_vocabulary=_build_due_vocabulary(),
        listening_focus=None,
        module_rotation=build_module_rotation(
            recommendation_lesson_type="lesson",
            recommendation_focus_area="grammar",
            recent_lessons=[],
            due_vocabulary=_build_due_vocabulary(),
            listening_focus=None,
            mistake_resolution=[],
        ),
    )

    assert steps
    assert steps[0].id.startswith("adaptive-rotation-")
