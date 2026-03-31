from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.models.user_profile import UserProfile as UserProfileModel
from app.repositories.mappers import to_user_profile
from app.schemas.profile import ProfileUpdateRequest, UserProfile


class ProfileRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def get_profile(self, profile_id: str | None = None) -> UserProfile | None:
        with self._session_factory() as session:
            model = self._get_profile_model(session, profile_id)
            return to_user_profile(model) if model else None

    def update_profile(self, payload: ProfileUpdateRequest) -> UserProfile:
        with self._session_factory() as session:
            model = session.get(UserProfileModel, payload.id)
            if not model:
                model = UserProfileModel(id=payload.id)
                session.add(model)

            model.name = payload.name
            model.native_language = payload.native_language
            model.current_level = payload.current_level
            model.target_level = payload.target_level
            model.profession_track = payload.profession_track
            model.preferred_ui_language = payload.preferred_ui_language
            model.preferred_explanation_language = payload.preferred_explanation_language
            model.lesson_duration = payload.lesson_duration
            model.speaking_priority = payload.speaking_priority
            model.grammar_priority = payload.grammar_priority
            model.profession_priority = payload.profession_priority

            session.commit()
            session.refresh(model)
            return to_user_profile(model)

    @staticmethod
    def _get_profile_model(session: Session, profile_id: str | None = None) -> UserProfileModel | None:
        if profile_id:
            return session.get(UserProfileModel, profile_id)

        return session.scalar(select(UserProfileModel).order_by(UserProfileModel.created_at.asc()).limit(1))

