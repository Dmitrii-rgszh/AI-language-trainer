from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.models.daily_loop_plan import DailyLoopPlan as DailyLoopPlanModel
from app.models.learner_journey_state import LearnerJourneyState as LearnerJourneyStateModel
from app.models.onboarding_session import OnboardingSession as OnboardingSessionModel
from app.schemas.journey import (
    DailyLoopPlan,
    DailyLoopStep,
    JourneyAccountDraft,
    LearnerJourneyState,
    OnboardingSession,
    ProofLessonHandoff,
)
from app.schemas.profile import UserProfile


class JourneyRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def create_onboarding_session(
        self,
        *,
        source: str,
        proof_lesson_handoff: dict | None = None,
    ) -> OnboardingSession:
        with self._session_factory() as session:
            model = OnboardingSessionModel(
                id=f"journey-{uuid4().hex[:12]}",
                source=source,
                status="proof_lesson" if proof_lesson_handoff else "draft",
                proof_lesson_handoff=proof_lesson_handoff or {},
                account_draft={},
                profile_draft={},
                current_step=0,
            )
            session.add(model)
            session.commit()
            session.refresh(model)
            return self._to_onboarding_session(model)

    def get_onboarding_session(self, session_id: str) -> OnboardingSession | None:
        with self._session_factory() as session:
            model = session.get(OnboardingSessionModel, session_id)
            return self._to_onboarding_session(model) if model else None

    def save_onboarding_draft(
        self,
        session_id: str,
        *,
        account_draft: dict,
        profile_draft: dict,
        current_step: int,
    ) -> OnboardingSession | None:
        with self._session_factory() as session:
            model = session.get(OnboardingSessionModel, session_id)
            if model is None:
                return None

            model.account_draft = account_draft
            model.profile_draft = profile_draft
            model.current_step = current_step
            model.status = "draft"
            session.commit()
            session.refresh(model)
            return self._to_onboarding_session(model)

    def attach_session_user(self, session_id: str, user_id: str) -> OnboardingSession | None:
        with self._session_factory() as session:
            model = session.get(OnboardingSessionModel, session_id)
            if model is None:
                return None

            model.user_id = user_id
            session.commit()
            session.refresh(model)
            return self._to_onboarding_session(model)

    def complete_onboarding_session(self, session_id: str, user_id: str) -> OnboardingSession | None:
        with self._session_factory() as session:
            model = session.get(OnboardingSessionModel, session_id)
            if model is None:
                return None

            model.user_id = user_id
            model.status = "completed"
            model.completed_at = datetime.utcnow()
            session.commit()
            session.refresh(model)
            return self._to_onboarding_session(model)

    def get_journey_state(self, user_id: str) -> LearnerJourneyState | None:
        with self._session_factory() as session:
            model = session.get(LearnerJourneyStateModel, user_id)
            return self._to_learner_journey_state(model) if model else None

    def upsert_journey_state(
        self,
        *,
        user_id: str,
        stage: str,
        source: str,
        preferred_mode: str,
        diagnostic_readiness: str,
        time_budget_minutes: int,
        current_focus_area: str,
        current_strategy_summary: str,
        next_best_action: str,
        proof_lesson_handoff: dict | None,
        strategy_snapshot: dict,
        onboarding_completed_at: datetime | None = None,
        last_daily_plan_id: str | None = None,
    ) -> LearnerJourneyState:
        with self._session_factory() as session:
            model = session.get(LearnerJourneyStateModel, user_id)
            if model is None:
                model = LearnerJourneyStateModel(user_id=user_id)
                session.add(model)

            model.stage = stage
            model.source = source
            model.preferred_mode = preferred_mode
            model.diagnostic_readiness = diagnostic_readiness
            model.time_budget_minutes = time_budget_minutes
            model.current_focus_area = current_focus_area
            model.current_strategy_summary = current_strategy_summary
            model.next_best_action = next_best_action
            model.proof_lesson_handoff = proof_lesson_handoff or {}
            model.strategy_snapshot = strategy_snapshot
            model.onboarding_completed_at = onboarding_completed_at
            model.last_daily_plan_id = last_daily_plan_id

            session.commit()
            session.refresh(model)
            return self._to_learner_journey_state(model)

    def get_daily_loop_plan(self, user_id: str, plan_date_key: str) -> DailyLoopPlan | None:
        with self._session_factory() as session:
            statement = select(DailyLoopPlanModel).where(
                DailyLoopPlanModel.user_id == user_id,
                DailyLoopPlanModel.plan_date_key == plan_date_key,
            )
            model = session.scalar(statement)
            return self._to_daily_loop_plan(model) if model else None

    def upsert_daily_loop_plan(
        self,
        *,
        user_id: str,
        plan_date_key: str,
        stage: str,
        session_kind: str,
        focus_area: str,
        headline: str,
        summary: str,
        why_this_now: str,
        next_step_hint: str,
        preferred_mode: str,
        time_budget_minutes: int,
        estimated_minutes: int,
        recommended_lesson_type: str,
        recommended_lesson_title: str,
        steps: list[dict],
        status: str = "planned",
    ) -> DailyLoopPlan:
        with self._session_factory() as session:
            statement = select(DailyLoopPlanModel).where(
                DailyLoopPlanModel.user_id == user_id,
                DailyLoopPlanModel.plan_date_key == plan_date_key,
            )
            model = session.scalar(statement)
            if model is None:
                model = DailyLoopPlanModel(
                    id=f"daily-loop-{uuid4().hex[:12]}",
                    user_id=user_id,
                    plan_date_key=plan_date_key,
                )
                session.add(model)

            model.status = status
            model.stage = stage
            model.session_kind = session_kind
            model.focus_area = focus_area
            model.headline = headline
            model.summary = summary
            model.why_this_now = why_this_now
            model.next_step_hint = next_step_hint
            model.preferred_mode = preferred_mode
            model.time_budget_minutes = time_budget_minutes
            model.estimated_minutes = estimated_minutes
            model.recommended_lesson_type = recommended_lesson_type
            model.recommended_lesson_title = recommended_lesson_title
            model.steps = steps

            session.commit()
            session.refresh(model)
            return self._to_daily_loop_plan(model)

    def attach_daily_loop_run(self, plan_id: str, run_id: str) -> DailyLoopPlan | None:
        with self._session_factory() as session:
            model = session.get(DailyLoopPlanModel, plan_id)
            if model is None:
                return None

            model.lesson_run_id = run_id
            model.status = "active"
            session.commit()
            session.refresh(model)
            return self._to_daily_loop_plan(model)

    def complete_daily_loop_plan_by_run(
        self,
        *,
        user_id: str,
        run_id: str,
        completion_summary: dict,
    ) -> DailyLoopPlan | None:
        with self._session_factory() as session:
            statement = select(DailyLoopPlanModel).where(
                DailyLoopPlanModel.user_id == user_id,
                DailyLoopPlanModel.lesson_run_id == run_id,
            )
            model = session.scalar(statement)
            if model is None:
                return None

            model.status = "completed"
            model.completed_at = datetime.utcnow()
            model.completion_summary = completion_summary
            session.commit()
            session.refresh(model)
            return self._to_daily_loop_plan(model)

    @staticmethod
    def _to_onboarding_session(model: OnboardingSessionModel) -> OnboardingSession:
        proof_lesson_handoff = JourneyRepository._parse_proof_lesson_handoff(model.proof_lesson_handoff)
        profile_draft = JourneyRepository._parse_profile_draft(model.profile_draft)
        return OnboardingSession(
            id=model.id,
            user_id=model.user_id,
            status=model.status,
            source=model.source,
            proof_lesson_handoff=proof_lesson_handoff,
            account_draft=JourneyAccountDraft.model_validate(model.account_draft or {}),
            profile_draft=profile_draft,
            current_step=model.current_step,
            completed_at=model.completed_at.isoformat() if model.completed_at else None,
            created_at=model.created_at.isoformat(),
            updated_at=model.updated_at.isoformat(),
        )

    @staticmethod
    def _to_learner_journey_state(model: LearnerJourneyStateModel) -> LearnerJourneyState:
        return LearnerJourneyState(
            user_id=model.user_id,
            stage=model.stage,
            source=model.source,
            preferred_mode=model.preferred_mode,
            diagnostic_readiness=model.diagnostic_readiness,
            time_budget_minutes=model.time_budget_minutes,
            current_focus_area=model.current_focus_area,
            current_strategy_summary=model.current_strategy_summary,
            next_best_action=model.next_best_action,
            last_daily_plan_id=model.last_daily_plan_id,
            proof_lesson_handoff=JourneyRepository._parse_proof_lesson_handoff(model.proof_lesson_handoff),
            strategy_snapshot=model.strategy_snapshot or {},
            onboarding_completed_at=(
                model.onboarding_completed_at.isoformat() if model.onboarding_completed_at else None
            ),
            created_at=model.created_at.isoformat(),
            updated_at=model.updated_at.isoformat(),
        )

    @staticmethod
    def _to_daily_loop_plan(model: DailyLoopPlanModel) -> DailyLoopPlan:
        return DailyLoopPlan(
            id=model.id,
            plan_date_key=model.plan_date_key,
            status=model.status,
            stage=model.stage,
            session_kind=model.session_kind,
            focus_area=model.focus_area,
            headline=model.headline,
            summary=model.summary,
            why_this_now=model.why_this_now,
            next_step_hint=model.next_step_hint,
            preferred_mode=model.preferred_mode,
            time_budget_minutes=model.time_budget_minutes,
            estimated_minutes=model.estimated_minutes,
            recommended_lesson_type=model.recommended_lesson_type,
            recommended_lesson_title=model.recommended_lesson_title,
            lesson_run_id=model.lesson_run_id,
            completed_at=model.completed_at.isoformat() if model.completed_at else None,
            steps=[
                DailyLoopStep.model_validate(step)
                for step in (model.steps or [])
            ],
        )

    @staticmethod
    def _parse_proof_lesson_handoff(value: dict | None) -> ProofLessonHandoff | None:
        if not value:
            return None

        try:
            return ProofLessonHandoff.model_validate(value)
        except Exception:
            return None

    @staticmethod
    def _parse_profile_draft(value: dict | None) -> UserProfile | None:
        if not value:
            return None

        try:
            return UserProfile.model_validate(value)
        except Exception:
            return None
