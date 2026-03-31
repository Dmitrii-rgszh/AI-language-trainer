from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.models.user_provider_preference import UserProviderPreference as UserProviderPreferenceModel
from app.repositories.mappers import to_provider_preference
from app.schemas.provider import ProviderPreference, ProviderPreferenceUpdateRequest, ProviderType


class ProviderPreferenceRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def list_preferences(self, user_id: str) -> list[ProviderPreference]:
        with self._session_factory() as session:
            statement = (
                select(UserProviderPreferenceModel)
                .where(UserProviderPreferenceModel.user_id == user_id)
                .order_by(UserProviderPreferenceModel.provider_type.asc())
            )
            models = session.scalars(statement).all()
            return [to_provider_preference(model) for model in models]

    def upsert_preference(
        self,
        user_id: str,
        provider_type: ProviderType,
        payload: ProviderPreferenceUpdateRequest,
    ) -> ProviderPreference:
        with self._session_factory() as session:
            model = session.get(
                UserProviderPreferenceModel,
                {"user_id": user_id, "provider_type": provider_type},
            )
            if not model:
                model = UserProviderPreferenceModel(user_id=user_id, provider_type=provider_type)
                session.add(model)

            model.selected_provider = payload.selected_provider
            model.enabled = payload.enabled
            model.settings = payload.settings

            session.commit()
            session.refresh(model)
            return to_provider_preference(model)
