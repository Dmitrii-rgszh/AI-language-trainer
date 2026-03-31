from __future__ import annotations

from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.models.user_account import UserAccount as UserAccountModel
from app.repositories.mappers import to_user_account
from app.schemas.user_account import UserAccount, UserAccountUpdateRequest


class UserIdentityConflictError(ValueError):
    pass


class UserAccountRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def get_user(self, user_id: str) -> UserAccount | None:
        with self._session_factory() as session:
            model = session.get(UserAccountModel, user_id)
            return to_user_account(model) if model else None

    def resolve_user(self, login: str, email: str) -> UserAccount:
        with self._session_factory() as session:
            model = self._resolve_model(session, login, email)
            session.commit()
            session.refresh(model)
            return to_user_account(model)

    def update_user(self, user_id: str, payload: UserAccountUpdateRequest) -> UserAccount:
        with self._session_factory() as session:
            model = session.get(UserAccountModel, user_id)
            if model is None:
                raise LookupError(user_id)

            conflicting_login = session.scalar(
                select(UserAccountModel).where(
                    UserAccountModel.login == payload.login,
                    UserAccountModel.id != user_id,
                )
            )
            conflicting_email = session.scalar(
                select(UserAccountModel).where(
                    UserAccountModel.email == payload.email,
                    UserAccountModel.id != user_id,
                )
            )
            if conflicting_login or conflicting_email:
                raise UserIdentityConflictError("Login or email is already used by another user.")

            model.login = payload.login
            model.email = payload.email
            session.commit()
            session.refresh(model)
            return to_user_account(model)

    @staticmethod
    def _resolve_model(session: Session, login: str, email: str) -> UserAccountModel:
        by_login = session.scalar(select(UserAccountModel).where(UserAccountModel.login == login))
        by_email = session.scalar(select(UserAccountModel).where(UserAccountModel.email == email))

        if by_login and by_email and by_login.id != by_email.id:
            raise UserIdentityConflictError("Login and email belong to different users.")

        model = by_login or by_email
        if model is None:
            model = UserAccountModel(id=f"user-{uuid4().hex[:12]}", login=login, email=email)
            session.add(model)
            session.flush()
            return model

        model.login = login
        model.email = email
        return model
