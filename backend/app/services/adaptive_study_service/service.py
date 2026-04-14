from __future__ import annotations

from datetime import datetime

from app.core.errors import ServiceUnavailableError
from app.repositories.journey_repository import JourneyRepository
from app.repositories.lesson_repository import LessonRepository
from app.repositories.lesson_runtime_repository import LessonRuntimeRepository
from app.repositories.mistake_repository import MistakeRepository
from app.repositories.progress_repository import ProgressRepository
from app.repositories.recommendation_repository import RecommendationRepository
from app.repositories.vocabulary_repository import VocabularyRepository
from app.schemas.adaptive import (
    AdaptiveStrategyAlignment,
    AdaptiveStudyLoop,
    MistakeResolutionSignal,
    VocabularyHub,
    VocabularyLoopSummary,
    VocabularyReviewItem,
)
from app.schemas.lesson import LessonRunState
from app.schemas.mistake import WeakSpot
from app.schemas.profile import UserProfile
from app.schemas.journey import DailyLoopPlan, LearnerJourneyState
from app.services.adaptive_study_service.loop_builder import (
    build_adaptive_study_loop,
    derive_generation_rationale,
)
from app.services.adaptive_study_service.loop_heuristics import detect_progress_focus
from app.services.adaptive_study_service.loop_heuristics import build_progress_trajectory
from app.services.adaptive_study_service.loop_heuristics import build_progress_score_map
from app.services.adaptive_study_service.vocabulary_hub_builder import build_vocabulary_hub
from app.services.recommendation_service.service import RecommendationService


class AdaptiveStudyService:
    def __init__(
        self,
        lesson_repository: LessonRepository,
        lesson_runtime_repository: LessonRuntimeRepository,
        recommendation_service: RecommendationService | RecommendationRepository,
        mistake_repository: MistakeRepository,
        progress_repository: ProgressRepository,
        vocabulary_repository: VocabularyRepository,
        journey_repository: JourneyRepository | None = None,
    ) -> None:
        self._lesson_repository = lesson_repository
        self._lesson_runtime_repository = lesson_runtime_repository
        self._recommendation_service = recommendation_service
        self._mistake_repository = mistake_repository
        self._progress_repository = progress_repository
        self._vocabulary_repository = vocabulary_repository
        self._journey_repository = journey_repository

    def get_loop(self, profile: UserProfile) -> AdaptiveStudyLoop | None:
        recommendation = self._recommendation_service.get_next_step(profile)
        if recommendation is None:
            return None

        weak_spots = self._mistake_repository.list_weak_spots(profile.id, limit=3)
        mistakes = self._mistake_repository.list_mistakes(profile.id)
        progress = self._progress_repository.get_latest_snapshot(profile.id)
        recent_progress = self._progress_repository.list_recent_snapshots(profile.id, limit=3)
        recent_lessons = self._lesson_repository.list_recent_completed_lessons(profile.id, limit=3)
        due_vocabulary = self._vocabulary_repository.list_due_items(profile.id, limit=4)
        vocabulary_summary = self._vocabulary_repository.get_summary(profile.id)
        vocabulary_backlinks = self._vocabulary_repository.list_mistake_backlinks(profile.id, limit=4)
        journey_state = self._journey_repository.get_journey_state(profile.id) if self._journey_repository else None
        daily_loop_plan = (
            self._journey_repository.get_daily_loop_plan(profile.id, datetime.utcnow().date().isoformat())
            if self._journey_repository
            else None
        )
        module_rotation = build_adaptive_study_loop(
            profile=profile,
            recommendation=recommendation,
            weak_spots=weak_spots,
            mistakes=mistakes,
            progress=progress,
            recent_lessons=recent_lessons,
            due_vocabulary=due_vocabulary,
            vocabulary_summary=vocabulary_summary,
            vocabulary_backlinks=vocabulary_backlinks,
            strategy_alignment=self._build_strategy_alignment(
                recommendation=recommendation,
                weak_spots=weak_spots,
                due_vocabulary=due_vocabulary,
                progress=progress,
                recent_progress=recent_progress,
                journey_state=journey_state,
                daily_loop_plan=daily_loop_plan,
                profile=profile,
            ),
        )

        return module_rotation

    def review_vocabulary(self, user_id: str, item_id: str, successful: bool) -> VocabularyReviewItem | None:
        return self._vocabulary_repository.review_item(user_id, item_id, successful)

    def get_vocabulary_hub(self, user_id: str) -> VocabularyHub:
        return build_vocabulary_hub(
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
    def _build_generation_rationale(
        recommendation_lesson_type: str,
        weak_spots: list[WeakSpot],
        vocabulary_summary: VocabularyLoopSummary,
        listening_focus: str | None,
        mistake_resolution: list[MistakeResolutionSignal],
    ) -> list[str]:
        return derive_generation_rationale(
            recommendation_lesson_type=recommendation_lesson_type,
            weak_spots=weak_spots,
            vocabulary_summary=vocabulary_summary,
            listening_focus=listening_focus,
            mistake_resolution=mistake_resolution,
        )

    @staticmethod
    def _build_strategy_alignment(
        *,
        recommendation,
        weak_spots: list[WeakSpot],
        due_vocabulary: list[VocabularyReviewItem],
        progress,
        recent_progress,
        journey_state: LearnerJourneyState | None,
        daily_loop_plan: DailyLoopPlan | None,
        profile: UserProfile,
    ) -> AdaptiveStrategyAlignment | None:
        if not journey_state and not daily_loop_plan:
            return None

        snapshot = journey_state.strategy_snapshot if journey_state else {}
        session_summary = snapshot.get("sessionSummary") if isinstance(snapshot.get("sessionSummary"), dict) else None
        active_plan_seed = snapshot.get("activePlanSeed") if isinstance(snapshot.get("activePlanSeed"), dict) else None
        carry_over_label = (
            str(session_summary.get("carryOverSignalLabel"))
            if session_summary and session_summary.get("carryOverSignalLabel")
            else None
        )
        watch_signal_label = (
            str(session_summary.get("watchSignalLabel"))
            if session_summary and session_summary.get("watchSignalLabel")
            else weak_spots[0].title if weak_spots else None
        )
        route_seed_source = (
            str(active_plan_seed.get("source"))
            if active_plan_seed and active_plan_seed.get("source")
            else "daily_loop_plan"
            if daily_loop_plan
            else "recommendation"
        )
        route_seed_detail = (
            session_summary.get("headline")
            if session_summary and session_summary.get("headline")
            else daily_loop_plan.why_this_now
            if daily_loop_plan
            else recommendation.goal
        )
        why_now = (
            daily_loop_plan.why_this_now
            if daily_loop_plan
            else journey_state.current_strategy_summary
            if journey_state
            else recommendation.goal
        )
        next_best_action = (
            journey_state.next_best_action
            if journey_state
            else daily_loop_plan.next_step_hint
            if daily_loop_plan
            else recommendation.goal
        )
        progress_focus = detect_progress_focus(progress, profile.onboarding_answers.active_skill_focus)
        progress_score_map = build_progress_score_map(progress)
        trajectory = build_progress_trajectory(recent_progress, profile.onboarding_answers.active_skill_focus)
        recommended_module_key = (
            weak_spots[0].category
            if weak_spots
            else progress_focus
            or (trajectory.focus_skill if trajectory else None)
            or recommendation.focus_area.split(",")[0]
        )
        recommended_module_reason = (
            weak_spots[0].recommendation
            if weak_spots
            else trajectory.summary
            if trajectory and not progress_focus
            else f"Keep the route centered on {progress_focus or recommendation.focus_area}."
        )
        if due_vocabulary and not weak_spots:
            recommended_module_key = "vocabulary"
            recommended_module_reason = f"Keep {due_vocabulary[0].word} active so the route stays sticky."

        return AdaptiveStrategyAlignment(
            focus_area=daily_loop_plan.focus_area if daily_loop_plan else journey_state.current_focus_area if journey_state else recommendation.focus_area,
            route_title=daily_loop_plan.recommended_lesson_title if daily_loop_plan else recommendation.title,
            route_seed_source=route_seed_source,
            route_seed_detail=str(route_seed_detail),
            why_now=str(why_now),
            next_best_action=str(next_best_action),
            carry_over_signal_label=carry_over_label,
            watch_signal_label=watch_signal_label,
            recommended_module_key=recommended_module_key,
            recommended_module_reason=recommended_module_reason,
            live_progress_focus=progress_focus,
            live_progress_score=progress_score_map.get(progress_focus, 0) if progress_focus else None,
            live_progress_reason=(
                f"Fresh progress is currently weakest in {progress_focus}, so the adaptive route is leaning there before it widens again."
                if progress_focus
                else None
            ),
            skill_trajectory=trajectory,
        )
