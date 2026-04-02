from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.vocabulary_item import VocabularyItem as VocabularyItemModel


def load_user_vocabulary_items(session: Session, user_id: str) -> list[VocabularyItemModel]:
    statement = select(VocabularyItemModel).where(VocabularyItemModel.user_id == user_id)
    return session.scalars(statement).all()


def load_due_candidate_items(session: Session, user_id: str) -> list[VocabularyItemModel]:
    statement = (
        select(VocabularyItemModel)
        .where(VocabularyItemModel.user_id == user_id)
        .order_by(VocabularyItemModel.repetition_stage.asc(), VocabularyItemModel.word.asc())
    )
    return session.scalars(statement).all()


def load_recent_vocabulary_items(
    session: Session,
    user_id: str,
    limit: int,
) -> list[VocabularyItemModel]:
    statement = (
        select(VocabularyItemModel)
        .where(VocabularyItemModel.user_id == user_id)
        .order_by(VocabularyItemModel.last_reviewed_at.desc().nullslast(), VocabularyItemModel.word.asc())
        .limit(limit)
    )
    return session.scalars(statement).all()


def load_vocabulary_item(session: Session, user_id: str, item_id: str) -> VocabularyItemModel | None:
    statement = select(VocabularyItemModel).where(
        VocabularyItemModel.user_id == user_id,
        VocabularyItemModel.id == item_id,
    )
    return session.scalar(statement)


def load_vocabulary_item_by_word(session: Session, user_id: str, word: str) -> VocabularyItemModel | None:
    statement = select(VocabularyItemModel).where(
        VocabularyItemModel.user_id == user_id,
        VocabularyItemModel.word == word,
    )
    return session.scalar(statement)
