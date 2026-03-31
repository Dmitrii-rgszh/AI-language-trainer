from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.models.user_onboarding import UserOnboarding as UserOnboardingModel
from app.repositories.mappers import to_user_onboarding
from app.schemas.onboarding import UserOnboarding
from app.schemas.profile import OnboardingAnswers


class OnboardingRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def get_onboarding(self, user_id: str) -> UserOnboarding | None:
        with self._session_factory() as session:
            model = session.scalar(select(UserOnboardingModel).where(UserOnboardingModel.user_id == user_id))
            return to_user_onboarding(model) if model else None

    def upsert_onboarding(self, user_id: str, answers: OnboardingAnswers) -> UserOnboarding:
        with self._session_factory() as session:
            model = session.scalar(select(UserOnboardingModel).where(UserOnboardingModel.user_id == user_id))
            if model is None:
                model = UserOnboardingModel(
                    id=f"onboarding-{user_id}",
                    user_id=user_id,
                    answers=answers.model_dump(mode="json"),
                    completed_at=datetime.utcnow(),
                )
                session.add(model)
            else:
                model.answers = answers.model_dump(mode="json")
                model.completed_at = datetime.utcnow()

            session.commit()
            session.refresh(model)
            return to_user_onboarding(model)
