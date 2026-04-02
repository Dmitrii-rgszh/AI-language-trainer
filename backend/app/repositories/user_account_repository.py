from __future__ import annotations

import re
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from app.models.user_account import UserAccount as UserAccountModel
from app.repositories.account_mappers import to_user_account
from app.schemas.user_account import LoginAvailabilityResponse, UserAccount, UserAccountUpdateRequest


class UserIdentityConflictError(ValueError):
    pass


class UserAuthenticationError(ValueError):
    pass


def _normalized_identity(value: str) -> str:
    return value.strip().lower()


def _normalize_login_candidate(value: str) -> str:
    compact = re.sub(r"\s+", "_", value.strip().lower())
    compact = re.sub(r"[^\w-]", "", compact, flags=re.UNICODE)
    compact = re.sub(r"_+", "_", compact).strip("_-")
    return compact or "learner"


def _compose_login_candidate(base: str, suffix: str) -> str:
    clipped_base = base[: max(1, 64 - len(suffix))]
    return f"{clipped_base}{suffix}"


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
            login_model = self._find_by_login(session, login)
            email_model = self._find_by_email(session, email)

            if login_model and email_model and login_model.id == email_model.id:
                return to_user_account(login_model)

            raise UserAuthenticationError("Account not found for this login and email.")

    def check_login_availability(self, login: str, email: str | None = None) -> LoginAvailabilityResponse:
        normalized_login = login.strip()
        normalized_email = email.strip() if email else None

        with self._session_factory() as session:
            login_model = self._find_by_login(session, normalized_login)
            email_model = self._find_by_email(session, normalized_email) if normalized_email else None

            if login_model is None:
                return LoginAvailabilityResponse(
                    login=normalized_login,
                    normalized_login=_normalize_login_candidate(normalized_login),
                    available=True,
                    status="available",
                )

            if email_model and email_model.id == login_model.id:
                return LoginAvailabilityResponse(
                    login=normalized_login,
                    normalized_login=_normalize_login_candidate(normalized_login),
                    available=True,
                    status="existing_account",
                )

            return LoginAvailabilityResponse(
                login=normalized_login,
                normalized_login=_normalize_login_candidate(normalized_login),
                available=False,
                status="taken",
                suggestions=self._build_login_suggestions(session, normalized_login),
            )

    def update_user(self, user_id: str, payload: UserAccountUpdateRequest) -> UserAccount:
        with self._session_factory() as session:
            model = session.get(UserAccountModel, user_id)
            if model is None:
                raise LookupError(user_id)

            conflicting_login = session.scalar(
                select(UserAccountModel).where(
                    func.lower(UserAccountModel.login) == _normalized_identity(payload.login),
                    UserAccountModel.id != user_id,
                )
            )
            conflicting_email = session.scalar(
                select(UserAccountModel).where(
                    func.lower(UserAccountModel.email) == _normalized_identity(payload.email),
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
        by_login = UserAccountRepository._find_by_login(session, login)
        by_email = UserAccountRepository._find_by_email(session, email)

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
    def _find_by_login(session: Session, login: str | None) -> UserAccountModel | None:
        if not login:
            return None
        return session.scalar(
            select(UserAccountModel).where(func.lower(UserAccountModel.login) == _normalized_identity(login))
        )

    @staticmethod
    def _find_by_email(session: Session, email: str | None) -> UserAccountModel | None:
        if not email:
            return None
        return session.scalar(
            select(UserAccountModel).where(func.lower(UserAccountModel.email) == _normalized_identity(email))
        )

    @staticmethod
    def _build_login_suggestions(session: Session, login: str, limit: int = 4) -> list[str]:
        base = _normalize_login_candidate(login)
        suffixes = [
            "_1",
            "_2",
            "_3",
            "_7",
            f"_{datetime.now(timezone.utc).year}",
            str(datetime.now(timezone.utc).year)[-2:],
            "_pro",
            "_study",
        ]

        candidates: list[str] = []
        seen: set[str] = set()
        for suffix in suffixes:
            candidate = _compose_login_candidate(base, suffix)
            lowered = candidate.lower()
            if lowered == base.lower() or lowered in seen:
                continue
            seen.add(lowered)
            candidates.append(candidate)

        taken_candidates = {
            row[0]
            for row in session.execute(
                select(func.lower(UserAccountModel.login)).where(
                    func.lower(UserAccountModel.login).in_([candidate.lower() for candidate in candidates])
                )
            )
        }

        available_candidates = [
            candidate for candidate in candidates if candidate.lower() not in taken_candidates and candidate.lower() != login.lower()
        ]
        return available_candidates[:limit]
