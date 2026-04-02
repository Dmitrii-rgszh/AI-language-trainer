from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.user_account import UserAccount as UserAccountModel
from app.repositories.user_account_policies import normalized_identity


def find_user_by_login(session: Session, login: str | None) -> UserAccountModel | None:
    if not login:
        return None
    return session.scalar(
        select(UserAccountModel).where(func.lower(UserAccountModel.login) == normalized_identity(login))
    )


def find_user_by_email(session: Session, email: str | None) -> UserAccountModel | None:
    if not email:
        return None
    return session.scalar(
        select(UserAccountModel).where(func.lower(UserAccountModel.email) == normalized_identity(email))
    )


def find_conflicting_login(session: Session, user_id: str, login: str) -> UserAccountModel | None:
    return session.scalar(
        select(UserAccountModel).where(
            func.lower(UserAccountModel.login) == normalized_identity(login),
            UserAccountModel.id != user_id,
        )
    )


def find_conflicting_email(session: Session, user_id: str, email: str) -> UserAccountModel | None:
    return session.scalar(
        select(UserAccountModel).where(
            func.lower(UserAccountModel.email) == normalized_identity(email),
            UserAccountModel.id != user_id,
        )
    )


def find_taken_logins(session: Session, candidates: list[str]) -> set[str]:
    return {
        row[0]
        for row in session.execute(
            select(func.lower(UserAccountModel.login)).where(
                func.lower(UserAccountModel.login).in_([candidate.lower() for candidate in candidates])
            )
        )
    }
