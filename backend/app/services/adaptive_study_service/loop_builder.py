from __future__ import annotations

from app.schemas.adaptive import (
    AdaptiveStrategyAlignment,
    AdaptiveStudyLoop,
    MistakeVocabularyBacklink,
    MistakeResolutionSignal,
    VocabularyLoopSummary,
    VocabularyReviewItem,
)
from app.schemas.lesson import LessonRecommendation
from app.schemas.mistake import Mistake, WeakSpot
from app.schemas.profile import UserProfile
from app.schemas.progress import LessonHistoryItem, ProgressSnapshot
from app.services.adaptive_study_service.loop_copy import (
    build_generation_rationale,
    build_headline,
    build_summary,
)
from app.services.adaptive_study_service.loop_heuristics import (
    build_mistake_resolution,
    detect_listening_focus,
)
from app.services.adaptive_study_service.loop_rotation import (
    build_module_rotation,
    build_next_steps,
)


def build_adaptive_study_loop(
    profile: UserProfile,
    recommendation: LessonRecommendation,
    weak_spots: list[WeakSpot],
    mistakes: list[Mistake],
    progress: ProgressSnapshot | None,
    recent_lessons: list[LessonHistoryItem],
    due_vocabulary: list[VocabularyReviewItem],
    vocabulary_summary: VocabularyLoopSummary,
    vocabulary_backlinks: list[MistakeVocabularyBacklink],
    strategy_alignment: AdaptiveStrategyAlignment | None = None,
) -> AdaptiveStudyLoop:
    mistake_resolution = build_mistake_resolution(mistakes, vocabulary_backlinks)
    listening_focus = detect_listening_focus(progress, weak_spots)
    module_rotation = build_module_rotation(
        recommendation_lesson_type=recommendation.lesson_type,
        recommendation_focus_area=recommendation.focus_area,
        recent_lessons=recent_lessons,
        due_vocabulary=due_vocabulary,
        listening_focus=listening_focus,
        mistake_resolution=mistake_resolution,
    )

    focus_area = weak_spots[0].category if weak_spots else recommendation.focus_area
    headline = build_headline(profile.name, focus_area)
    summary = build_summary(
        weak_spots=weak_spots,
        due_vocabulary=due_vocabulary,
        minutes_completed_today=progress.minutes_completed_today if progress else 0,
        listening_focus=listening_focus,
        vocabulary_summary=vocabulary_summary,
    )
    generation_rationale = build_generation_rationale(
        recommendation_lesson_type=recommendation.lesson_type,
        weak_spots=weak_spots,
        vocabulary_summary=vocabulary_summary,
        listening_focus=listening_focus,
        mistake_resolution=mistake_resolution,
    )

    return AdaptiveStudyLoop(
        focus_area=focus_area,
        headline=headline,
        summary=summary,
        recommendation=recommendation,
        weak_spots=weak_spots,
        due_vocabulary=due_vocabulary,
        vocabulary_backlinks=vocabulary_backlinks,
        mistake_resolution=mistake_resolution,
        module_rotation=module_rotation,
        vocabulary_summary=vocabulary_summary,
        listening_focus=listening_focus,
        generation_rationale=generation_rationale,
        next_steps=build_next_steps(
            recommendation_lesson_type=recommendation.lesson_type,
            focus_area=focus_area,
            due_vocabulary=due_vocabulary,
            listening_focus=listening_focus,
            module_rotation=module_rotation,
        ),
        strategy_alignment=strategy_alignment,
    )


def derive_generation_rationale(
    recommendation_lesson_type: str,
    weak_spots: list[WeakSpot],
    vocabulary_summary: VocabularyLoopSummary,
    listening_focus: str | None,
    mistake_resolution: list[MistakeResolutionSignal],
) -> list[str]:
    return build_generation_rationale(
        recommendation_lesson_type=recommendation_lesson_type,
        weak_spots=weak_spots,
        vocabulary_summary=vocabulary_summary,
        listening_focus=listening_focus,
        mistake_resolution=mistake_resolution,
    )
