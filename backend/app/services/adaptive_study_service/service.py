from __future__ import annotations

from datetime import datetime

from app.core.errors import ServiceUnavailableError
from app.repositories.lesson_repository import LessonRepository
from app.repositories.lesson_runtime_repository import LessonRuntimeRepository
from app.repositories.mistake_repository import MistakeRepository, WEAK_SPOT_TITLE_MAP
from app.repositories.progress_repository import ProgressRepository
from app.repositories.recommendation_repository import RecommendationRepository
from app.repositories.vocabulary_repository import VocabularyRepository
from app.schemas.lesson import LessonRunState
from app.schemas.adaptive import (
    AdaptiveLoopStep,
    AdaptiveStudyLoop,
    MistakeResolutionSignal,
    MistakeVocabularyBacklink,
    ModuleRotationItem,
    VocabularyHub,
    VocabularyLoopSummary,
    VocabularyReviewItem,
)
from app.schemas.mistake import Mistake
from app.schemas.profile import UserProfile


class AdaptiveStudyService:
    def __init__(
        self,
        lesson_repository: LessonRepository,
        lesson_runtime_repository: LessonRuntimeRepository,
        recommendation_repository: RecommendationRepository,
        mistake_repository: MistakeRepository,
        progress_repository: ProgressRepository,
        vocabulary_repository: VocabularyRepository,
    ) -> None:
        self._lesson_repository = lesson_repository
        self._lesson_runtime_repository = lesson_runtime_repository
        self._recommendation_repository = recommendation_repository
        self._mistake_repository = mistake_repository
        self._progress_repository = progress_repository
        self._vocabulary_repository = vocabulary_repository

    def get_loop(self, profile: UserProfile) -> AdaptiveStudyLoop | None:
        recommendation = self._recommendation_repository.get_next_step(profile)
        if recommendation is None:
            return None

        weak_spots = self._mistake_repository.list_weak_spots(profile.id, limit=3)
        mistakes = self._mistake_repository.list_mistakes(profile.id)
        progress = self._progress_repository.get_latest_snapshot(profile.id)
        recent_lessons = self._lesson_repository.list_recent_completed_lessons(profile.id, limit=3)
        due_vocabulary = self._vocabulary_repository.list_due_items(profile.id, limit=4)
        vocabulary_summary = self._vocabulary_repository.get_summary(profile.id)
        vocabulary_backlinks = self._vocabulary_repository.list_mistake_backlinks(profile.id, limit=4)
        mistake_resolution = self._build_mistake_resolution(mistakes, vocabulary_backlinks)
        listening_focus = self._detect_listening_focus(progress, weak_spots)
        module_rotation = self._build_module_rotation(
            recommendation_lesson_type=recommendation.lesson_type,
            recommendation_focus_area=recommendation.focus_area,
            recent_lessons=recent_lessons,
            due_vocabulary=due_vocabulary,
            listening_focus=listening_focus,
            mistake_resolution=mistake_resolution,
        )

        focus_area = weak_spots[0].category if weak_spots else recommendation.focus_area
        headline = self._build_headline(profile.name, focus_area)
        generation_rationale = self._build_generation_rationale(
            recommendation.lesson_type,
            weak_spots,
            vocabulary_summary,
            listening_focus,
            mistake_resolution,
        )
        summary = self._build_summary(
            weak_spots,
            due_vocabulary,
            progress.minutes_completed_today if progress else 0,
            listening_focus,
            vocabulary_summary,
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
            next_steps=self._build_next_steps(
                recommendation.lesson_type,
                focus_area,
                due_vocabulary,
                listening_focus,
                module_rotation,
            ),
        )

    def review_vocabulary(self, user_id: str, item_id: str, successful: bool) -> VocabularyReviewItem | None:
        return self._vocabulary_repository.review_item(user_id, item_id, successful)

    def get_vocabulary_hub(self, user_id: str) -> VocabularyHub:
        return VocabularyHub(
            summary=self._vocabulary_repository.get_summary(user_id),
            due_items=self._vocabulary_repository.list_due_items(user_id, limit=12),
            recent_items=self._vocabulary_repository.list_recent_items(user_id, limit=10),
            mistake_backlinks=self._vocabulary_repository.list_mistake_backlinks(user_id, limit=6),
        )

    def start_recovery_run(self, profile: UserProfile) -> LessonRunState:
        loop = self.get_loop(profile)
        if loop is None:
            raise ServiceUnavailableError("Adaptive study loop is not available.")

        template = self._lesson_repository.create_recovery_template(
            profession_track=profile.profession_track,
            weak_spots=loop.weak_spots,
            due_vocabulary=loop.due_vocabulary,
            listening_focus=loop.listening_focus,
        )
        lesson_run = self._lesson_runtime_repository.start_lesson_run(
            user_id=profile.id,
            profession_track=profile.profession_track,
            template_id=template.id,
        )
        if lesson_run is None:
            raise ServiceUnavailableError("Recovery lesson could not be generated.")

        return lesson_run

    @staticmethod
    def _build_headline(name: str, focus_area: str) -> str:
        return f"{name}, today's adaptive focus is {focus_area.replace('_', ' ')}."

    @staticmethod
    def _build_summary(weak_spots: list, due_vocabulary: list, minutes_completed_today: int) -> str:
        weak_spot_summary = weak_spots[0].title if weak_spots else "current lesson momentum"
        due_words = len(due_vocabulary)
        return (
            f"Start from {weak_spot_summary}, keep the daily chain moving, "
            f"and clear {due_words} vocabulary review item{'s' if due_words != 1 else ''}. "
            f"Minutes completed today: {minutes_completed_today}."
        )
    @staticmethod
    def _build_summary(
        weak_spots: list,
        due_vocabulary: list,
        minutes_completed_today: int,
        listening_focus: str | None,
        vocabulary_summary: VocabularyLoopSummary,
    ) -> str:
        weak_spot_summary = weak_spots[0].title if weak_spots else "current lesson momentum"
        due_words = len(due_vocabulary)
        listening_part = (
            f" Listening also needs support around {listening_focus.replace('_', ' ')}."
            if listening_focus
            else ""
        )
        vocabulary_part = (
            f" Vocabulary queue: {vocabulary_summary.active_count} active, {vocabulary_summary.mastered_count} mastered."
        )
        return (
            f"Start from {weak_spot_summary}, keep the daily chain moving, "
            f"and clear {due_words} vocabulary review item{'s' if due_words != 1 else ''}."
            f"{listening_part}{vocabulary_part} Minutes completed today: {minutes_completed_today}."
        )

    @staticmethod
    def _detect_listening_focus(progress, weak_spots: list) -> str | None:
        if any(getattr(spot, "category", "") == "listening" for spot in weak_spots):
            return "audio_comprehension"
        if progress is None:
            return None
        if progress.listening_score <= 55:
            return "audio_comprehension"
        if progress.listening_score < min(progress.speaking_score or 100, progress.writing_score or 100):
            return "detail_capture"
        return None

    @staticmethod
    def _build_generation_rationale(
        recommendation_lesson_type: str,
        weak_spots: list,
        vocabulary_summary: VocabularyLoopSummary,
        listening_focus: str | None,
        mistake_resolution: list[MistakeResolutionSignal],
    ) -> list[str]:
        rationale: list[str] = []
        state_seed = (
            recommendation_lesson_type,
            weak_spots[0].title if weak_spots else "none",
            vocabulary_summary.due_count,
            vocabulary_summary.active_count,
            listening_focus or "none",
            "-".join(item.status for item in mistake_resolution[:2]) or "none",
        )
        if weak_spots:
            rationale.append(
                AdaptiveStudyService._pick_variant(
                    [
                        f"Primary weak spot: {weak_spots[0].title}.",
                        f"Current correction pressure is centered on {weak_spots[0].title}.",
                        f"The loop is still anchored around {weak_spots[0].title}.",
                    ],
                    *state_seed,
                    "weak-spot",
                )
            )
        recovering = [item.weak_spot_title for item in mistake_resolution if item.status in {"recovering", "stabilizing"}]
        if recovering:
            easing_targets = ", ".join(recovering[:2])
            rationale.append(
                AdaptiveStudyService._pick_variant(
                    [
                        f"Recovery pressure is easing for: {easing_targets}.",
                        f"These weak spots are starting to settle: {easing_targets}.",
                        f"Repair intensity can relax a little around: {easing_targets}.",
                    ],
                    *state_seed,
                    easing_targets,
                    "recovery-easing",
                )
            )
        if listening_focus:
            rationale.append(
                AdaptiveStudyService._pick_variant(
                    [
                        f"Listening support added for {listening_focus.replace('_', ' ')}.",
                        f"An audio-first support layer was added for {listening_focus.replace('_', ' ')}.",
                        f"The loop keeps a listening assist focused on {listening_focus.replace('_', ' ')}.",
                    ],
                    *state_seed,
                    listening_focus,
                    "listening",
                )
            )
        if vocabulary_summary.due_count > 0:
            due_label = f"{vocabulary_summary.due_count} due item{'s' if vocabulary_summary.due_count != 1 else ''}"
            rationale.append(
                AdaptiveStudyService._pick_variant(
                    [
                        f"Vocabulary queue has {due_label}.",
                        f"The repetition queue is carrying {due_label}.",
                        f"Vocabulary review is still live with {due_label}.",
                    ],
                    *state_seed,
                    vocabulary_summary.due_count,
                    "vocabulary-due",
                )
            )
        if vocabulary_summary.weakest_category:
            rationale.append(
                AdaptiveStudyService._pick_variant(
                    [
                        f"Most overloaded vocabulary category: {vocabulary_summary.weakest_category}.",
                        f"The heaviest vocabulary carry-over is in {vocabulary_summary.weakest_category}.",
                        f"Vocabulary pressure is leaning most toward {vocabulary_summary.weakest_category}.",
                    ],
                    *state_seed,
                    vocabulary_summary.weakest_category,
                    "vocabulary-category",
                )
            )
        rationale.append(
            AdaptiveStudyService._pick_variant(
                [
                    "Next lesson generation is recovery-first.",
                    "The next generated step still opens with recovery work.",
                    "The loop is keeping recovery at the front of the next generated lesson.",
                ],
                *state_seed,
                "track-recovery",
            )
            if recommendation_lesson_type == "recovery"
            else AdaptiveStudyService._pick_variant(
                [
                    "Next lesson generation returns to the main track.",
                    "The next generated step leans back into the main lesson flow.",
                    "The loop is ready to move back toward the broader lesson track.",
                ],
                *state_seed,
                "track-main",
            )
        )
        return rationale

    @staticmethod
    def _build_module_rotation(
        recommendation_lesson_type: str,
        recommendation_focus_area: str,
        recent_lessons: list,
        due_vocabulary: list[VocabularyReviewItem],
        listening_focus: str | None,
        mistake_resolution: list[MistakeResolutionSignal],
    ) -> list[ModuleRotationItem]:
        recent_types = [item.lesson_type for item in recent_lessons[:2]]
        repeated_lesson_pressure = sum(1 for item in recent_types if item in {"mixed", "grammar", "professional", "writing", "diagnostic", "recovery"})
        easing_recovery = any(item.status in {"recovering", "stabilizing"} for item in mistake_resolution)

        candidates: list[tuple[str, int, str, str]] = []
        lesson_penalty = 3 if repeated_lesson_pressure >= 1 and easing_recovery else 1
        candidates.append(
            (
                "lesson",
                lesson_penalty,
                "Return to the main lesson flow",
                "Use the broader lesson track to keep corrected patterns alive in context.",
            )
        )

        speaking_priority = 0 if recommendation_focus_area in {"speaking", "grammar", "profession"} or easing_recovery else 2
        candidates.append(
            (
                "speaking",
                speaking_priority,
                "Speaking refresh",
                "Short guided speaking keeps the corrected pattern active without forcing a full recovery loop.",
            )
        )

        if due_vocabulary:
            candidates.append(
                (
                    "vocabulary",
                    0,
                    "Vocabulary repetition",
                    f"Review {len(due_vocabulary)} due item{'s' if len(due_vocabulary) != 1 else ''} before the next larger module.",
                )
            )

        if listening_focus:
            candidates.append(
                (
                    "listening",
                    1 if easing_recovery else 0,
                    "Listening support",
                    f"Add one short audio-first support block for {listening_focus.replace('_', ' ')}.",
                )
            )

        if recommendation_lesson_type == "recovery":
            candidates.insert(
                0,
                (
                    "recovery",
                    -1,
                    "Recovery lesson",
                    "Use the focused recovery block first, then rotate back into the broader flow.",
                ),
            )

        ranked = sorted(candidates, key=lambda item: item[1])
        route_map = {
            "recovery": "/lesson-runner",
            "lesson": "/lesson-runner",
            "speaking": "/speaking",
            "vocabulary": "/vocabulary",
            "listening": "/activity",
        }

        return [
            ModuleRotationItem(
                module_key=module_key,
                title=title,
                reason=reason,
                route=route_map[module_key],
                priority=index + 1,
            )
            for index, (module_key, _score, title, reason) in enumerate(ranked)
        ]

    @staticmethod
    def _build_mistake_resolution(
        mistakes: list[Mistake],
        vocabulary_backlinks: list[MistakeVocabularyBacklink],
        limit: int = 4,
    ) -> list[MistakeResolutionSignal]:
        if not mistakes:
            return []

        backlink_map = {item.weak_spot_title: item for item in vocabulary_backlinks}
        now = datetime.utcnow()
        ranked = sorted(mistakes, key=lambda item: item.repetition_count, reverse=True)[:limit]
        signals: list[MistakeResolutionSignal] = []

        for mistake in ranked:
            title = WEAK_SPOT_TITLE_MAP.get(mistake.subtype, mistake.subtype.replace("-", " ").title())
            backlink = backlink_map.get(title)
            linked_vocabulary_count = backlink.active_count if backlink else 0
            last_seen_days_ago = max(0, (now - mistake.last_seen_at.replace(tzinfo=None)).days)

            if linked_vocabulary_count >= 2 and last_seen_days_ago >= 5:
                status = "stabilizing"
                hint = "This weak spot has moved into vocabulary review and has not resurfaced recently."
            elif linked_vocabulary_count >= 1 and last_seen_days_ago >= 2:
                status = "recovering"
                hint = "The pattern is still being reviewed, but it is appearing less often in fresh corrections."
            else:
                status = "active"
                hint = "This weak spot is still repeating often enough that it should stay in active recovery."

            signals.append(
                MistakeResolutionSignal(
                    weak_spot_title=title,
                    weak_spot_category=mistake.category,
                    status=status,
                    repetition_count=mistake.repetition_count,
                    last_seen_days_ago=last_seen_days_ago,
                    linked_vocabulary_count=linked_vocabulary_count,
                    resolution_hint=hint,
                )
            )

        return signals

    @staticmethod
    def _build_next_steps(
        recommendation_lesson_type: str,
        focus_area: str,
        due_vocabulary: list[VocabularyReviewItem],
        listening_focus: str | None,
        module_rotation: list[ModuleRotationItem],
    ) -> list[AdaptiveLoopStep]:
        steps: list[AdaptiveLoopStep] = []
        if module_rotation and recommendation_lesson_type != "recovery":
            for item in module_rotation[:3]:
                steps.append(
                    AdaptiveLoopStep(
                        id=f"adaptive-rotation-{item.module_key}",
                        title=item.title,
                        description=item.reason,
                        route=item.route,
                        step_type=item.module_key,
                    )
                )
            return steps

        if recommendation_lesson_type == "recovery":
            steps.append(
                AdaptiveLoopStep(
                    id="adaptive-step-recovery",
                    title="Recover your main weak spot",
                    description=f"Open a focused drill for {focus_area.replace('_', ' ')} and fix the repeated pattern.",
                    route="/lesson-runner",
                    step_type="recovery",
                )
            )
        else:
            steps.append(
                AdaptiveLoopStep(
                    id="adaptive-step-lesson",
                    title="Return to the main track",
                    description="Use the corrected pattern inside a fuller lesson so recovery turns into stable progress.",
                    route="/lesson-runner",
                    step_type="lesson",
                )
            )
        if due_vocabulary:
            steps.append(
                AdaptiveLoopStep(
                    id="adaptive-step-vocabulary",
                    title="Review due vocabulary",
                    description=f"Repeat {len(due_vocabulary)} words before the next full lesson block.",
                    route="/activity",
                    step_type="vocabulary",
                ),
            )
        if listening_focus:
            steps.append(
                AdaptiveLoopStep(
                    id="adaptive-step-listening",
                    title="Reinforce listening detail",
                    description=f"Use one short audio-first block to stabilize {listening_focus.replace('_', ' ')} before the next full lesson.",
                    route="/lesson-runner",
                    step_type="listening",
                )
            )
        if recommendation_lesson_type == "recovery":
            steps.append(
                AdaptiveLoopStep(
                    id="adaptive-step-lesson",
                    title="Continue with the recommended lesson",
                    description="Move forward after recovery so the app keeps pushing the long-term track ahead.",
                    route="/lesson-runner",
                    step_type="lesson",
                )
            )
        else:
            steps.append(
                AdaptiveLoopStep(
                    id="adaptive-step-progress",
                    title="Check the refreshed roadmap",
                    description="Confirm that the loop has shifted and keep following the next recommendation.",
                    route="/dashboard",
                    step_type="roadmap",
                )
            )
        return steps

    @staticmethod
    def _pick_variant(variants: list[str], *seed_parts: object) -> str:
        if not variants:
            return ""
        seed = "|".join(str(part) for part in seed_parts if part is not None)
        if not seed:
            return variants[0]
        weighted_seed = sum((index + 1) * ord(char) for index, char in enumerate(seed))
        index = (weighted_seed + len(seed_parts) * 17) % len(variants)
        return variants[index]
