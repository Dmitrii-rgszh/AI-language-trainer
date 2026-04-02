from __future__ import annotations

from uuid import uuid4

from sqlalchemy.orm import Session, sessionmaker

from app.models.user_account import UserAccount as UserAccountModel
from app.repositories.account_mappers import to_user_account
from app.repositories.user_account_policies import build_login_candidates, normalize_login_candidate
from app.repositories.user_account_queries import (
    find_conflicting_email,
    find_conflicting_login,
    find_taken_logins,
    find_user_by_email,
    find_user_by_login,
)
from app.schemas.user_account import LoginAvailabilityResponse, UserAccount, UserAccountUpdateRequest


class UserIdentityConflictError(ValueError):
    pass


class UserAuthenticationError(ValueError):
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

    def sign_in(self, login: str, email: str) -> UserAccount:
        with self._session_factory() as session:
            login_model = find_user_by_login(session, login)
            email_model = find_user_by_email(session, email)

            if login_model and email_model and login_model.id == email_model.id:
                return to_user_account(login_model)

            raise UserAuthenticationError("Account not found for this login and email.")

    def check_login_availability(self, login: str, email: str | None = None) -> LoginAvailabilityResponse:
        normalized_login = login.strip()
        normalized_email = email.strip() if email else None

        with self._session_factory() as session:
            login_model = find_user_by_login(session, normalized_login)
            email_model = find_user_by_email(session, normalized_email) if normalized_email else None

            if login_model is None:
                return LoginAvailabilityResponse(
                    login=normalized_login,
                    normalized_login=normalize_login_candidate(normalized_login),
                    available=True,
                    status="available",
                )

            if email_model and email_model.id == login_model.id:
                return LoginAvailabilityResponse(
                    login=normalized_login,
                    normalized_login=normalize_login_candidate(normalized_login),
                    available=True,
                    status="existing_account",
                )

            return LoginAvailabilityResponse(
                login=normalized_login,
                normalized_login=normalize_login_candidate(normalized_login),
                available=False,
                status="taken",
                suggestions=self._build_login_suggestions(session, normalized_login),
            )

    def update_user(self, user_id: str, payload: UserAccountUpdateRequest) -> UserAccount:
        with self._session_factory() as session:
            model = session.get(UserAccountModel, user_id)
            if model is None:
                raise LookupError(user_id)

            conflicting_login = find_conflicting_login(session, user_id, payload.login)
            conflicting_email = find_conflicting_email(session, user_id, payload.email)
            if conflicting_login or conflicting_email:
                raise UserIdentityConflictError("Login or email is already used by another user.")

            model.login = payload.login
            model.email = payload.email
            session.commit()
            session.refresh(model)
            return to_user_account(model)

    @staticmethod
    def _resolve_model(session: Session, login: str, email: str) -> UserAccountModel:
        by_login = find_user_by_login(session, login)
        by_email = find_user_by_email(session, email)

        if by_login and by_email and by_login.id != by_email.id:
            raise UserIdentityConflictError("Login and email belong to different users.")

        if by_login and not by_email:
            raise UserIdentityConflictError("This login is already used by another user.")

        if by_email and not by_login:
            raise UserIdentityConflictError("This email is already used by another user.")

        model = by_login or by_email
        if model is None:
            model = UserAccountModel(id=f"user-{uuid4().hex[:12]}", login=login, email=email)
            session.add(model)
            session.flush()
            return model

        model.login = login
        model.email = email
        return model

    @staticmethod
    def _build_login_suggestions(session: Session, login: str, limit: int = 4) -> list[str]:
        candidates = build_login_candidates(login)
        taken_candidates = find_taken_logins(session, candidates)

        available_candidates = [
            candidate for candidate in candidates if candidate.lower() not in taken_candidates and candidate.lower() != login.lower()
        ]
        return available_candidates[:limit]
