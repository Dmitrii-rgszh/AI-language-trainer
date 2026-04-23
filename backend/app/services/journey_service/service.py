from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from app.core.errors import NotFoundError, ServiceUnavailableError
from app.repositories.journey_repository import JourneyRepository
from app.repositories.lesson_repository import LessonRepository
from app.repositories.lesson_runtime_repository import LessonRuntimeRepository
from app.repositories.mistake_repository import MistakeRepository
from app.repositories.progress_repository import ProgressRepository
from app.repositories.vocabulary_repository import VocabularyRepository
from app.schemas.journey import (
    DailyRitual,
    DailyLoopPlan,
    LearnerJourneyState,
    OnboardingSession,
    SaveOnboardingSessionDraftRequest,
    StartOnboardingSessionRequest,
    TaskDrivenInput,
)
from app.schemas.lesson import LessonRecommendation, LessonRunState
from app.schemas.mistake import WeakSpot
from app.schemas.profile import UserProfile
from app.services.adaptive_study_service.rotation_builder import build_module_rotation
from app.services.adaptive_study_service.loop_heuristics import build_progress_trajectory
from app.services.adaptive_study_service.loop_heuristics import build_strategy_memory
from app.services.learning_blueprint_service.service import LearningBlueprintService
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
        progress_repository: ProgressRepository | None = None,
    ) -> None:
        self._repository = repository
        self._lesson_repository = lesson_repository
        self._lesson_runtime_repository = lesson_runtime_repository
        self._recommendation_service = recommendation_service
        self._mistake_repository = mistake_repository
        self._vocabulary_repository = vocabulary_repository
        self._progress_repository = progress_repository
        self._learning_blueprint_service = LearningBlueprintService()

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
            return self._attach_daily_ritual(existing_plan, profile=profile, current_state=self._repository.get_journey_state(profile.id))

        existing_state = self._repository.get_journey_state(profile.id)
        recommendation = self._recommendation_service.get_next_step(profile)
        follow_up_preview = self._resolve_follow_up_preview(existing_state)
        route_follow_up_memory = self._extract_route_follow_up_memory(existing_state)
        ritual_signal_memory = self._build_ritual_signal_memory(profile.id, existing_state)
        task_driven_follow_up_focus = (
            self._map_route_to_focus_area(str(route_follow_up_memory.get("currentRoute")))
            if route_follow_up_memory
            and str(route_follow_up_memory.get("stageLabel") or "") == "Task-driven handoff"
            else None
        )
        focus_area = (
            str(follow_up_preview.get("focusArea"))
            if follow_up_preview and follow_up_preview.get("focusArea")
            else task_driven_follow_up_focus
            if task_driven_follow_up_focus
            else str(ritual_signal_memory.get("recommendedFocus"))
            if self._should_prioritize_ritual_signal_focus(ritual_signal_memory)
            and ritual_signal_memory
            and ritual_signal_memory.get("recommendedFocus")
            else self._determine_focus_area(profile, None, recommendation, existing_state)
        )
        route_entry_memory = self._extract_route_entry_memory(existing_state)
        route_recovery_memory = self._extract_route_recovery_memory(existing_state)
        route_entry_reset_label = self._build_route_entry_memory_reset_label(route_entry_memory)
        if route_entry_reset_label and route_recovery_memory and route_recovery_memory.get("focusSkill"):
            focus_area = str(route_recovery_memory.get("focusSkill"))
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
        return self._attach_daily_ritual(plan, profile=profile, current_state=existing_state)

    def get_journey_state(self, profile: UserProfile) -> LearnerJourneyState | None:
        return self._repository.get_journey_state(profile.id)

    def register_route_reentry_support_step(
        self,
        *,
        profile: UserProfile,
        route: str,
    ) -> LearnerJourneyState:
        current_state = self._repository.get_journey_state(profile.id)
        if current_state is None:
            raise NotFoundError("Journey state was not found.")

        route_recovery_memory = self._extract_route_recovery_memory(current_state)
        route_reentry_progress = self._build_route_reentry_progress(
            current_state=current_state,
            route_recovery_memory=route_recovery_memory,
        )
        snapshot = dict(current_state.strategy_snapshot)
        if route_reentry_progress is not None:
            ordered_routes = [
                str(item)
                for item in route_reentry_progress.get("orderedRoutes", [])
                if isinstance(item, str)
            ]
            if route not in ordered_routes:
                return current_state

            completed_routes = [
                str(item)
                for item in route_reentry_progress.get("completedRoutes", [])
                if isinstance(item, str) and item in ordered_routes
            ]
            if route not in completed_routes:
                completed_routes.append(route)

            next_route = next(
                (candidate for candidate in ordered_routes if candidate not in completed_routes),
                None,
            )
            route_reentry_progress["completedRoutes"] = completed_routes
            route_reentry_progress["nextRoute"] = next_route
            route_reentry_progress["status"] = "completed" if next_route is None else "active"
            snapshot["routeReentryProgress"] = route_reentry_progress
        elif str(route_recovery_memory.get("phase") or "") != "support_reopen_arc":
            return current_state

        route_follow_up_memory = self._build_route_follow_up_memory(
            route_recovery_memory=route_recovery_memory,
            route_reentry_progress=route_reentry_progress,
            route_entry_memory=self._extract_route_entry_memory(current_state),
            ritual_signal_memory=self._extract_ritual_signal_memory(current_state),
            existing_route_follow_up_memory=self._extract_route_follow_up_memory(current_state),
        )
        if route_reentry_progress is None and str(route_recovery_memory.get("phase") or "") == "support_reopen_arc":
            route_follow_up_memory = self._complete_support_reopen_follow_up_memory(
                route=route,
                route_recovery_memory=route_recovery_memory,
                existing_route_follow_up_memory=route_follow_up_memory or self._extract_route_follow_up_memory(current_state),
            )
            if route_follow_up_memory is None:
                return current_state
        elif route_reentry_progress is None:
            return current_state
        if route_follow_up_memory:
            snapshot["routeFollowUpMemory"] = route_follow_up_memory
        else:
            snapshot.pop("routeFollowUpMemory", None)
        if str(route_recovery_memory.get("phase") or "") == "support_reopen_arc" and route_follow_up_memory:
            temp_state = current_state.model_copy(update={"strategy_snapshot": snapshot})
            route_recovery_memory = self._extend_support_reopen_arc(
                user_id=profile.id,
                route_recovery_memory=route_recovery_memory,
                current_state=temp_state,
            )
            snapshot["routeRecoveryMemory"] = route_recovery_memory
            route_follow_up_memory = self._build_route_follow_up_memory(
                route_recovery_memory=route_recovery_memory,
                route_reentry_progress=route_reentry_progress,
                route_entry_memory=self._extract_route_entry_memory(temp_state),
                ritual_signal_memory=self._extract_ritual_signal_memory(temp_state),
                existing_route_follow_up_memory=route_follow_up_memory,
            )
            if route_follow_up_memory:
                snapshot["routeFollowUpMemory"] = route_follow_up_memory
        current_strategy_summary = (
            self._build_route_follow_up_summary_line(route_follow_up_memory)
            if str(route_recovery_memory.get("phase") or "") == "support_reopen_arc"
            else self._build_route_reentry_progress_summary(
                route_reentry_progress,
                route_recovery_memory,
                fallback=current_state.current_strategy_summary,
            )
        )
        next_best_action = (
            self._build_route_follow_up_action_hint(route_follow_up_memory)
            or self._build_route_reentry_progress_next_action(
                route_reentry_progress,
                fallback=current_state.next_best_action,
            )
        )
        snapshot["learningBlueprint"] = self._build_learning_blueprint(
            profile=profile,
            focus_area=current_state.current_focus_area,
            recommendation=None,
            current_state=current_state,
            current_strategy_summary=current_strategy_summary,
            next_best_action=next_best_action,
            route_snapshot=snapshot,
        )
        return self._repository.upsert_journey_state(
            user_id=profile.id,
            stage=current_state.stage,
            source=current_state.source,
            preferred_mode=current_state.preferred_mode,
            diagnostic_readiness=current_state.diagnostic_readiness,
            time_budget_minutes=current_state.time_budget_minutes,
            current_focus_area=current_state.current_focus_area,
            current_strategy_summary=current_strategy_summary,
            next_best_action=next_best_action,
            proof_lesson_handoff=(
                current_state.proof_lesson_handoff.model_dump(mode="json")
                if current_state.proof_lesson_handoff
                else {}
            ),
            strategy_snapshot=snapshot,
            onboarding_completed_at=self._resolve_onboarding_completed_at(current_state),
            last_daily_plan_id=current_state.last_daily_plan_id,
        )

    def register_route_entry(
        self,
        *,
        profile: UserProfile,
        route: str,
        source: str,
    ) -> LearnerJourneyState:
        current_state = self._repository.get_journey_state(profile.id)
        if current_state is None:
            raise NotFoundError("Journey state was not found.")

        snapshot = dict(current_state.strategy_snapshot)
        snapshot["routeEntryMemory"] = self._build_route_entry_memory(
            current_state=current_state,
            route=route,
            source=source,
        )
        route_follow_up_memory = self._build_route_follow_up_memory(
            route_recovery_memory=self._extract_route_recovery_memory(current_state),
            route_reentry_progress=self._extract_route_reentry_progress(current_state),
            route_entry_memory=snapshot.get("routeEntryMemory") if isinstance(snapshot.get("routeEntryMemory"), dict) else None,
            ritual_signal_memory=self._extract_ritual_signal_memory(current_state),
            existing_route_follow_up_memory=self._extract_route_follow_up_memory(current_state),
        )
        if route_follow_up_memory:
            snapshot["routeFollowUpMemory"] = route_follow_up_memory
        else:
            snapshot.pop("routeFollowUpMemory", None)
        current_strategy_summary = (
            self._build_route_follow_up_summary_line(route_follow_up_memory)
            or current_state.current_strategy_summary
        )
        next_best_action = (
            self._build_route_follow_up_action_hint(route_follow_up_memory)
            or current_state.next_best_action
        )
        snapshot["learningBlueprint"] = self._build_learning_blueprint(
            profile=profile,
            focus_area=current_state.current_focus_area,
            recommendation=None,
            current_state=current_state,
            current_strategy_summary=current_strategy_summary,
            next_best_action=next_best_action,
            route_snapshot=snapshot,
        )
        return self._repository.upsert_journey_state(
            user_id=profile.id,
            stage=current_state.stage,
            source=current_state.source,
            preferred_mode=current_state.preferred_mode,
            diagnostic_readiness=current_state.diagnostic_readiness,
            time_budget_minutes=current_state.time_budget_minutes,
            current_focus_area=current_state.current_focus_area,
            current_strategy_summary=current_strategy_summary,
            next_best_action=next_best_action,
            proof_lesson_handoff=(
                current_state.proof_lesson_handoff.model_dump(mode="json")
                if current_state.proof_lesson_handoff
                else {}
            ),
            strategy_snapshot=snapshot,
            onboarding_completed_at=self._resolve_onboarding_completed_at(current_state),
            last_daily_plan_id=current_state.last_daily_plan_id,
        )

    def register_task_driven_step(
        self,
        *,
        profile: UserProfile,
        input_route: str,
        response_route: str,
    ) -> LearnerJourneyState:
        current_state = self._repository.get_journey_state(profile.id)
        if current_state is None:
            raise NotFoundError("Journey state was not found.")

        snapshot = dict(current_state.strategy_snapshot)
        existing_follow_up_memory = self._extract_route_follow_up_memory(current_state)
        completion_count = (
            int(existing_follow_up_memory.get("completionCount"))
            if existing_follow_up_memory and existing_follow_up_memory.get("completionCount")
            else 0
        )
        route_follow_up_memory = {
            "currentRoute": response_route,
            "currentLabel": self._map_task_driven_response_label(response_route),
            "followUpRoute": "/daily-loop",
            "followUpLabel": "daily route",
            "stageLabel": "Task-driven handoff",
            "status": "active",
            "summary": (
                f"The route has already captured its {self._map_task_driven_input_label(input_route)}, "
                f"so it should move through {self._map_task_driven_response_label(response_route)} next and then reconnect through the daily route."
            ),
            "completionCount": completion_count + 1,
            "lastCompletedRoute": input_route,
            "lastCompletedAt": datetime.utcnow().isoformat(),
        }
        snapshot["routeFollowUpMemory"] = route_follow_up_memory
        current_focus_area = self._map_route_to_focus_area(response_route) or current_state.current_focus_area
        current_strategy_summary = (
            self._build_route_follow_up_summary_line(route_follow_up_memory)
            or current_state.current_strategy_summary
        )
        next_best_action = (
            self._build_route_follow_up_action_hint(route_follow_up_memory)
            or current_state.next_best_action
        )
        snapshot["learningBlueprint"] = self._build_learning_blueprint(
            profile=profile,
            focus_area=current_focus_area,
            recommendation=None,
            current_state=current_state.model_copy(update={"strategy_snapshot": snapshot}),
            current_strategy_summary=current_strategy_summary,
            next_best_action=next_best_action,
            plan=self._repository.get_daily_loop_plan(profile.id, datetime.utcnow().date().isoformat()),
            route_snapshot=snapshot,
        )
        return self._repository.upsert_journey_state(
            user_id=profile.id,
            stage=current_state.stage,
            source=current_state.source,
            preferred_mode=current_state.preferred_mode,
            diagnostic_readiness=current_state.diagnostic_readiness,
            time_budget_minutes=current_state.time_budget_minutes,
            current_focus_area=current_focus_area,
            current_strategy_summary=current_strategy_summary,
            next_best_action=next_best_action,
            proof_lesson_handoff=(
                current_state.proof_lesson_handoff.model_dump(mode="json")
                if current_state.proof_lesson_handoff
                else {}
            ),
            strategy_snapshot=snapshot,
            onboarding_completed_at=self._resolve_onboarding_completed_at(current_state),
            last_daily_plan_id=current_state.last_daily_plan_id,
        )

    def register_ritual_signal(
        self,
        *,
        profile: UserProfile,
        signal_type: str,
        route: str,
        label: str,
        summary: str | None = None,
    ) -> LearnerJourneyState:
        current_state = self._repository.get_journey_state(profile.id)
        if current_state is None:
            raise NotFoundError("Journey state was not found.")

        snapshot = dict(current_state.strategy_snapshot)
        existing_memory = (
            snapshot.get("ritualSignalMemory")
            if isinstance(snapshot.get("ritualSignalMemory"), dict)
            else {}
        )
        previous_type = str(existing_memory.get("activeSignalType") or "")
        previous_count = int(existing_memory.get("signalCount") or 0) if previous_type == signal_type else 0
        signal_count = previous_count + 1
        window_stage = (
            "fresh_capture"
            if signal_count == 1
            else "stabilizing_signal"
            if signal_count == 2
            else "ready_to_carry"
        )
        recommended_focus = (
            "vocabulary"
            if signal_type == "word_journal"
            else "speaking"
            if signal_type == "spontaneous_voice"
            else current_state.current_focus_area
        )
        action_hint = (
            f"Keep one light route step around {label} so the captured phrase comes back in real use before it goes cold."
            if signal_type == "word_journal"
            else f"Keep one live speaking step around {label} so the spontaneous voice signal settles before the route widens."
        )
        summary_line = (
            summary
            or (
                f"The route has a fresh word journal signal through {label}, so the next 1-2 sessions should reuse that phrase inside real output."
                if signal_type == "word_journal"
                else f"The route has a fresh spontaneous voice signal through {label}, so the next 1-2 sessions should keep one low-pressure speaking pass alive."
            )
        )
        recent_signals = [
            item
            for item in existing_memory.get("recentSignals", [])
            if isinstance(item, dict)
        ][:4]
        recent_signals.insert(
            0,
            {
                "signalType": signal_type,
                "route": route,
                "label": label,
                "summary": summary_line,
                "recordedAt": datetime.utcnow().isoformat(),
            },
        )
        snapshot["ritualSignalMemory"] = {
            "activeSignalType": signal_type,
            "activeRoute": route,
            "activeLabel": label,
            "recommendedFocus": recommended_focus,
            "signalCount": signal_count,
            "windowDays": 2,
            "windowStage": window_stage,
            "arcStep": "capture",
            "summary": summary_line,
            "actionHint": action_hint,
            "recordedAt": datetime.utcnow().isoformat(),
            "recentSignals": recent_signals[:5],
        }
        current_strategy_summary = summary_line
        next_best_action = action_hint
        snapshot["learningBlueprint"] = self._build_learning_blueprint(
            profile=profile,
            focus_area=recommended_focus,
            recommendation=None,
            current_state=current_state.model_copy(update={"strategy_snapshot": snapshot}),
            current_strategy_summary=current_strategy_summary,
            next_best_action=next_best_action,
            route_snapshot=snapshot,
        )
        return self._repository.upsert_journey_state(
            user_id=profile.id,
            stage=current_state.stage,
            source=current_state.source,
            preferred_mode=current_state.preferred_mode,
            diagnostic_readiness=current_state.diagnostic_readiness,
            time_budget_minutes=current_state.time_budget_minutes,
            current_focus_area=recommended_focus,
            current_strategy_summary=current_strategy_summary,
            next_best_action=next_best_action,
            proof_lesson_handoff=(
                current_state.proof_lesson_handoff.model_dump(mode="json")
                if current_state.proof_lesson_handoff
                else {}
            ),
            strategy_snapshot=snapshot,
            onboarding_completed_at=self._resolve_onboarding_completed_at(current_state),
            last_daily_plan_id=current_state.last_daily_plan_id,
        )

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
                route_cadence_memory=self._build_route_cadence_memory(profile.id, current_state),
                route_recovery_memory=self._apply_task_driven_transfer_recovery_override(
                    self._build_route_recovery_memory(
                        user_id=profile.id,
                        current_state=current_state,
                        session_summary=session_summary,
                        skill_trajectory=self._build_skill_trajectory_memory(
                            profile.id,
                            current_state,
                            active_skill_focus=profile.onboarding_answers.active_skill_focus,
                        ),
                        strategy_memory=self._build_strategy_memory(
                            profile.id,
                            current_state,
                            active_skill_focus=profile.onboarding_answers.active_skill_focus,
                        ),
                        route_cadence_memory=self._build_route_cadence_memory(profile.id, current_state),
                    ),
                    session_summary=session_summary,
                ),
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
            return self._attach_daily_ritual(existing_plan, profile=profile, current_state=current_state)

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
        preferred_mode = profile.onboarding_answers.preferred_mode
        practice_shift = (
            session_summary.get("practiceMixEvaluation")
            if session_summary and isinstance(session_summary.get("practiceMixEvaluation"), dict)
            else None
        )
        task_driven_transfer_evaluation = (
            session_summary.get("taskDrivenTransferEvaluation")
            if session_summary and isinstance(session_summary.get("taskDrivenTransferEvaluation"), dict)
            else None
        )
        skill_trajectory = self._build_skill_trajectory_memory(
            profile.id,
            current_state,
            active_skill_focus=profile.onboarding_answers.active_skill_focus,
        )
        strategy_memory = self._build_strategy_memory(
            profile.id,
            current_state,
            active_skill_focus=profile.onboarding_answers.active_skill_focus,
        )
        route_cadence_memory = self._build_route_cadence_memory(profile.id, current_state)
        route_recovery_memory = self._build_route_recovery_memory(
            user_id=profile.id,
            current_state=current_state,
            session_summary=session_summary,
            skill_trajectory=skill_trajectory,
            strategy_memory=strategy_memory,
            route_cadence_memory=route_cadence_memory,
        )
        route_reentry_progress = self._build_route_reentry_progress(
            current_state=current_state,
            route_recovery_memory=route_recovery_memory,
        )
        route_entry_memory = self._extract_route_entry_memory(current_state)
        route_follow_up_memory = self._extract_route_follow_up_memory(current_state)
        ritual_signal_memory = self._build_ritual_signal_memory(profile.id, current_state)
        estimated_minutes = self._resolve_estimated_minutes(
            lesson_duration=profile.lesson_duration,
            session_kind=session_kind,
            route_recovery_memory=route_recovery_memory,
            route_reentry_progress=route_reentry_progress,
        )
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
            headline=self._build_plan_headline(
                profile,
                focus_area,
                follow_up_preview=follow_up_preview,
                practice_shift=practice_shift,
                skill_trajectory=skill_trajectory,
                strategy_memory=strategy_memory,
                route_cadence_memory=route_cadence_memory,
                route_recovery_memory=route_recovery_memory,
                route_reentry_progress=route_reentry_progress,
                route_entry_memory=route_entry_memory,
                route_follow_up_memory=route_follow_up_memory,
                ritual_signal_memory=ritual_signal_memory,
            ),
            summary=self._build_plan_summary(
                profile,
                focus_area,
                recommendation,
                session,
                follow_up_preview=follow_up_preview,
                session_summary=session_summary,
                practice_shift=practice_shift,
                skill_trajectory=skill_trajectory,
                strategy_memory=strategy_memory,
                route_cadence_memory=route_cadence_memory,
                route_recovery_memory=route_recovery_memory,
                route_reentry_progress=route_reentry_progress,
                route_entry_memory=route_entry_memory,
                route_follow_up_memory=route_follow_up_memory,
                ritual_signal_memory=ritual_signal_memory,
            ),
            why_this_now=self._build_plan_reason(
                profile,
                focus_area,
                recommendation,
                session,
                follow_up_preview=follow_up_preview,
                session_summary=session_summary,
                practice_shift=practice_shift,
                skill_trajectory=skill_trajectory,
                strategy_memory=strategy_memory,
                route_cadence_memory=route_cadence_memory,
                route_recovery_memory=route_recovery_memory,
                route_reentry_progress=route_reentry_progress,
                route_entry_memory=route_entry_memory,
                route_follow_up_memory=route_follow_up_memory,
                ritual_signal_memory=ritual_signal_memory,
            ),
            next_step_hint=self._build_next_best_action_text(
                profile,
                session_kind,
                focus_area,
                follow_up_preview=follow_up_preview,
                practice_shift=practice_shift,
                skill_trajectory=skill_trajectory,
                strategy_memory=strategy_memory,
                route_cadence_memory=route_cadence_memory,
                route_recovery_memory=route_recovery_memory,
                route_reentry_progress=route_reentry_progress,
                route_entry_memory=route_entry_memory,
                route_follow_up_memory=route_follow_up_memory,
                ritual_signal_memory=ritual_signal_memory,
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
                practice_shift=practice_shift,
                skill_trajectory=skill_trajectory,
                strategy_memory=strategy_memory,
                route_cadence_memory=route_cadence_memory,
                route_recovery_memory=route_recovery_memory,
                route_reentry_progress=route_reentry_progress,
                ritual_signal_memory=ritual_signal_memory,
            ),
        )
        return self._attach_daily_ritual(plan, profile=profile, current_state=current_state)

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
        skill_trajectory = JourneyService._extract_skill_trajectory(current_state)
        strategy_memory = JourneyService._extract_strategy_memory(current_state)
        route_cadence_memory = JourneyService._extract_route_cadence_memory(current_state)
        route_recovery_memory = JourneyService._extract_route_recovery_memory(current_state)
        if current_state and current_state.stage == "daily_loop_ready" and session_summary:
            carry_over_label = session_summary.get("carryOverSignalLabel") or focus_area
            watch_label = session_summary.get("watchSignalLabel") or focus_area
            recommendation_goal = recommendation.goal if recommendation else "The next lesson keeps the main path moving."
            return (
                f"Today's strategy carries forward {carry_over_label} while keeping a close watch on {watch_label}. "
                f"{recommendation_goal}"
                + (
                    f" {JourneyService._build_strategy_memory_summary_line(strategy_memory)}"
                    if JourneyService._build_strategy_memory_summary_line(strategy_memory)
                    else ""
                )
                + (
                    f" {JourneyService._build_route_cadence_summary_line(route_cadence_memory)}"
                    if JourneyService._build_route_cadence_summary_line(route_cadence_memory)
                    else ""
                )
                + (
                    f" {JourneyService._build_route_recovery_summary_line(route_recovery_memory)}"
                    if JourneyService._build_route_recovery_summary_line(route_recovery_memory)
                    else ""
                )
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
            + (
                f" {JourneyService._build_trajectory_summary_line(skill_trajectory)}"
                if JourneyService._build_trajectory_summary_line(skill_trajectory)
                else ""
            )
            + (
                f" {JourneyService._build_strategy_memory_summary_line(strategy_memory)}"
                if JourneyService._build_strategy_memory_summary_line(strategy_memory)
                else ""
            )
            + (
                f" {JourneyService._build_route_cadence_summary_line(route_cadence_memory)}"
                if JourneyService._build_route_cadence_summary_line(route_cadence_memory)
                else ""
            )
            + (
                f" {JourneyService._build_route_recovery_summary_line(route_recovery_memory)}"
                if JourneyService._build_route_recovery_summary_line(route_recovery_memory)
                else ""
            )
        )

    def _build_strategy_snapshot(
        self,
        profile: UserProfile,
        focus_area: str,
        recommendation: LessonRecommendation | None,
        session: OnboardingSession | None,
    ) -> dict:
        snapshot = {
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
        skill_trajectory = self._build_skill_trajectory_memory(
            profile.id,
            active_skill_focus=profile.onboarding_answers.active_skill_focus,
        )
        if skill_trajectory:
            snapshot["skillTrajectory"] = skill_trajectory
        strategy_memory = self._build_strategy_memory(
            profile.id,
            active_skill_focus=profile.onboarding_answers.active_skill_focus,
        )
        if strategy_memory:
            snapshot["strategyMemory"] = strategy_memory
        route_cadence_memory = self._build_route_cadence_memory(profile.id)
        if route_cadence_memory:
            snapshot["routeCadenceMemory"] = route_cadence_memory
        route_recovery_memory = self._build_route_recovery_memory(
            user_id=profile.id,
            strategy_memory=strategy_memory,
            skill_trajectory=skill_trajectory,
            route_cadence_memory=route_cadence_memory,
        )
        if route_recovery_memory:
            snapshot["routeRecoveryMemory"] = route_recovery_memory
        route_reentry_progress = self._build_route_reentry_progress(
            current_state=None,
            route_recovery_memory=route_recovery_memory,
        )
        if route_reentry_progress:
            snapshot["routeReentryProgress"] = route_reentry_progress
        route_follow_up_memory = self._build_route_follow_up_memory(
            route_recovery_memory=route_recovery_memory,
            route_reentry_progress=route_reentry_progress,
            route_entry_memory=None,
            ritual_signal_memory=None,
        )
        if route_follow_up_memory:
            snapshot["routeFollowUpMemory"] = route_follow_up_memory
        snapshot["learningBlueprint"] = self._build_learning_blueprint(
            profile=profile,
            focus_area=focus_area,
            recommendation=recommendation,
            current_state=None,
            current_strategy_summary=self._build_strategy_summary(profile, focus_area, recommendation, session),
            next_best_action="Open the first personal route and keep the path connected.",
            route_snapshot=snapshot,
        )
        return snapshot

    def _build_learning_blueprint(
        self,
        *,
        profile: UserProfile,
        focus_area: str,
        recommendation: LessonRecommendation | None,
        current_state: LearnerJourneyState | None,
        current_strategy_summary: str,
        next_best_action: str,
        plan: DailyLoopPlan | None = None,
        route_snapshot: dict | None = None,
    ) -> dict:
        snapshot = route_snapshot or (current_state.strategy_snapshot if current_state else {})
        route_recovery_memory = (
            snapshot.get("routeRecoveryMemory")
            if isinstance(snapshot.get("routeRecoveryMemory"), dict)
            else self._extract_route_recovery_memory(current_state)
        )
        route_follow_up_memory = (
            snapshot.get("routeFollowUpMemory")
            if isinstance(snapshot.get("routeFollowUpMemory"), dict)
            else self._extract_route_follow_up_memory(current_state)
        )
        skill_trajectory = (
            snapshot.get("skillTrajectory")
            if isinstance(snapshot.get("skillTrajectory"), dict)
            else self._extract_skill_trajectory(current_state)
        )
        strategy_memory = (
            snapshot.get("strategyMemory")
            if isinstance(snapshot.get("strategyMemory"), dict)
            else self._extract_strategy_memory(current_state)
        )
        weak_spots = [
            weak_spot.model_dump(mode="json", by_alias=True)
            for weak_spot in self._mistake_repository.list_weak_spots(profile.id, limit=3)
        ]
        daily_loop_plan = (
            plan.model_dump(mode="json", by_alias=True)
            if plan is not None
            else None
        )
        blueprint = self._learning_blueprint_service.build(
            profile=profile,
            focus_area=focus_area,
            journey_stage=plan.stage if plan is not None else current_state.stage if current_state else "daily_loop_ready",
            current_strategy_summary=current_strategy_summary,
            next_best_action=next_best_action,
            recommendation=recommendation,
            route_recovery_memory=route_recovery_memory,
            route_follow_up_memory=route_follow_up_memory,
            skill_trajectory=skill_trajectory,
            strategy_memory=strategy_memory,
            weak_spots=weak_spots,
            daily_loop_plan=daily_loop_plan,
        )
        return blueprint.model_dump(mode="json", by_alias=True)

    @classmethod
    def _attach_daily_ritual(
        cls,
        plan: DailyLoopPlan,
        *,
        profile: UserProfile,
        current_state: LearnerJourneyState | None,
    ) -> DailyLoopPlan:
        ritual = DailyRitual.model_validate(
            cls._build_daily_ritual(plan, profile=profile, current_state=current_state)
        )
        task_driven_input = cls._build_task_driven_input(
            plan,
            profile=profile,
            current_state=current_state,
        )
        return plan.model_copy(
            update={
                "ritual": ritual,
                "task_driven_input": TaskDrivenInput.model_validate(task_driven_input) if task_driven_input else None,
            }
        )

    @classmethod
    def _build_daily_ritual(
        cls,
        plan: DailyLoopPlan,
        *,
        profile: UserProfile,
        current_state: LearnerJourneyState | None,
    ) -> dict:
        session_summary = cls._extract_session_summary(current_state)
        tomorrow_preview = (
            current_state.strategy_snapshot.get("tomorrowPreview")
            if current_state and isinstance(current_state.strategy_snapshot.get("tomorrowPreview"), dict)
            else None
        )
        stage_specs: list[dict] = []
        for step in plan.steps:
            emphasis = cls._map_daily_ritual_emphasis(step.id, step.skill)
            stage_specs.append(
                {
                    "id": step.id,
                    "title": step.title,
                    "summary": step.description,
                    "emphasis": emphasis,
                    "required": True,
                }
            )

        if not any(stage["id"] == "summary" for stage in stage_specs):
            stage_specs.append(
                {
                    "id": "summary",
                    "title": "Strategic summary",
                    "summary": "Close the route by naming what moved, what still needs watching, and what the next step should be.",
                    "emphasis": "closure",
                    "required": True,
                }
            )

        return {
            "headline": f"{plan.recommended_lesson_title} ritual",
            "promise": cls._build_daily_ritual_promise(plan, profile, current_state),
            "completionRule": (
                "The ritual is only complete after the final strategic summary closes the route and updates the next step."
            ),
            "closureRule": (
                str(tomorrow_preview.get("nextStepHint"))
                if tomorrow_preview and tomorrow_preview.get("nextStepHint")
                else str(session_summary.get("strategyShift"))
                if session_summary and session_summary.get("strategyShift")
                else plan.next_step_hint
            ),
            "stages": stage_specs,
        }

    @staticmethod
    def _map_daily_ritual_emphasis(step_id: str, skill: str) -> str:
        return (
            "entry"
            if step_id == "warm-start"
            else "memory"
            if step_id == "vocabulary-recall"
            else "pattern"
            if step_id == "grammar-pattern"
            else "input"
            if step_id == "input"
            else "output"
            if step_id == "response"
            else "micro-fix"
            if step_id == "pronunciation"
            else "reinforcement"
            if step_id == "reinforcement"
            else "closure"
            if step_id == "summary"
            else skill
        )

    @classmethod
    def _build_daily_ritual_promise(
        cls,
        plan: DailyLoopPlan,
        profile: UserProfile,
        current_state: LearnerJourneyState | None,
    ) -> str:
        day_shape = cls._extract_route_recovery_memory(current_state)
        shape_hint = (
            str(day_shape.get("sessionShape")).replace("_", " ")
            if day_shape and day_shape.get("sessionShape")
            else "connected"
        )
        ritual_elements = set(profile.onboarding_answers.ritual_elements)
        journal_clause = (
            " It should also keep one real-life word journal capture alive so the route remembers language from the learner's own day."
            if "daily_word_journal" in ritual_elements
            else ""
        )
        voice_clause = (
            " A short spontaneous voice pass should stay available too, so the learner hears their own English without over-preparing."
            if {"spontaneous_voice_notes", "highlight_lowlight_reflection"} & ritual_elements
            else ""
        )
        return (
            f"One {shape_hint} daily ritual around {plan.focus_area} that opens with guidance, "
            f"moves through active practice, and closes with an explicit next step inside a {profile.lesson_duration}-minute rhythm."
            f"{journal_clause}{voice_clause}"
        )

    @classmethod
    def _build_task_driven_input(
        cls,
        plan: DailyLoopPlan,
        *,
        profile: UserProfile,
        current_state: LearnerJourneyState | None,
    ) -> dict | None:
        if plan.completed_at:
            return None

        input_lane = cls._infer_input_lane(profile)
        input_step = next(
            (
                step
                for step in plan.steps
                if step.id == "input"
                or str(step.skill).lower() in {"reading", "listening"}
                or "reading" in str(step.title).lower()
                or "listening" in str(step.title).lower()
            ),
            None,
        )
        if input_step is None:
            return None

        response_route = (
            "/writing"
            if cls._infer_output_lane(profile) == "writing"
            else "/speaking"
            if cls._infer_output_lane(profile) == "speaking"
            else "/lesson-runner"
        )
        response_label = (
            "writing response"
            if response_route == "/writing"
            else "spoken response"
            if response_route == "/speaking"
            else "guided route"
        )
        input_label = "reading input" if input_lane == "reading" else "listening input"
        focus_area = current_state.current_focus_area if current_state else plan.focus_area

        return {
            "inputRoute": "/reading" if input_lane == "reading" else "/listening",
            "inputLabel": input_label,
            "responseRoute": response_route,
            "responseLabel": response_label,
            "title": "Text signal mission" if input_lane == "reading" else "Audio signal mission",
            "summary": (
                f"Take one useful text signal from {plan.headline}, convert it into a clearer {response_label}, "
                f"and return it to the route around {focus_area}."
                if input_lane == "reading"
                else f"Take one useful audio signal from {plan.headline}, convert it into a clearer {response_label}, "
                f"and return it to the route around {focus_area}."
            ),
            "bridge": (
                f"After the input pass, go straight back into the guided route while the signal is still fresh."
                if response_route == "/lesson-runner"
                else f"After the input pass, move the signal into {response_label} before returning to the wider route."
            ),
            "closure": f"The mission closes only after the {response_label} feeds the next connected route step.",
        }

    @staticmethod
    def _extract_ritual_value(plan: DailyLoopPlan, key: str):
        ritual = getattr(plan, "ritual", None)
        if ritual is None:
            return None
        if isinstance(ritual, dict):
            return ritual.get(key)
        return getattr(ritual, key, None)

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
        skill_trajectory = self._build_skill_trajectory_memory(
            profile.id,
            current_state,
            active_skill_focus=profile.onboarding_answers.active_skill_focus,
        )
        if skill_trajectory:
            snapshot["skillTrajectory"] = skill_trajectory
        strategy_memory = self._build_strategy_memory(
            profile.id,
            current_state,
            active_skill_focus=profile.onboarding_answers.active_skill_focus,
        )
        if strategy_memory:
            snapshot["strategyMemory"] = strategy_memory
        route_cadence_memory = self._build_route_cadence_memory(profile.id, current_state)
        if route_cadence_memory:
            snapshot["routeCadenceMemory"] = route_cadence_memory
        route_recovery_memory = self._build_route_recovery_memory(
            user_id=profile.id,
            current_state=current_state,
            skill_trajectory=skill_trajectory,
            strategy_memory=strategy_memory,
            route_cadence_memory=route_cadence_memory,
        )
        if route_recovery_memory:
            snapshot["routeRecoveryMemory"] = route_recovery_memory
        route_reentry_progress = self._build_route_reentry_progress(
            current_state=current_state,
            route_recovery_memory=route_recovery_memory,
        )
        if route_reentry_progress:
            snapshot["routeReentryProgress"] = route_reentry_progress
        else:
            snapshot.pop("routeReentryProgress", None)
        route_follow_up_memory = self._build_route_follow_up_memory(
            route_recovery_memory=route_recovery_memory,
            route_reentry_progress=route_reentry_progress,
            route_entry_memory=self._extract_route_entry_memory(current_state),
            ritual_signal_memory=self._extract_ritual_signal_memory(current_state),
            existing_route_follow_up_memory=self._extract_route_follow_up_memory(current_state),
        )
        if route_follow_up_memory:
            snapshot["routeFollowUpMemory"] = route_follow_up_memory
        else:
            snapshot.pop("routeFollowUpMemory", None)
        snapshot["learningBlueprint"] = self._build_learning_blueprint(
            profile=profile,
            focus_area=plan.focus_area,
            recommendation=recommendation,
            current_state=current_state,
            current_strategy_summary=self._build_strategy_summary(
                profile,
                plan.focus_area,
                recommendation,
                None,
                current_state,
            ),
            next_best_action="Finish today's loop to unlock the next focused step.",
            plan=plan,
            route_snapshot=snapshot,
        )
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
        skill_trajectory = self._build_skill_trajectory_memory(
            profile.id,
            current_state,
            active_skill_focus=profile.onboarding_answers.active_skill_focus,
        )
        if skill_trajectory:
            snapshot["skillTrajectory"] = skill_trajectory
        strategy_memory = self._build_strategy_memory(
            profile.id,
            current_state,
            active_skill_focus=profile.onboarding_answers.active_skill_focus,
        )
        if strategy_memory:
            snapshot["strategyMemory"] = strategy_memory
        route_cadence_memory = self._build_route_cadence_memory(profile.id, current_state)
        if route_cadence_memory:
            snapshot["routeCadenceMemory"] = route_cadence_memory
        route_recovery_memory = self._build_route_recovery_memory(
            user_id=profile.id,
            current_state=current_state,
            session_summary=self._extract_session_summary(current_state),
            skill_trajectory=skill_trajectory,
            strategy_memory=strategy_memory,
            route_cadence_memory=route_cadence_memory,
        )
        if route_recovery_memory:
            snapshot["routeRecoveryMemory"] = route_recovery_memory
        route_reentry_progress = self._build_route_reentry_progress(
            current_state=current_state,
            route_recovery_memory=route_recovery_memory,
        )
        if route_reentry_progress:
            snapshot["routeReentryProgress"] = route_reentry_progress
        else:
            snapshot.pop("routeReentryProgress", None)
        route_follow_up_memory = self._build_route_follow_up_memory(
            route_recovery_memory=route_recovery_memory,
            route_reentry_progress=route_reentry_progress,
            route_entry_memory=self._extract_route_entry_memory(current_state),
            ritual_signal_memory=self._extract_ritual_signal_memory(current_state),
            existing_route_follow_up_memory=self._extract_route_follow_up_memory(current_state),
        )
        if route_follow_up_memory:
            snapshot["routeFollowUpMemory"] = route_follow_up_memory
        else:
            snapshot.pop("routeFollowUpMemory", None)
        ritual_signal_memory = self._build_ritual_signal_memory(profile.id, current_state)
        if ritual_signal_memory:
            snapshot["ritualSignalMemory"] = ritual_signal_memory
        else:
            snapshot.pop("ritualSignalMemory", None)
        current_strategy_summary = self._build_strategy_summary(
            profile,
            plan.focus_area,
            recommendation,
            None,
            current_state,
        )
        snapshot["learningBlueprint"] = self._build_learning_blueprint(
            profile=profile,
            focus_area=plan.focus_area,
            recommendation=recommendation,
            current_state=current_state,
            current_strategy_summary=current_strategy_summary,
            next_best_action=plan.next_step_hint,
            plan=plan,
            route_snapshot=snapshot,
        )
        self._repository.upsert_journey_state(
            user_id=profile.id,
            stage="daily_loop_ready",
            source=current_state.source,
            preferred_mode=profile.onboarding_answers.preferred_mode,
            diagnostic_readiness=profile.onboarding_answers.diagnostic_readiness,
            time_budget_minutes=profile.lesson_duration,
            current_focus_area=plan.focus_area,
            current_strategy_summary=current_strategy_summary,
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
        session_summary = self._extract_session_summary(current_state)
        practice_shift = (
            session_summary.get("practiceMixEvaluation")
            if session_summary and isinstance(session_summary.get("practiceMixEvaluation"), dict)
            else None
        )
        task_driven_transfer_evaluation = (
            session_summary.get("taskDrivenTransferEvaluation")
            if session_summary and isinstance(session_summary.get("taskDrivenTransferEvaluation"), dict)
            else None
        )
        skill_trajectory = self._build_skill_trajectory_memory(
            profile.id,
            current_state,
            active_skill_focus=profile.onboarding_answers.active_skill_focus,
        )
        strategy_memory = self._build_strategy_memory(
            profile.id,
            current_state,
            active_skill_focus=profile.onboarding_answers.active_skill_focus,
        )
        route_cadence_memory = self._build_route_cadence_memory(profile.id, current_state)
        route_recovery_memory = self._build_route_recovery_memory(
            user_id=profile.id,
            current_state=current_state,
            session_summary=session_summary,
            skill_trajectory=skill_trajectory,
            strategy_memory=strategy_memory,
            route_cadence_memory=route_cadence_memory,
        )
        active_plan_seed = snapshot.get("activePlanSeed") if isinstance(snapshot.get("activePlanSeed"), dict) else None
        input_lane = self._infer_input_lane(profile)
        recent_lessons = self._lesson_repository.list_recent_completed_lessons(profile.id, limit=3)
        route_reentry_progress = self._build_route_reentry_progress(
            current_state=current_state,
            route_recovery_memory=route_recovery_memory,
        )
        route_entry_memory = self._extract_route_entry_memory(current_state)
        ritual_signal_memory = self._build_ritual_signal_memory(profile.id, current_state)
        learning_blueprint = (
            snapshot.get("learningBlueprint")
            if isinstance(snapshot.get("learningBlueprint"), dict)
            else None
        )
        if learning_blueprint is None:
            learning_blueprint = self._build_learning_blueprint(
                profile=profile,
                focus_area=plan.focus_area,
                recommendation=recommendation,
                current_state=current_state,
                current_strategy_summary=plan.summary,
                next_best_action=plan.next_step_hint,
                plan=plan,
                route_snapshot={
                    **snapshot,
                    "skillTrajectory": skill_trajectory,
                    "strategyMemory": strategy_memory,
                    "routeCadenceMemory": route_cadence_memory,
                    "routeRecoveryMemory": route_recovery_memory,
                },
            )
        module_rotation = build_module_rotation(
            recommendation_lesson_type=recommendation.lesson_type if recommendation else plan.recommended_lesson_type,
            recommendation_focus_area=plan.focus_area,
            recent_lessons=recent_lessons,
            due_vocabulary=due_vocabulary,
            listening_focus=input_lane if input_lane == "listening" else None,
            mistake_resolution=[],
            active_skill_focus=profile.onboarding_answers.active_skill_focus,
            preferred_mode=profile.onboarding_answers.preferred_mode,
            route_seed_source=(
                str(active_plan_seed.get("source"))
                if active_plan_seed and active_plan_seed.get("source")
                else "tomorrow_preview"
                if continuity_seed
                else "daily_loop_plan"
            ),
        )
        practice_mix = self._build_route_practice_mix(
            profile=profile,
            plan=plan,
            module_rotation=module_rotation,
            weak_spots=weak_spots,
            due_vocabulary=due_vocabulary,
            continuity_seed=continuity_seed,
            input_lane=input_lane,
            practice_shift=practice_shift,
            skill_trajectory=skill_trajectory,
            strategy_memory=strategy_memory,
            route_recovery_memory=route_recovery_memory,
            route_reentry_progress=route_reentry_progress,
            route_entry_memory=route_entry_memory,
            route_follow_up_memory=self._extract_route_follow_up_memory(current_state),
            task_driven_transfer_evaluation=task_driven_transfer_evaluation,
            ritual_signal_memory=ritual_signal_memory,
        )
        return {
            "focusArea": plan.focus_area,
            "sessionKind": plan.session_kind,
            "routeHeadline": plan.headline,
            "routeSummary": plan.summary,
            "dailyRitualHeadline": (
                self._extract_ritual_value(plan, "headline")
                if getattr(plan, "ritual", None)
                else None
            ),
            "dailyRitualPromise": (
                self._extract_ritual_value(plan, "promise")
                if getattr(plan, "ritual", None)
                else None
            ),
            "dailyRitualStageIds": (
                [
                    stage.id if hasattr(stage, "id") else stage.get("id")
                    for stage in (self._extract_ritual_value(plan, "stages") or [])
                    if (hasattr(stage, "id") and getattr(stage, "id")) or (isinstance(stage, dict) and stage.get("id"))
                ]
                if getattr(plan, "ritual", None)
                else None
            ),
            "taskDrivenInput": (
                plan.task_driven_input.model_dump(mode="json", by_alias=True)
                if getattr(plan, "task_driven_input", None)
                else None
            ),
            "whyNow": plan.why_this_now,
            "nextBestAction": plan.next_step_hint,
            "primaryGoal": profile.onboarding_answers.primary_goal,
            "professionTrack": profile.profession_track,
            "preferredMode": profile.onboarding_answers.preferred_mode,
            "activeSkillFocus": profile.onboarding_answers.active_skill_focus,
            "inputLane": input_lane,
            "outputLane": self._infer_output_lane(profile),
            "moduleRotationKeys": [item.module_key for item in module_rotation[:3]],
            "moduleRotationTitles": [item.title for item in module_rotation[:3]],
            "weakSpotTitles": [spot.title for spot in weak_spots[:3]],
            "weakSpotCategories": [spot.category for spot in weak_spots[:3]],
            "practiceMix": practice_mix,
            "skillTrajectory": skill_trajectory,
            "strategyMemory": strategy_memory,
            "routeCadenceMemory": route_cadence_memory,
            "routeRecoveryMemory": route_recovery_memory,
            "routeReentryProgress": route_reentry_progress,
            "routeEntryMemory": route_entry_memory,
            "routeEntryResetActive": bool(self._build_route_entry_memory_reset_label(route_entry_memory)),
            "routeEntryResetLabel": self._build_route_entry_memory_reset_label(route_entry_memory),
            "ritualSignalMemory": ritual_signal_memory,
            "ritualSignalType": (
                str(ritual_signal_memory.get("activeSignalType"))
                if ritual_signal_memory and ritual_signal_memory.get("activeSignalType")
                else None
            ),
            "ritualSignalLabel": (
                str(ritual_signal_memory.get("activeLabel"))
                if ritual_signal_memory and ritual_signal_memory.get("activeLabel")
                else None
            ),
            "ritualSignalStage": (
                str(ritual_signal_memory.get("windowStage"))
                if ritual_signal_memory and ritual_signal_memory.get("windowStage")
                else None
            ),
            "ritualSignalWindowStage": (
                str(ritual_signal_memory.get("routeWindowStage"))
                if ritual_signal_memory and ritual_signal_memory.get("routeWindowStage")
                else None
            ),
            "ritualSignalWindowDays": (
                int(ritual_signal_memory.get("windowDays"))
                if ritual_signal_memory and ritual_signal_memory.get("windowDays") is not None
                else None
            ),
            "ritualSignalWindowRemainingDays": (
                int(ritual_signal_memory.get("windowRemainingDays"))
                if ritual_signal_memory and ritual_signal_memory.get("windowRemainingDays") is not None
                else None
            ),
            "ritualSignalSummary": (
                str(ritual_signal_memory.get("summary"))
                if ritual_signal_memory and ritual_signal_memory.get("summary")
                else None
            ),
            "learningBlueprintHeadline": (
                str(learning_blueprint.get("headline"))
                if learning_blueprint and learning_blueprint.get("headline")
                else None
            ),
            "learningBlueprintNorthStar": (
                str(learning_blueprint.get("northStar"))
                if learning_blueprint and learning_blueprint.get("northStar")
                else None
            ),
            "learningBlueprintPhaseLabel": (
                str(learning_blueprint.get("currentPhaseLabel"))
                if learning_blueprint and learning_blueprint.get("currentPhaseLabel")
                else None
            ),
            "learningBlueprintSuccessSignal": (
                str(learning_blueprint.get("successSignal"))
                if learning_blueprint and learning_blueprint.get("successSignal")
                else None
            ),
            "learningBlueprintPillars": (
                [
                    str(item.get("title"))
                    for item in learning_blueprint.get("focusPillars", [])
                    if isinstance(item, dict) and item.get("title")
                ][:3]
                if learning_blueprint
                else None
            ),
            "skillTrajectorySummary": (
                str(skill_trajectory.get("summary"))
                if skill_trajectory and skill_trajectory.get("summary")
                else None
            ),
            "skillTrajectoryFocus": (
                str(skill_trajectory.get("focusSkill"))
                if skill_trajectory and skill_trajectory.get("focusSkill")
                else None
            ),
            "skillTrajectoryDirection": (
                str(skill_trajectory.get("direction"))
                if skill_trajectory and skill_trajectory.get("direction")
                else None
            ),
            "strategyMemorySummary": (
                str(strategy_memory.get("summary"))
                if strategy_memory and strategy_memory.get("summary")
                else None
            ),
            "strategyMemoryFocus": (
                str(strategy_memory.get("focusSkill"))
                if strategy_memory and strategy_memory.get("focusSkill")
                else None
            ),
            "strategyMemoryLevel": (
                str(strategy_memory.get("persistenceLevel"))
                if strategy_memory and strategy_memory.get("persistenceLevel")
                else None
            ),
            "routeCadenceSummary": (
                str(route_cadence_memory.get("summary"))
                if route_cadence_memory and route_cadence_memory.get("summary")
                else None
            ),
            "routeCadenceStatus": (
                str(route_cadence_memory.get("status"))
                if route_cadence_memory and route_cadence_memory.get("status")
                else None
            ),
            "routeRecoverySummary": (
                str(route_recovery_memory.get("summary"))
                if route_recovery_memory and route_recovery_memory.get("summary")
                else None
            ),
            "routeRecoveryPhase": (
                str(route_recovery_memory.get("phase"))
                if route_recovery_memory and route_recovery_memory.get("phase")
                else None
            ),
            "routeRecoveryActionHint": (
                str(route_recovery_memory.get("actionHint"))
                if route_recovery_memory and route_recovery_memory.get("actionHint")
                else None
            ),
            "routeRecoveryNextPhaseHint": (
                str(route_recovery_memory.get("nextPhaseHint"))
                if route_recovery_memory and route_recovery_memory.get("nextPhaseHint")
                else None
            ),
            "routeRecoveryStage": (
                str(route_recovery_memory.get("reopenStage"))
                if route_recovery_memory and route_recovery_memory.get("reopenStage")
                else None
            ),
            "routeRecoveryExpansionReady": (
                bool(route_recovery_memory.get("expansionReady"))
                if route_recovery_memory and route_recovery_memory.get("expansionReady") is not None
                else None
            ),
            "routeRecoveryFollowUpCompletionCount": (
                int(route_recovery_memory.get("followUpCompletionCount"))
                if route_recovery_memory and route_recovery_memory.get("followUpCompletionCount") is not None
                else None
            ),
            "routeRecoveryDecisionBias": (
                str(route_recovery_memory.get("decisionBias"))
                if route_recovery_memory and route_recovery_memory.get("decisionBias")
                else None
            ),
            "routeRecoveryDecisionWindowDays": (
                int(route_recovery_memory.get("decisionWindowDays"))
                if route_recovery_memory and route_recovery_memory.get("decisionWindowDays") is not None
                else None
            ),
            "routeRecoveryDecisionWindowStage": (
                str(route_recovery_memory.get("decisionWindowStage"))
                if route_recovery_memory and route_recovery_memory.get("decisionWindowStage")
                else None
            ),
            "routeRecoveryDecisionWindowRemainingDays": (
                int(route_recovery_memory.get("decisionWindowRemainingDays"))
                if route_recovery_memory and route_recovery_memory.get("decisionWindowRemainingDays") is not None
                else None
            ),
            "routeReentryNextRoute": (
                str(route_reentry_progress.get("nextRoute"))
                if route_reentry_progress and route_reentry_progress.get("nextRoute")
                else None
            ),
            "routeReentryNextLabel": (
                self._label_route_reentry_route(str(route_reentry_progress.get("nextRoute")))
                if route_reentry_progress and route_reentry_progress.get("nextRoute")
                else None
            ),
            "practiceShiftSummary": (
                str(practice_shift.get("summaryLine"))
                if practice_shift and practice_shift.get("summaryLine")
                else None
            ),
            "leadPracticeTitle": (
                str(practice_shift.get("leadPracticeTitle"))
                if practice_shift and practice_shift.get("leadPracticeTitle")
                else None
            ),
            "weakestPracticeTitle": (
                str(practice_shift.get("weakestPracticeTitle"))
                if practice_shift and practice_shift.get("weakestPracticeTitle")
                else None
            ),
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

    @staticmethod
    def _build_route_practice_mix(
        *,
        profile: UserProfile,
        plan: DailyLoopPlan,
        module_rotation: list,
        weak_spots: list[WeakSpot],
        due_vocabulary: list,
        continuity_seed: dict | None,
        input_lane: str,
        practice_shift: dict | None = None,
        skill_trajectory: dict | None = None,
        strategy_memory: dict | None = None,
        route_recovery_memory: dict | None = None,
        route_reentry_progress: dict | None = None,
        route_entry_memory: dict | None = None,
        route_follow_up_memory: dict | None = None,
        task_driven_transfer_evaluation: dict | None = None,
        ritual_signal_memory: dict | None = None,
    ) -> list[dict]:
        weights = {
            "lesson": 18,
            "speaking": 12,
            "writing": 8,
            "grammar": 8,
            "vocabulary": 6,
            "listening": 5,
            "reading": 5,
            "pronunciation": 4,
            "profession": 4,
        }
        title_map = {
            "lesson": "Main lesson flow",
            "speaking": "Speaking practice",
            "writing": "Writing practice",
            "grammar": "Grammar patterning",
            "vocabulary": "Vocabulary recall",
            "listening": "Listening input",
            "reading": "Reading input",
            "pronunciation": "Pronunciation control",
            "profession": "Professional framing",
        }
        reason_map = {
            "lesson": "Keep one connected route instead of fragmenting the session into isolated drills.",
            "speaking": "Speaking keeps the route active in live output.",
            "writing": "Writing slows the route down just enough to stabilize structure before pressure returns.",
            "grammar": "Grammar keeps the route structurally reliable while the skill widens again.",
            "vocabulary": "Vocabulary helps the next response feel easier and more reusable.",
            "listening": "Listening gives the route fresh input before the response block.",
            "reading": "Reading gives the route a calmer text anchor before the response block.",
            "pronunciation": "Pronunciation keeps clarity and confidence attached to the live route.",
            "profession": "Professional framing keeps the route useful in a real scenario, not generic.",
        }
        output_lane = JourneyService._infer_output_lane(profile)
        preferred_mode = profile.onboarding_answers.preferred_mode
        focus_area = plan.focus_area
        active_skill_focus = {
            skill.strip()
            for skill in profile.onboarding_answers.active_skill_focus
            if skill and skill.strip()
        }
        weak_categories = {
            spot.category.strip()
            for spot in weak_spots
            if spot.category and spot.category.strip()
        }
        focus_tokens = {
            token.strip()
            for token in str(focus_area or "").replace("/", ",").split(",")
            if token.strip()
        }
        focus_tokens.update(active_skill_focus)

        if preferred_mode == "text_first":
            weights["writing"] += 11
            weights["reading"] += 9
            weights["speaking"] = max(6, weights["speaking"] - 4)
        elif preferred_mode == "voice_first":
            weights["speaking"] += 9
            weights["pronunciation"] += 7
            weights["listening"] += 4

        if input_lane == "listening":
            weights["listening"] += 5
        elif input_lane == "reading":
            weights["reading"] += 5
        if output_lane == "writing":
            weights["writing"] += 5
        elif output_lane == "speaking":
            weights["speaking"] += 5

        for module_key in focus_tokens:
            if module_key in weights:
                weights[module_key] += 14 if module_key == focus_area else 8

        if "grammar" in weak_categories:
            weights["grammar"] += 6
        if "pronunciation" in weak_categories:
            weights["pronunciation"] += 5
        if "vocabulary" in weak_categories or due_vocabulary:
            weights["vocabulary"] += 7 if due_vocabulary else 4

        if continuity_seed:
            weights["lesson"] += 4
            carry_over = str(continuity_seed.get("carryOverSignalLabel") or "").lower()
            watch_signal = str(continuity_seed.get("watchSignalLabel") or "").lower()
            if "speak" in carry_over or "fluency" in carry_over:
                weights["speaking"] += 4
            if "write" in carry_over:
                weights["writing"] += 4
            if "grammar" in carry_over or "tense" in watch_signal:
                weights["grammar"] += 4
            if "pronunciation" in carry_over or "pronunciation" in watch_signal:
                weights["pronunciation"] += 4

        transfer_outcome = (
            str(task_driven_transfer_evaluation.get("transferOutcome"))
            if task_driven_transfer_evaluation and task_driven_transfer_evaluation.get("transferOutcome")
            else ""
        )
        transfer_input_route = (
            str(task_driven_transfer_evaluation.get("inputRoute"))
            if task_driven_transfer_evaluation and task_driven_transfer_evaluation.get("inputRoute")
            else ""
        )
        transfer_response_route = (
            str(task_driven_transfer_evaluation.get("responseRoute"))
            if task_driven_transfer_evaluation and task_driven_transfer_evaluation.get("responseRoute")
            else ""
        )
        transfer_input_focus = JourneyService._map_route_to_focus_area(transfer_input_route)
        transfer_response_focus = JourneyService._map_route_to_focus_area(transfer_response_route)
        transfer_input_label = (
            str(task_driven_transfer_evaluation.get("inputLabel"))
            if task_driven_transfer_evaluation and task_driven_transfer_evaluation.get("inputLabel")
            else JourneyService._map_task_driven_input_label(transfer_input_route)
            if transfer_input_route
            else None
        )
        transfer_response_label = (
            str(task_driven_transfer_evaluation.get("responseLabel"))
            if task_driven_transfer_evaluation and task_driven_transfer_evaluation.get("responseLabel")
            else JourneyService._map_task_driven_response_label(transfer_response_route)
            if transfer_response_route
            else None
        )
        if transfer_response_focus in weights and transfer_outcome:
            weights["lesson"] += 4
            if transfer_outcome == "held":
                weights[transfer_response_focus] += 5
                if transfer_input_focus in weights:
                    weights[transfer_input_focus] += 3
            elif transfer_outcome == "usable":
                weights[transfer_response_focus] += 9
                if transfer_input_focus in weights:
                    weights[transfer_input_focus] += 4
            else:
                weights[transfer_response_focus] += 12
                if transfer_input_focus in weights:
                    weights[transfer_input_focus] += 4

        ritual_signal_type = (
            str(ritual_signal_memory.get("activeSignalType"))
            if ritual_signal_memory and ritual_signal_memory.get("activeSignalType")
            else ""
        )
        ritual_signal_label = (
            str(ritual_signal_memory.get("activeLabel"))
            if ritual_signal_memory and ritual_signal_memory.get("activeLabel")
            else ""
        )
        ritual_signal_window_stage = (
            str(ritual_signal_memory.get("windowStage"))
            if ritual_signal_memory and ritual_signal_memory.get("windowStage")
            else ""
        )
        if ritual_signal_type == "word_journal":
            if ritual_signal_window_stage == "ready_to_carry":
                weights["lesson"] += 7
                weights["vocabulary"] += 3
                weights["writing"] += 2
                reason_map["lesson"] = (
                    f"The route can widen again while still carrying {ritual_signal_label or 'the saved phrase'} inside the broader lesson flow."
                )
                reason_map["vocabulary"] = (
                    f"{ritual_signal_label or 'The saved phrase'} should stay available as a light support lane instead of forcing another narrow capture pass."
                )
                reason_map["writing"] = (
                    f"Written output should reuse {ritual_signal_label or 'the saved phrase'} naturally inside the broader route."
                )
            elif ritual_signal_window_stage == "reuse_in_route":
                weights["lesson"] += 3
                weights["vocabulary"] += 7
                weights["writing"] += 5
                reason_map["vocabulary"] = (
                    f"The route should reuse the word journal capture around {ritual_signal_label or 'the saved phrase'} once more before it simply rides inside the broader flow."
                )
                reason_map["writing"] = (
                    f"The route should carry {ritual_signal_label or 'the fresh phrase'} through one more connected written response."
                )
            else:
                weights["vocabulary"] += 10
                weights["writing"] += 6
                reason_map["vocabulary"] = (
                    f"The route is protecting the live word journal capture around {ritual_signal_label or 'the saved phrase'}, so vocabulary should come back in real use."
                )
                reason_map["writing"] = (
                    f"The route should carry {ritual_signal_label or 'the fresh phrase'} into written output before the ritual signal fades."
                )
        elif ritual_signal_type == "spontaneous_voice":
            if ritual_signal_window_stage == "ready_to_carry":
                weights["lesson"] += 7
                weights["speaking"] += 3
                weights["pronunciation"] += 2
                reason_map["lesson"] = (
                    f"The route can widen again while keeping the live voice signal from {ritual_signal_label or 'the reflection pass'} inside the broader lesson flow."
                )
                reason_map["speaking"] = (
                    f"The live voice signal from {ritual_signal_label or 'the reflection pass'} should stay available without forcing another narrow ritual pass."
                )
                reason_map["pronunciation"] = (
                    "A light pronunciation layer helps the broader route keep that voice signal clear without rebuilding the whole day around it."
                )
            elif ritual_signal_window_stage == "reuse_in_route":
                weights["lesson"] += 3
                weights["speaking"] += 7
                weights["pronunciation"] += 3
                reason_map["speaking"] = (
                    f"The route should reuse the live voice signal from {ritual_signal_label or 'the reflection pass'} once more before widening fully."
                )
                reason_map["pronunciation"] = (
                    "A light pronunciation layer helps that spontaneous voice signal settle across one more connected response."
                )
            else:
                weights["speaking"] += 10
                weights["pronunciation"] += 4
                reason_map["speaking"] = (
                    f"The route is protecting the live voice signal from {ritual_signal_label or 'the reflection pass'}, so speaking should stay active across the next response."
                )
                reason_map["pronunciation"] = (
                    "A light pronunciation layer helps the spontaneous voice ritual settle without turning into pressure."
                )

        trajectory_focus = (
            str(skill_trajectory.get("focusSkill"))
            if skill_trajectory and skill_trajectory.get("focusSkill")
            else ""
        )
        trajectory_direction = (
            str(skill_trajectory.get("direction"))
            if skill_trajectory and skill_trajectory.get("direction")
            else ""
        )
        if trajectory_focus in weights:
            weights[trajectory_focus] += (
                8 if trajectory_direction == "slipping" else 5 if trajectory_direction == "stable" else 2
            )
            if trajectory_direction == "slipping":
                reason_map[trajectory_focus] = (
                    "Recent learner-model history shows this skill slipping across sessions, so the route keeps more support here."
                )
            elif trajectory_direction == "stable":
                reason_map[trajectory_focus] = (
                    "Recent learner-model history says this skill is still fragile, so the route keeps it active instead of assuming it is solved."
                )
            else:
                reason_map[trajectory_focus] = (
                    "Recent learner-model history shows this skill improving, so the route can use that momentum as a support lane."
                )

        strategy_focus = (
            str(strategy_memory.get("focusSkill"))
            if strategy_memory and strategy_memory.get("focusSkill")
            else ""
        )
        strategy_level = (
            str(strategy_memory.get("persistenceLevel"))
            if strategy_memory and strategy_memory.get("persistenceLevel")
            else ""
        )
        if strategy_focus in weights:
            weights[strategy_focus] += (
                9 if strategy_level == "persistent" else 6 if strategy_level == "recurring" else 3
            )
            if strategy_level == "persistent":
                reason_map[strategy_focus] = (
                    "Longer learner-memory keeps returning to this skill, so the route treats it as a durable strategy signal."
                )
            elif strategy_level == "recurring":
                reason_map[strategy_focus] = (
                    "This skill keeps resurfacing across sessions, so the route revisits it on purpose instead of waiting for another drop."
                )
            elif strategy_level == "emerging":
                reason_map[strategy_focus] = (
                    "This skill is starting to drift across the longer history, so the route protects it early."
                )

        recovery_phase = (
            str(route_recovery_memory.get("phase"))
            if route_recovery_memory and route_recovery_memory.get("phase")
            else ""
        )
        recovery_reopen_stage = (
            str(route_recovery_memory.get("reopenStage"))
            if route_recovery_memory and route_recovery_memory.get("reopenStage")
            else ""
        )
        recovery_focus = (
            str(route_recovery_memory.get("focusSkill"))
            if route_recovery_memory and route_recovery_memory.get("focusSkill")
            else ""
        )
        recovery_support = (
            str(route_recovery_memory.get("supportPracticeTitle"))
            if route_recovery_memory and route_recovery_memory.get("supportPracticeTitle")
            else ""
        )
        if recovery_phase == "route_rebuild":
            weights["lesson"] += 8
            weights["vocabulary"] += 6
            if recovery_focus in weights:
                weights[recovery_focus] += 5
            reason_map["lesson"] = (
                "The route is in a multi-day rebuild phase, so the main lesson flow needs to reopen gently instead of fragmenting."
            )
            reason_map["vocabulary"] = (
                "A lighter vocabulary layer helps reopen the route with a visible win before wider pressure returns."
            )
        elif recovery_phase == "protected_return":
            weights["lesson"] += 6
            if preferred_mode == "text_first":
                weights["writing"] += 5
            else:
                weights["speaking"] += 3
            if recovery_focus in weights:
                weights[recovery_focus] += 4
            reason_map["lesson"] = (
                "The route is still in a protected return phase, so the session should stay connected and not widen too abruptly."
            )
        elif recovery_phase == "support_reopen_arc":
            if recovery_reopen_stage == "ready_to_expand":
                weights["lesson"] += 10
                weights["listening"] += 2
                if recovery_focus in weights:
                    weights[recovery_focus] += 2
                    reason_map[recovery_focus] = (
                        "This support lane stays available inside the route, but it no longer needs to carry the whole session by itself."
                    )
                reason_map["lesson"] = (
                    "The reopen arc is ready to widen, so the broader daily route should lead again while the support lane stays available inside it."
                )
            elif recovery_reopen_stage == "settling_back_in":
                weights["lesson"] += 6
                if recovery_focus in weights:
                    weights[recovery_focus] += 8
                    reason_map[recovery_focus] = (
                        "The reopened support lane still needs one more connected settling pass before the wider route returns."
                    )
                reason_map["lesson"] = (
                    "The route is reconnecting through the daily flow, but it still needs to protect one more settling pass around the reopened support lane."
                )
            else:
                weights["lesson"] += 5
                if recovery_focus in weights:
                    weights[recovery_focus] += 6
                    reason_map[recovery_focus] = (
                        "The calmer reset has already landed, so this support lane can return early inside the next connected route."
                    )
                reason_map["lesson"] = (
                    "The route is reopening a deferred support lane, but it still needs the main lesson flow to stay connected around it."
                )
        elif recovery_phase == "skill_repair_cycle" and recovery_focus in weights:
            weights[recovery_focus] += 7
            reason_map[recovery_focus] = (
                "Multi-day recovery strategy keeps returning to this skill, so the route treats it as the main repair cycle across several sessions."
            )
        elif recovery_phase == "targeted_stabilization" and recovery_focus in weights:
            weights[recovery_focus] += 5
            if recovery_support:
                reason_map[recovery_focus] = (
                    f"The route is stabilizing {recovery_focus} across the next sessions, with {recovery_support} acting as the support lane."
                )
            recovery_decision_bias = (
                str(route_recovery_memory.get("decisionBias"))
                if route_recovery_memory and route_recovery_memory.get("decisionBias")
                else ""
            )
            recovery_decision_stage = (
                str(route_recovery_memory.get("decisionWindowStage"))
                if route_recovery_memory and route_recovery_memory.get("decisionWindowStage")
                else ""
            )
            if recovery_decision_bias == "task_transfer_window":
                if recovery_decision_stage == "protect_response":
                    weights[recovery_focus] += 6
                    weights["lesson"] += 4
                    reason_map[recovery_focus] = (
                        f"The route is in a protected transfer window, so {recovery_support or recovery_focus} should carry the next session more deliberately."
                    )
                elif recovery_decision_stage == "stabilize_transfer":
                    weights[recovery_focus] += 4
                    weights["lesson"] += 5
                    reason_map[recovery_focus] = (
                        f"The route is in a stabilizing transfer pass, so {recovery_support or recovery_focus} stays active while the broader lesson reconnects around it."
                    )
        elif recovery_phase == "steady_extension" and recovery_focus in weights:
            recovery_decision_bias = (
                str(route_recovery_memory.get("decisionBias"))
                if route_recovery_memory and route_recovery_memory.get("decisionBias")
                else ""
            )
            recovery_decision_stage = (
                str(route_recovery_memory.get("decisionWindowStage"))
                if route_recovery_memory and route_recovery_memory.get("decisionWindowStage")
                else ""
            )
            if recovery_decision_bias == "task_transfer_window" and recovery_decision_stage == "ready_to_widen":
                weights["lesson"] += 8
                weights[recovery_focus] += 2
                reason_map["lesson"] = (
                    f"The protected transfer window has already held, so the broader lesson can widen again while {recovery_support or recovery_focus} stays available."
                )

        if practice_shift:
            lead_practice_key = str(practice_shift.get("leadPracticeKey") or "")
            weakest_practice_key = str(practice_shift.get("weakestPracticeKey") or "")
            strongest_practice_key = str(practice_shift.get("strongestPracticeKey") or "")
            lead_outcome = str(practice_shift.get("leadOutcome") or "")

            if lead_practice_key in weights:
                weights[lead_practice_key] += 4 if lead_outcome == "held" else 2 if lead_outcome == "usable" else 1
            if weakest_practice_key in weights:
                weights[weakest_practice_key] += 9 if lead_outcome in {"held", "usable"} else 6
                reason_map[weakest_practice_key] = (
                    "Yesterday this practice type stayed weaker, so the next route should give it more structured support."
                )
            if strongest_practice_key in weights and strongest_practice_key != lead_practice_key:
                weights[strongest_practice_key] += 5 if lead_outcome == "fragile" else 2
                reason_map[strongest_practice_key] = (
                    "This practice type looked most reliable in the previous route and can support the next session."
                )

        reentry_next_route = (
            str(route_reentry_progress.get("nextRoute"))
            if route_reentry_progress and route_reentry_progress.get("nextRoute")
            else ""
        )
        reentry_phase = (
            str(route_reentry_progress.get("phase"))
            if route_reentry_progress and route_reentry_progress.get("phase")
            else ""
        )
        reentry_focus = JourneyService._map_route_to_focus_area(reentry_next_route)
        route_entry_reset_label = JourneyService._build_route_entry_memory_reset_label(route_entry_memory)
        route_entry_reset_active = bool(route_entry_reset_label)
        if reentry_focus in weights:
            if route_entry_reset_active:
                weights[reentry_focus] = max(4, weights[reentry_focus] - 6)
                weights["lesson"] += 11
                weights["vocabulary"] += 4
                if recovery_focus in weights:
                    weights[recovery_focus] += 4
                reason_map["lesson"] = (
                    "This route resets through the calmer main lesson flow before reopening the same support surface again."
                )
                reason_map["vocabulary"] = (
                    "A lighter recall layer helps the route regain momentum before the repeated support surface reopens."
                )
                reason_map[reentry_focus] = (
                    f"{route_entry_reset_label.capitalize()} has already reopened repeatedly, so today's route keeps it lighter until the calmer main path settles again."
                )
            else:
                reentry_boost = 16
                if recovery_phase == "support_reopen_arc" and recovery_reopen_stage == "ready_to_expand":
                    reentry_boost = 4
                    reason_map[reentry_focus] = (
                        f"{JourneyService._label_route_reentry_route(reentry_next_route)} stays available inside the wider route, but it no longer needs to lead the whole session."
                    )
                elif recovery_phase == "support_reopen_arc" and recovery_reopen_stage == "settling_back_in":
                    reentry_boost = 12
                    reason_map[reentry_focus] = (
                        f"The active reopen arc still needs one more settling pass through {JourneyService._label_route_reentry_route(reentry_next_route)} before the route widens."
                    )
                else:
                    reason_map[reentry_focus] = (
                        f"The active recovery sequence should reopen through {JourneyService._label_route_reentry_route(reentry_next_route)}, "
                        "so the route raises this practice directly inside the next session."
                    )
                weights[reentry_focus] += reentry_boost
                if reentry_phase == "skill_repair_cycle":
                    weights["lesson"] += 3
                if reentry_focus == "writing" and preferred_mode != "voice_first":
                    weights["writing"] += 4
                elif reentry_focus == "speaking":
                    weights["speaking"] += 3
                elif reentry_focus == "grammar":
                    weights["grammar"] += 2

        task_driven_stage = (
            str(route_follow_up_memory.get("stageLabel"))
            if route_follow_up_memory and route_follow_up_memory.get("stageLabel")
            else ""
        )
        task_driven_response_route = (
            str(route_follow_up_memory.get("currentRoute"))
            if route_follow_up_memory and route_follow_up_memory.get("currentRoute")
            else ""
        )
        task_driven_input_route = (
            str(route_follow_up_memory.get("lastCompletedRoute"))
            if route_follow_up_memory and route_follow_up_memory.get("lastCompletedRoute")
            else ""
        )
        task_driven_response_focus = JourneyService._map_route_to_focus_area(task_driven_response_route)
        task_driven_input_focus = JourneyService._map_route_to_focus_area(task_driven_input_route)
        if task_driven_stage == "Task-driven handoff":
            weights["lesson"] += 4
            reason_map["lesson"] = (
                "The route is carrying a task-driven handoff, so the main lesson flow should keep the input and response steps connected instead of resetting between them."
            )
            if task_driven_response_focus in weights:
                weights[task_driven_response_focus] += 10
                reason_map[task_driven_response_focus] = (
                    f"The route has already taken its input signal, so the next session should consolidate through {JourneyService._map_task_driven_response_label(task_driven_response_route)}."
                )
            if task_driven_input_focus in weights:
                weights[task_driven_input_focus] += 6
                reason_map[task_driven_input_focus] = (
                    f"The previous route already opened through {JourneyService._map_task_driven_input_label(task_driven_input_route)}, so this signal should stay visible while the response step lands."
                )

        for boost, item in enumerate(module_rotation[:4]):
            weights[item.module_key] = weights.get(item.module_key, 4) + (14 - boost * 3)
            title_map[item.module_key] = item.title
            reason_map[item.module_key] = item.reason

        if transfer_response_focus in weights and transfer_outcome:
            if transfer_outcome == "held":
                reason_map["lesson"] = (
                    f"The previous {transfer_input_label or 'task-driven input'} carried well into {transfer_response_label or 'the response lane'}, so the main lesson can widen while keeping that transfer alive."
                )
                reason_map[transfer_response_focus] = (
                    f"The last route proved that {transfer_response_label or 'the response lane'} can hold the signal from {transfer_input_label or 'the input pass'}, so it stays active inside a broader lesson-led mix."
                )
            elif transfer_outcome == "usable":
                reason_map["lesson"] = (
                    f"The previous route got useful value from {transfer_input_label or 'the input pass'}, but the main lesson still needs to keep {transfer_response_label or 'the response lane'} connected for one more pass."
                )
                reason_map[transfer_response_focus] = (
                    f"The transfer into {transfer_response_label or 'the response lane'} worked, but it still needs one more connected pass before the route widens."
                )
            else:
                reason_map["lesson"] = (
                    f"The route should stay connected around {transfer_response_label or 'the response lane'} so the signal from {transfer_input_label or 'the input pass'} does not get lost between sessions."
                )
                reason_map[transfer_response_focus] = (
                    f"The move from {transfer_input_label or 'the input pass'} into {transfer_response_label or 'the response lane'} is still fragile, so the next session deliberately protects that response lane."
                )

        primary_goal_text = str(profile.onboarding_answers.primary_goal or "").lower()
        if profile.profession_track and profile.profession_track != "general" and (
            "profession" in focus_tokens or "work" in primary_goal_text
        ):
            weights["profession"] += 6

        if ritual_signal_window_stage == "ready_to_carry":
            ritual_lead_module = (
                "vocabulary"
                if ritual_signal_type == "word_journal"
                else "speaking"
                if ritual_signal_type == "spontaneous_voice"
                else ""
            )
            if ritual_lead_module in weights:
                weights["lesson"] = max(weights["lesson"], weights[ritual_lead_module] + 2)

        ordered_weights = sorted(weights.items(), key=lambda item: item[1], reverse=True)
        total = sum(weight for _key, weight in ordered_weights) or 1
        mix: list[dict] = []
        for index, (module_key, weight) in enumerate(ordered_weights[:5]):
            share = round(weight / total * 100)
            emphasis = "lead" if index == 0 else "support" if index < 3 else "light"
            mix.append(
                {
                    "moduleKey": module_key,
                    "title": title_map.get(module_key, module_key.replace("_", " ").title()),
                    "share": share,
                    "emphasis": emphasis,
                    "reason": reason_map.get(module_key, "Keep this module in the route when it supports the next step."),
                }
            )

        if mix:
            mix[0]["share"] = max(int(mix[0]["share"]), 24)
        return mix

    @classmethod
    def _build_completed_session_summary(
        cls,
        *,
        completed_plan: DailyLoopPlan | None,
        lesson_run: LessonRunState,
        weak_spots: list[WeakSpot],
        tomorrow_focus_area: str,
    ) -> dict:
        practice_evaluation = cls._build_practice_mix_evaluation(lesson_run)
        strongest_signal, weakest_signal = cls._extract_block_performance_signals(lesson_run)
        outcome_band = cls._determine_outcome_band(lesson_run)
        top_weak_spot = weak_spots[0].title if weak_spots else None
        strongest_label = (
            practice_evaluation.get("strongestPracticeTitle")
            if practice_evaluation and practice_evaluation.get("strongestPracticeTitle")
            else strongest_signal["label"]
            if strongest_signal
            else (completed_plan.focus_area if completed_plan else "today's route")
        )
        weakest_label = (
            practice_evaluation.get("weakestPracticeTitle")
            if practice_evaluation and practice_evaluation.get("weakestPracticeTitle")
            else weakest_signal["label"]
            if weakest_signal
            else (completed_plan.focus_area if completed_plan else "the core signal")
        )
        carry_over_label = strongest_label if outcome_band in {"breakthrough", "stable", "checkpoint"} else tomorrow_focus_area
        watch_label = top_weak_spot or weakest_label
        practice_shift = (
            str(practice_evaluation.get("summaryLine"))
            if practice_evaluation and practice_evaluation.get("summaryLine")
            else None
        )
        route_recovery_evaluation = cls._build_route_recovery_evaluation(
            lesson_run=lesson_run,
            outcome_band=outcome_band,
        )
        task_driven_transfer_evaluation = cls._build_task_driven_transfer_evaluation(
            lesson_run=lesson_run,
            outcome_band=outcome_band,
        )
        ritual_signal_evaluation = cls._build_ritual_signal_evaluation(
            lesson_run=lesson_run,
            outcome_band=outcome_band,
        )

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

        if practice_shift:
            strategy_shift = f"{strategy_shift} {practice_shift}"
        if route_recovery_evaluation and route_recovery_evaluation.get("summary"):
            strategy_shift = f"{strategy_shift} {route_recovery_evaluation['summary']}"
        if task_driven_transfer_evaluation and task_driven_transfer_evaluation.get("summary"):
            strategy_shift = f"{strategy_shift} {task_driven_transfer_evaluation['summary']}"
        if ritual_signal_evaluation and ritual_signal_evaluation.get("summary"):
            strategy_shift = f"{strategy_shift} {ritual_signal_evaluation['summary']}"

        summary = {
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
            "practiceMixEvaluation": practice_evaluation,
        }
        if route_recovery_evaluation:
            summary["routeRecoveryEvaluation"] = route_recovery_evaluation
        if task_driven_transfer_evaluation:
            summary["taskDrivenTransferEvaluation"] = task_driven_transfer_evaluation
        if ritual_signal_evaluation:
            summary["ritualSignalEvaluation"] = ritual_signal_evaluation
        return summary

    @classmethod
    def _build_route_recovery_evaluation(
        cls,
        *,
        lesson_run: LessonRunState,
        outcome_band: str,
    ) -> dict | None:
        route_context = cls._extract_route_context(lesson_run)
        route_recovery_phase = str(route_context.get("routeRecoveryPhase") or "")
        if route_recovery_phase != "support_reopen_arc":
            return None

        current_stage = str(route_context.get("routeRecoveryStage") or "first_reopen")
        support_label = (
            str(route_context.get("routeReentryNextLabel"))
            if route_context.get("routeReentryNextLabel")
            else str(route_context.get("focusArea") or "the reopened support lane")
        )
        support_route = (
            str(route_context.get("routeReentryNextRoute"))
            if route_context.get("routeReentryNextRoute")
            else None
        )
        focus_area = str(route_context.get("focusArea") or "")
        existing_completion_count = (
            int(route_context.get("routeRecoveryFollowUpCompletionCount"))
            if route_context.get("routeRecoveryFollowUpCompletionCount") is not None
            else 0
        )
        stage_completion_floor = (
            2
            if current_stage == "ready_to_expand"
            else 1
            if current_stage == "settling_back_in"
            else 0
        )
        completion_count = max(existing_completion_count, stage_completion_floor) + 1

        if current_stage == "ready_to_expand":
            if outcome_band == "fragile":
                next_stage = "settling_back_in"
                session_shape = "protected_mix"
                summary = (
                    f"The widening pass still left {support_label} a little fragile, so the route should step back into one more connected settling pass."
                )
                action_hint = (
                    f"Reconnect through the daily route, then give {support_label} one more controlled settling pass before widening again."
                )
            else:
                next_stage = "ready_to_expand"
                session_shape = "guided_balance"
                summary = (
                    f"The wider pass held cleanly, so the route can keep widening while {support_label} stays available inside the broader flow."
                )
                action_hint = (
                    f"Let the broader daily route lead again and keep {support_label} available as support instead of the whole center of the day."
                )
        elif current_stage == "settling_back_in":
            if outcome_band in {"stable", "breakthrough", "checkpoint"}:
                next_stage = "ready_to_expand"
                session_shape = "guided_balance"
                summary = (
                    f"This settling pass landed cleanly, so the route can widen again while keeping {support_label} available inside the broader flow."
                )
                action_hint = (
                    f"Let the broader daily route lead next and keep {support_label} available without forcing it to dominate the whole session."
                )
            else:
                next_stage = "settling_back_in"
                session_shape = "protected_mix"
                summary = (
                    f"{support_label.capitalize()} still needs one more connected settling pass before the route widens again."
                )
                action_hint = (
                    f"Use one more connected daily-route pass to settle {support_label} before you widen the route again."
                )
        else:
            next_stage = "settling_back_in"
            session_shape = "protected_mix"
            summary = (
                f"The first reopen pass has landed, so the route should reconnect through the daily route and give {support_label} one settling pass before it widens."
            )
            action_hint = (
                f"Reconnect through the daily route first, then use one controlled settling pass around {support_label}."
            )

        return {
            "phase": "support_reopen_arc",
            "currentStage": current_stage,
            "nextStage": next_stage,
            "sessionShape": session_shape,
            "supportLabel": support_label,
            "supportRoute": support_route,
            "focusArea": focus_area or None,
            "summary": summary,
            "actionHint": action_hint,
            "outcomeBand": outcome_band,
            "completionCount": completion_count,
        }

    @classmethod
    def _build_task_driven_transfer_evaluation(
        cls,
        *,
        lesson_run: LessonRunState,
        outcome_band: str,
    ) -> dict | None:
        route_context = cls._extract_route_context(lesson_run)
        task_driven_input = (
            route_context.get("taskDrivenInput")
            if isinstance(route_context.get("taskDrivenInput"), dict)
            else None
        )
        if not task_driven_input:
            return None

        input_route = str(task_driven_input.get("inputRoute") or "").strip()
        response_route = str(task_driven_input.get("responseRoute") or "").strip()
        if not input_route or not response_route:
            return None

        input_label = str(
            task_driven_input.get("inputLabel")
            or cls._map_task_driven_input_label(input_route)
        )
        response_label = str(
            task_driven_input.get("responseLabel")
            or cls._map_task_driven_response_label(response_route)
        )
        input_focus = cls._map_route_to_focus_area(input_route) or "reading"
        response_focus = cls._map_route_to_focus_area(response_route) or "writing"

        block_by_id = {block.id: block for block in lesson_run.lesson.blocks}
        input_scores: list[int] = []
        response_scores: list[int] = []
        for block_run in lesson_run.block_runs:
            if block_run.score is None:
                continue
            block = block_by_id.get(block_run.block_id)
            if block is None:
                continue
            practice_key = cls._map_block_type_to_practice_key(block.block_type)
            if practice_key == input_focus:
                input_scores.append(block_run.score)
            if practice_key == response_focus:
                response_scores.append(block_run.score)

        input_average = round(sum(input_scores) / len(input_scores)) if input_scores else None
        response_average = round(sum(response_scores) / len(response_scores)) if response_scores else None
        response_score = response_average if response_average is not None else lesson_run.score
        input_score = input_average if input_average is not None else response_score
        score_gap = input_score - response_score

        if response_score >= 82 and score_gap <= 8:
            transfer_outcome = "held"
            summary = (
                f"The {input_label.lower()} signal carried cleanly into {response_label.lower()}, so the route can trust that transfer."
            )
            next_bias = "expand_response_lane"
        elif response_score >= 68 and score_gap <= 16 and outcome_band != "fragile":
            transfer_outcome = "usable"
            summary = (
                f"The {input_label.lower()} signal reached {response_label.lower()}, but the route should keep that response lane supported for one more pass."
            )
            next_bias = "support_response_lane"
        else:
            transfer_outcome = "fragile"
            summary = (
                f"The route captured {input_label.lower()}, but the transfer into {response_label.lower()} is still fragile and needs another controlled pass."
            )
            next_bias = "protect_response_lane"

        current_window_stage = ""
        current_window_bias = str(route_context.get("routeRecoveryDecisionBias") or "")
        if current_window_bias == "task_transfer_window":
            current_window_stage = str(route_context.get("routeRecoveryDecisionWindowStage") or "")
        next_window_stage, next_window_days, window_action = cls._resolve_task_transfer_window_progression(
            current_window_stage=current_window_stage,
            transfer_outcome=transfer_outcome,
        )
        if next_window_stage == "close_window":
            window_summary = (
                f"The response pass held cleanly, so the protected transfer window can close and the broader route can lead again while {response_label.lower()} stays reusable."
            )
        elif next_window_stage == "protect_response":
            window_summary = (
                f"The route should keep {response_label.lower()} protected for another pass before widening again."
            )
        elif next_window_stage == "stabilize_transfer":
            window_summary = (
                f"The route can leave full protection, but it should keep one stabilizing pass around {response_label.lower()} before widening further."
            )
        else:
            window_summary = (
                f"The protected transfer window has held well enough to let the route start widening again while {response_label.lower()} stays available."
            )

        return {
            "inputRoute": input_route,
            "inputLabel": input_label,
            "responseRoute": response_route,
            "responseLabel": response_label,
            "inputAverageScore": input_average,
            "responseAverageScore": response_average,
            "transferOutcome": transfer_outcome,
            "summary": summary,
            "nextBias": next_bias,
            "currentWindowStage": current_window_stage or None,
            "nextWindowStage": next_window_stage,
            "nextWindowDays": next_window_days,
            "windowAction": window_action,
            "windowSummary": window_summary,
        }

    @staticmethod
    def _resolve_ritual_signal_window_progression(
        *,
        current_window_stage: str,
        outcome_band: str,
    ) -> tuple[str, int, str]:
        stage = current_window_stage or "fresh_capture"
        strong_outcome = outcome_band in {"stable", "breakthrough", "checkpoint"}

        if stage == "fresh_capture":
            return (
                ("reuse_in_route", 1, "advance_to_reuse")
                if strong_outcome
                else ("fresh_capture", 2, "extend_capture")
            )
        if stage == "reuse_in_route":
            return (
                ("ready_to_carry", 1, "advance_to_carry")
                if strong_outcome
                else ("reuse_in_route", 1, "keep_reusing")
            )
        if stage == "ready_to_carry":
            return (
                ("close_window", 0, "close_window")
                if strong_outcome
                else ("reuse_in_route", 1, "step_back_to_reuse")
            )
        return (
            ("ready_to_carry", 1, "advance_to_carry")
            if strong_outcome
            else ("reuse_in_route", 1, "keep_reusing")
        )

    @staticmethod
    def _map_ritual_signal_route_window_stage(window_stage: str) -> str:
        return (
            "protect_ritual"
            if window_stage == "fresh_capture"
            else "reuse_in_response"
            if window_stage == "reuse_in_route"
            else "carry_inside_route"
            if window_stage == "ready_to_carry"
            else ""
        )

    @classmethod
    def _build_ritual_signal_evaluation(
        cls,
        *,
        lesson_run: LessonRunState,
        outcome_band: str,
    ) -> dict | None:
        route_context = cls._extract_route_context(lesson_run)
        ritual_signal_type = str(route_context.get("ritualSignalType") or "")
        ritual_signal_label = str(route_context.get("ritualSignalLabel") or "")
        if not ritual_signal_type or not ritual_signal_label:
            return None

        current_window_stage = str(route_context.get("ritualSignalStage") or "fresh_capture")
        next_window_stage, next_window_days, window_action = cls._resolve_ritual_signal_window_progression(
            current_window_stage=current_window_stage,
            outcome_band=outcome_band,
        )
        focus_area = str(route_context.get("focusArea") or "") or None
        current_arc_step = (
            "reuse"
            if current_window_stage == "reuse_in_route"
            else "carry_forward"
            if current_window_stage == "ready_to_carry"
            else "capture"
        )
        next_arc_step = (
            "carry_forward"
            if next_window_stage == "ready_to_carry"
            else "reuse"
            if next_window_stage == "reuse_in_route"
            else "closed"
            if next_window_stage == "close_window"
            else "capture"
        )

        if ritual_signal_type == "word_journal":
            if next_window_stage == "close_window":
                summary = (
                    f"The route has already carried {ritual_signal_label} cleanly enough that the ritual window can close and the phrase can stay available without forced protection."
                )
                action_hint = (
                    f"Let the broader route lead again while keeping {ritual_signal_label} available as a reusable phrase."
                )
            elif next_window_stage == "ready_to_carry":
                summary = (
                    f"The route reused {ritual_signal_label} cleanly, so the next session can carry it forward inside a broader response instead of treating it like a fresh capture."
                )
                action_hint = (
                    f"Carry {ritual_signal_label} forward through the broader route instead of forcing another narrow reuse pass."
                )
            elif next_window_stage == "reuse_in_route":
                summary = (
                    f"The route has already moved {ritual_signal_label} out of capture, so the next session should reuse it once more before the phrase starts living inside the broader flow."
                )
                action_hint = (
                    f"Give {ritual_signal_label} one more connected reuse pass before widening fully."
                )
            else:
                summary = (
                    f"{ritual_signal_label.capitalize()} still needs a clearer first reuse pass before the route can move beyond simple capture."
                )
                action_hint = (
                    f"Keep the next route close to {ritual_signal_label} and bring it back into real output again."
                )
        else:
            if next_window_stage == "close_window":
                summary = (
                    f"The live voice signal from {ritual_signal_label} has already carried cleanly enough that the ritual window can close without losing spontaneity."
                )
                action_hint = (
                    f"Let the broader speaking route lead again while keeping the live voice signal from {ritual_signal_label} available."
                )
            elif next_window_stage == "ready_to_carry":
                summary = (
                    f"The live voice signal from {ritual_signal_label} held cleanly, so the next session can carry it forward inside a broader speaking route."
                )
                action_hint = (
                    f"Carry the live voice signal from {ritual_signal_label} into the broader route instead of forcing another narrow ritual pass."
                )
            elif next_window_stage == "reuse_in_route":
                summary = (
                    f"The live voice signal from {ritual_signal_label} is out of pure capture, so the next session should reuse it once more before widening further."
                )
                action_hint = (
                    f"Give the live voice signal from {ritual_signal_label} one more connected reuse pass."
                )
            else:
                summary = (
                    f"The live voice signal from {ritual_signal_label} still needs a clearer first reuse pass before the route can widen."
                )
                action_hint = (
                    f"Keep one more low-pressure speaking pass around {ritual_signal_label} before widening."
                )

        return {
            "signalType": ritual_signal_type,
            "label": ritual_signal_label,
            "focusArea": focus_area,
            "currentWindowStage": current_window_stage,
            "nextWindowStage": next_window_stage,
            "currentArcStep": current_arc_step,
            "nextArcStep": next_arc_step,
            "nextWindowDays": next_window_days,
            "windowAction": window_action,
            "summary": summary,
            "actionHint": action_hint,
            "outcomeBand": outcome_band,
        }

    @staticmethod
    def _resolve_task_transfer_window_progression(
        *,
        current_window_stage: str,
        transfer_outcome: str,
    ) -> tuple[str, int, str]:
        stage = current_window_stage or ""
        outcome = transfer_outcome or "usable"

        if stage == "protect_response":
            if outcome == "fragile":
                return "protect_response", 2, "extend_protection"
            if outcome == "usable":
                return "stabilize_transfer", 1, "advance_to_stabilizing"
            return "ready_to_widen", 1, "advance_to_widen"

        if stage == "stabilize_transfer":
            if outcome == "fragile":
                return "protect_response", 2, "step_back_to_protection"
            if outcome == "usable":
                return "stabilize_transfer", 1, "keep_stabilizing"
            return "ready_to_widen", 1, "advance_to_widen"

        if stage == "ready_to_widen":
            if outcome == "fragile":
                return "stabilize_transfer", 1, "step_back_to_stabilizing"
            if outcome == "usable":
                return "ready_to_widen", 1, "hold_widening"
            return "close_window", 0, "close_window"

        if outcome == "fragile":
            return "protect_response", 2, "extend_protection"
        if outcome == "usable":
            return "stabilize_transfer", 1, "advance_to_stabilizing"
        return "ready_to_widen", 1, "advance_to_widen"

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
        route_recovery_evaluation = (
            session_summary.get("routeRecoveryEvaluation")
            if isinstance(session_summary.get("routeRecoveryEvaluation"), dict)
            else None
        )
        task_driven_transfer_evaluation = (
            session_summary.get("taskDrivenTransferEvaluation")
            if isinstance(session_summary.get("taskDrivenTransferEvaluation"), dict)
            else None
        )
        ritual_signal_evaluation = (
            session_summary.get("ritualSignalEvaluation")
            if isinstance(session_summary.get("ritualSignalEvaluation"), dict)
            else None
        )

        if route_recovery_evaluation and route_recovery_evaluation.get("phase") == "support_reopen_arc":
            next_stage = str(route_recovery_evaluation.get("nextStage") or "")
            support_label = str(route_recovery_evaluation.get("supportLabel") or watch_label)
            if next_stage == "ready_to_expand":
                headline = f"Tomorrow widens back into the connected daily route around {focus_area}."
                reason = str(route_recovery_evaluation.get("summary") or session_summary["strategyShift"])
                next_step_hint = (
                    f"Return tomorrow and let the broader daily route lead while keeping {support_label} available inside the flow."
                )
                continuity_mode = "reopen_widen"
            else:
                headline = f"Tomorrow keeps one more connected settling pass around {focus_area}."
                reason = str(route_recovery_evaluation.get("summary") or session_summary["strategyShift"])
                next_step_hint = (
                    f"Return tomorrow for one more connected settling pass before the route widens again around {support_label}."
                )
                continuity_mode = "reopen_settle"
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

        if task_driven_transfer_evaluation:
            input_label = str(task_driven_transfer_evaluation.get("inputLabel") or carry_over_label)
            response_label = str(task_driven_transfer_evaluation.get("responseLabel") or watch_label)
            transfer_outcome = str(task_driven_transfer_evaluation.get("transferOutcome") or "usable")
            transfer_summary = str(
                task_driven_transfer_evaluation.get("summary") or session_summary["strategyShift"]
            )
            next_window_stage = str(task_driven_transfer_evaluation.get("nextWindowStage") or "")
            window_summary = str(task_driven_transfer_evaluation.get("windowSummary") or transfer_summary)
            if next_window_stage == "close_window":
                headline = f"Tomorrow can widen fully again while keeping {response_label.lower()} reusable."
                reason = window_summary
                next_step_hint = (
                    f"Return tomorrow and let the broader route lead again while keeping {input_label.lower()} flowing into {response_label.lower()}."
                )
                continuity_mode = "task_driven_widen"
            elif next_window_stage == "ready_to_widen" or transfer_outcome == "held":
                headline = f"Tomorrow can widen from {input_label.lower()} into {response_label.lower()} without losing the route."
                reason = (
                    f"{window_summary} The route can now let the broader daily session lead while keeping that transfer alive."
                )
                next_step_hint = (
                    f"Return tomorrow and let the broader route lead while carrying {input_label.lower()} forward into {response_label.lower()}."
                )
                continuity_mode = "task_driven_carry"
            elif next_window_stage == "stabilize_transfer" or transfer_outcome == "usable":
                headline = f"Tomorrow should keep building from {input_label.lower()} into {response_label.lower()}."
                reason = (
                    f"{window_summary} The route should give that response lane one more connected pass before widening further."
                )
                next_step_hint = (
                    f"Return tomorrow for one more connected {response_label.lower()} pass so the signal from {input_label.lower()} becomes easier to reuse."
                )
                continuity_mode = "task_driven_support"
            else:
                headline = f"Tomorrow should protect the move from {input_label.lower()} into {response_label.lower()}."
                reason = (
                    f"{window_summary} The input signal landed, but the route still needs to protect the response lane before it broadens."
                )
                next_step_hint = (
                    f"Return tomorrow and keep the route tighter around {response_label.lower()} so the signal from {input_label.lower()} does not get lost."
                )
                continuity_mode = "task_driven_protect"
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

        if ritual_signal_evaluation:
            ritual_label = str(ritual_signal_evaluation.get("label") or carry_over_label)
            next_window_stage = str(ritual_signal_evaluation.get("nextWindowStage") or "")
            summary = str(ritual_signal_evaluation.get("summary") or session_summary["strategyShift"])
            if next_window_stage == "close_window":
                headline = f"Tomorrow can widen again while keeping {ritual_label.lower()} quietly available."
                reason = summary
                next_step_hint = (
                    f"Return tomorrow and let the broader route lead again while keeping {ritual_label.lower()} alive without forcing a separate ritual pass."
                )
                continuity_mode = "ritual_close"
            elif next_window_stage == "ready_to_carry":
                headline = f"Tomorrow should carry {ritual_label.lower()} inside the broader route."
                reason = summary
                next_step_hint = (
                    f"Return tomorrow and carry {ritual_label.lower()} through the broader route instead of restarting from capture."
                )
                continuity_mode = "ritual_carry"
            elif next_window_stage == "reuse_in_route":
                headline = f"Tomorrow should reuse {ritual_label.lower()} one more time inside the route."
                reason = summary
                next_step_hint = (
                    f"Return tomorrow for one more connected reuse pass around {ritual_label.lower()} before the route widens further."
                )
                continuity_mode = "ritual_reuse"
            else:
                headline = f"Tomorrow should keep protecting {ritual_label.lower()} as a fresh ritual signal."
                reason = summary
                next_step_hint = (
                    f"Return tomorrow and keep the route close to {ritual_label.lower()} until the first real reuse pass lands."
                )
                continuity_mode = "ritual_capture"
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
        route_cadence_memory: dict | None = None,
        route_recovery_memory: dict | None = None,
    ) -> str:
        cadence_line = JourneyService._build_route_cadence_summary_line(route_cadence_memory)
        recovery_line = JourneyService._build_route_recovery_summary_line(route_recovery_memory)
        return (
            f"{session_summary['headline']} {session_summary['strategyShift']}"
            + (f" {cadence_line}" if cadence_line else "")
            + (f" {recovery_line}" if recovery_line else "")
        )

    def _build_completed_strategy_snapshot(
        self,
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
        skill_trajectory = self._build_skill_trajectory_memory(
            profile.id,
            current_state,
            active_skill_focus=profile.onboarding_answers.active_skill_focus,
        )
        if skill_trajectory:
            snapshot["skillTrajectory"] = skill_trajectory
        strategy_memory = self._build_strategy_memory(
            profile.id,
            current_state,
            active_skill_focus=profile.onboarding_answers.active_skill_focus,
        )
        if strategy_memory:
            snapshot["strategyMemory"] = strategy_memory
        route_cadence_memory = self._build_route_cadence_memory(profile.id, current_state)
        if route_cadence_memory:
            snapshot["routeCadenceMemory"] = route_cadence_memory
        route_recovery_memory = self._build_route_recovery_memory(
            user_id=profile.id,
            current_state=current_state,
            session_summary=session_summary,
            skill_trajectory=skill_trajectory,
            strategy_memory=strategy_memory,
            route_cadence_memory=route_cadence_memory,
        )
        route_recovery_memory = self._apply_task_driven_transfer_recovery_override(
            route_recovery_memory,
            session_summary=session_summary,
        )
        if route_recovery_memory:
            snapshot["routeRecoveryMemory"] = route_recovery_memory
        route_reentry_progress = self._build_route_reentry_progress(
            current_state=current_state,
            route_recovery_memory=route_recovery_memory,
        )
        if route_reentry_progress:
            snapshot["routeReentryProgress"] = route_reentry_progress
        else:
            snapshot.pop("routeReentryProgress", None)
        route_follow_up_memory = self._build_route_follow_up_memory(
            route_recovery_memory=route_recovery_memory,
            route_reentry_progress=route_reentry_progress,
            route_entry_memory=self._extract_route_entry_memory(current_state),
            ritual_signal_memory=self._extract_ritual_signal_memory(current_state),
            existing_route_follow_up_memory=self._extract_route_follow_up_memory(current_state),
        )
        if route_follow_up_memory:
            snapshot["routeFollowUpMemory"] = route_follow_up_memory
        else:
            snapshot.pop("routeFollowUpMemory", None)
        ritual_signal_evaluation = (
            session_summary.get("ritualSignalEvaluation")
            if isinstance(session_summary.get("ritualSignalEvaluation"), dict)
            else None
        )
        existing_ritual_signal_memory = (
            snapshot.get("ritualSignalMemory")
            if isinstance(snapshot.get("ritualSignalMemory"), dict)
            else self._extract_ritual_signal_memory(current_state)
        )
        snapshot = self._apply_ritual_signal_memory_override(
            snapshot,
            ritual_signal_memory=existing_ritual_signal_memory,
            ritual_signal_evaluation=ritual_signal_evaluation,
        )
        updated_ritual_signal_memory = (
            snapshot.get("ritualSignalMemory")
            if isinstance(snapshot.get("ritualSignalMemory"), dict)
            else None
        )
        route_follow_up_memory = self._build_route_follow_up_memory(
            route_recovery_memory=route_recovery_memory,
            route_reentry_progress=route_reentry_progress,
            route_entry_memory=self._extract_route_entry_memory(current_state),
            ritual_signal_memory=updated_ritual_signal_memory,
            existing_route_follow_up_memory=route_follow_up_memory,
        )
        if route_follow_up_memory:
            snapshot["routeFollowUpMemory"] = route_follow_up_memory
        else:
            snapshot.pop("routeFollowUpMemory", None)
        snapshot["learningBlueprint"] = self._build_learning_blueprint(
            profile=profile,
            focus_area=focus_area,
            recommendation=recommendation,
            current_state=current_state,
            current_strategy_summary=self._build_completed_strategy_summary(
                session_summary=session_summary,
                route_cadence_memory=route_cadence_memory,
                route_recovery_memory=route_recovery_memory,
            ),
            next_best_action=tomorrow_preview["nextStepHint"],
            route_snapshot=snapshot,
        )
        return snapshot

    @staticmethod
    def _apply_ritual_signal_memory_override(
        snapshot: dict,
        *,
        ritual_signal_memory: dict | None,
        ritual_signal_evaluation: dict | None,
    ) -> dict:
        if not ritual_signal_memory or not ritual_signal_evaluation:
            return snapshot

        updated_snapshot = dict(snapshot)
        next_window_stage = str(ritual_signal_evaluation.get("nextWindowStage") or "")
        if next_window_stage == "close_window":
            updated_snapshot.pop("ritualSignalMemory", None)
            return updated_snapshot

        updated_snapshot["ritualSignalMemory"] = {
            **ritual_signal_memory,
            "windowStage": next_window_stage or ritual_signal_memory.get("windowStage"),
            "windowDays": (
                int(ritual_signal_evaluation.get("nextWindowDays"))
                if ritual_signal_evaluation.get("nextWindowDays") is not None
                else ritual_signal_memory.get("windowDays")
            ),
            "arcStep": (
                str(ritual_signal_evaluation.get("nextArcStep"))
                if ritual_signal_evaluation.get("nextArcStep")
                else ritual_signal_memory.get("arcStep")
            ),
            "windowRemainingDays": (
                int(ritual_signal_evaluation.get("nextWindowDays"))
                if ritual_signal_evaluation.get("nextWindowDays") is not None
                else ritual_signal_memory.get("windowRemainingDays")
            ),
            "routeWindowBias": "ritual_signal_window",
            "routeWindowStage": JourneyService._map_ritual_signal_route_window_stage(
                next_window_stage or str(ritual_signal_memory.get("windowStage") or "")
            ),
            "summary": (
                str(ritual_signal_evaluation.get("summary"))
                if ritual_signal_evaluation.get("summary")
                else ritual_signal_memory.get("summary")
            ),
            "actionHint": (
                str(ritual_signal_evaluation.get("actionHint"))
                if ritual_signal_evaluation.get("actionHint")
                else ritual_signal_memory.get("actionHint")
            ),
            "lastEvaluationAction": (
                str(ritual_signal_evaluation.get("windowAction"))
                if ritual_signal_evaluation.get("windowAction")
                else ritual_signal_memory.get("lastEvaluationAction")
            ),
        }
        return updated_snapshot

    @staticmethod
    def _apply_task_driven_transfer_recovery_override(
        route_recovery_memory: dict | None,
        *,
        session_summary: dict | None,
    ) -> dict | None:
        if not route_recovery_memory or not session_summary:
            return route_recovery_memory
        task_driven_transfer = (
            session_summary.get("taskDrivenTransferEvaluation")
            if isinstance(session_summary.get("taskDrivenTransferEvaluation"), dict)
            else None
        )
        if not task_driven_transfer:
            return route_recovery_memory

        next_window_stage = str(task_driven_transfer.get("nextWindowStage") or "")
        if not next_window_stage:
            return route_recovery_memory

        response_label = str(
            task_driven_transfer.get("responseLabel")
            or route_recovery_memory.get("supportPracticeTitle")
            or "the response lane"
        )
        next_window_days = (
            int(task_driven_transfer.get("nextWindowDays"))
            if task_driven_transfer.get("nextWindowDays") is not None
            else 1
        )
        window_summary = str(task_driven_transfer.get("windowSummary") or route_recovery_memory.get("summary") or "")
        updated = dict(route_recovery_memory)
        updated["supportPracticeTitle"] = response_label
        updated["transferOutcome"] = str(task_driven_transfer.get("transferOutcome") or updated.get("transferOutcome") or "")
        updated["transferWindowAction"] = str(task_driven_transfer.get("windowAction") or "")
        updated["transferNextWindowStage"] = next_window_stage

        if task_driven_transfer.get("inputLabel"):
            updated["transferInputLabel"] = str(task_driven_transfer.get("inputLabel"))
        if task_driven_transfer.get("responseLabel"):
            updated["transferResponseLabel"] = str(task_driven_transfer.get("responseLabel"))

        if next_window_stage == "close_window":
            updated["phase"] = "steady_extension"
            updated["sessionShape"] = "forward_mix"
            updated["summary"] = (
                window_summary
                or f"The protected transfer window has held cleanly enough that the broader route can lead again while {response_label} stays reusable."
            )
            updated["actionHint"] = (
                f"Let the broader route lead again and keep {response_label} available as quiet support."
            )
            updated["nextPhaseHint"] = (
                f"If the broader route keeps carrying {response_label} cleanly, the transfer window can stay closed."
            )
            updated.pop("decisionBias", None)
            updated.pop("decisionWindowDays", None)
            updated.pop("decisionWindowStage", None)
            updated.pop("decisionWindowRemainingDays", None)
            return updated

        updated["decisionBias"] = "task_transfer_window"
        updated["decisionWindowDays"] = next_window_days
        updated["decisionWindowStage"] = next_window_stage
        updated["decisionWindowRemainingDays"] = next_window_days

        if next_window_stage == "protect_response":
            updated["phase"] = "targeted_stabilization"
            updated["sessionShape"] = "focused_support"
        elif next_window_stage == "stabilize_transfer":
            updated["phase"] = "targeted_stabilization"
            updated["sessionShape"] = "guided_balance"
        else:
            updated["phase"] = "steady_extension"
            updated["sessionShape"] = "forward_mix"
        updated["summary"] = window_summary or updated.get("summary")
        return updated

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

    @classmethod
    def _build_practice_mix_evaluation(cls, lesson_run: LessonRunState) -> dict | None:
        route_context = cls._extract_route_context(lesson_run)
        practice_mix_items = (
            route_context.get("practiceMix")
            if isinstance(route_context.get("practiceMix"), list)
            else []
        )
        practice_mix = {
            str(item.get("moduleKey")): item
            for item in practice_mix_items
            if isinstance(item, dict) and item.get("moduleKey")
        }
        if not practice_mix:
            return None

        block_by_id = {block.id: block for block in lesson_run.lesson.blocks}
        score_buckets: dict[str, list[int]] = {}
        for block_run in lesson_run.block_runs:
            if block_run.score is None:
                continue
            block = block_by_id.get(block_run.block_id)
            if block is None:
                continue
            module_key = cls._map_block_type_to_practice_key(block.block_type)
            score_buckets.setdefault(module_key, []).append(block_run.score)

        practiced = []
        for module_key, scores in score_buckets.items():
            if not scores:
                continue
            mix_item = practice_mix.get(module_key, {})
            practiced.append(
                {
                    "moduleKey": module_key,
                    "title": mix_item.get("title") or cls._label_block_type(f"{module_key}_block"),
                    "share": mix_item.get("share"),
                    "emphasis": mix_item.get("emphasis"),
                    "averageScore": round(sum(scores) / len(scores)),
                }
            )

        if not practiced:
            return None

        practiced_sorted = sorted(practiced, key=lambda item: item["averageScore"], reverse=True)
        strongest = practiced_sorted[0]
        weakest = practiced_sorted[-1]
        lead_mix_item = next(
            (
                item
                for item in practice_mix_items
                if isinstance(item, dict) and item.get("emphasis") == "lead" and item.get("moduleKey")
            ),
            None,
        )
        lead_module_key = (
            str(lead_mix_item.get("moduleKey"))
            if isinstance(lead_mix_item, dict) and lead_mix_item.get("moduleKey")
            else strongest["moduleKey"]
        )
        lead_result = next((item for item in practiced_sorted if item["moduleKey"] == lead_module_key), None)
        lead_title = (
            str(lead_mix_item.get("title"))
            if isinstance(lead_mix_item, dict) and lead_mix_item.get("title")
            else lead_result["title"]
            if lead_result
            else strongest["title"]
        )
        lead_score = lead_result["averageScore"] if lead_result else None
        if lead_score is None:
            lead_outcome = "unmeasured"
        elif lead_score >= 80:
            lead_outcome = "held"
        elif lead_score >= 68:
            lead_outcome = "usable"
        else:
            lead_outcome = "fragile"

        if strongest["moduleKey"] == weakest["moduleKey"]:
            summary_line = f"The route mostly measured {strongest['title']}, so tomorrow should keep that same practice type honest before widening."
        elif lead_outcome == "held":
            summary_line = f"{lead_title} carried the route best, while {weakest['title']} still needs support in the next session."
        elif lead_outcome == "usable":
            summary_line = f"{lead_title} stayed usable, but the route should rebalance toward {weakest['title']} before it broadens again."
        else:
            summary_line = f"{lead_title} stayed fragile, so tomorrow should reduce pressure and support it through {strongest['title']}."

        return {
            "leadPracticeKey": lead_module_key,
            "leadPracticeTitle": lead_title,
            "leadOutcome": lead_outcome,
            "leadAverageScore": lead_score,
            "strongestPracticeKey": strongest["moduleKey"],
            "strongestPracticeTitle": strongest["title"],
            "strongestPracticeScore": strongest["averageScore"],
            "weakestPracticeKey": weakest["moduleKey"],
            "weakestPracticeTitle": weakest["title"],
            "weakestPracticeScore": weakest["averageScore"],
            "summaryLine": summary_line,
        }

    @staticmethod
    def _extract_route_context(lesson_run: LessonRunState) -> dict:
        for block in lesson_run.lesson.blocks:
            route_context = block.payload.get("routeContext") if isinstance(block.payload, dict) else None
            if isinstance(route_context, dict) and route_context:
                return route_context
        return {}

    @staticmethod
    def _map_block_type_to_practice_key(block_type: str) -> str:
        return {
            "review_block": "lesson",
            "summary_block": "lesson",
            "grammar_block": "grammar",
            "vocab_block": "vocabulary",
            "speaking_block": "speaking",
            "pronunciation_block": "pronunciation",
            "listening_block": "listening",
            "reading_block": "reading",
            "writing_block": "writing",
            "profession_block": "profession",
        }.get(block_type, block_type.replace("_block", ""))

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
            "reading_block": "reading input",
            "writing_block": "writing response",
            "profession_block": "work scenario",
            "reflection_block": "reflection",
            "summary_block": "strategic summary",
        }
        return labels.get(block_type, block_type.replace("_", " "))

    @staticmethod
    def _build_next_best_action(profile: UserProfile, plan: DailyLoopPlan) -> str:
        if plan.next_step_hint:
            return plan.next_step_hint
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

    @staticmethod
    def _extract_skill_trajectory(current_state: LearnerJourneyState | None) -> dict | None:
        if not current_state:
            return None

        value = current_state.strategy_snapshot.get("skillTrajectory")
        return value if isinstance(value, dict) and value else None

    @staticmethod
    def _extract_strategy_memory(current_state: LearnerJourneyState | None) -> dict | None:
        if not current_state:
            return None

        value = current_state.strategy_snapshot.get("strategyMemory")
        return value if isinstance(value, dict) and value else None

    @staticmethod
    def _extract_route_cadence_memory(current_state: LearnerJourneyState | None) -> dict | None:
        if not current_state:
            return None

        value = current_state.strategy_snapshot.get("routeCadenceMemory")
        return value if isinstance(value, dict) and value else None

    @staticmethod
    def _extract_route_recovery_memory(current_state: LearnerJourneyState | None) -> dict | None:
        if not current_state:
            return None

        value = current_state.strategy_snapshot.get("routeRecoveryMemory")
        return value if isinstance(value, dict) and value else None

    @staticmethod
    def _extract_route_reentry_progress(current_state: LearnerJourneyState | None) -> dict | None:
        if not current_state:
            return None

        value = current_state.strategy_snapshot.get("routeReentryProgress")
        return value if isinstance(value, dict) and value else None

    @staticmethod
    def _extract_route_entry_memory(current_state: LearnerJourneyState | None) -> dict | None:
        if not current_state:
            return None

        value = current_state.strategy_snapshot.get("routeEntryMemory")
        return value if isinstance(value, dict) and value else None

    @staticmethod
    def _extract_route_follow_up_memory(current_state: LearnerJourneyState | None) -> dict | None:
        if not current_state:
            return None

        value = current_state.strategy_snapshot.get("routeFollowUpMemory")
        return value if isinstance(value, dict) and value else None

    @staticmethod
    def _extract_ritual_signal_memory(current_state: LearnerJourneyState | None) -> dict | None:
        if not current_state:
            return None

        value = current_state.strategy_snapshot.get("ritualSignalMemory")
        return value if isinstance(value, dict) and value else None

    @staticmethod
    def _should_prioritize_ritual_signal_focus(ritual_signal_memory: dict | None) -> bool:
        if not ritual_signal_memory:
            return False

        window_stage = str(ritual_signal_memory.get("windowStage") or "")
        return window_stage in {"", "fresh_capture", "reuse_in_route"}

    def _build_ritual_signal_memory(
        self,
        user_id: str,
        current_state: LearnerJourneyState | None,
    ) -> dict | None:
        existing_memory = self._extract_ritual_signal_memory(current_state)
        if not existing_memory:
            return None

        recorded_at_raw = str(
            existing_memory.get("recordedAt")
            or (
                existing_memory.get("recentSignals")[0].get("recordedAt")
                if isinstance(existing_memory.get("recentSignals"), list)
                and existing_memory.get("recentSignals")
                and isinstance(existing_memory.get("recentSignals")[0], dict)
                and existing_memory.get("recentSignals")[0].get("recordedAt")
                else ""
            )
        ).strip()
        recorded_at: datetime | None = None
        if recorded_at_raw:
            try:
                recorded_at = datetime.fromisoformat(recorded_at_raw)
            except ValueError:
                recorded_at = None

        recent_plans = self._repository.list_recent_daily_loop_plans(user_id, limit=6)
        completed_since_capture = 0
        if recorded_at is not None:
            for plan in recent_plans:
                if not plan.completed_at:
                    continue
                completed_at = plan.completed_at
                if isinstance(completed_at, str):
                    try:
                        completed_at = datetime.fromisoformat(completed_at)
                    except ValueError:
                        continue
                if completed_at.tzinfo is not None:
                    completed_at = completed_at.replace(tzinfo=None)
                if completed_at >= recorded_at:
                    completed_since_capture += 1
        else:
            completed_since_capture = len([plan for plan in recent_plans if plan.completed_at][:2])

        active_signal_type = str(existing_memory.get("activeSignalType") or "")
        active_label = str(existing_memory.get("activeLabel") or "the ritual signal")
        recommended_focus = str(existing_memory.get("recommendedFocus") or "")
        recent_signals = [
            item
            for item in existing_memory.get("recentSignals", [])
            if isinstance(item, dict)
        ][:5]
        if completed_since_capture <= 0:
            window_stage = "fresh_capture"
            window_days = 2
            arc_step = "capture"
            summary = (
                f"The route is still in the capture phase around {active_label}, so the next session should reuse it quickly before it goes cold."
                if active_signal_type == "word_journal"
                else f"The route is still in the capture phase around {active_label}, so the next session should reuse that live voice signal before it fades."
            )
            action_hint = (
                f"Keep one light route step around {active_label} so the captured phrase comes back in real use before it goes cold."
                if active_signal_type == "word_journal"
                else f"Keep one live speaking step around {active_label} so the spontaneous voice signal settles before the route widens."
            )
        elif completed_since_capture == 1:
            window_stage = "reuse_in_route"
            window_days = 1
            arc_step = "reuse"
            summary = (
                f"The route has already reused {active_label} once, so the next session should carry it forward into a broader response instead of starting a new ritual from zero."
                if active_signal_type == "word_journal"
                else f"The route has already reused the live voice signal from {active_label} once, so the next session should carry it forward into a broader speaking pass."
            )
            action_hint = (
                f"Use one more connected route around {active_label}, then start carrying it into the broader daily flow."
            )
        else:
            window_stage = "ready_to_carry"
            window_days = 1
            arc_step = "carry_forward"
            summary = (
                f"The route has already reused {active_label} across connected days, so it can now carry that ritual signal inside the broader route without forcing it to dominate."
                if active_signal_type == "word_journal"
                else f"The route has already reused the live voice signal from {active_label} across connected days, so it can now carry it inside the broader speaking route."
            )
            action_hint = (
                f"Let the broader route lead again while keeping {active_label} available as a live ritual carry-over."
            )

        return {
            **existing_memory,
            "recommendedFocus": recommended_focus or existing_memory.get("recommendedFocus"),
            "windowStage": window_stage,
            "windowDays": window_days,
            "windowRemainingDays": window_days,
            "arcStep": arc_step,
            "routeWindowBias": "ritual_signal_window",
            "routeWindowStage": self._map_ritual_signal_route_window_stage(window_stage),
            "completedSinceCapture": completed_since_capture,
            "summary": summary,
            "actionHint": action_hint,
            "recordedAt": recorded_at_raw or datetime.utcnow().isoformat(),
            "recentSignals": recent_signals,
        }

    @staticmethod
    def _map_route_to_support_label(route: str | None) -> str | None:
        return (
            "grammar support"
            if route == "/grammar"
            else "vocabulary support"
            if route == "/vocabulary"
            else "reading input"
            if route == "/reading"
            else "listening input"
            if route == "/listening"
            else "speaking support"
            if route == "/speaking"
            else "pronunciation support"
            if route == "/pronunciation"
            else "writing support"
            if route == "/writing"
            else "professional support"
            if route == "/profession"
            else "daily route"
            if route == "/daily-loop"
            else "guided route"
            if route == "/lesson-runner"
            else route
        )

    @staticmethod
    def _map_reopen_stage_label(stage: str | None) -> str | None:
        return (
            "First reopen"
            if stage == "first_reopen"
            else "Settling pass"
            if stage == "settling_back_in"
            else "Ready to widen"
            if stage == "ready_to_expand"
            else None
        )

    def _build_route_follow_up_memory(
        self,
        *,
        route_recovery_memory: dict | None,
        route_reentry_progress: dict | None,
        route_entry_memory: dict | None,
        ritual_signal_memory: dict | None = None,
        existing_route_follow_up_memory: dict | None = None,
    ) -> dict | None:
        next_route = (
            str(route_reentry_progress.get("nextRoute"))
            if route_reentry_progress and route_reentry_progress.get("nextRoute")
            else None
        )
        active_next_route = (
            str(route_entry_memory.get("activeNextRoute"))
            if route_entry_memory and route_entry_memory.get("activeNextRoute")
            else None
        )
        reopen_route = (
            active_next_route
            if route_entry_memory and route_entry_memory.get("readyToReopenActiveNextRoute")
            else next_route
        )
        reopen_label = self._map_route_to_support_label(reopen_route)
        reopen_stage = (
            str(route_recovery_memory.get("reopenStage"))
            if route_recovery_memory and route_recovery_memory.get("reopenStage")
            else None
        )
        reopen_stage_label = self._map_reopen_stage_label(reopen_stage)
        recovery_phase = (
            str(route_recovery_memory.get("phase"))
            if route_recovery_memory and route_recovery_memory.get("phase")
            else None
        )
        completion_count = (
            int(existing_route_follow_up_memory.get("completionCount"))
            if existing_route_follow_up_memory and existing_route_follow_up_memory.get("completionCount")
            else 0
        )
        last_completed_route = (
            str(existing_route_follow_up_memory.get("lastCompletedRoute"))
            if existing_route_follow_up_memory and existing_route_follow_up_memory.get("lastCompletedRoute")
            else None
        )
        last_completed_at = (
            str(existing_route_follow_up_memory.get("lastCompletedAt"))
            if existing_route_follow_up_memory and existing_route_follow_up_memory.get("lastCompletedAt")
            else None
        )

        if recovery_phase == "support_reopen_arc" and reopen_route and reopen_label:
            if reopen_stage == "ready_to_expand":
                return {
                    "currentRoute": "/daily-loop",
                    "currentLabel": "daily route",
                    "followUpRoute": reopen_route,
                    "followUpLabel": reopen_label,
                    "stageLabel": reopen_stage_label,
                    "status": "active",
                    "summary": f"The route widens through the daily route first, then keeps {reopen_label} available inside the broader flow.",
                    "completionCount": completion_count,
                    "lastCompletedRoute": last_completed_route,
                    "lastCompletedAt": last_completed_at,
                }
            if completion_count > 0 and last_completed_route == reopen_route:
                return {
                    "currentRoute": "/daily-loop",
                    "currentLabel": "daily route",
                    "followUpRoute": reopen_route,
                    "followUpLabel": reopen_label,
                    "stageLabel": reopen_stage_label or "Settling pass",
                    "status": "active",
                    "summary": (
                        f"{reopen_label} has already landed once inside the connected route, so the next route should reconnect through the daily route before giving it one more settling pass."
                    ),
                    "completionCount": completion_count,
                    "lastCompletedRoute": last_completed_route,
                    "lastCompletedAt": last_completed_at,
                }
            return {
                "currentRoute": reopen_route,
                "currentLabel": reopen_label,
                "followUpRoute": "/daily-loop",
                "followUpLabel": "daily route",
                "stageLabel": reopen_stage_label,
                "status": "active",
                "summary": f"The route should reopen through {reopen_label} first, then flow back into the connected daily route.",
                "completionCount": completion_count,
                "lastCompletedRoute": last_completed_route,
                "lastCompletedAt": last_completed_at,
            }

        if next_route and recovery_phase in {"skill_repair_cycle", "targeted_stabilization"}:
            next_label = self._map_route_to_support_label(next_route)
            return {
                "currentRoute": next_route,
                "currentLabel": next_label,
                "followUpRoute": "/daily-loop",
                "followUpLabel": "daily route",
                "stageLabel": None,
                "status": "active",
                "summary": f"The sequenced recovery route should reopen through {next_label} before returning to the main route.",
                "completionCount": completion_count,
                "lastCompletedRoute": last_completed_route,
                "lastCompletedAt": last_completed_at,
            }

        if (
            existing_route_follow_up_memory
            and str(existing_route_follow_up_memory.get("stageLabel") or "") == "Task-driven handoff"
        ):
            return existing_route_follow_up_memory

        ritual_route = (
            str(ritual_signal_memory.get("activeRoute"))
            if ritual_signal_memory and ritual_signal_memory.get("activeRoute")
            else None
        )
        ritual_route_label = self._map_route_to_support_label(ritual_route)
        ritual_label = (
            str(ritual_signal_memory.get("activeLabel"))
            if ritual_signal_memory and ritual_signal_memory.get("activeLabel")
            else "the ritual signal"
        )
        ritual_window_stage = (
            str(ritual_signal_memory.get("routeWindowStage"))
            if ritual_signal_memory and ritual_signal_memory.get("routeWindowStage")
            else None
        )
        if ritual_route and ritual_route_label and ritual_window_stage == "protect_ritual":
            return {
                "currentRoute": ritual_route,
                "currentLabel": ritual_route_label,
                "followUpRoute": "/daily-loop",
                "followUpLabel": "daily route",
                "carryRoute": "/activity",
                "carryLabel": "activity trail",
                "stageLabel": "Protect ritual",
                "status": "active",
                "summary": (
                    f"The route should start through {ritual_route_label}, then reconnect through the daily route and only after that widen into the broader activity trail while keeping {ritual_label} alive."
                ),
                "completionCount": completion_count,
                "lastCompletedRoute": last_completed_route,
                "lastCompletedAt": last_completed_at,
            }
        if ritual_route and ritual_route_label and ritual_window_stage == "reuse_in_response":
            return {
                "currentRoute": "/daily-loop",
                "currentLabel": "daily route",
                "followUpRoute": "/activity",
                "followUpLabel": "activity trail",
                "carryRoute": ritual_route,
                "carryLabel": ritual_route_label,
                "stageLabel": "Reuse in response",
                "status": "active",
                "summary": (
                    f"The route should reuse {ritual_label} inside the connected daily route now, then widen into the activity trail while keeping {ritual_route_label} quietly available."
                ),
                "completionCount": completion_count,
                "lastCompletedRoute": last_completed_route,
                "lastCompletedAt": last_completed_at,
            }
        if ritual_route and ritual_route_label and ritual_window_stage == "carry_inside_route":
            return {
                "currentRoute": "/daily-loop",
                "currentLabel": "daily route",
                "followUpRoute": "/activity",
                "followUpLabel": "activity trail",
                "carryRoute": ritual_route,
                "carryLabel": ritual_route_label,
                "stageLabel": "Carry inside route",
                "status": "active",
                "summary": (
                    f"The broader daily route should lead again now, then extend through the activity trail while keeping {ritual_label} available as a light carry-over instead of reopening a separate ritual branch."
                ),
                "completionCount": completion_count,
                "lastCompletedRoute": last_completed_route,
                "lastCompletedAt": last_completed_at,
            }

        return None

    def _complete_support_reopen_follow_up_memory(
        self,
        *,
        route: str,
        route_recovery_memory: dict | None,
        existing_route_follow_up_memory: dict | None,
    ) -> dict | None:
        if not route_recovery_memory or str(route_recovery_memory.get("phase") or "") != "support_reopen_arc":
            return existing_route_follow_up_memory
        if not existing_route_follow_up_memory:
            return existing_route_follow_up_memory

        reopen_route = (
            str(route_recovery_memory.get("reopenTargetRoute"))
            if route_recovery_memory.get("reopenTargetRoute")
            else str(existing_route_follow_up_memory.get("followUpRoute") or "")
        )
        reopen_label = (
            str(route_recovery_memory.get("reopenTargetLabel"))
            if route_recovery_memory.get("reopenTargetLabel")
            else self._map_route_to_support_label(reopen_route)
        )
        current_route = str(existing_route_follow_up_memory.get("currentRoute") or "")
        follow_up_route = str(existing_route_follow_up_memory.get("followUpRoute") or "")
        if route not in {reopen_route, current_route, follow_up_route}:
            return existing_route_follow_up_memory

        completion_count = int(existing_route_follow_up_memory.get("completionCount") or 0) + 1
        completed_at = datetime.utcnow().isoformat()
        if completion_count >= 2:
            stage_label = "Ready to widen"
            summary = (
                f"{reopen_label or 'This support step'} has already landed across two connected reopen passes, "
                "so the next route should widen through the daily route while keeping that support lane available inside the broader flow."
            )
            follow_up_label = reopen_label
        else:
            stage_label = "Settling pass"
            summary = (
                f"{reopen_label or 'This support step'} has landed once inside the connected route, "
                "so the next route should reconnect through the daily route before giving it one more settling pass."
            )
            follow_up_label = reopen_label

        return {
            **existing_route_follow_up_memory,
            "currentRoute": "/daily-loop",
            "currentLabel": "daily route",
            "followUpRoute": reopen_route,
            "followUpLabel": follow_up_label,
            "stageLabel": stage_label,
            "status": "active",
            "summary": summary,
            "completionCount": completion_count,
            "lastCompletedRoute": route,
            "lastCompletedAt": completed_at,
        }

    @staticmethod
    def _map_focus_skill_to_route(focus_skill: str | None) -> str | None:
        return (
            "/grammar"
            if focus_skill == "grammar"
            else "/speaking"
            if focus_skill == "speaking"
            else "/pronunciation"
            if focus_skill == "pronunciation"
            else "/writing"
            if focus_skill == "writing"
            else "/profession"
            if focus_skill == "profession"
            else "/vocabulary"
            if focus_skill == "vocabulary"
            else None
        )

    @staticmethod
    def _build_ordered_support_routes(focus_route: str | None) -> list[str]:
        route_map = {
            "/grammar": ["/grammar", "/writing", "/speaking", "/vocabulary", "/pronunciation"],
            "/vocabulary": ["/vocabulary", "/speaking", "/writing", "/grammar", "/pronunciation"],
            "/speaking": ["/speaking", "/pronunciation", "/writing", "/vocabulary", "/grammar"],
            "/pronunciation": ["/pronunciation", "/speaking", "/vocabulary", "/grammar", "/writing"],
            "/writing": ["/writing", "/grammar", "/vocabulary", "/speaking", "/pronunciation"],
            "/profession": ["/profession", "/speaking", "/writing", "/vocabulary", "/grammar"],
        }
        ordered_routes = route_map.get(focus_route, [focus_route] if focus_route else [])
        return [route for route in ordered_routes if route]

    def _build_route_reentry_progress(
        self,
        *,
        current_state: LearnerJourneyState | None,
        route_recovery_memory: dict | None,
    ) -> dict | None:
        if not route_recovery_memory:
            return None

        phase = str(route_recovery_memory.get("phase") or "")
        if phase not in {"skill_repair_cycle", "targeted_stabilization"}:
            return None

        focus_skill = str(
            route_recovery_memory.get("focusSkill")
            or (current_state.current_focus_area if current_state else "")
        ) or None
        focus_route = self._map_focus_skill_to_route(focus_skill)
        ordered_routes = self._build_ordered_support_routes(focus_route)
        if not ordered_routes:
            return None

        sequence_key = ":".join(
            [
                "route-reentry",
                current_state.user_id if current_state else "anonymous",
                current_state.last_daily_plan_id if current_state and current_state.last_daily_plan_id else "route",
                phase,
                focus_skill or "general",
            ]
        )
        existing = self._extract_route_reentry_progress(current_state)
        completed_routes: list[str] = []
        should_reuse_existing = False
        if existing:
            existing_phase = str(existing.get("phase") or "")
            existing_focus_skill = str(existing.get("focusSkill") or "") or None
            should_reuse_existing = (
                str(existing.get("sequenceKey")) == sequence_key
                or (
                    existing_phase == phase
                    and existing_focus_skill == focus_skill
                )
            )

        if existing and should_reuse_existing:
            completed_routes = [
                str(item)
                for item in existing.get("completedRoutes", [])
                if isinstance(item, str) and item in ordered_routes
            ]
        next_route = next(
            (candidate for candidate in ordered_routes if candidate not in completed_routes),
            None,
        )
        return {
            "sequenceKey": sequence_key,
            "phase": phase,
            "focusSkill": focus_skill,
            "orderedRoutes": ordered_routes,
            "completedRoutes": completed_routes,
            "nextRoute": next_route,
            "status": "completed" if next_route is None else "active",
        }

    def _build_route_entry_memory(
        self,
        *,
        current_state: LearnerJourneyState,
        route: str,
        source: str,
    ) -> dict:
        existing_memory = self._extract_route_entry_memory(current_state) or {}
        recent_entries = [
            entry
            for entry in existing_memory.get("recentEntries", [])
            if isinstance(entry, dict)
        ]
        route_recovery_memory = self._extract_route_recovery_memory(current_state) or {}
        route_reentry_progress = self._extract_route_reentry_progress(current_state) or {}
        recent_entries.append(
            {
                "route": route,
                "source": source,
                "enteredAt": datetime.utcnow().isoformat(),
                "stage": current_state.stage,
                "recoveryPhase": route_recovery_memory.get("phase"),
                "sessionShape": route_recovery_memory.get("sessionShape"),
                "nextRoute": route_reentry_progress.get("nextRoute"),
            }
        )
        trimmed_entries = recent_entries[-6:]
        repeated_route_count = sum(
            1 for item in trimmed_entries[-3:] if str(item.get("route") or "") == route
        )
        active_next_route = (
            str(route_reentry_progress.get("nextRoute"))
            if route_reentry_progress.get("nextRoute")
            else None
        )
        active_next_route_visits = (
            sum(
                1
                for item in trimmed_entries
                if active_next_route and str(item.get("route") or "") == active_next_route
            )
            if active_next_route
            else 0
        )
        connected_reset_routes = {"/daily-loop", "/lesson-runner"}
        last_active_next_route_index = (
            max(
                (
                    index
                    for index, item in enumerate(trimmed_entries)
                    if active_next_route and str(item.get("route") or "") == active_next_route
                ),
                default=-1,
            )
            if active_next_route
            else -1
        )
        connected_reset_visits = (
            sum(
                1
                for item in trimmed_entries[last_active_next_route_index + 1 :]
                if str(item.get("route") or "") in connected_reset_routes
            )
            if active_next_route and last_active_next_route_index >= 0
            else 0
        )
        ready_to_reopen_active_next_route = bool(
            active_next_route
            and active_next_route_visits >= 2
            and connected_reset_visits >= 2
        )
        return {
            "recentEntries": trimmed_entries,
            "lastRoute": route,
            "lastSource": source,
            "repeatedRouteCount": repeated_route_count,
            "activeNextRoute": active_next_route,
            "activeNextRouteVisits": active_next_route_visits,
            "connectedResetVisits": connected_reset_visits,
            "readyToReopenActiveNextRoute": ready_to_reopen_active_next_route,
        }

    @staticmethod
    def _label_route_reentry_route(route: str | None) -> str:
        route_labels = {
            "/grammar": "grammar support",
            "/vocabulary": "vocabulary support",
            "/speaking": "speaking support",
            "/pronunciation": "pronunciation support",
            "/writing": "writing support",
            "/profession": "professional support",
        }
        return route_labels.get(route or "", "the next support step")

    @staticmethod
    def _map_route_to_focus_area(route: str | None) -> str | None:
        route_map = {
            "/grammar": "grammar",
            "/vocabulary": "vocabulary",
            "/reading": "reading",
            "/listening": "listening",
            "/speaking": "speaking",
            "/pronunciation": "pronunciation",
            "/writing": "writing",
            "/profession": "profession",
        }
        return route_map.get(route or "")

    @staticmethod
    def _map_task_driven_input_label(route: str) -> str:
        return "reading input" if route == "/reading" else "listening input" if route == "/listening" else "task input"

    @staticmethod
    def _map_task_driven_response_label(route: str) -> str:
        return (
            "writing response"
            if route == "/writing"
            else "spoken response"
            if route == "/speaking"
            else "guided route"
            if route == "/lesson-runner"
            else JourneyService._map_route_to_support_label(route) or "next route step"
        )

    @classmethod
    def _build_route_reentry_summary_line(cls, route_reentry_progress: dict | None) -> str | None:
        if not route_reentry_progress or route_reentry_progress.get("status") == "completed":
            return None
        next_route = route_reentry_progress.get("nextRoute")
        if not next_route:
            return None
        completed_steps = len(route_reentry_progress.get("completedRoutes", []))
        total_steps = len(route_reentry_progress.get("orderedRoutes", []))
        return (
            f"Sequenced recovery has already cleared {completed_steps} of {total_steps} support steps, "
            f"so this route should reopen through {cls._label_route_reentry_route(str(next_route))} next."
        )

    @classmethod
    def _build_route_reentry_action_hint(cls, route_reentry_progress: dict | None) -> str | None:
        if not route_reentry_progress or route_reentry_progress.get("status") == "completed":
            return None
        next_route = route_reentry_progress.get("nextRoute")
        if not next_route:
            return None
        return f"Use {cls._label_route_reentry_route(str(next_route))} next so the recovery sequence stays in order."

    @staticmethod
    def _build_route_follow_up_summary_line(route_follow_up_memory: dict | None) -> str | None:
        if not route_follow_up_memory:
            return None
        summary = route_follow_up_memory.get("summary")
        return str(summary) if summary else None

    @staticmethod
    def _build_route_follow_up_action_hint(route_follow_up_memory: dict | None) -> str | None:
        if not route_follow_up_memory:
            return None
        current_label = (
            str(route_follow_up_memory.get("currentLabel"))
            if route_follow_up_memory.get("currentLabel")
            else None
        )
        follow_up_label = (
            str(route_follow_up_memory.get("followUpLabel"))
            if route_follow_up_memory.get("followUpLabel")
            else None
        )
        carry_label = (
            str(route_follow_up_memory.get("carryLabel"))
            if route_follow_up_memory.get("carryLabel")
            else None
        )
        if current_label and follow_up_label and carry_label:
            return (
                f"Move through {current_label} now, then continue through {follow_up_label} while keeping {carry_label} lightly available so the route stays connected."
            )
        if current_label and follow_up_label:
            return f"Move through {current_label} now, then continue through {follow_up_label} so the route stays connected."
        if follow_up_label:
            return f"Continue through {follow_up_label} next so the route keeps its sequence."
        return None

    @classmethod
    def _build_route_entry_memory_reset_label(cls, route_entry_memory: dict | None) -> str | None:
        if not route_entry_memory:
            return None
        active_next_route = route_entry_memory.get("activeNextRoute")
        active_next_route_visits = int(route_entry_memory.get("activeNextRouteVisits") or 0)
        ready_to_reopen = bool(route_entry_memory.get("readyToReopenActiveNextRoute"))
        if not active_next_route or active_next_route_visits < 2 or ready_to_reopen:
            return None
        return cls._label_route_reentry_route(str(active_next_route))

    @classmethod
    def _build_route_entry_memory_reopen_label(cls, route_entry_memory: dict | None) -> str | None:
        if not route_entry_memory or not route_entry_memory.get("readyToReopenActiveNextRoute"):
            return None
        active_next_route = route_entry_memory.get("activeNextRoute")
        if not active_next_route:
            return None
        return cls._label_route_reentry_route(str(active_next_route))

    @classmethod
    def _build_route_entry_memory_summary_line(cls, route_entry_memory: dict | None) -> str | None:
        reset_label = cls._build_route_entry_memory_reset_label(route_entry_memory)
        if reset_label:
            active_next_route_visits = int(route_entry_memory.get("activeNextRouteVisits") or 0)
            return (
                f"{reset_label.capitalize()} has already reopened {active_next_route_visits} times in recent returns, "
                "so today's route resets through the calmer main path before trying that support surface again."
            )
        reopen_label = cls._build_route_entry_memory_reopen_label(route_entry_memory)
        if not reopen_label:
            return None
        connected_reset_visits = int(route_entry_memory.get("connectedResetVisits") or 0)
        return (
            f"Connected reset has already landed across {connected_reset_visits} calmer route passes, "
            f"so the route can reopen through {reopen_label} again without losing continuity."
        )

    @classmethod
    def _build_route_entry_memory_action_hint(cls, route_entry_memory: dict | None) -> str | None:
        reset_label = cls._build_route_entry_memory_reset_label(route_entry_memory)
        if reset_label:
            return f"Use today's calmer main route first, then reopen {reset_label} after the sequence regains momentum."
        reopen_label = cls._build_route_entry_memory_reopen_label(route_entry_memory)
        if not reopen_label:
            return None
        return f"Bring {reopen_label} back early inside the next connected route, but keep the rest of the session on the main path."

    @classmethod
    def _build_route_reentry_progress_summary(
        cls,
        route_reentry_progress: dict,
        route_recovery_memory: dict | None,
        *,
        fallback: str,
    ) -> str:
        next_route = route_reentry_progress.get("nextRoute")
        if next_route:
            return (
                f"{route_recovery_memory.get('summary') if route_recovery_memory else fallback} "
                f"The recovery sequence is now reopening through {cls._label_route_reentry_route(str(next_route))}."
            )
        return (
            f"{route_recovery_memory.get('summary') if route_recovery_memory else fallback} "
            "The sequenced support steps are complete, so the route can widen again without losing continuity."
        )

    @classmethod
    def _build_route_reentry_progress_next_action(
        cls,
        route_reentry_progress: dict,
        *,
        fallback: str,
    ) -> str:
        next_route = route_reentry_progress.get("nextRoute")
        if next_route:
            return f"Open {cls._label_route_reentry_route(str(next_route))} next so the recovery sequence stays in order."
        return fallback

    def _build_skill_trajectory_memory(
        self,
        user_id: str,
        current_state: LearnerJourneyState | None = None,
        active_skill_focus: list[str] | None = None,
    ) -> dict | None:
        resolved_active_skill_focus = self._resolve_active_skill_focus(
            current_state=current_state,
            active_skill_focus=active_skill_focus,
        )
        if self._progress_repository is not None:
            recent_progress = self._progress_repository.list_recent_snapshots(user_id, limit=3)
            trajectory = build_progress_trajectory(recent_progress, resolved_active_skill_focus)
            if trajectory is not None:
                return trajectory.model_dump(mode="json", by_alias=True)
        return self._extract_skill_trajectory(current_state)

    def _build_strategy_memory(
        self,
        user_id: str,
        current_state: LearnerJourneyState | None = None,
        active_skill_focus: list[str] | None = None,
    ) -> dict | None:
        resolved_active_skill_focus = self._resolve_active_skill_focus(
            current_state=current_state,
            active_skill_focus=active_skill_focus,
        )
        if self._progress_repository is not None:
            recent_progress = self._progress_repository.list_recent_snapshots(user_id, limit=5)
            strategy_memory = build_strategy_memory(recent_progress, resolved_active_skill_focus)
            if strategy_memory is not None:
                return strategy_memory.model_dump(mode="json", by_alias=True)
        return self._extract_strategy_memory(current_state)

    def _build_route_cadence_memory(
        self,
        user_id: str,
        current_state: LearnerJourneyState | None = None,
    ) -> dict | None:
        recent_plans = self._repository.list_recent_daily_loop_plans(user_id, limit=6)
        cadence_memory = self._summarize_route_cadence_memory(recent_plans)
        if cadence_memory is not None:
            return cadence_memory
        return self._extract_route_cadence_memory(current_state)

    def _build_route_recovery_memory(
        self,
        *,
        user_id: str | None = None,
        current_state: LearnerJourneyState | None = None,
        session_summary: dict | None = None,
        skill_trajectory: dict | None = None,
        strategy_memory: dict | None = None,
        route_cadence_memory: dict | None = None,
    ) -> dict | None:
        recovery_memory = self._summarize_route_recovery_memory(
            session_summary=session_summary or self._extract_session_summary(current_state),
            skill_trajectory=skill_trajectory or self._extract_skill_trajectory(current_state),
            strategy_memory=strategy_memory or self._extract_strategy_memory(current_state),
            route_cadence_memory=route_cadence_memory or self._extract_route_cadence_memory(current_state),
            route_entry_memory=self._extract_route_entry_memory(current_state),
        )
        existing_recovery_memory = self._extract_route_recovery_memory(current_state)
        existing_reentry_progress = self._extract_route_reentry_progress(current_state)

        if (
            existing_recovery_memory
            and existing_reentry_progress
            and str(existing_reentry_progress.get("status") or "") == "active"
            and str(existing_recovery_memory.get("phase") or "") in {"skill_repair_cycle", "targeted_stabilization", "support_reopen_arc"}
            and (
                recovery_memory is None
                or str(recovery_memory.get("phase") or "") not in {"skill_repair_cycle", "targeted_stabilization", "support_reopen_arc"}
            )
        ):
            return existing_recovery_memory

        if recovery_memory is not None:
            if user_id and str(recovery_memory.get("phase") or "") == "support_reopen_arc":
                recovery_memory = self._extend_support_reopen_arc(
                    user_id=user_id,
                    route_recovery_memory=recovery_memory,
                    current_state=current_state,
                )
            elif (
                user_id
                and str(recovery_memory.get("decisionBias") or "") == "task_transfer_window"
                and not recovery_memory.get("transferWindowAction")
            ):
                recovery_memory = self._extend_task_transfer_window(
                    user_id=user_id,
                    route_recovery_memory=recovery_memory,
                )
            return recovery_memory
        return existing_recovery_memory

    def _extend_task_transfer_window(
        self,
        *,
        user_id: str,
        route_recovery_memory: dict,
    ) -> dict:
        focus_skill = str(route_recovery_memory.get("focusSkill") or "")
        if not focus_skill:
            return route_recovery_memory

        today_key = datetime.utcnow().date().isoformat()
        recent_plans = self._repository.list_recent_daily_loop_plans(user_id, limit=5)
        completed_focus_days = [
            plan
            for plan in recent_plans
            if plan.plan_date_key != today_key
            and plan.focus_area == focus_skill
            and plan.status == "completed"
        ]
        completed_passes = len(completed_focus_days)
        transfer_outcome = str(route_recovery_memory.get("transferOutcome") or "")
        support_label = str(route_recovery_memory.get("supportPracticeTitle") or "the response lane")

        if transfer_outcome == "fragile":
            if completed_passes >= 2:
                stage = "ready_to_widen"
                session_shape = "forward_mix"
                summary = (
                    f"The protected response work has already held across two connected passes, so the route can widen again while keeping {support_label} available."
                )
                action_hint = (
                    f"Let the broader daily route lead again while keeping {support_label} available as quiet support."
                )
                next_phase_hint = (
                    f"If {support_label} stays stable inside the broader mix, the route can fully release the protected transfer window."
                )
                remaining_days = 1
            elif completed_passes >= 1:
                stage = "stabilize_transfer"
                session_shape = "guided_balance"
                summary = (
                    f"The first protected response pass has landed, so the route now needs one stabilizing pass before it widens again around {support_label}."
                )
                action_hint = (
                    f"Keep one more connected pass around {support_label} before you let the broader route widen again."
                )
                next_phase_hint = (
                    f"If this stabilizing pass holds, {support_label} can stay inside a broader route without being the whole focus."
                )
                remaining_days = 1
            else:
                stage = "protect_response"
                session_shape = "focused_support"
                summary = (
                    f"The route should protect {support_label} first, because the last input-to-response transfer was still fragile."
                )
                action_hint = (
                    f"Use the next route as a protected response pass around {support_label} before you widen back out."
                )
                next_phase_hint = (
                    f"After the protected response pass lands, the route can move into one stabilizing pass before widening."
                )
                remaining_days = 2
        elif transfer_outcome == "usable":
            if completed_passes >= 1:
                stage = "ready_to_widen"
                session_shape = "forward_mix"
                summary = (
                    f"The response lane has already stabilized enough, so the route can widen again while keeping {support_label} alive inside the broader mix."
                )
                action_hint = (
                    f"Let the broader route lead now and keep {support_label} available without forcing another narrow pass."
                )
                next_phase_hint = (
                    f"If {support_label} stays reusable in the broader mix, the task-transfer window can phase out."
                )
                remaining_days = 1
            else:
                stage = "stabilize_transfer"
                session_shape = "guided_balance"
                summary = (
                    f"The route should use one stabilizing pass around {support_label} so the last task-driven transfer becomes easier to reuse."
                )
                action_hint = (
                    f"Keep one more connected pass around {support_label} before the route widens further."
                )
                next_phase_hint = (
                    f"If this stabilizing pass holds, the route can widen back into the broader mix."
                )
                remaining_days = 1
        else:
            stage = "ready_to_widen"
            session_shape = "forward_mix"
            summary = (
                f"The last task-driven transfer held cleanly, so the route can widen while keeping {support_label} available inside the broader mix."
            )
            action_hint = (
                f"Let the broader route lead and keep {support_label} available as quiet support."
            )
            next_phase_hint = (
                f"If the broader route still carries {support_label} cleanly, the transfer window can phase out."
            )
            remaining_days = 1

        refreshed = dict(route_recovery_memory)
        refreshed["sessionShape"] = session_shape
        refreshed["summary"] = summary
        refreshed["actionHint"] = action_hint
        refreshed["nextPhaseHint"] = next_phase_hint
        refreshed["decisionWindowStage"] = stage
        refreshed["decisionWindowRemainingDays"] = remaining_days
        refreshed["decisionWindowDays"] = max(int(route_recovery_memory.get("decisionWindowDays") or remaining_days), remaining_days)
        return refreshed

    def _extend_support_reopen_arc(
        self,
        *,
        user_id: str,
        route_recovery_memory: dict,
        current_state: LearnerJourneyState | None = None,
    ) -> dict:
        reopen_focus = (
            str(route_recovery_memory.get("focusSkill"))
            if route_recovery_memory.get("focusSkill")
            else None
        )
        if not reopen_focus:
            return route_recovery_memory

        today_key = datetime.utcnow().date().isoformat()
        recent_plans = self._repository.list_recent_daily_loop_plans(user_id, limit=5)
        reopen_days = [
            plan
            for plan in recent_plans
            if plan.plan_date_key != today_key and plan.focus_area == reopen_focus
        ]
        reopen_day_count = len(reopen_days)
        route_follow_up_memory = self._extract_route_follow_up_memory(current_state)
        persisted_completion_count = (
            int(route_follow_up_memory.get("completionCount"))
            if route_follow_up_memory and route_follow_up_memory.get("completionCount")
            else 0
        )
        derived_completion_count = (
            int(route_recovery_memory.get("followUpCompletionCount"))
            if route_recovery_memory.get("followUpCompletionCount") is not None
            else 0
        )
        completion_count = max(persisted_completion_count, derived_completion_count)
        effective_reopen_count = max(reopen_day_count, completion_count)
        base_support_label = route_recovery_memory.get("supportPracticeTitle") or reopen_focus
        if effective_reopen_count >= 2:
            decision_window_days = max(int(route_recovery_memory.get("horizonDays") or 0), 2)
            wider_route_days = [
                plan
                for plan in recent_plans
                if plan.plan_date_key != today_key and plan.focus_area != reopen_focus
            ]
            widening_pass_count = min(len(wider_route_days), decision_window_days)
            decision_window_remaining_days = max(decision_window_days - widening_pass_count, 0)
            if widening_pass_count <= 0:
                decision_window_stage = "first_widening_pass"
                summary = (
                    f"{base_support_label} has already landed across {effective_reopen_count} connected reopen passes, so the next route should act as the first wider pass without dropping it."
                )
                action_hint = (
                    f"Use the next route as the first widening pass: let the daily route lead while {base_support_label} stays available inside the mix."
                )
                next_phase_hint = (
                    f"If this first widening pass stays stable, the route can use one more broader pass before it starts extending forward again."
                )
            elif widening_pass_count == 1:
                decision_window_stage = "stabilizing_widening"
                summary = (
                    f"{base_support_label} has already survived the first wider pass, so the next route should stabilize that broader mix once more before extending further."
                )
                action_hint = (
                    f"Use the next route to stabilize the wider mix: keep the daily route leading and let {base_support_label} stay connected without reclaiming the whole session."
                )
                next_phase_hint = (
                    f"If this stabilizing pass also holds, the route can start extending beyond the controlled widening window."
                )
            else:
                decision_window_stage = "ready_for_extension"
                summary = (
                    f"{base_support_label} has already held across the recent widening passes, so the route can begin extending forward again without treating it as a protected center lane."
                )
                action_hint = (
                    f"Let the broader route keep leading and start widening beyond the reopen window while {base_support_label} stays available as quiet support."
                )
                next_phase_hint = (
                    f"If the route keeps feeling stable, the reopen arc can dissolve into steady extension from here."
                )
            return {
                **route_recovery_memory,
                "sessionShape": "guided_balance",
                "reopenStage": "ready_to_expand",
                "reopenDayCount": reopen_day_count,
                "followUpCompletionCount": completion_count,
                "decisionBias": "widening_window",
                "decisionWindowDays": decision_window_days,
                "decisionWindowStage": decision_window_stage,
                "decisionWindowRemainingDays": decision_window_remaining_days,
                "wideningPassCount": widening_pass_count,
                "summary": summary,
                "actionHint": action_hint,
                "nextPhaseHint": next_phase_hint,
                "expansionReady": True,
            }
        if effective_reopen_count == 1:
            return {
                **route_recovery_memory,
                "reopenStage": "settling_back_in",
                "reopenDayCount": reopen_day_count,
                "followUpCompletionCount": completion_count,
                "decisionBias": "settling_window",
                "decisionWindowDays": 1,
                "decisionWindowStage": "settling_pass",
                "decisionWindowRemainingDays": 1,
                "summary": (
                    f"{base_support_label} has already landed once inside the connected route, so the next pass should reconnect through the daily route and settle it before the route widens."
                ),
                "actionHint": (
                    f"Use the next connected route to settle {base_support_label}, then let the wider path reopen again."
                ),
                "nextPhaseHint": (
                    f"If this settling pass holds, the route can widen after that without another protected reset."
                ),
                "expansionReady": False,
            }
        return {
            **route_recovery_memory,
            "reopenStage": "first_reopen",
            "reopenDayCount": 0,
            "followUpCompletionCount": completion_count,
            "expansionReady": False,
            "decisionBias": "settling_window",
            "decisionWindowDays": 1,
            "decisionWindowStage": "settling_pass",
            "decisionWindowRemainingDays": 1,
        }

    @staticmethod
    def _summarize_route_cadence_memory(
        recent_plans: list[DailyLoopPlan],
        *,
        reference_date: date | None = None,
    ) -> dict | None:
        if not recent_plans:
            return None

        today = reference_date or datetime.utcnow().date()
        parsed_plans: list[tuple[DailyLoopPlan, date]] = []
        for plan in recent_plans:
            try:
                parsed_date = date.fromisoformat(plan.plan_date_key)
            except ValueError:
                continue
            parsed_plans.append((plan, parsed_date))

        if not parsed_plans:
            return None

        completed_plans = [item for item in parsed_plans if item[0].completed_at]
        missed_plans = [
            item
            for item in parsed_plans
            if not item[0].completed_at and item[1] < today
        ]
        last_completed_date = completed_plans[0][1] if completed_plans else None
        idle_days = (
            max((today - last_completed_date).days, 0)
            if last_completed_date is not None
            else max(len(parsed_plans), 1)
        )
        completed_recently = len([item for item in parsed_plans[:4] if item[0].completed_at])

        if not completed_plans:
            status = "building_rhythm"
            summary = (
                "The route is still building its return rhythm, so the next step should stay simple and easy to re-enter."
            )
            action_hint = (
                "Keep this route short and finishable until the first few returns start to feel stable."
            )
        elif idle_days >= 4 or len(missed_plans) >= 2:
            status = "route_rescue"
            summary = (
                f"Recent route rhythm has slipped for about {idle_days} days, so the next entry should restart gently instead of widening immediately."
            )
            action_hint = (
                "Start with a short warm re-entry and one visible win before pushing the route wider again."
            )
        elif idle_days >= 2 or len(missed_plans) >= 1:
            status = "gentle_reentry"
            summary = (
                "The learner is returning after a short break, so the route should reopen calmly before it asks for more range."
            )
            action_hint = (
                "Use a calmer restart and let the route earn momentum again instead of jumping straight into pressure."
            )
        elif completed_recently >= 3:
            status = "steady_return"
            summary = (
                "Recent route history shows a steady return rhythm, so the next step can stay crisp and forward-moving."
            )
            action_hint = (
                "Keep the ritual moving with a clear next step instead of restarting from zero."
            )
        else:
            status = "warming_up"
            summary = (
                "The route is starting to stabilize, so the next step should stay clear and easy to complete."
            )
            action_hint = (
                "Keep the route compact enough to finish and easy to pick up again tomorrow."
            )

        return {
            "status": status,
            "observedPlans": len(parsed_plans),
            "completedPlans": len(completed_plans),
            "missedPlans": len(missed_plans),
            "idleDays": idle_days,
            "summary": summary,
            "actionHint": action_hint,
        }

    @staticmethod
    def _summarize_route_recovery_memory(
        *,
        session_summary: dict | None = None,
        skill_trajectory: dict | None = None,
        strategy_memory: dict | None = None,
        route_cadence_memory: dict | None = None,
        route_entry_memory: dict | None = None,
    ) -> dict | None:
        cadence_status = str(route_cadence_memory.get("status") or "") if route_cadence_memory else ""
        strategy_focus = (
            str(strategy_memory.get("focusSkill"))
            if strategy_memory and strategy_memory.get("focusSkill")
            else ""
        )
        strategy_level = (
            str(strategy_memory.get("persistenceLevel"))
            if strategy_memory and strategy_memory.get("persistenceLevel")
            else ""
        )
        trajectory_focus = (
            str(skill_trajectory.get("focusSkill"))
            if skill_trajectory and skill_trajectory.get("focusSkill")
            else ""
        )
        trajectory_direction = (
            str(skill_trajectory.get("direction"))
            if skill_trajectory and skill_trajectory.get("direction")
            else ""
        )
        practice_shift = (
            session_summary.get("practiceMixEvaluation")
            if session_summary and isinstance(session_summary.get("practiceMixEvaluation"), dict)
            else None
        )
        support_practice_title = (
            str(practice_shift.get("strongestPracticeTitle"))
            if practice_shift and practice_shift.get("strongestPracticeTitle")
            else str(practice_shift.get("leadPracticeTitle"))
            if practice_shift and practice_shift.get("leadPracticeTitle")
            else str(session_summary.get("carryOverSignalLabel"))
            if session_summary and session_summary.get("carryOverSignalLabel")
            else None
        )
        focus_skill = (
            strategy_focus
            or trajectory_focus
            or str(session_summary.get("watchSignalLabel"))
            if session_summary and session_summary.get("watchSignalLabel")
            else None
        )
        outcome_band = str(session_summary.get("outcomeBand") or "") if session_summary else ""
        route_recovery_evaluation = (
            session_summary.get("routeRecoveryEvaluation")
            if session_summary and isinstance(session_summary.get("routeRecoveryEvaluation"), dict)
            else None
        )
        task_driven_transfer_evaluation = (
            session_summary.get("taskDrivenTransferEvaluation")
            if session_summary and isinstance(session_summary.get("taskDrivenTransferEvaluation"), dict)
            else None
        )
        has_route_recovery_override = bool(
            route_recovery_evaluation and str(route_recovery_evaluation.get("phase") or "") == "support_reopen_arc"
        )
        has_task_driven_transfer_signal = bool(task_driven_transfer_evaluation)
        has_reopen_entry_signal = bool(
            route_entry_memory
            and route_entry_memory.get("readyToReopenActiveNextRoute")
            and route_entry_memory.get("activeNextRoute")
        )

        if (
            not cadence_status
            and not strategy_focus
            and not trajectory_focus
            and not has_route_recovery_override
            and not has_task_driven_transfer_signal
            and not has_reopen_entry_signal
        ):
            return None

        reopen_stage = None
        expansion_ready = None
        follow_up_completion_count = None
        decision_bias = None
        decision_window_days = None
        decision_window_stage = None
        decision_window_remaining_days = None

        if cadence_status in {"route_rescue", "building_rhythm"}:
            horizon_days = 3 if strategy_level in {"persistent", "recurring"} or trajectory_direction == "slipping" else 2
            summary = (
                f"The route should rebuild over the next {horizon_days} sessions, staying gentle while it protects {focus_skill or 'the weakest signal'}."
            )
            action_hint = (
                f"Keep the next {horizon_days} routes short and finishable, using {support_practice_title or 'one visible win'} as the support lane before the route widens again."
            )
            next_phase_hint = "Once the rhythm returns, widen back into fuller mixed practice without dropping the protected signal."
            phase = "route_rebuild"
            session_shape = "gentle_restart"
        elif cadence_status == "gentle_reentry":
            horizon_days = 3 if strategy_level == "persistent" else 2
            summary = (
                f"The route is back in motion, but the next {horizon_days} sessions should still protect {focus_skill or 'the current weak area'} before opening fully."
            )
            action_hint = (
                f"Use a protected return for the next {horizon_days} routes and let {support_practice_title or 'the calmer support lane'} carry some of the load."
            )
            next_phase_hint = "If the return rhythm holds, the route can widen again after these protected sessions."
            phase = "protected_return"
            session_shape = "protected_mix"
        elif strategy_level in {"persistent", "recurring"}:
            horizon_days = 3 if strategy_level == "persistent" else 2
            summary = (
                f"{focus_skill or 'This signal'} needs a multi-day repair cycle, so the next {horizon_days} routes should keep revisiting it on purpose."
            )
            action_hint = (
                f"Treat {focus_skill or 'this skill'} as the durable repair target and use {support_practice_title or 'the strongest practice lane'} to keep it supported."
            )
            next_phase_hint = "After this repair cycle, the route can broaden without forgetting the longer-term pressure point."
            phase = "skill_repair_cycle"
            session_shape = "focused_support"
        elif trajectory_direction in {"slipping", "stable"}:
            horizon_days = 2
            summary = (
                f"The route should spend the next {horizon_days} sessions stabilizing {focus_skill or 'the slipping signal'} before it pushes wider again."
            )
            action_hint = (
                f"Keep {focus_skill or 'the weak signal'} in view and let {support_practice_title or 'the strongest practice lane'} support the next sessions."
            )
            next_phase_hint = "If the signal steadies, the route can widen naturally after this stabilization pass."
            phase = "targeted_stabilization"
            session_shape = "guided_balance"
        elif cadence_status == "steady_return":
            horizon_days = 2
            summary = (
                f"The return rhythm is holding, so the next {horizon_days} routes can extend forward while still protecting {focus_skill or 'the current route focus'}."
            )
            action_hint = (
                f"Keep momentum through connected sessions and let {support_practice_title or 'the strongest practice lane'} support the extension."
            )
            next_phase_hint = "The route can keep widening gradually as long as the daily rhythm stays steady."
            phase = "steady_extension"
            session_shape = "forward_mix"
        elif task_driven_transfer_evaluation:
            horizon_days = 1
            summary = "The route should keep the last input-to-response transfer connected a little longer."
            action_hint = "Keep the response lane connected before the route widens again."
            next_phase_hint = "If the next connected pass holds, the route can widen again naturally."
            phase = "targeted_stabilization"
            session_shape = "guided_balance"
        else:
            return None

        if outcome_band == "fragile" and phase not in {"route_rebuild", "protected_return"}:
            action_hint = (
                f"Keep tomorrow narrower and let {support_practice_title or 'the strongest practice lane'} absorb pressure while {focus_skill or 'the weak signal'} stabilizes."
            )

        route_entry_reset_label = JourneyService._build_route_entry_memory_reset_label(route_entry_memory)
        route_entry_reset_visits = int(route_entry_memory.get("activeNextRouteVisits") or 0) if route_entry_memory else 0
        if route_entry_reset_label and route_entry_reset_visits >= 2 and phase in {
            "skill_repair_cycle",
            "targeted_stabilization",
            "protected_return",
        }:
            horizon_days = max(horizon_days, 2)
            phase = "protected_return"
            session_shape = "protected_mix"
            summary = (
                f"The route should spend the next {horizon_days} sessions reconnecting through the calmer main path before reopening {route_entry_reset_label} again, "
                f"while it keeps protecting {focus_skill or 'the current weak signal'}."
            )
            action_hint = (
                f"Use the next {horizon_days} routes as connected reset passes, keep {focus_skill or 'the focus signal'} steady, "
                f"and reopen {route_entry_reset_label} only after the calmer main route lands cleanly."
            )
            next_phase_hint = (
                f"If the calmer reset holds, {route_entry_reset_label} can reopen again without trapping the learner in the same side-surface."
            )

        route_entry_reopen_label = JourneyService._build_route_entry_memory_reopen_label(route_entry_memory)
        route_entry_reopen_visits = int(route_entry_memory.get("connectedResetVisits") or 0) if route_entry_memory else 0
        route_entry_reopen_route = (
            str(route_entry_memory.get("activeNextRoute"))
            if route_entry_memory and route_entry_memory.get("activeNextRoute")
            else None
        )
        route_entry_reopen_focus = JourneyService._map_route_to_focus_area(route_entry_reopen_route)
        if route_entry_reopen_label and route_entry_reopen_visits >= 2:
            horizon_days = max(horizon_days, 2)
            phase = "support_reopen_arc"
            session_shape = "protected_mix"
            summary = (
                f"The calmer reset has landed, so the next {horizon_days} sessions should reopen through {route_entry_reopen_label} "
                f"while still protecting {focus_skill or 'the current weak signal'}."
            )
            action_hint = (
                f"Let {route_entry_reopen_label} come back early inside the next {horizon_days} routes, but keep the rest of the route connected so the reopen does not turn into a side-track."
            )
            next_phase_hint = (
                f"If {route_entry_reopen_label} holds cleanly inside the connected route, the recovery arc can widen again without another reset pass."
            )
            support_practice_title = route_entry_reopen_label
            if route_entry_reopen_focus:
                focus_skill = route_entry_reopen_focus

        if route_recovery_evaluation and str(route_recovery_evaluation.get("phase") or "") == "support_reopen_arc":
            next_stage = str(route_recovery_evaluation.get("nextStage") or "")
            evaluation_support_label = str(
                route_recovery_evaluation.get("supportLabel") or support_practice_title or route_entry_reopen_label or "the reopened support lane"
            )
            evaluation_focus = str(route_recovery_evaluation.get("focusArea") or focus_skill or "") or None
            horizon_days = max(horizon_days, 2)
            phase = "support_reopen_arc"
            support_practice_title = evaluation_support_label
            if evaluation_focus:
                focus_skill = evaluation_focus
            if next_stage == "ready_to_expand":
                session_shape = "guided_balance"
                summary = str(
                    route_recovery_evaluation.get("summary")
                    or f"The reopen arc is ready to widen again while keeping {evaluation_support_label} available inside the broader route."
                )
                action_hint = str(
                    route_recovery_evaluation.get("actionHint")
                    or f"Let the broader daily route lead again while keeping {evaluation_support_label} available as support."
                )
                next_phase_hint = (
                    f"If {evaluation_support_label} stays stable inside the wider route, the reopen arc can phase out into steady extension."
                )
                reopen_stage = "ready_to_expand"
                expansion_ready = True
                decision_bias = "widening_window"
                decision_window_days = max(horizon_days, 2)
                decision_window_stage = "first_widening_pass"
                decision_window_remaining_days = decision_window_days
            else:
                session_shape = "protected_mix"
                summary = str(
                    route_recovery_evaluation.get("summary")
                    or f"The route still needs one more connected settling pass around {evaluation_support_label} before it widens again."
                )
                action_hint = str(
                    route_recovery_evaluation.get("actionHint")
                    or f"Use one more connected settling pass around {evaluation_support_label} before widening the route again."
                )
                next_phase_hint = (
                    f"If this settling pass lands cleanly, {evaluation_support_label} can stay available while the broader route widens again."
                )
                reopen_stage = "settling_back_in"
                expansion_ready = False
                decision_bias = "settling_window"
                decision_window_days = 1
                decision_window_stage = "settling_pass"
                decision_window_remaining_days = 1
            follow_up_completion_count = (
                int(route_recovery_evaluation.get("completionCount"))
                if route_recovery_evaluation.get("completionCount") is not None
                else None
            )
        elif task_driven_transfer_evaluation:
            response_route = str(task_driven_transfer_evaluation.get("responseRoute") or "")
            response_focus = JourneyService._map_route_to_focus_area(response_route)
            response_label = str(
                task_driven_transfer_evaluation.get("responseLabel")
                or (JourneyService._map_task_driven_response_label(response_route) if response_route else "the response lane")
            )
            transfer_outcome = str(task_driven_transfer_evaluation.get("transferOutcome") or "usable")
            transfer_summary = str(
                task_driven_transfer_evaluation.get("summary")
                or f"The route should keep {response_label} connected a little longer."
            )
            next_window_stage = str(task_driven_transfer_evaluation.get("nextWindowStage") or "")
            next_window_days = (
                int(task_driven_transfer_evaluation.get("nextWindowDays"))
                if task_driven_transfer_evaluation.get("nextWindowDays") is not None
                else None
            )
            window_action = str(task_driven_transfer_evaluation.get("windowAction") or "")
            window_summary = str(task_driven_transfer_evaluation.get("windowSummary") or "")
            phase = "targeted_stabilization" if transfer_outcome in {"fragile", "usable"} else "steady_extension"
            focus_skill = response_focus or focus_skill
            support_practice_title = response_label
            if next_window_stage == "close_window":
                horizon_days = max(horizon_days, 1)
                phase = "steady_extension"
                session_shape = "forward_mix"
                summary = (
                    window_summary
                    or f"The protected transfer window has held cleanly enough that the broader route can lead again while {response_label} stays reusable."
                )
                action_hint = (
                    f"Let the broader daily route lead again and keep {response_label} available as quiet support instead of the main protection target."
                )
                next_phase_hint = (
                    f"If the broader route keeps carrying {response_label} cleanly, the transfer window can stay closed."
                )
            else:
                resolved_window_stage = next_window_stage
                if not resolved_window_stage:
                    resolved_window_stage, _, _ = JourneyService._resolve_task_transfer_window_progression(
                        current_window_stage="",
                        transfer_outcome=transfer_outcome,
                    )
                if resolved_window_stage == "protect_response":
                    horizon_days = max(horizon_days, 2)
                    session_shape = "focused_support"
                    summary = (
                        window_summary
                        or f"{transfer_summary} The next routes should protect {response_label} before the route widens again."
                    )
                    action_hint = (
                        f"Use the next route as a protected {response_label} pass, then give it one stabilizing pass before widening."
                    )
                    next_phase_hint = (
                        f"After the protected and stabilizing passes, the route can widen again if {response_label} stays reusable."
                    )
                    decision_bias = "task_transfer_window"
                    decision_window_days = next_window_days if next_window_days is not None else 2
                    decision_window_stage = "protect_response"
                    decision_window_remaining_days = decision_window_days
                elif resolved_window_stage == "stabilize_transfer":
                    horizon_days = max(horizon_days, 2)
                    session_shape = "guided_balance"
                    summary = (
                        window_summary
                        or f"{transfer_summary} The route should use one stabilizing pass around {response_label} before it widens further."
                    )
                    action_hint = (
                        f"Keep one more connected pass around {response_label}, then let the broader route widen again."
                    )
                    next_phase_hint = (
                        f"If the stabilizing pass holds, {response_label} can stay inside the broader mix without extra protection."
                    )
                    decision_bias = "task_transfer_window"
                    decision_window_days = next_window_days if next_window_days is not None else 1
                    decision_window_stage = "stabilize_transfer"
                    decision_window_remaining_days = decision_window_days
                else:
                    horizon_days = max(horizon_days, 1)
                    session_shape = "forward_mix"
                    summary = (
                        window_summary
                        or f"{transfer_summary} The route can widen again while keeping {response_label} available inside the broader mix."
                    )
                    action_hint = (
                        f"Let the broader route lead and keep {response_label} available as quiet support."
                    )
                    next_phase_hint = (
                        f"If the broader route keeps carrying {response_label} cleanly, the transfer window can phase out."
                    )
                    decision_bias = "task_transfer_window"
                    decision_window_days = next_window_days if next_window_days is not None else 1
                    decision_window_stage = "ready_to_widen"
                    decision_window_remaining_days = decision_window_days
            follow_up_completion_count = None
        else:
            reopen_stage = None
            expansion_ready = None
            follow_up_completion_count = None
            decision_bias = None
            decision_window_days = None
            decision_window_stage = None
            decision_window_remaining_days = None

        result = {
            "phase": phase,
            "horizonDays": horizon_days,
            "focusSkill": focus_skill,
            "supportPracticeTitle": support_practice_title,
            "sessionShape": session_shape,
            "summary": summary,
            "actionHint": action_hint,
            "nextPhaseHint": next_phase_hint,
            "reopenTargetLabel": route_entry_reopen_label,
            "reopenTargetRoute": route_entry_reopen_route,
            "reopenReady": bool(route_entry_reopen_label),
        }
        if reopen_stage is not None:
            result["reopenStage"] = reopen_stage
        if expansion_ready is not None:
            result["expansionReady"] = expansion_ready
        if follow_up_completion_count is not None:
            result["followUpCompletionCount"] = follow_up_completion_count
        if decision_bias is not None:
            result["decisionBias"] = decision_bias
        if decision_window_days is not None:
            result["decisionWindowDays"] = decision_window_days
        if decision_window_stage is not None:
            result["decisionWindowStage"] = decision_window_stage
        if decision_window_remaining_days is not None:
            result["decisionWindowRemainingDays"] = decision_window_remaining_days
        if task_driven_transfer_evaluation:
            result["transferOutcome"] = str(task_driven_transfer_evaluation.get("transferOutcome") or "")
            if task_driven_transfer_evaluation.get("inputLabel"):
                result["transferInputLabel"] = str(task_driven_transfer_evaluation.get("inputLabel"))
            if task_driven_transfer_evaluation.get("responseLabel"):
                result["transferResponseLabel"] = str(task_driven_transfer_evaluation.get("responseLabel"))
            if task_driven_transfer_evaluation.get("windowAction"):
                result["transferWindowAction"] = str(task_driven_transfer_evaluation.get("windowAction"))
            if task_driven_transfer_evaluation.get("nextWindowStage"):
                result["transferNextWindowStage"] = str(task_driven_transfer_evaluation.get("nextWindowStage"))
        return result

    @staticmethod
    def _resolve_active_skill_focus(
        *,
        current_state: LearnerJourneyState | None = None,
        active_skill_focus: list[str] | None = None,
    ) -> list[str]:
        if active_skill_focus:
            return [skill.strip() for skill in active_skill_focus if skill and skill.strip()]
        if not current_state:
            return []
        value = current_state.strategy_snapshot.get("activeSkillFocus")
        if not isinstance(value, list):
            return []
        return [str(skill).strip() for skill in value if isinstance(skill, str) and skill.strip()]

    @staticmethod
    def _trajectory_focus_label(skill_trajectory: dict | None) -> str | None:
        if not skill_trajectory or not skill_trajectory.get("focusSkill"):
            return None
        return str(skill_trajectory.get("focusSkill"))

    @staticmethod
    def _build_trajectory_summary_line(skill_trajectory: dict | None) -> str | None:
        if not skill_trajectory or not skill_trajectory.get("summary"):
            return None
        direction = str(skill_trajectory.get("direction") or "")
        if direction not in {"slipping", "stable", "improving"}:
            return None
        return str(skill_trajectory.get("summary"))

    @staticmethod
    def _build_trajectory_action_hint(skill_trajectory: dict | None) -> str | None:
        focus_skill = JourneyService._trajectory_focus_label(skill_trajectory)
        direction = str(skill_trajectory.get("direction") or "") if skill_trajectory else ""
        if not focus_skill or direction not in {"slipping", "stable", "improving"}:
            return None
        if direction == "slipping":
            return f"Stay especially deliberate around {focus_skill}, because it has been slipping across recent sessions."
        if direction == "stable":
            return f"Keep {focus_skill} warm inside this route, because it still looks fragile across recent sessions."
        return f"Use the recent momentum in {focus_skill} as support while the route keeps moving."

    @staticmethod
    def _strategy_memory_focus_label(strategy_memory: dict | None) -> str | None:
        if not strategy_memory or not strategy_memory.get("focusSkill"):
            return None
        return str(strategy_memory.get("focusSkill"))

    @staticmethod
    def _build_strategy_memory_summary_line(strategy_memory: dict | None) -> str | None:
        if not strategy_memory or not strategy_memory.get("summary"):
            return None
        persistence_level = str(strategy_memory.get("persistenceLevel") or "")
        if persistence_level not in {"persistent", "recurring", "emerging"}:
            return None
        return str(strategy_memory.get("summary"))

    @staticmethod
    def _build_strategy_memory_action_hint(strategy_memory: dict | None) -> str | None:
        focus_skill = JourneyService._strategy_memory_focus_label(strategy_memory)
        persistence_level = str(strategy_memory.get("persistenceLevel") or "") if strategy_memory else ""
        if not focus_skill or persistence_level not in {"persistent", "recurring", "emerging"}:
            return None
        if persistence_level == "persistent":
            return f"Treat {focus_skill} as a durable strategy focus, because it has stayed weak across a longer window."
        if persistence_level == "recurring":
            return f"Return to {focus_skill} deliberately, because it keeps resurfacing across the longer history."
        return f"Start protecting {focus_skill} earlier, because it is emerging as the next longer-term weak area."

    @staticmethod
    def _build_route_cadence_summary_line(route_cadence_memory: dict | None) -> str | None:
        if not route_cadence_memory or not route_cadence_memory.get("summary"):
            return None
        status = str(route_cadence_memory.get("status") or "")
        if status not in {"building_rhythm", "warming_up", "gentle_reentry", "route_rescue", "steady_return"}:
            return None
        return str(route_cadence_memory.get("summary"))

    @staticmethod
    def _build_route_cadence_action_hint(route_cadence_memory: dict | None) -> str | None:
        if not route_cadence_memory or not route_cadence_memory.get("actionHint"):
            return None
        status = str(route_cadence_memory.get("status") or "")
        if status not in {"building_rhythm", "warming_up", "gentle_reentry", "route_rescue", "steady_return"}:
            return None
        return str(route_cadence_memory.get("actionHint"))

    @staticmethod
    def _build_route_recovery_summary_line(route_recovery_memory: dict | None) -> str | None:
        if not route_recovery_memory or not route_recovery_memory.get("summary"):
            return None
        phase = str(route_recovery_memory.get("phase") or "")
        if phase not in {"route_rebuild", "protected_return", "skill_repair_cycle", "targeted_stabilization", "steady_extension", "support_reopen_arc"}:
            return None
        return str(route_recovery_memory.get("summary"))

    @staticmethod
    def _build_route_recovery_action_hint(route_recovery_memory: dict | None) -> str | None:
        if not route_recovery_memory or not route_recovery_memory.get("actionHint"):
            return None
        phase = str(route_recovery_memory.get("phase") or "")
        if phase not in {"route_rebuild", "protected_return", "skill_repair_cycle", "targeted_stabilization", "steady_extension", "support_reopen_arc"}:
            return None
        return str(route_recovery_memory.get("actionHint"))

    @staticmethod
    def _build_route_recovery_decision_window_line(route_recovery_memory: dict | None) -> str | None:
        if not route_recovery_memory:
            return None
        decision_bias = str(route_recovery_memory.get("decisionBias") or "")
        decision_window_days = (
            int(route_recovery_memory.get("decisionWindowDays"))
            if route_recovery_memory.get("decisionWindowDays") is not None
            else 0
        )
        support_label = str(route_recovery_memory.get("supportPracticeTitle") or "the reopened support lane")
        decision_window_stage = str(route_recovery_memory.get("decisionWindowStage") or "")
        decision_window_remaining_days = (
            int(route_recovery_memory.get("decisionWindowRemainingDays"))
            if route_recovery_memory.get("decisionWindowRemainingDays") is not None
            else decision_window_days
        )
        if decision_bias == "widening_window" and decision_window_days > 0:
            if decision_window_stage == "first_widening_pass":
                return (
                    f"The next route should act as the first widening pass: let the broader daily route lead while {support_label} stays available inside the mix."
                )
            if decision_window_stage == "stabilizing_widening":
                return (
                    f"The wider route now needs one more stabilizing pass: keep the daily route leading while {support_label} stays connected inside the broader mix."
                )
            if decision_window_stage == "ready_for_extension":
                return (
                    f"The controlled widening window has already held across recent passes, so the route can start extending forward again while {support_label} stays as quiet support."
                )
            return (
                f"For the next {decision_window_remaining_days} route decisions, the broader daily route should keep leading while {support_label} stays available inside the mix."
            )
        if decision_bias == "settling_window" and decision_window_days > 0:
            return (
                f"For the next {decision_window_days} route decision, keep {support_label} inside one more connected settling pass before widening again."
            )
        if decision_bias == "task_transfer_window" and decision_window_days > 0:
            if decision_window_stage == "protect_response":
                return (
                    f"The next route should protect {support_label} first, because the last task-driven transfer still looked fragile."
                )
            if decision_window_stage == "stabilize_transfer":
                return (
                    f"The next route should use one stabilizing pass around {support_label} before the broader mix widens again."
                )
            if decision_window_stage == "ready_to_widen":
                return (
                    f"The protected transfer window has already held, so the broader route can widen again while {support_label} stays available."
                )
            return (
                f"For the next {decision_window_remaining_days} route decisions, keep {support_label} protected inside a connected transfer window."
            )
        return None

    @staticmethod
    def _build_route_recovery_decision_window_hint(route_recovery_memory: dict | None) -> str | None:
        if not route_recovery_memory:
            return None
        decision_bias = str(route_recovery_memory.get("decisionBias") or "")
        decision_window_days = (
            int(route_recovery_memory.get("decisionWindowDays"))
            if route_recovery_memory.get("decisionWindowDays") is not None
            else 0
        )
        support_label = str(route_recovery_memory.get("supportPracticeTitle") or "the reopened support lane")
        decision_window_stage = str(route_recovery_memory.get("decisionWindowStage") or "")
        decision_window_remaining_days = (
            int(route_recovery_memory.get("decisionWindowRemainingDays"))
            if route_recovery_memory.get("decisionWindowRemainingDays") is not None
            else decision_window_days
        )
        if decision_bias == "widening_window" and decision_window_days > 0:
            if decision_window_stage == "first_widening_pass":
                return (
                    f"Treat the next route as the first widening pass: let the main daily route lead and keep {support_label} available without forcing it to dominate."
                )
            if decision_window_stage == "stabilizing_widening":
                return (
                    f"Treat the next route as a stabilizing widening pass: keep the daily route broad, connected, and calm while {support_label} stays available inside it."
                )
            if decision_window_stage == "ready_for_extension":
                return (
                    f"The controlled widening window has already held, so the next route can extend a little further while {support_label} stays available as support."
                )
            return (
                f"Treat the next {decision_window_remaining_days} routes as a controlled widening window: let the main daily route lead and keep {support_label} available without forcing it to dominate."
            )
        if decision_bias == "settling_window" and decision_window_days > 0:
            return (
                f"Treat the next route as a settling window: reconnect through the daily route and keep {support_label} protected before widening again."
            )
        if decision_bias == "task_transfer_window" and decision_window_days > 0:
            if decision_window_stage == "protect_response":
                return (
                    f"Treat the next route as a protected response pass: keep the route centered on {support_label} before widening again."
                )
            if decision_window_stage == "stabilize_transfer":
                return (
                    f"Treat the next route as a stabilizing transfer pass: keep {support_label} connected, then let the broader route widen."
                )
            if decision_window_stage == "ready_to_widen":
                return (
                    f"The protected transfer window has held, so the next route can widen while keeping {support_label} quietly available."
                )
            return (
                f"Treat the next {decision_window_remaining_days} routes as a protected transfer window around {support_label}."
            )
        return None

    @staticmethod
    def _build_ritual_signal_window_line(ritual_signal_memory: dict | None) -> str | None:
        if not ritual_signal_memory:
            return None
        decision_bias = str(ritual_signal_memory.get("routeWindowBias") or "")
        if decision_bias != "ritual_signal_window":
            return None
        window_stage = str(ritual_signal_memory.get("routeWindowStage") or "")
        active_label = str(ritual_signal_memory.get("activeLabel") or "the ritual signal")
        remaining_days = (
            int(ritual_signal_memory.get("windowRemainingDays"))
            if ritual_signal_memory.get("windowRemainingDays") is not None
            else int(ritual_signal_memory.get("windowDays") or 0)
        )
        if window_stage == "protect_ritual":
            return (
                f"For the next {max(remaining_days, 1)} route decisions, keep {active_label} inside a protected ritual pass before the route widens."
            )
        if window_stage == "reuse_in_response":
            return (
                f"The next route should reuse {active_label} directly inside the response lane once more before the ritual signal broadens."
            )
        if window_stage == "carry_inside_route":
            return (
                f"The next route can widen again while carrying {active_label} quietly inside the broader lesson flow."
            )
        return None

    @staticmethod
    def _build_ritual_signal_window_hint(ritual_signal_memory: dict | None) -> str | None:
        if not ritual_signal_memory:
            return None
        decision_bias = str(ritual_signal_memory.get("routeWindowBias") or "")
        if decision_bias != "ritual_signal_window":
            return None
        window_stage = str(ritual_signal_memory.get("routeWindowStage") or "")
        active_label = str(ritual_signal_memory.get("activeLabel") or "the ritual signal")
        remaining_days = (
            int(ritual_signal_memory.get("windowRemainingDays"))
            if ritual_signal_memory.get("windowRemainingDays") is not None
            else int(ritual_signal_memory.get("windowDays") or 0)
        )
        if window_stage == "protect_ritual":
            return (
                f"Treat the next {max(remaining_days, 1)} route step as a protected ritual pass around {active_label} before widening."
            )
        if window_stage == "reuse_in_response":
            return (
                f"Treat the next route as a connected reuse pass: bring {active_label} straight into the response lane once more."
            )
        if window_stage == "carry_inside_route":
            return (
                f"Let the broader route lead again while keeping {active_label} available as a quiet carry-over."
            )
        return None

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
        practice_shift: dict | None = None,
        skill_trajectory: dict | None = None,
        strategy_memory: dict | None = None,
        route_cadence_memory: dict | None = None,
        route_recovery_memory: dict | None = None,
        route_reentry_progress: dict | None = None,
        route_entry_memory: dict | None = None,
        route_follow_up_memory: dict | None = None,
        ritual_signal_memory: dict | None = None,
    ) -> str:
        learner_name = profile.name.strip() or "Learner"
        carry_over_label = (
            str(follow_up_preview.get("carryOverSignalLabel"))
            if follow_up_preview and follow_up_preview.get("carryOverSignalLabel")
            else None
        )
        lead_practice_title = (
            str(practice_shift.get("leadPracticeTitle"))
            if practice_shift and practice_shift.get("leadPracticeTitle")
            else None
        )
        trajectory_focus = JourneyService._trajectory_focus_label(skill_trajectory)
        strategy_focus = JourneyService._strategy_memory_focus_label(strategy_memory)
        cadence_status = str(route_cadence_memory.get("status") or "") if route_cadence_memory else ""
        recovery_phase = str(route_recovery_memory.get("phase") or "") if route_recovery_memory else ""
        recovery_focus = (
            str(route_recovery_memory.get("focusSkill"))
            if route_recovery_memory and route_recovery_memory.get("focusSkill")
            else None
        )
        recovery_horizon = (
            int(route_recovery_memory.get("horizonDays"))
            if route_recovery_memory and route_recovery_memory.get("horizonDays")
            else None
        )
        reentry_next_route = (
            str(route_reentry_progress.get("nextRoute"))
            if route_reentry_progress and route_reentry_progress.get("nextRoute")
            else None
        )
        reentry_label = JourneyService._label_route_reentry_route(reentry_next_route) if reentry_next_route else None
        route_entry_reset = JourneyService._build_route_entry_memory_reset_label(route_entry_memory)
        route_follow_up_label = (
            str(route_follow_up_memory.get("followUpLabel"))
            if route_follow_up_memory and route_follow_up_memory.get("followUpLabel")
            else None
        )
        ritual_label = (
            str(ritual_signal_memory.get("activeLabel"))
            if ritual_signal_memory and ritual_signal_memory.get("activeLabel")
            else None
        )
        ritual_type = (
            str(ritual_signal_memory.get("activeSignalType"))
            if ritual_signal_memory and ritual_signal_memory.get("activeSignalType")
            else ""
        )
        ritual_stage = (
            str(ritual_signal_memory.get("windowStage"))
            if ritual_signal_memory and ritual_signal_memory.get("windowStage")
            else ""
        )
        if ritual_label and not follow_up_preview and not reentry_label and not route_entry_reset:
            if ritual_type == "word_journal":
                if ritual_stage == "ready_to_carry":
                    return f"{learner_name}, today's route carries {ritual_label} through a broader vocabulary-to-response arc."
                return f"{learner_name}, today's route keeps {ritual_label} alive inside a connected vocabulary-to-response arc."
            if ritual_type == "spontaneous_voice":
                if ritual_stage == "ready_to_carry":
                    return f"{learner_name}, today's route carries your live voice signal from {ritual_label} into a broader speaking-led arc."
                return f"{learner_name}, today's route keeps the live voice signal from {ritual_label} inside a connected speaking arc."
        if carry_over_label:
            if lead_practice_title:
                if route_entry_reset:
                    return f"{learner_name}, today's route carries forward {carry_over_label} but resets through the calmer main path before reopening {route_entry_reset} again."
                if route_follow_up_label and reentry_label:
                    return f"{learner_name}, today's route carries forward {carry_over_label}, moves through {reentry_label}, and then reconnects through {route_follow_up_label}."
                if reentry_label:
                    return f"{learner_name}, today's route carries forward {carry_over_label} and reopens through {reentry_label} while {recovery_focus or focus_area} stays protected."
                if recovery_phase == "route_rebuild":
                    return f"{learner_name}, today's route gently rebuilds around {carry_over_label} and protects {recovery_focus or focus_area} across the next {recovery_horizon or 2} sessions."
                if recovery_phase == "protected_return":
                    return f"{learner_name}, today's route reopens around {carry_over_label} and keeps {recovery_focus or focus_area} protected for the next {recovery_horizon or 2} sessions."
                if recovery_phase == "support_reopen_arc":
                    return f"{learner_name}, today's route carries forward {carry_over_label} and reopens a protected support lane around {recovery_focus or focus_area}."
                if strategy_focus:
                    return f"{learner_name}, today's route carries forward {carry_over_label}, rebalances through {lead_practice_title}, and keeps durable support on {strategy_focus} around {focus_area}."
                if trajectory_focus:
                    return f"{learner_name}, today's route carries forward {carry_over_label}, rebalances through {lead_practice_title}, and keeps extra support on {trajectory_focus} around {focus_area}."
                return f"{learner_name}, today's route carries forward {carry_over_label} and rebalances through {lead_practice_title} around {focus_area}."
            if route_follow_up_label and reentry_label:
                return f"{learner_name}, today's route carries forward {carry_over_label}, reopens through {reentry_label}, and then reconnects through {route_follow_up_label}."
            if reentry_label:
                return f"{learner_name}, today's route carries forward {carry_over_label} and reopens through {reentry_label}."
            return f"{learner_name}, today's route carries forward {carry_over_label} around {focus_area}."
        if reentry_label:
            if route_entry_reset:
                return f"{learner_name}, today's route resets through the calmer main path before reopening {route_entry_reset} again."
            if route_follow_up_label:
                return f"{learner_name}, today's route reopens through {reentry_label} and then reconnects through {route_follow_up_label}."
            return f"{learner_name}, today's route reopens through {reentry_label} while {recovery_focus or focus_area} stays protected."
        if recovery_phase == "route_rebuild":
            return f"{learner_name}, today's route gently rebuilds the habit around {focus_area} and protects {recovery_focus or focus_area} across the next {recovery_horizon or 2} sessions."
        if recovery_phase == "protected_return":
            return f"{learner_name}, today's route reopens calmly around {focus_area} and keeps {recovery_focus or focus_area} protected for the next {recovery_horizon or 2} sessions."
        if recovery_phase == "support_reopen_arc":
            return f"{learner_name}, today's route reopens a protected support lane around {focus_area} while the wider route stays connected."
        if recovery_phase == "skill_repair_cycle":
            return f"{learner_name}, today's route keeps {focus_area} moving while {recovery_focus or focus_area} stays in a multi-day repair cycle."
        if cadence_status == "route_rescue":
            return f"{learner_name}, today's route gently reopens around {focus_area} so the habit can restart without overload."
        if cadence_status == "gentle_reentry":
            return f"{learner_name}, today's route reopens calmly around {focus_area} before it widens again."
        if cadence_status == "steady_return":
            return f"{learner_name}, today's route keeps the daily rhythm moving around {focus_area}."
        if strategy_focus:
            return f"{learner_name}, today's route keeps {focus_area} moving while protecting the longer strategy signal around {strategy_focus}."
        if trajectory_focus:
            return f"{learner_name}, today's route keeps {focus_area} moving while protecting the multi-day signal around {trajectory_focus}."
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
        practice_shift: dict | None = None,
        skill_trajectory: dict | None = None,
        strategy_memory: dict | None = None,
        route_cadence_memory: dict | None = None,
        route_recovery_memory: dict | None = None,
        route_reentry_progress: dict | None = None,
        route_entry_memory: dict | None = None,
        route_follow_up_memory: dict | None = None,
        ritual_signal_memory: dict | None = None,
    ) -> str:
        trajectory_line = JourneyService._build_trajectory_summary_line(skill_trajectory)
        strategy_line = JourneyService._build_strategy_memory_summary_line(strategy_memory)
        cadence_line = JourneyService._build_route_cadence_summary_line(route_cadence_memory)
        recovery_line = JourneyService._build_route_recovery_summary_line(route_recovery_memory)
        reentry_line = JourneyService._build_route_reentry_summary_line(route_reentry_progress)
        route_entry_line = JourneyService._build_route_entry_memory_summary_line(route_entry_memory)
        route_follow_up_line = JourneyService._build_route_follow_up_summary_line(route_follow_up_memory)
        recovery_window_line = JourneyService._build_route_recovery_decision_window_line(route_recovery_memory)
        ritual_line = (
            str(ritual_signal_memory.get("summary"))
            if ritual_signal_memory and ritual_signal_memory.get("summary")
            else None
        )
        ritual_window_line = JourneyService._build_ritual_signal_window_line(ritual_signal_memory)
        task_driven_transfer_line = None
        if session_summary and isinstance(session_summary.get("taskDrivenTransferEvaluation"), dict):
            task_driven_transfer = session_summary["taskDrivenTransferEvaluation"]
            transfer_outcome = str(task_driven_transfer.get("transferOutcome") or "")
            response_label = str(task_driven_transfer.get("responseLabel") or focus_area)
            if transfer_outcome == "fragile":
                task_driven_transfer_line = (
                    f"The next route should stay protected around {response_label} before the broader mix widens again."
                )
            elif transfer_outcome == "usable":
                task_driven_transfer_line = (
                    f"The next route should use one stabilizing pass around {response_label} before widening further."
                )
            elif transfer_outcome == "held":
                task_driven_transfer_line = (
                    f"The broader route can widen again while keeping {response_label} available inside the mix."
                )
        if follow_up_preview:
            carry_over_label = follow_up_preview.get("carryOverSignalLabel") or focus_area
            watch_label = follow_up_preview.get("watchSignalLabel") or focus_area
            shift_line = (
                str(practice_shift.get("summaryLine"))
                if practice_shift and practice_shift.get("summaryLine")
                else session_summary.get("strategyShift")
                if session_summary
                else None
            )
            shift_line = (
                shift_line
                or (str(follow_up_preview.get("reason")) if follow_up_preview.get("reason") else None)
                or task_driven_transfer_line
                or recovery_window_line
                or recovery_line
                or route_follow_up_line
                or "The route keeps the next step connected instead of widening too early."
            )
            return (
                f"Today's route picks up from yesterday by carrying forward {carry_over_label} and keeping {watch_label} in view. "
                f"{shift_line}"
                + (f" {trajectory_line}" if trajectory_line else "")
                + (f" {strategy_line}" if strategy_line else "")
                + (f" {cadence_line}" if cadence_line else "")
                + (f" {recovery_line}" if recovery_line else "")
                + (f" {reentry_line}" if reentry_line else "")
                + (f" {route_entry_line}" if route_entry_line else "")
                + (f" {route_follow_up_line}" if route_follow_up_line else "")
                + (f" {recovery_window_line}" if recovery_window_line else "")
                + (f" {ritual_line}" if ritual_line else "")
                + (f" {ritual_window_line}" if ritual_window_line else "")
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
            + (f" {trajectory_line}" if trajectory_line else "")
            + (f" {strategy_line}" if strategy_line else "")
            + (f" {cadence_line}" if cadence_line else "")
            + (f" {recovery_line}" if recovery_line else "")
            + (f" {reentry_line}" if reentry_line else "")
            + (f" {route_entry_line}" if route_entry_line else "")
            + (f" {route_follow_up_line}" if route_follow_up_line else "")
            + (f" {recovery_window_line}" if recovery_window_line else "")
            + (f" {ritual_line}" if ritual_line else "")
            + (f" {ritual_window_line}" if ritual_window_line else "")
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
        practice_shift: dict | None = None,
        skill_trajectory: dict | None = None,
        strategy_memory: dict | None = None,
        route_cadence_memory: dict | None = None,
        route_recovery_memory: dict | None = None,
        route_reentry_progress: dict | None = None,
        route_entry_memory: dict | None = None,
        route_follow_up_memory: dict | None = None,
        ritual_signal_memory: dict | None = None,
    ) -> str:
        trajectory_line = JourneyService._build_trajectory_summary_line(skill_trajectory)
        strategy_line = JourneyService._build_strategy_memory_summary_line(strategy_memory)
        cadence_line = JourneyService._build_route_cadence_summary_line(route_cadence_memory)
        recovery_line = JourneyService._build_route_recovery_summary_line(route_recovery_memory)
        reentry_line = JourneyService._build_route_reentry_summary_line(route_reentry_progress)
        route_entry_line = JourneyService._build_route_entry_memory_summary_line(route_entry_memory)
        route_follow_up_line = JourneyService._build_route_follow_up_summary_line(route_follow_up_memory)
        recovery_window_line = JourneyService._build_route_recovery_decision_window_line(route_recovery_memory)
        ritual_line = (
            str(ritual_signal_memory.get("summary"))
            if ritual_signal_memory and ritual_signal_memory.get("summary")
            else None
        )
        ritual_window_line = JourneyService._build_ritual_signal_window_line(ritual_signal_memory)
        task_driven_transfer_line = None
        if session_summary and isinstance(session_summary.get("taskDrivenTransferEvaluation"), dict):
            task_driven_transfer = session_summary["taskDrivenTransferEvaluation"]
            transfer_outcome = str(task_driven_transfer.get("transferOutcome") or "")
            response_label = str(task_driven_transfer.get("responseLabel") or focus_area)
            if transfer_outcome == "fragile":
                task_driven_transfer_line = (
                    f"The route is deliberately protecting {response_label} before it widens again."
                )
            elif transfer_outcome == "usable":
                task_driven_transfer_line = (
                    f"The route is using one stabilizing pass around {response_label} before it widens again."
                )
            elif transfer_outcome == "held":
                task_driven_transfer_line = (
                    f"The route can widen again while keeping {response_label} connected inside the broader mix."
                )
        if follow_up_preview:
            carry_over_label = follow_up_preview.get("carryOverSignalLabel") or focus_area
            watch_label = follow_up_preview.get("watchSignalLabel") or focus_area
            summary_headline = session_summary.get("headline") if session_summary else follow_up_preview.get("headline")
            practice_line = (
                str(practice_shift.get("summaryLine"))
                if practice_shift and practice_shift.get("summaryLine")
                else None
            )
            return (
                f"{summary_headline} The route now carries {carry_over_label} forward while staying careful around {watch_label}."
                + (f" {practice_line}" if practice_line else "")
                + (f" {task_driven_transfer_line}" if task_driven_transfer_line else "")
                + (f" {trajectory_line}" if trajectory_line else "")
                + (f" {strategy_line}" if strategy_line else "")
                + (f" {cadence_line}" if cadence_line else "")
                + (f" {recovery_line}" if recovery_line else "")
                + (f" {reentry_line}" if reentry_line else "")
                + (f" {route_entry_line}" if route_entry_line else "")
                + (f" {route_follow_up_line}" if route_follow_up_line else "")
                + (f" {recovery_window_line}" if recovery_window_line else "")
                + (f" {ritual_line}" if ritual_line else "")
                + (f" {ritual_window_line}" if ritual_window_line else "")
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
            + (f" {trajectory_line}" if trajectory_line else "")
            + (f" {strategy_line}" if strategy_line else "")
            + (f" {cadence_line}" if cadence_line else "")
            + (f" {recovery_line}" if recovery_line else "")
            + (f" {reentry_line}" if reentry_line else "")
            + (f" {route_entry_line}" if route_entry_line else "")
            + (f" {route_follow_up_line}" if route_follow_up_line else "")
            + (f" {recovery_window_line}" if recovery_window_line else "")
            + (f" {ritual_line}" if ritual_line else "")
            + (f" {ritual_window_line}" if ritual_window_line else "")
        )

    @staticmethod
    def _build_next_best_action_text(
        profile: UserProfile,
        session_kind: str,
        focus_area: str,
        *,
        follow_up_preview: dict | None = None,
        practice_shift: dict | None = None,
        skill_trajectory: dict | None = None,
        strategy_memory: dict | None = None,
        route_cadence_memory: dict | None = None,
        route_recovery_memory: dict | None = None,
        route_reentry_progress: dict | None = None,
        route_entry_memory: dict | None = None,
        route_follow_up_memory: dict | None = None,
        ritual_signal_memory: dict | None = None,
    ) -> str:
        trajectory_hint = JourneyService._build_trajectory_action_hint(skill_trajectory)
        strategy_hint = JourneyService._build_strategy_memory_action_hint(strategy_memory)
        cadence_hint = JourneyService._build_route_cadence_action_hint(route_cadence_memory)
        recovery_hint = JourneyService._build_route_recovery_action_hint(route_recovery_memory)
        reentry_hint = JourneyService._build_route_reentry_action_hint(route_reentry_progress)
        route_entry_hint = JourneyService._build_route_entry_memory_action_hint(route_entry_memory)
        route_follow_up_hint = JourneyService._build_route_follow_up_action_hint(route_follow_up_memory)
        recovery_window_hint = JourneyService._build_route_recovery_decision_window_hint(route_recovery_memory)
        ritual_hint = (
            str(ritual_signal_memory.get("actionHint"))
            if ritual_signal_memory and ritual_signal_memory.get("actionHint")
            else None
        )
        ritual_window_hint = JourneyService._build_ritual_signal_window_hint(ritual_signal_memory)
        if follow_up_preview and follow_up_preview.get("nextStepHint"):
            practice_line = (
                str(practice_shift.get("summaryLine"))
                if practice_shift and practice_shift.get("summaryLine")
                else None
            )
            return (
                str(follow_up_preview["nextStepHint"])
                + (f" {practice_line}" if practice_line else "")
                + (f" {trajectory_hint}" if trajectory_hint else "")
                + (f" {strategy_hint}" if strategy_hint else "")
                + (f" {cadence_hint}" if cadence_hint else "")
                + (f" {recovery_hint}" if recovery_hint else "")
                + (f" {reentry_hint}" if reentry_hint else "")
                + (f" {route_entry_hint}" if route_entry_hint else "")
                + (f" {route_follow_up_hint}" if route_follow_up_hint else "")
                + (f" {recovery_window_hint}" if recovery_window_hint else "")
                + (f" {ritual_hint}" if ritual_hint else "")
                + (f" {ritual_window_hint}" if ritual_window_hint else "")
            )
        if ritual_hint and session_kind != "diagnostic":
            return (
                ritual_hint
                + (f" {route_follow_up_hint}" if route_follow_up_hint else "")
                + (f" {trajectory_hint}" if trajectory_hint else "")
                + (f" {strategy_hint}" if strategy_hint else "")
                + (f" {cadence_hint}" if cadence_hint else "")
                + (f" {recovery_hint}" if recovery_hint else "")
                + (f" {recovery_window_hint}" if recovery_window_hint else "")
                + (f" {ritual_window_hint}" if ritual_window_hint else "")
            )
        if route_follow_up_hint and session_kind != "diagnostic":
            return (
                route_follow_up_hint
                + (f" {trajectory_hint}" if trajectory_hint else "")
                + (f" {strategy_hint}" if strategy_hint else "")
                + (f" {cadence_hint}" if cadence_hint else "")
                + (f" {recovery_hint}" if recovery_hint else "")
                + (f" {recovery_window_hint}" if recovery_window_hint else "")
                + (f" {ritual_window_hint}" if ritual_window_hint else "")
            )
        if route_entry_hint and session_kind != "diagnostic":
            return (
                route_entry_hint
                + (f" {trajectory_hint}" if trajectory_hint else "")
                + (f" {strategy_hint}" if strategy_hint else "")
                + (f" {cadence_hint}" if cadence_hint else "")
                + (f" {recovery_hint}" if recovery_hint else "")
                + (f" {recovery_window_hint}" if recovery_window_hint else "")
                + (f" {ritual_window_hint}" if ritual_window_hint else "")
            )
        if reentry_hint and session_kind != "diagnostic":
            return (
                reentry_hint
                + (f" {trajectory_hint}" if trajectory_hint else "")
                + (f" {strategy_hint}" if strategy_hint else "")
                + (f" {cadence_hint}" if cadence_hint else "")
                + (f" {recovery_hint}" if recovery_hint else "")
                + (f" {recovery_window_hint}" if recovery_window_hint else "")
                + (f" {ritual_window_hint}" if ritual_window_hint else "")
            )
        if session_kind == "diagnostic":
            return "Finish the checkpoint now, then tomorrow's route will become more personalized." + (
                f" {cadence_hint}" if cadence_hint else ""
            ) + (
                f" {recovery_hint}" if recovery_hint else ""
            )
        if profile.onboarding_answers.preferred_mode == "text_first":
            return (
                f"Start with a calm text-led loop, then deepen {focus_area} through the next guided response."
                + (f" {trajectory_hint}" if trajectory_hint else "")
                + (f" {strategy_hint}" if strategy_hint else "")
                + (f" {cadence_hint}" if cadence_hint else "")
                + (f" {recovery_hint}" if recovery_hint else "")
                + (f" {recovery_window_hint}" if recovery_window_hint else "")
            )
        if profile.onboarding_answers.preferred_mode == "voice_first":
            return (
                f"Start with a voice-led loop and let the next plan respond to your speaking signal."
                + (f" {trajectory_hint}" if trajectory_hint else "")
                + (f" {strategy_hint}" if strategy_hint else "")
                + (f" {cadence_hint}" if cadence_hint else "")
                + (f" {recovery_hint}" if recovery_hint else "")
                + (f" {recovery_window_hint}" if recovery_window_hint else "")
                + (f" {ritual_window_hint}" if ritual_window_hint else "")
            )
        return (
            f"Open the loop, complete one guided session, and the next plan will sharpen around {focus_area}."
            + (f" {trajectory_hint}" if trajectory_hint else "")
            + (f" {strategy_hint}" if strategy_hint else "")
            + (f" {cadence_hint}" if cadence_hint else "")
            + (f" {recovery_hint}" if recovery_hint else "")
            + (f" {recovery_window_hint}" if recovery_window_hint else "")
            + (f" {ritual_window_hint}" if ritual_window_hint else "")
        )

    def _build_daily_steps(
        self,
        profile: UserProfile,
        focus_area: str,
        estimated_minutes: int,
        *,
        carry_over_label: str | None = None,
        watch_label: str | None = None,
        practice_shift: dict | None = None,
        skill_trajectory: dict | None = None,
        strategy_memory: dict | None = None,
        route_cadence_memory: dict | None = None,
        route_recovery_memory: dict | None = None,
        route_reentry_progress: dict | None = None,
        ritual_signal_memory: dict | None = None,
    ) -> list[dict]:
        input_lane = self._infer_input_lane(profile)
        output_lane = self._infer_output_lane(profile)
        lead_practice_key = (
            str(practice_shift.get("leadPracticeKey"))
            if practice_shift and practice_shift.get("leadPracticeKey")
            else None
        )
        weakest_practice_key = (
            str(practice_shift.get("weakestPracticeKey"))
            if practice_shift and practice_shift.get("weakestPracticeKey")
            else None
        )
        weakest_practice_title = (
            str(practice_shift.get("weakestPracticeTitle"))
            if practice_shift and practice_shift.get("weakestPracticeTitle")
            else None
        )
        trajectory_focus = JourneyService._trajectory_focus_label(skill_trajectory)
        trajectory_direction = (
            str(skill_trajectory.get("direction"))
            if skill_trajectory and skill_trajectory.get("direction")
            else None
        )
        strategy_focus = JourneyService._strategy_memory_focus_label(strategy_memory)
        strategy_level = (
            str(strategy_memory.get("persistenceLevel"))
            if strategy_memory and strategy_memory.get("persistenceLevel")
            else None
        )
        cadence_status = (
            str(route_cadence_memory.get("status"))
            if route_cadence_memory and route_cadence_memory.get("status")
            else None
        )
        recovery_phase = (
            str(route_recovery_memory.get("phase"))
            if route_recovery_memory and route_recovery_memory.get("phase")
            else None
        )
        recovery_focus = (
            str(route_recovery_memory.get("focusSkill"))
            if route_recovery_memory and route_recovery_memory.get("focusSkill")
            else None
        )
        recovery_support = (
            str(route_recovery_memory.get("supportPracticeTitle"))
            if route_recovery_memory and route_recovery_memory.get("supportPracticeTitle")
            else None
        )
        recovery_horizon = (
            int(route_recovery_memory.get("horizonDays"))
            if route_recovery_memory and route_recovery_memory.get("horizonDays")
            else None
        )
        recovery_next_phase = (
            str(route_recovery_memory.get("nextPhaseHint"))
            if route_recovery_memory and route_recovery_memory.get("nextPhaseHint")
            else None
        )
        session_shape = (
            str(route_recovery_memory.get("sessionShape"))
            if route_recovery_memory and route_recovery_memory.get("sessionShape")
            else None
        )
        reentry_next_route = (
            str(route_reentry_progress.get("nextRoute"))
            if route_reentry_progress and route_reentry_progress.get("nextRoute")
            else None
        )
        reentry_focus = self._map_route_to_focus_area(reentry_next_route)
        reentry_label = self._label_route_reentry_route(reentry_next_route) if reentry_next_route else None
        ritual_type = (
            str(ritual_signal_memory.get("activeSignalType"))
            if ritual_signal_memory and ritual_signal_memory.get("activeSignalType")
            else None
        )
        ritual_label = (
            str(ritual_signal_memory.get("activeLabel"))
            if ritual_signal_memory and ritual_signal_memory.get("activeLabel")
            else None
        )
        ritual_window_stage = (
            str(ritual_signal_memory.get("routeWindowStage"))
            if ritual_signal_memory and ritual_signal_memory.get("routeWindowStage")
            else None
        )
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

        if ritual_type == "word_journal" and ritual_label:
            step_specs = [
                (
                    step_id,
                    "vocabulary" if step_id == "vocabulary-recall" else "writing" if step_id == "response" and output_lane == "writing" else skill,
                    "Word journal recall" if step_id == "vocabulary-recall" else title,
                    (
                        f"Bring back {ritual_label} from the word journal and reuse it in a live phrase before it goes cold."
                        if step_id == "vocabulary-recall"
                        else f"Write the response so {ritual_label} comes back in real output, not only as a saved note."
                        if step_id == "response" and output_lane == "writing"
                        else description
                    ),
                    weight + 1 if step_id in {"vocabulary-recall", "response"} else weight,
                )
                for step_id, skill, title, description, weight in step_specs
            ]
        elif ritual_type == "spontaneous_voice" and ritual_label:
            step_specs = [
                (
                    step_id,
                    "speaking" if step_id == "response" else skill,
                    "Voice ritual response" if step_id == "response" else title,
                    (
                        f"Answer out loud again while the live voice signal from {ritual_label} is still fresh."
                        if step_id == "response"
                        else description
                    ),
                    weight + 1 if step_id == "response" else weight,
                )
                for step_id, skill, title, description, weight in step_specs
            ]

        if ritual_window_stage == "protect_ritual":
            step_specs = [
                (
                    step_id,
                    skill,
                    "Protected ritual recall" if step_id == "vocabulary-recall" and ritual_type == "word_journal" else title,
                    (
                        f"Keep {ritual_label} inside a protected ritual pass before the route widens."
                        if step_id == "vocabulary-recall" and ritual_type == "word_journal"
                        else f"Use one low-pressure response so {ritual_label} lands once before the broader route takes over."
                        if step_id == "response"
                        else description
                    ),
                    weight + 1 if step_id in {"vocabulary-recall", "response"} else weight,
                )
                for step_id, skill, title, description, weight in step_specs
            ]
        elif ritual_window_stage == "reuse_in_response":
            step_specs = [
                (
                    step_id,
                    skill,
                    "Connected ritual reuse" if step_id == "response" else title,
                    (
                        f"Bring {ritual_label} directly into this response again so the ritual signal starts living inside the route."
                        if step_id == "response"
                        else description
                    ),
                    weight + 1 if step_id == "response" else weight,
                )
                for step_id, skill, title, description, weight in step_specs
            ]
            step_specs = self._move_step_before_ids(
                step_specs,
                step_id="response",
                before_ids={"pronunciation", "reinforcement", "summary"},
            )
        elif ritual_window_stage == "carry_inside_route":
            step_specs = [
                (
                    step_id,
                    skill,
                    "Carry forward" if step_id == "reinforcement" else title,
                    (
                        f"Keep {ritual_label} lightly available while the broader route leads again."
                        if step_id == "reinforcement"
                        else f"See how the broader route carried {ritual_label} without rebuilding the whole session around it."
                        if step_id == "summary"
                        else description
                    ),
                    weight if step_id != "vocabulary-recall" else max(weight - 1, 1),
                )
                for step_id, skill, title, description, weight in step_specs
            ]

        if cadence_status in {"route_rescue", "gentle_reentry"}:
            step_specs = [
                (
                    step_id,
                    skill,
                    title,
                    (
                        "Liza reopens the route gently so you can get a visible win before the session widens again."
                        if step_id == "warm-start"
                        else description
                    ),
                    weight,
                )
                for step_id, skill, title, description, weight in step_specs
            ]
        elif cadence_status == "steady_return":
            step_specs = [
                (
                    step_id,
                    skill,
                    title,
                    (
                        "Liza keeps the opening crisp because the daily return rhythm is already holding."
                        if step_id == "warm-start"
                        else description
                    ),
                    weight,
                )
                for step_id, skill, title, description, weight in step_specs
            ]

        if recovery_phase in {"route_rebuild", "protected_return", "skill_repair_cycle", "targeted_stabilization", "support_reopen_arc"}:
            refreshed_specs = []
            for step_id, skill, title, description, weight in step_specs:
                if step_id == "warm-start":
                    refreshed_specs.append(
                        (
                            step_id,
                            skill,
                            "Support reopen" if recovery_phase == "support_reopen_arc" else title,
                            (
                                f"Liza reopens {reentry_label or 'the deferred support lane'} inside a connected route, so {recovery_focus or focus_area} stays protected while the route widens carefully."
                                if recovery_phase == "support_reopen_arc"
                                else f"Liza frames this session as part of a {recovery_horizon or 2}-route recovery arc, keeping {recovery_focus or focus_area} protected while the route stays finishable."
                            ),
                            weight + (1 if recovery_phase == "route_rebuild" else 0),
                        )
                    )
                elif step_id == "summary":
                    refreshed_specs.append(
                        (
                            step_id,
                            skill,
                            title,
                            (
                                f"See whether {reentry_label or 'the reopened support lane'} held cleanly inside the connected route, what still needs guarding, and how the next route continues the reopen arc. {recovery_next_phase or ''}".strip()
                                if recovery_phase == "support_reopen_arc"
                                else f"See what changed today, what still needs guarding, and how the next route continues the recovery arc. {recovery_next_phase or ''}".strip()
                            ),
                            weight,
                        )
                    )
                elif step_id == "reinforcement" and recovery_support:
                    refreshed_specs.append(
                        (
                            step_id,
                            skill,
                            title,
                            (
                                f"Use {recovery_support} as the support lane, but keep it inside the main route so {recovery_focus or focus_area} stays protected while the reopen settles."
                                if recovery_phase == "support_reopen_arc"
                                else f"Use {recovery_support} as the support lane so {recovery_focus or focus_area} stays protected across the next sessions."
                            ),
                            weight + (2 if recovery_phase == "support_reopen_arc" else 1),
                        )
                    )
                else:
                    refreshed_specs.append((step_id, skill, title, description, weight))
            step_specs = refreshed_specs

        reentry_step_id: str | None = None
        if reentry_label and reentry_focus:
            reentry_step_map = {
                "grammar": ("grammar-pattern", "grammar", "Grammar support step", "Reopen the route through grammar support before the wider sequence returns.", 4),
                "writing": ("writing-support", "writing", "Writing support step", "Use one calmer written pass so the recovery sequence can reopen in order.", 4),
                "speaking": ("speaking-support", "speaking", "Speaking support step", "Use one controlled spoken pass so the recovery sequence stays live without widening too fast.", 4),
                "pronunciation": ("pronunciation", "pronunciation", "Pronunciation support step", "Protect one pronunciation signal before the next support surface reopens.", 3),
                "reading": ("input", "reading", "Reading support step", "Use one short reading pass so the text-first route can reopen in a calmer order.", 4),
                "profession": ("profession-support", "profession", "Professional support step", "Reconnect the route to one real work scenario before widening again.", 4),
                "vocabulary": ("vocabulary-recall", "vocabulary", "Vocabulary support step", "Bring back the route words that make the next reopened step easier.", 4),
            }
            replacement = reentry_step_map.get(reentry_focus)
            replace_index = next(
                (index for index, spec in enumerate(step_specs) if spec[0] in {"vocabulary-recall", "grammar-pattern", "pronunciation", "reinforcement"}),
                None,
            )
            if replacement is not None and replace_index is not None:
                step_specs[replace_index] = replacement
                reentry_step_id = replacement[0]

        weakness_support_map = {
            "grammar": ("grammar-pattern", "grammar", weakest_practice_title or "Grammar support", f"Give {focus_area} more structural support before the route widens again.", 4),
            "writing": ("writing-support", "writing", weakest_practice_title or "Writing support", "Stabilize one calmer written response before widening into faster output.", 4),
            "speaking": ("speaking-support", "speaking", weakest_practice_title or "Speaking support", "Keep one spoken answer short and controlled so the route does not drift.", 4),
            "pronunciation": ("pronunciation", "pronunciation", weakest_practice_title or "Pronunciation support", "Protect one pronunciation issue while the route still feels fresh.", 3),
            "listening": ("input", "listening", weakest_practice_title or "Listening support", "Add one clearer input cue before responding so the route has more support.", 4),
            "reading": ("input", "reading", weakest_practice_title or "Reading support", "Add one clearer text cue before responding so the route has more structure.", 4),
            "profession": ("profession-support", "profession", weakest_practice_title or "Professional framing", "Ground the route in one real task so the language stays useful.", 4),
            "vocabulary": ("vocabulary-recall", "vocabulary", weakest_practice_title or "Vocabulary support", "Bring back the route words that make the next answer easier to build.", 4),
        }
        if weakest_practice_key in weakness_support_map:
            replacement = weakness_support_map[weakest_practice_key]
            replace_index = next(
                (index for index, spec in enumerate(step_specs) if spec[0] in {"vocabulary-recall", "grammar-pattern", "pronunciation"}),
                None,
            )
            if replace_index is not None:
                step_specs[replace_index] = replacement

        if lead_practice_key == "writing":
            step_specs = [
                (
                    step_id,
                    "writing" if step_id == "response" else skill,
                    "Guided writing response" if step_id == "response" else title,
                    (
                        f"Draft a clear written response that carries {carry_over_label or focus_area} before widening the route."
                        if step_id == "response"
                        else description
                    ),
                    weight + 1 if step_id == "response" else weight,
                )
                for step_id, skill, title, description, weight in step_specs
            ]
        elif lead_practice_key == "speaking":
            step_specs = [
                (
                    step_id,
                    "speaking" if step_id == "response" else skill,
                    "Guided speaking response" if step_id == "response" else title,
                    (
                        f"Answer out loud first and keep {carry_over_label or focus_area} active while the route is still live."
                        if step_id == "response"
                        else description
                    ),
                    weight + 1 if step_id == "response" else weight,
                )
                for step_id, skill, title, description, weight in step_specs
            ]
        elif lead_practice_key == "reading":
            step_specs = [
                (
                    step_id,
                    "reading" if step_id == "input" else skill,
                    "Guided reading input" if step_id == "input" else title,
                    (
                        f"Read one calmer input cue first so {carry_over_label or focus_area} is clear before you build the response."
                        if step_id == "input"
                        else description
                    ),
                    weight + 1 if step_id == "input" else weight,
                )
                for step_id, skill, title, description, weight in step_specs
            ]

        if strategy_focus and strategy_level in {"persistent", "recurring", "emerging"}:
            strategy_step_id = {
                "grammar": "grammar-pattern",
                "vocabulary": "vocabulary-recall",
                "listening": "input",
                "reading": "input",
                "pronunciation": "pronunciation",
                "speaking": "response",
                "writing": "response",
                "profession": "reinforcement",
            }.get(strategy_focus)
            if strategy_step_id:
                refreshed_specs = []
                for step_id, skill, title, description, weight in step_specs:
                    if step_id == strategy_step_id:
                        refreshed_specs.append(
                            (
                                step_id,
                                skill,
                                title,
                                f"{description} Keep a longer-term eye on {strategy_focus}, because it remains a {strategy_level} route signal across recent sessions.",
                                weight + (1 if strategy_level == "persistent" else 0),
                            )
                        )
                    else:
                        refreshed_specs.append((step_id, skill, title, description, weight))
                step_specs = refreshed_specs

        if trajectory_focus and trajectory_direction in {"slipping", "stable", "improving"}:
            trajectory_step_id = {
                "grammar": "grammar-pattern",
                "vocabulary": "vocabulary-recall",
                "listening": "input",
                "reading": "input",
                "pronunciation": "pronunciation",
                "speaking": "response",
                "writing": "response",
                "profession": "reinforcement",
            }.get(trajectory_focus)
            if trajectory_step_id:
                refreshed_specs = []
                for step_id, skill, title, description, weight in step_specs:
                    if step_id == trajectory_step_id:
                        refreshed_specs.append(
                            (
                                step_id,
                                skill,
                                title,
                                (
                                    f"{description} Keep extra attention on {trajectory_focus} because recent sessions show it {trajectory_direction}."
                                    if trajectory_direction in {"slipping", "stable"}
                                    else f"{description} Build from the recent momentum in {trajectory_focus} while the route is still fresh."
                                ),
                                weight,
                            )
                        )
                    else:
                        refreshed_specs.append((step_id, skill, title, description, weight))
                step_specs = refreshed_specs

        step_specs = self._apply_session_shape_to_step_specs(
            step_specs,
            session_shape=session_shape,
            recovery_phase=recovery_phase,
            focus_area=focus_area,
            recovery_focus=recovery_focus,
            reentry_focus=reentry_focus,
            reentry_step_id=reentry_step_id,
        )

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
    def _resolve_estimated_minutes(
        *,
        lesson_duration: int,
        session_kind: str,
        route_recovery_memory: dict | None = None,
        route_reentry_progress: dict | None = None,
    ) -> int:
        estimated = max(15, min(lesson_duration, 32))
        if session_kind == "diagnostic":
            return estimated

        session_shape = (
            str(route_recovery_memory.get("sessionShape"))
            if route_recovery_memory and route_recovery_memory.get("sessionShape")
            else ""
        )
        recovery_phase = (
            str(route_recovery_memory.get("phase"))
            if route_recovery_memory and route_recovery_memory.get("phase")
            else ""
        )
        if session_shape == "gentle_restart":
            estimated = max(14, min(estimated - 4, 18))
        elif session_shape == "protected_mix":
            if recovery_phase == "support_reopen_arc":
                estimated = max(19, min(estimated + 1, 23))
            else:
                estimated = max(16, min(estimated - 2, 22))
        elif session_shape == "focused_support":
            estimated = max(18, min(estimated, 24))
        elif session_shape == "guided_balance":
            estimated = max(18, min(estimated + 1, 25))
        elif session_shape == "forward_mix":
            estimated = max(20, min(estimated + 2, 30))
        elif session_kind == "recovery":
            estimated = max(18, min(estimated, 24))

        if route_reentry_progress and route_reentry_progress.get("nextRoute"):
            estimated = max(18, estimated)
        return estimated

    @staticmethod
    def _move_step_before_ids(
        step_specs: list[tuple[str, str, str, str, int]],
        *,
        step_id: str,
        before_ids: set[str],
    ) -> list[tuple[str, str, str, str, int]]:
        source_index = next((index for index, spec in enumerate(step_specs) if spec[0] == step_id), None)
        target_index = next((index for index, spec in enumerate(step_specs) if spec[0] in before_ids), None)
        if source_index is None or target_index is None or source_index < target_index:
            return step_specs

        reordered = list(step_specs)
        moved = reordered.pop(source_index)
        reordered.insert(target_index, moved)
        return reordered

    def _apply_session_shape_to_step_specs(
        self,
        step_specs: list[tuple[str, str, str, str, int]],
        *,
        session_shape: str | None,
        recovery_phase: str | None,
        focus_area: str,
        recovery_focus: str | None,
        reentry_focus: str | None,
        reentry_step_id: str | None,
    ) -> list[tuple[str, str, str, str, int]]:
        if not session_shape:
            return step_specs

        if session_shape == "gentle_restart":
            allowed_ids = {"warm-start", "vocabulary-recall", "input", "response", "reinforcement", "summary"}
            if reentry_step_id:
                allowed_ids.add(reentry_step_id)
            filtered_specs = [spec for spec in step_specs if spec[0] in allowed_ids]
            shaped_specs: list[tuple[str, str, str, str, int]] = []
            for step_id, skill, title, description, weight in filtered_specs:
                if step_id == "warm-start":
                    shaped_specs.append(
                        (
                            step_id,
                            skill,
                            "Gentle restart",
                            f"Liza keeps this restart short, calm, and finishable so {recovery_focus or focus_area} can come back without overload.",
                            weight,
                        )
                    )
                elif step_id == "response":
                    shaped_specs.append(
                        (
                            step_id,
                            skill,
                            title,
                            f"Take one visible win around {focus_area} before the route widens again tomorrow.",
                            max(weight, 6),
                        )
                    )
                else:
                    shaped_specs.append((step_id, skill, title, description, weight))
            return shaped_specs

        if session_shape == "protected_mix":
            filtered_specs = [
                spec
                for spec in step_specs
                if spec[0] != "pronunciation" or (reentry_focus == "pronunciation" or recovery_focus == "pronunciation")
            ]
            if reentry_step_id:
                filtered_specs = self._move_step_before_ids(
                    filtered_specs,
                    step_id=reentry_step_id,
                    before_ids=(
                        {"grammar-pattern", "input", "response", "reinforcement", "summary"}
                        if recovery_phase == "support_reopen_arc"
                        else {"input", "response", "reinforcement", "summary"}
                    ),
                )
            return filtered_specs

        if session_shape in {"focused_support", "guided_balance"}:
            lead_support_step_id = reentry_step_id or {
                "grammar": "grammar-pattern",
                "vocabulary": "vocabulary-recall",
                "listening": "input",
                "pronunciation": "pronunciation",
                "speaking": "response",
                "writing": "writing-support",
                "profession": "profession-support",
            }.get(recovery_focus or "")
            if lead_support_step_id:
                return self._move_step_before_ids(
                    step_specs,
                    step_id=lead_support_step_id,
                    before_ids={"input", "response", "reinforcement", "summary"},
                )
            return step_specs

        if session_shape == "forward_mix":
            if not any(spec[0] == "stretch-response" for spec in step_specs):
                return [
                    *step_specs[:-1],
                    (
                        "stretch-response",
                        "reinforcement",
                        "Stretch response",
                        f"Push one slightly wider variation while {focus_area} stays stable enough to extend forward.",
                        2,
                    ),
                    step_specs[-1],
                ]
        return step_specs

    @staticmethod
    def _infer_input_lane(profile: UserProfile) -> str:
        preferred_mode = profile.onboarding_answers.preferred_mode
        if preferred_mode == "text_first":
            return "reading"
        if preferred_mode == "mixed":
            ritual_elements = set(profile.onboarding_answers.ritual_elements)
            if "reading_for_pleasure" in ritual_elements and "spontaneous_voice_notes" not in ritual_elements:
                return "reading"
        return "listening"

    @staticmethod
    def _infer_output_lane(profile: UserProfile) -> str:
        preferred_mode = profile.onboarding_answers.preferred_mode
        if preferred_mode == "text_first":
            return "writing"
        if preferred_mode == "mixed":
            ritual_elements = set(profile.onboarding_answers.ritual_elements)
            if "reading_for_pleasure" in ritual_elements and "spontaneous_voice_notes" not in ritual_elements:
                return "writing"
        return "speaking"

    @staticmethod
    def _resolve_onboarding_completed_at(current_state: LearnerJourneyState | None) -> datetime:
        if current_state and current_state.onboarding_completed_at:
            return datetime.fromisoformat(current_state.onboarding_completed_at)
        return datetime.utcnow()
