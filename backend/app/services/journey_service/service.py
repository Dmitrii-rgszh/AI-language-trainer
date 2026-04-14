from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.core.errors import NotFoundError, ServiceUnavailableError
from app.repositories.journey_repository import JourneyRepository
from app.repositories.lesson_repository import LessonRepository
from app.repositories.lesson_runtime_repository import LessonRuntimeRepository
from app.repositories.mistake_repository import MistakeRepository
from app.repositories.vocabulary_repository import VocabularyRepository
from app.schemas.journey import (
    DailyLoopPlan,
    LearnerJourneyState,
    OnboardingSession,
    SaveOnboardingSessionDraftRequest,
    StartOnboardingSessionRequest,
)
from app.schemas.lesson import LessonRecommendation, LessonRunState
from app.schemas.mistake import WeakSpot
from app.schemas.profile import UserProfile
from app.services.adaptive_study_service.rotation_builder import build_module_rotation
from app.services.recommendation_service.service import RecommendationService


@dataclass(frozen=True)
class JourneyCompletionResult:
    session: OnboardingSession | None
    journey_state: LearnerJourneyState
    daily_loop_plan: DailyLoopPlan


class JourneyService:
    def __init__(
        self,
        repository: JourneyRepository,
        lesson_repository: LessonRepository,
        lesson_runtime_repository: LessonRuntimeRepository,
        recommendation_service: RecommendationService,
        mistake_repository: MistakeRepository,
        vocabulary_repository: VocabularyRepository,
    ) -> None:
        self._repository = repository
        self._lesson_repository = lesson_repository
        self._lesson_runtime_repository = lesson_runtime_repository
        self._recommendation_service = recommendation_service
        self._mistake_repository = mistake_repository
        self._vocabulary_repository = vocabulary_repository

    def start_onboarding_session(self, payload: StartOnboardingSessionRequest) -> OnboardingSession:
        return self._repository.create_onboarding_session(
            source=payload.source,
            proof_lesson_handoff=(
                payload.proof_lesson_handoff.model_dump(mode="json")
                if payload.proof_lesson_handoff
                else None
            ),
        )

    def get_onboarding_session(self, session_id: str) -> OnboardingSession:
        session = self._repository.get_onboarding_session(session_id)
        if session is None:
            raise NotFoundError("Onboarding session was not found.")
        return session

    def save_onboarding_draft(
        self,
        session_id: str,
        payload: SaveOnboardingSessionDraftRequest,
    ) -> OnboardingSession:
        session = self._repository.save_onboarding_draft(
            session_id,
            account_draft=payload.account_draft.model_dump(mode="json"),
            profile_draft=payload.profile_draft.model_dump(mode="json"),
            current_step=payload.current_step,
        )
        if session is None:
            raise NotFoundError("Onboarding session was not found.")
        return session

    def finalize_onboarding(
        self,
        *,
        user_id: str,
        profile: UserProfile,
        session_id: str | None = None,
    ) -> JourneyCompletionResult:
        session = None
        if session_id:
            session = self._repository.complete_onboarding_session(session_id, user_id)

        recommendation = self._recommendation_service.get_next_step(profile)
        focus_area = self._determine_focus_area(profile, session, recommendation)
        preferred_mode = profile.onboarding_answers.preferred_mode
        diagnostic_readiness = profile.onboarding_answers.diagnostic_readiness
        source = session.source if session else "direct_onboarding"

        daily_loop_plan = self._ensure_today_plan(
            profile,
            session=session,
            recommendation=recommendation,
            focus_area=focus_area,
            stage="first_path",
        )
        journey_state = self._repository.upsert_journey_state(
            user_id=user_id,
            stage="daily_loop_ready",
            source=source,
            preferred_mode=preferred_mode,
            diagnostic_readiness=diagnostic_readiness,
            time_budget_minutes=profile.lesson_duration,
            current_focus_area=focus_area,
            current_strategy_summary=self._build_strategy_summary(profile, focus_area, recommendation, session),
            next_best_action=self._build_next_best_action(profile, daily_loop_plan),
            proof_lesson_handoff=(
                session.proof_lesson_handoff.model_dump(mode="json")
                if session and session.proof_lesson_handoff
                else {}
            ),
            strategy_snapshot=self._build_strategy_snapshot(profile, focus_area, recommendation, session),
            onboarding_completed_at=datetime.utcnow(),
            last_daily_plan_id=daily_loop_plan.id,
        )
        return JourneyCompletionResult(
            session=session,
            journey_state=journey_state,
            daily_loop_plan=daily_loop_plan,
        )

    def get_today_plan(self, profile: UserProfile) -> DailyLoopPlan:
        date_key = datetime.utcnow().date().isoformat()
        existing_plan = self._repository.get_daily_loop_plan(profile.id, date_key)
        if existing_plan is not None:
            return existing_plan

        existing_state = self._repository.get_journey_state(profile.id)
        recommendation = self._recommendation_service.get_next_step(profile)
        follow_up_preview = self._resolve_follow_up_preview(existing_state)
        focus_area = (
            str(follow_up_preview.get("focusArea"))
            if follow_up_preview and follow_up_preview.get("focusArea")
            else self._determine_focus_area(profile, None, recommendation, existing_state)
        )
        plan = self._ensure_today_plan(
            profile,
            session=None,
            recommendation=recommendation,
            focus_area=focus_area,
            stage=(
                "daily_loop_ready"
                if existing_state and existing_state.stage == "daily_loop_completed"
                else existing_state.stage if existing_state else "daily_loop_ready"
            ),
            current_state=existing_state,
            follow_up_preview=follow_up_preview,
        )
        if existing_state and existing_state.stage == "daily_loop_completed":
            self._refresh_state_for_ready_plan(
                profile=profile,
                current_state=existing_state,
                plan=plan,
                recommendation=recommendation,
                follow_up_preview=follow_up_preview,
            )
        return plan

    def get_journey_state(self, profile: UserProfile) -> LearnerJourneyState | None:
        return self._repository.get_journey_state(profile.id)

    def start_today_session(self, profile: UserProfile) -> LessonRunState:
        plan = self.get_today_plan(profile)
        current_state = self._repository.get_journey_state(profile.id)
        active_run = self._lesson_runtime_repository.get_active_lesson_run(profile.id)
        if active_run is not None:
            if plan.lesson_run_id != active_run.run_id:
                self._repository.attach_daily_loop_run(plan.id, active_run.run_id)
            return active_run

        recommendation = self._recommendation_service.get_next_step(profile)

        if plan.session_kind == "diagnostic":
            template = self._lesson_repository.create_diagnostic_template(
                profession_track=profile.profession_track,
                current_level=profile.current_level,
                target_level=profile.target_level,
            )
            lesson_run = self._lesson_runtime_repository.start_lesson_run(
                user_id=profile.id,
                profession_track=profile.profession_track,
                template_id=template.id,
            )
        elif plan.session_kind == "recovery":
            weak_spots = self._mistake_repository.list_weak_spots(profile.id, limit=3)
            due_vocabulary = self._vocabulary_repository.list_due_items(profile.id, limit=4)
            template = self._lesson_repository.create_recovery_template(
                profession_track=profile.profession_track,
                weak_spots=weak_spots,
                due_vocabulary=due_vocabulary,
                listening_focus=self._infer_input_lane(profile),
            )
            lesson_run = self._lesson_runtime_repository.start_lesson_run(
                user_id=profile.id,
                profession_track=profile.profession_track,
                template_id=template.id,
            )
        else:
            weak_spots = self._mistake_repository.list_weak_spots(profile.id, limit=3)
            due_vocabulary = self._vocabulary_repository.list_due_items(profile.id, limit=4)
            continuity_seed = self._build_continuity_template_seed(current_state, plan)
            guided_route_template = self._lesson_repository.create_guided_route_template(
                profession_track=profile.profession_track,
                route_context=self._build_guided_route_context(
                    profile=profile,
                    plan=plan,
                    current_state=current_state,
                    recommendation=recommendation,
                    weak_spots=weak_spots,
                    due_vocabulary=due_vocabulary,
                    continuity_seed=continuity_seed,
                ),
                weak_spots=weak_spots,
                due_vocabulary=due_vocabulary,
                continuity_seed=continuity_seed,
            )
            lesson_run = self._lesson_runtime_repository.start_lesson_run(
                user_id=profile.id,
                profession_track=profile.profession_track,
                template_id=guided_route_template.id if guided_route_template else None,
            )

        if lesson_run is None:
            raise ServiceUnavailableError("Daily loop session could not be started.")

        self._repository.attach_daily_loop_run(plan.id, lesson_run.run_id)
        self._repository.upsert_journey_state(
            user_id=profile.id,
            stage="daily_loop_active",
            source=current_state.source if current_state else "proof_lesson",
            preferred_mode=profile.onboarding_answers.preferred_mode,
            diagnostic_readiness=profile.onboarding_answers.diagnostic_readiness,
            time_budget_minutes=profile.lesson_duration,
            current_focus_area=plan.focus_area,
            current_strategy_summary=self._build_strategy_summary(
                profile,
                plan.focus_area,
                recommendation,
                None,
                current_state,
            ),
            next_best_action="Finish today's loop to unlock the next focused step.",
            proof_lesson_handoff=(
                current_state.proof_lesson_handoff.model_dump(mode="json")
                if current_state and current_state.proof_lesson_handoff
                else {}
            ),
            strategy_snapshot=self._build_active_strategy_snapshot(
                current_state=current_state,
                profile=profile,
                plan=plan,
                recommendation=recommendation,
            ),
            onboarding_completed_at=self._resolve_onboarding_completed_at(current_state),
            last_daily_plan_id=plan.id,
        )
        return lesson_run

    def register_completed_lesson(self, profile: UserProfile, lesson_run: LessonRunState) -> None:
        current_state = self._repository.get_journey_state(profile.id)
        recommendation = self._recommendation_service.get_next_step(profile)
        weak_spots = self._mistake_repository.list_weak_spots(profile.id, limit=3)
        tomorrow_focus_area = self._determine_focus_area(profile, None, recommendation, current_state)
        tomorrow_session_kind = self._determine_session_kind(profile, recommendation)
        session_summary = self._build_completed_session_summary(
            completed_plan=self._repository.get_daily_loop_plan(profile.id, datetime.utcnow().date().isoformat()),
            lesson_run=lesson_run,
            weak_spots=weak_spots,
            tomorrow_focus_area=tomorrow_focus_area,
        )
        tomorrow_preview = self._build_tomorrow_preview(
            profile,
            focus_area=tomorrow_focus_area,
            session_kind=tomorrow_session_kind,
            recommendation=recommendation,
            session_summary=session_summary,
        )
        completed_plan = self._repository.complete_daily_loop_plan_by_run(
            user_id=profile.id,
            run_id=lesson_run.run_id,
            completion_summary={
                "score": lesson_run.score,
                "lessonTitle": lesson_run.lesson.title,
                "completedAt": lesson_run.completed_at,
                "lessonType": lesson_run.lesson.lesson_type,
                "sessionSummary": session_summary,
                "tomorrowPreview": tomorrow_preview,
            },
        )
        if completed_plan is None:
            return

        self._repository.upsert_journey_state(
            user_id=profile.id,
            stage="daily_loop_completed",
            source=current_state.source if current_state else "proof_lesson",
            preferred_mode=profile.onboarding_answers.preferred_mode,
            diagnostic_readiness=profile.onboarding_answers.diagnostic_readiness,
            time_budget_minutes=profile.lesson_duration,
            current_focus_area=tomorrow_focus_area,
            current_strategy_summary=self._build_completed_strategy_summary(
                session_summary=session_summary,
            ),
            next_best_action=tomorrow_preview["nextStepHint"],
            proof_lesson_handoff=(
                current_state.proof_lesson_handoff.model_dump(mode="json")
                if current_state and current_state.proof_lesson_handoff
                else {}
            ),
            strategy_snapshot=self._build_completed_strategy_snapshot(
                current_state=current_state,
                profile=profile,
                focus_area=tomorrow_focus_area,
                recommendation=recommendation,
                lesson_run=lesson_run,
                session_summary=session_summary,
                tomorrow_preview=tomorrow_preview,
            ),
            onboarding_completed_at=(
                datetime.fromisoformat(current_state.onboarding_completed_at)
                if current_state and current_state.onboarding_completed_at
                else datetime.utcnow()
            ),
            last_daily_plan_id=completed_plan.id,
        )

    def _ensure_today_plan(
        self,
        profile: UserProfile,
        *,
        session: OnboardingSession | None,
        recommendation: LessonRecommendation | None,
        focus_area: str,
        stage: str,
        current_state: LearnerJourneyState | None = None,
        follow_up_preview: dict | None = None,
    ) -> DailyLoopPlan:
        date_key = datetime.utcnow().date().isoformat()
        existing_plan = self._repository.get_daily_loop_plan(profile.id, date_key)
        if existing_plan is not None:
            return existing_plan

        session_summary = self._extract_session_summary(current_state)
        session_kind = (
            str(follow_up_preview.get("sessionKind"))
            if follow_up_preview and follow_up_preview.get("sessionKind")
            else self._determine_session_kind(profile, recommendation)
        )
        recommended_lesson_type = (
            "diagnostic"
            if session_kind == "diagnostic"
            else "recovery"
            if session_kind == "recovery"
            else recommendation.lesson_type if recommendation else "core"
        )
        recommended_lesson_title = (
            str(follow_up_preview.get("recommendedLessonTitle"))
            if follow_up_preview and follow_up_preview.get("recommendedLessonTitle")
            else "Diagnostic checkpoint"
            if session_kind == "diagnostic"
            else recommendation.title if recommendation else "Daily guided lesson"
        )
        estimated_minutes = max(15, min(profile.lesson_duration, 32))
        preferred_mode = profile.onboarding_answers.preferred_mode
        carry_over_label = (
            str(follow_up_preview.get("carryOverSignalLabel"))
            if follow_up_preview and follow_up_preview.get("carryOverSignalLabel")
            else str(session_summary.get("carryOverSignalLabel"))
            if session_summary and session_summary.get("carryOverSignalLabel")
            else None
        )
        watch_label = (
            str(follow_up_preview.get("watchSignalLabel"))
            if follow_up_preview and follow_up_preview.get("watchSignalLabel")
            else str(session_summary.get("watchSignalLabel"))
            if session_summary and session_summary.get("watchSignalLabel")
            else None
        )
        plan = self._repository.upsert_daily_loop_plan(
            user_id=profile.id,
            plan_date_key=date_key,
            stage=stage,
            session_kind=session_kind,
            focus_area=focus_area,
            headline=self._build_plan_headline(profile, focus_area, follow_up_preview=follow_up_preview),
            summary=self._build_plan_summary(
                profile,
                focus_area,
                recommendation,
                session,
                follow_up_preview=follow_up_preview,
                session_summary=session_summary,
            ),
            why_this_now=self._build_plan_reason(
                profile,
                focus_area,
                recommendation,
                session,
                follow_up_preview=follow_up_preview,
                session_summary=session_summary,
            ),
            next_step_hint=self._build_next_best_action_text(
                profile,
                session_kind,
                focus_area,
                follow_up_preview=follow_up_preview,
            ),
            preferred_mode=preferred_mode,
            time_budget_minutes=profile.lesson_duration,
            estimated_minutes=estimated_minutes,
            recommended_lesson_type=recommended_lesson_type,
            recommended_lesson_title=recommended_lesson_title,
            steps=self._build_daily_steps(
                profile,
                focus_area,
                estimated_minutes,
                carry_over_label=carry_over_label,
                watch_label=watch_label,
            ),
        )
        return plan

    @staticmethod
    def _determine_session_kind(profile: UserProfile, recommendation: LessonRecommendation | None) -> str:
        if profile.onboarding_answers.diagnostic_readiness == "checkpoint_now":
            return "diagnostic"
        if recommendation and recommendation.lesson_type == "recovery":
            return "recovery"
        return "recommended"

    @staticmethod
    def _determine_focus_area(
        profile: UserProfile,
        session: OnboardingSession | None,
        recommendation: LessonRecommendation | None,
        current_state: LearnerJourneyState | None = None,
    ) -> str:
        if recommendation and recommendation.focus_area:
            normalized_focus = JourneyService._normalize_focus_area(
                recommendation.focus_area,
                profile=profile,
                session=session,
                current_state=current_state,
            )
            if normalized_focus:
                return normalized_focus
        if current_state and current_state.current_focus_area:
            return current_state.current_focus_area
        if session and session.proof_lesson_handoff and session.proof_lesson_handoff.directions:
            return session.proof_lesson_handoff.directions[0]
        if profile.onboarding_answers.active_skill_focus:
            return profile.onboarding_answers.active_skill_focus[0]
        return "speaking"

    @staticmethod
    def _normalize_focus_area(
        raw_focus_area: str,
        *,
        profile: UserProfile,
        session: OnboardingSession | None,
        current_state: LearnerJourneyState | None,
    ) -> str | None:
        normalized_tokens = [
            token.strip()
            for token in raw_focus_area.replace(";", ",").split(",")
            if token.strip()
        ]
        if not normalized_tokens:
            return None
        if len(normalized_tokens) == 1:
            return normalized_tokens[0]

        candidate_order: list[str] = []
        if current_state and current_state.current_focus_area:
            candidate_order.append(current_state.current_focus_area)
        if session and session.proof_lesson_handoff:
            candidate_order.extend(session.proof_lesson_handoff.directions)
        candidate_order.extend(profile.onboarding_answers.active_skill_focus)

        for candidate in candidate_order:
            if candidate in normalized_tokens:
                return candidate
        return normalized_tokens[0]

    @staticmethod
    def _build_strategy_summary(
        profile: UserProfile,
        focus_area: str,
        recommendation: LessonRecommendation | None,
        session: OnboardingSession | None,
        current_state: LearnerJourneyState | None = None,
    ) -> str:
        session_summary = JourneyService._extract_session_summary(current_state)
        if current_state and current_state.stage == "daily_loop_ready" and session_summary:
            carry_over_label = session_summary.get("carryOverSignalLabel") or focus_area
            watch_label = session_summary.get("watchSignalLabel") or focus_area
            recommendation_goal = recommendation.goal if recommendation else "The next lesson keeps the main path moving."
            return (
                f"Today's strategy carries forward {carry_over_label} while keeping a close watch on {watch_label}. "
                f"{recommendation_goal}"
            )

        source_phrase = ""
        if session and session.proof_lesson_handoff:
            source_phrase = (
                f" Proof lesson started from '{session.proof_lesson_handoff.after_phrase}'."
            )
        recommendation_goal = recommendation.goal if recommendation else "The next lesson keeps the main path moving."
        return (
            f"Current strategy leans on {focus_area} first, then reinforces adjacent skills. "
            f"{recommendation_goal}{source_phrase}"
        )

    def _build_strategy_snapshot(
        self,
        profile: UserProfile,
        focus_area: str,
        recommendation: LessonRecommendation | None,
        session: OnboardingSession | None,
    ) -> dict:
        return {
            "primaryGoal": profile.onboarding_answers.primary_goal,
            "preferredMode": profile.onboarding_answers.preferred_mode,
            "diagnosticReadiness": profile.onboarding_answers.diagnostic_readiness,
            "timeBudgetMinutes": profile.lesson_duration,
            "focusArea": focus_area,
            "activeSkillFocus": profile.onboarding_answers.active_skill_focus,
            "proofLessonDirections": session.proof_lesson_handoff.directions if session and session.proof_lesson_handoff else [],
            "recommendationTitle": recommendation.title if recommendation else None,
            "recommendationType": recommendation.lesson_type if recommendation else None,
        }

    def _build_active_strategy_snapshot(
        self,
        *,
        current_state: LearnerJourneyState | None,
        profile: UserProfile,
        plan: DailyLoopPlan,
        recommendation: LessonRecommendation | None,
    ) -> dict:
        snapshot = dict(current_state.strategy_snapshot) if current_state else {}
        snapshot.update(
            self._build_strategy_snapshot(
                profile,
                plan.focus_area,
                recommendation,
                None,
            )
        )
        active_plan_seed = snapshot.get("activePlanSeed")
        snapshot["activePlanSeed"] = {
            "source": (
                str(active_plan_seed.get("source"))
                if isinstance(active_plan_seed, dict) and active_plan_seed.get("source")
                else "daily_loop_plan"
            ),
            "planDateKey": plan.plan_date_key,
            "focusArea": plan.focus_area,
            "sessionKind": plan.session_kind,
        }
        return snapshot

    def _refresh_state_for_ready_plan(
        self,
        *,
        profile: UserProfile,
        current_state: LearnerJourneyState,
        plan: DailyLoopPlan,
        recommendation: LessonRecommendation | None,
        follow_up_preview: dict | None,
    ) -> None:
        snapshot = dict(current_state.strategy_snapshot)
        snapshot.update(
            {
                "focusArea": plan.focus_area,
                "recommendationTitle": recommendation.title if recommendation else None,
                "recommendationType": recommendation.lesson_type if recommendation else None,
                "activePlanSeed": {
                    "source": "tomorrow_preview" if follow_up_preview else "recommendation",
                    "planDateKey": plan.plan_date_key,
                    "focusArea": plan.focus_area,
                    "sessionKind": plan.session_kind,
                },
            }
        )
        self._repository.upsert_journey_state(
            user_id=profile.id,
            stage="daily_loop_ready",
            source=current_state.source,
            preferred_mode=profile.onboarding_answers.preferred_mode,
            diagnostic_readiness=profile.onboarding_answers.diagnostic_readiness,
            time_budget_minutes=profile.lesson_duration,
            current_focus_area=plan.focus_area,
            current_strategy_summary=self._build_strategy_summary(
                profile,
                plan.focus_area,
                recommendation,
                None,
                current_state,
            ),
            next_best_action=plan.next_step_hint,
            proof_lesson_handoff=(
                current_state.proof_lesson_handoff.model_dump(mode="json")
                if current_state.proof_lesson_handoff
                else {}
            ),
            strategy_snapshot=snapshot,
            onboarding_completed_at=self._resolve_onboarding_completed_at(current_state),
            last_daily_plan_id=plan.id,
        )

    def _build_guided_route_context(
        self,
        *,
        profile: UserProfile,
        plan: DailyLoopPlan,
        current_state: LearnerJourneyState | None,
        recommendation: LessonRecommendation | None,
        weak_spots: list[WeakSpot],
        due_vocabulary: list,
        continuity_seed: dict | None,
    ) -> dict:
        snapshot = current_state.strategy_snapshot if current_state else {}
        active_plan_seed = snapshot.get("activePlanSeed") if isinstance(snapshot.get("activePlanSeed"), dict) else None
        input_lane = self._infer_input_lane(profile)
        recent_lessons = self._lesson_repository.list_recent_completed_lessons(profile.id, limit=3)
        module_rotation = build_module_rotation(
            recommendation_lesson_type=recommendation.lesson_type if recommendation else plan.recommended_lesson_type,
            recommendation_focus_area=plan.focus_area,
            recent_lessons=recent_lessons,
            due_vocabulary=due_vocabulary,
            listening_focus=input_lane if input_lane == "listening" else None,
            mistake_resolution=[],
        )
        return {
            "focusArea": plan.focus_area,
            "sessionKind": plan.session_kind,
            "routeHeadline": plan.headline,
            "routeSummary": plan.summary,
            "whyNow": plan.why_this_now,
            "nextBestAction": plan.next_step_hint,
            "primaryGoal": profile.onboarding_answers.primary_goal,
            "preferredMode": profile.onboarding_answers.preferred_mode,
            "activeSkillFocus": profile.onboarding_answers.active_skill_focus,
            "inputLane": input_lane,
            "outputLane": self._infer_output_lane(profile),
            "moduleRotationKeys": [item.module_key for item in module_rotation[:3]],
            "weakSpotTitles": [spot.title for spot in weak_spots[:3]],
            "routeSeedSource": (
                str(active_plan_seed.get("source"))
                if active_plan_seed and active_plan_seed.get("source")
                else "tomorrow_preview"
                if continuity_seed
                else "daily_loop_plan"
            ),
            "recommendationTitle": recommendation.title if recommendation else plan.recommended_lesson_title,
            "recommendationType": recommendation.lesson_type if recommendation else plan.recommended_lesson_type,
        }

    @classmethod
    def _build_completed_session_summary(
        cls,
        *,
        completed_plan: DailyLoopPlan | None,
        lesson_run: LessonRunState,
        weak_spots: list[WeakSpot],
        tomorrow_focus_area: str,
    ) -> dict:
        strongest_signal, weakest_signal = cls._extract_block_performance_signals(lesson_run)
        outcome_band = cls._determine_outcome_band(lesson_run)
        top_weak_spot = weak_spots[0].title if weak_spots else None
        strongest_label = strongest_signal["label"] if strongest_signal else (completed_plan.focus_area if completed_plan else "today's route")
        weakest_label = weakest_signal["label"] if weakest_signal else (completed_plan.focus_area if completed_plan else "the core signal")
        carry_over_label = strongest_label if outcome_band in {"breakthrough", "stable", "checkpoint"} else tomorrow_focus_area
        watch_label = top_weak_spot or weakest_label

        if outcome_band == "checkpoint":
            headline = "This checkpoint gave the route a clearer calibration."
            what_worked = (
                f"The clearest signal came from {strongest_label}, so the next route no longer has to rely on the first onboarding guess alone."
            )
            watch_signal = (
                f"The system should still watch {watch_label} before it widens the route too fast."
            )
            strategy_shift = (
                f"Tomorrow can rebuild around {tomorrow_focus_area} with a more honest starting point."
            )
            coach_note = (
                "Checkpoint value comes from better calibration, not only from a higher score."
            )
        elif outcome_band == "breakthrough":
            headline = "This session produced a stable forward signal."
            what_worked = (
                f"{strongest_label} held up best, which means the route can carry that signal into the next session with more confidence."
            )
            watch_signal = (
                f"The route should still keep {watch_label} in view so today's progress does not become a one-off spike."
            )
            strategy_shift = (
                f"Tomorrow can stay ambitious around {tomorrow_focus_area} while carrying forward {carry_over_label}."
            )
            coach_note = (
                "The right follow-up now is continuity, not random extra practice."
            )
        elif outcome_band == "stable":
            headline = "This session kept the route stable."
            what_worked = (
                f"{strongest_label} gave the system enough confidence to keep the main route connected instead of restarting from scratch."
            )
            watch_signal = (
                f"The system still needs to watch {watch_label} so the route does not drift into the same weak pattern again."
            )
            strategy_shift = (
                f"Tomorrow stays centered on {tomorrow_focus_area} while keeping a light watch on {watch_label}."
            )
            coach_note = (
                "This is the moment to keep the ritual going and let the next route sharpen naturally."
            )
        else:
            headline = "This session exposed a weak signal that still needs protection."
            what_worked = (
                f"There is still usable momentum in {strongest_label}, so the route does not need a full reset."
            )
            watch_signal = (
                f"The weakest signal was {weakest_label}, and the system should treat {watch_label} carefully before widening the route again."
            )
            strategy_shift = (
                f"Tomorrow should stay narrower around {tomorrow_focus_area} until {watch_label} feels more reliable."
            )
            coach_note = (
                "Avoid scattering into random modules now. Let the next route absorb the weak signal first."
            )

        return {
            "outcomeBand": outcome_band,
            "headline": headline,
            "whatWorked": what_worked,
            "watchSignal": watch_signal,
            "strategyShift": strategy_shift,
            "coachNote": coach_note,
            "carryOverSignalLabel": carry_over_label,
            "watchSignalLabel": watch_label,
            "weakSpotTitle": top_weak_spot,
            "strongestSignalLabel": strongest_label,
            "weakestSignalLabel": weakest_label,
        }

    @staticmethod
    def _build_tomorrow_preview(
        profile: UserProfile,
        *,
        focus_area: str,
        session_kind: str,
        recommendation: LessonRecommendation | None,
        session_summary: dict,
    ) -> dict:
        recommended_lesson_title = (
            "Diagnostic checkpoint"
            if session_kind == "diagnostic"
            else recommendation.title if recommendation else "Guided daily lesson"
        )
        carry_over_label = session_summary.get("carryOverSignalLabel") or focus_area
        watch_label = session_summary.get("watchSignalLabel") or focus_area
        outcome_band = session_summary.get("outcomeBand") or "stable"

        if session_kind == "diagnostic":
            headline = f"Tomorrow uses this checkpoint to shape a more precise route around {focus_area}."
            reason = (
                f"{session_summary['headline']} {session_summary['strategyShift']}"
            )
            next_step_hint = "Come back tomorrow and let the recalibrated route start from this checkpoint signal."
            continuity_mode = "recalibrate"
        elif session_kind == "recovery":
            headline = f"Tomorrow keeps the route recovery-shaped around {focus_area}."
            reason = (
                f"{session_summary['watchSignal']} This is still the most useful place to stabilize before the route broadens again."
            )
            next_step_hint = f"Return tomorrow for the recovery-shaped route and stabilize {watch_label}."
            continuity_mode = "recovery"
        elif outcome_band == "breakthrough":
            headline = f"Tomorrow keeps moving around {focus_area} without dropping {carry_over_label}."
            reason = (
                f"{session_summary['whatWorked']} The route can stay open while still keeping {watch_label} in view."
            )
            next_step_hint = f"Return tomorrow and keep the guided route moving while carrying {carry_over_label} into the next session."
            continuity_mode = "carry_forward"
        elif outcome_band == "fragile":
            headline = f"Tomorrow should stay narrower around {focus_area}."
            reason = (
                f"{session_summary['watchSignal']} The route needs one more controlled pass before it broadens again."
            )
            next_step_hint = f"Return tomorrow and let the route stay tighter around {watch_label} before you widen back out."
            continuity_mode = "stabilize"
        else:
            headline = f"Tomorrow keeps moving through a guided session around {focus_area}."
            reason = (
                f"{session_summary['strategyShift']} The route stays aligned with {profile.onboarding_answers.primary_goal}."
            )
            next_step_hint = f"Return tomorrow for the next guided loop and keep {watch_label} in view while the route stays continuous."
            continuity_mode = "guided"

        return {
            "focusArea": focus_area,
            "sessionKind": session_kind,
            "headline": headline,
            "reason": reason,
            "nextStepHint": next_step_hint,
            "recommendedLessonTitle": recommended_lesson_title,
            "continuityMode": continuity_mode,
            "carryOverSignalLabel": carry_over_label,
            "watchSignalLabel": watch_label,
        }

    @staticmethod
    def _build_completed_strategy_summary(
        *,
        session_summary: dict,
    ) -> str:
        return f"{session_summary['headline']} {session_summary['strategyShift']}"

    @staticmethod
    def _build_completed_strategy_snapshot(
        *,
        current_state: LearnerJourneyState | None,
        profile: UserProfile,
        focus_area: str,
        recommendation: LessonRecommendation | None,
        lesson_run: LessonRunState,
        session_summary: dict,
        tomorrow_preview: dict,
    ) -> dict:
        snapshot = dict(current_state.strategy_snapshot) if current_state else {}
        snapshot.update(
            {
                "primaryGoal": profile.onboarding_answers.primary_goal,
                "preferredMode": profile.onboarding_answers.preferred_mode,
                "diagnosticReadiness": profile.onboarding_answers.diagnostic_readiness,
                "timeBudgetMinutes": profile.lesson_duration,
                "focusArea": focus_area,
                "activeSkillFocus": profile.onboarding_answers.active_skill_focus,
                "recommendationTitle": recommendation.title if recommendation else None,
                "recommendationType": recommendation.lesson_type if recommendation else None,
                "completedLesson": {
                    "lessonTitle": lesson_run.lesson.title,
                    "lessonType": lesson_run.lesson.lesson_type,
                    "score": lesson_run.score,
                    "completedAt": lesson_run.completed_at,
                },
                "sessionSummary": session_summary,
                "tomorrowPreview": tomorrow_preview,
            }
        )
        return snapshot

    @staticmethod
    def _determine_outcome_band(lesson_run: LessonRunState) -> str:
        if lesson_run.lesson.lesson_type == "diagnostic":
            return "checkpoint"

        score = lesson_run.score or 0
        if score >= 86:
            return "breakthrough"
        if score >= 72:
            return "stable"
        return "fragile"

    @staticmethod
    def _extract_block_performance_signals(lesson_run: LessonRunState) -> tuple[dict | None, dict | None]:
        block_by_id = {block.id: block for block in lesson_run.lesson.blocks}
        scored_blocks: list[dict] = []
        for block_run in lesson_run.block_runs:
            if block_run.score is None:
                continue
            block = block_by_id.get(block_run.block_id)
            if block is None:
                continue
            scored_blocks.append(
                {
                    "label": block.title or JourneyService._label_block_type(block.block_type),
                    "score": block_run.score,
                }
            )

        if not scored_blocks:
            return None, None

        strongest = max(scored_blocks, key=lambda item: item["score"])
        weakest = min(scored_blocks, key=lambda item: item["score"])
        return strongest, weakest

    @staticmethod
    def _label_block_type(block_type: str) -> str:
        labels = {
            "intro_block": "warm start",
            "review_block": "recovery review",
            "grammar_block": "grammar pattern",
            "vocab_block": "vocabulary recall",
            "speaking_block": "speaking response",
            "pronunciation_block": "pronunciation control",
            "listening_block": "listening input",
            "writing_block": "writing response",
            "profession_block": "work scenario",
            "reflection_block": "reflection",
            "summary_block": "strategic summary",
        }
        return labels.get(block_type, block_type.replace("_", " "))

    @staticmethod
    def _build_next_best_action(profile: UserProfile, plan: DailyLoopPlan) -> str:
        if plan.session_kind == "diagnostic":
            return "Run the short checkpoint first, then the next loop will become more precise."
        if profile.onboarding_answers.preferred_mode == "voice_first":
            return "Start today's loop from the speaking side and let the system refine the next step."
        return "Open today's guided loop and complete the first focused session."

    @staticmethod
    def _resolve_follow_up_preview(current_state: LearnerJourneyState | None) -> dict | None:
        if not current_state or current_state.stage != "daily_loop_completed":
            return None

        value = current_state.strategy_snapshot.get("tomorrowPreview")
        return value if isinstance(value, dict) and value else None

    @staticmethod
    def _extract_session_summary(current_state: LearnerJourneyState | None) -> dict | None:
        if not current_state:
            return None

        value = current_state.strategy_snapshot.get("sessionSummary")
        return value if isinstance(value, dict) and value else None

    @classmethod
    def _build_continuity_template_seed(
        cls,
        current_state: LearnerJourneyState | None,
        plan: DailyLoopPlan,
    ) -> dict | None:
        if not current_state:
            return None

        active_plan_seed = current_state.strategy_snapshot.get("activePlanSeed")
        if not isinstance(active_plan_seed, dict) or active_plan_seed.get("source") != "tomorrow_preview":
            return None

        follow_up_preview_value = current_state.strategy_snapshot.get("tomorrowPreview")
        follow_up_preview = (
            follow_up_preview_value
            if isinstance(follow_up_preview_value, dict) and follow_up_preview_value
            else None
        )
        session_summary = cls._extract_session_summary(current_state)
        if not follow_up_preview or not session_summary:
            return None

        return {
            "focusArea": plan.focus_area,
            "sessionKind": plan.session_kind,
            "continuityMode": follow_up_preview.get("continuityMode"),
            "headline": session_summary.get("headline"),
            "strategyShift": session_summary.get("strategyShift"),
            "carryOverSignalLabel": follow_up_preview.get("carryOverSignalLabel") or session_summary.get("carryOverSignalLabel"),
            "watchSignalLabel": follow_up_preview.get("watchSignalLabel") or session_summary.get("watchSignalLabel"),
        }

    @staticmethod
    def _build_plan_headline(
        profile: UserProfile,
        focus_area: str,
        *,
        follow_up_preview: dict | None = None,
    ) -> str:
        learner_name = profile.name.strip() or "Learner"
        carry_over_label = (
            str(follow_up_preview.get("carryOverSignalLabel"))
            if follow_up_preview and follow_up_preview.get("carryOverSignalLabel")
            else None
        )
        if carry_over_label:
            return f"{learner_name}, today's route carries forward {carry_over_label} around {focus_area}."
        return f"{learner_name}, this is your first guided daily loop around {focus_area}."

    @staticmethod
    def _build_plan_summary(
        profile: UserProfile,
        focus_area: str,
        recommendation: LessonRecommendation | None,
        session: OnboardingSession | None,
        *,
        follow_up_preview: dict | None = None,
        session_summary: dict | None = None,
    ) -> str:
        if follow_up_preview:
            carry_over_label = follow_up_preview.get("carryOverSignalLabel") or focus_area
            watch_label = follow_up_preview.get("watchSignalLabel") or focus_area
            shift_line = session_summary.get("strategyShift") if session_summary else follow_up_preview.get("reason")
            return (
                f"Today's route picks up from yesterday by carrying forward {carry_over_label} and keeping {watch_label} in view. "
                f"{shift_line}"
            )

        proof_reference = ""
        if session and session.proof_lesson_handoff:
            proof_reference = (
                f" We carry forward the proof-lesson phrase '{session.proof_lesson_handoff.after_phrase}'."
            )
        recommendation_line = recommendation.goal if recommendation else "The loop starts with a guided multi-skill lesson."
        return (
            f"The first loop is tuned to {profile.onboarding_answers.primary_goal} with {focus_area} as the lead signal. "
            f"{recommendation_line}{proof_reference}"
        )

    @staticmethod
    def _build_plan_reason(
        profile: UserProfile,
        focus_area: str,
        recommendation: LessonRecommendation | None,
        session: OnboardingSession | None,
        *,
        follow_up_preview: dict | None = None,
        session_summary: dict | None = None,
    ) -> str:
        if follow_up_preview:
            carry_over_label = follow_up_preview.get("carryOverSignalLabel") or focus_area
            watch_label = follow_up_preview.get("watchSignalLabel") or focus_area
            summary_headline = session_summary.get("headline") if session_summary else follow_up_preview.get("headline")
            return (
                f"{summary_headline} The route now carries {carry_over_label} forward while staying careful around {watch_label}."
            )

        proof_signal = ""
        if session and session.proof_lesson_handoff:
            proof_signal = (
                f" The proof lesson already showed a useful starting pattern around {focus_area}."
            )
        recommendation_reason = (
            recommendation.goal if recommendation else "The loop keeps the path simple and focused."
        )
        return (
            f"You asked for {profile.onboarding_answers.primary_goal}, prefer a {profile.onboarding_answers.preferred_mode} flow, "
            f"and can spend about {profile.lesson_duration} minutes.{proof_signal} {recommendation_reason}"
        )

    @staticmethod
    def _build_next_best_action_text(
        profile: UserProfile,
        session_kind: str,
        focus_area: str,
        *,
        follow_up_preview: dict | None = None,
    ) -> str:
        if follow_up_preview and follow_up_preview.get("nextStepHint"):
            return str(follow_up_preview["nextStepHint"])
        if session_kind == "diagnostic":
            return "Finish the checkpoint now, then tomorrow's route will become more personalized."
        if profile.onboarding_answers.preferred_mode == "text_first":
            return f"Start with a calm text-led loop, then deepen {focus_area} through the next guided response."
        if profile.onboarding_answers.preferred_mode == "voice_first":
            return f"Start with a voice-led loop and let the next plan respond to your speaking signal."
        return f"Open the loop, complete one guided session, and the next plan will sharpen around {focus_area}."

    def _build_daily_steps(
        self,
        profile: UserProfile,
        focus_area: str,
        estimated_minutes: int,
        *,
        carry_over_label: str | None = None,
        watch_label: str | None = None,
    ) -> list[dict]:
        input_lane = self._infer_input_lane(profile)
        output_lane = self._infer_output_lane(profile)
        step_specs = [
            ("warm-start", "coach", "Warm start", "Liza sets the goal of this session and explains why it matters now.", 2),
            ("vocabulary-recall", "vocabulary", "Vocabulary recall", "Bring back a few words that the next session needs immediately.", 3),
            ("grammar-pattern", "grammar", "Grammar pattern", f"Reinforce one pattern that supports {focus_area}.", 3),
            ("input", input_lane, f"{input_lane.capitalize()} input", f"Take in one short {input_lane} cue before responding.", 4),
            (
                "response",
                output_lane,
                f"{output_lane.capitalize()} response",
                (
                    f"Respond in a way that carries forward {carry_over_label} while staying useful for the main goal."
                    if carry_over_label
                    else "Respond in a way that trains the main goal, not just correctness."
                ),
                5,
            ),
            ("pronunciation", "pronunciation", "Pronunciation micro-fix", "Tighten one sound or rhythm issue while the material is still fresh.", 2),
            (
                "reinforcement",
                "reinforcement",
                "Reinforcement",
                (
                    f"Repeat the key pattern in a slightly different form so {watch_label} becomes more stable."
                    if watch_label
                    else "Repeat the key pattern in a slightly different form to make it stick."
                ),
                2,
            ),
            (
                "summary",
                "summary",
                "Strategic summary",
                (
                    f"See what improved, what still needs watching, and how the route keeps {carry_over_label or focus_area} moving next."
                ),
                2,
            ),
        ]
        total_weight = sum(weight for *_, weight in step_specs)
        scale = max(estimated_minutes / total_weight, 1)
        steps: list[dict] = []
        for step_id, skill, title, description, weight in step_specs:
            steps.append(
                {
                    "id": step_id,
                    "skill": skill,
                    "title": title,
                    "description": description,
                    "durationMinutes": max(1, round(weight * scale)),
                }
            )
        return steps

    @staticmethod
    def _infer_input_lane(profile: UserProfile) -> str:
        preferred_mode = profile.onboarding_answers.preferred_mode
        if preferred_mode == "text_first":
            return "reading"
        return "listening"

    @staticmethod
    def _infer_output_lane(profile: UserProfile) -> str:
        preferred_mode = profile.onboarding_answers.preferred_mode
        if preferred_mode == "text_first":
            return "writing"
        return "speaking"

    @staticmethod
    def _resolve_onboarding_completed_at(current_state: LearnerJourneyState | None) -> datetime:
        if current_state and current_state.onboarding_completed_at:
            return datetime.fromisoformat(current_state.onboarding_completed_at)
        return datetime.utcnow()
