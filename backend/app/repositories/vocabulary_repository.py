from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy.orm import Session, sessionmaker

from app.models.vocabulary_item import VocabularyItem as VocabularyItemModel
from app.repositories.vocabulary_capture import build_capture
from app.repositories.vocabulary_mappers import (
    build_mistake_backlinks,
    build_summary,
    is_due,
    to_review_item,
)
from app.repositories.vocabulary_queries import (
    load_due_candidate_items,
    load_recent_vocabulary_items,
    load_user_vocabulary_items,
    load_vocabulary_item,
    load_vocabulary_item_by_word,
)
from app.schemas.adaptive import MistakeVocabularyBacklink, VocabularyLoopSummary, VocabularyReviewItem
from app.schemas.blueprint import VocabularyStatus
from app.schemas.mistake_extraction import ExtractedMistake


class VocabularyRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def list_due_items(self, user_id: str, limit: int = 5) -> list[VocabularyReviewItem]:
        with self._session_factory() as session:
            models = load_due_candidate_items(session, user_id)
            due_items = [to_review_item(model) for model in models if is_due(model)]
            return due_items[:limit]

    def review_item(self, user_id: str, item_id: str, successful: bool) -> VocabularyReviewItem | None:
        with self._session_factory() as session:
            model = load_vocabulary_item(session, user_id, item_id)
            if not model:
                return None

            model.last_reviewed_at = datetime.utcnow()
            if successful:
                model.repetition_stage = min(10, model.repetition_stage + 1)
                model.learned_status = (
                    VocabularyStatus.MASTERED if model.repetition_stage >= 5 else VocabularyStatus.ACTIVE
                )
            else:
                model.repetition_stage = max(0, model.repetition_stage - 1)
                model.learned_status = VocabularyStatus.ACTIVE

            session.commit()
            session.refresh(model)
            return to_review_item(model)

    def get_summary(self, user_id: str) -> VocabularyLoopSummary:
        with self._session_factory() as session:
            models = load_user_vocabulary_items(session, user_id)
            return build_summary(models)

    def list_recent_items(self, user_id: str, limit: int = 8) -> list[VocabularyReviewItem]:
        with self._session_factory() as session:
            models = load_recent_vocabulary_items(session, user_id, limit)
            return [to_review_item(model) for model in models]

    def list_mistake_backlinks(self, user_id: str, limit: int = 6) -> list[MistakeVocabularyBacklink]:
        with self._session_factory() as session:
            models = load_user_vocabulary_items(session, user_id)
        return build_mistake_backlinks(models, limit=limit)

    def capture_from_mistakes(self, user_id: str, mistakes: list[ExtractedMistake]) -> list[VocabularyReviewItem]:
        captures = [capture for mistake in mistakes if (capture := build_capture(mistake)) is not None]
        if not captures:
            return []

        with self._session_factory() as session:
            saved: list[VocabularyItemModel] = []
            for capture in captures:
                existing = load_vocabulary_item_by_word(session, user_id, capture["word"])
                if existing:
                    existing.context = capture["context"]
                    existing.translation = capture["translation"]
                    existing.category = capture["category"]
                    existing.source_module = capture["source_module"]
                    existing.review_reason = capture["review_reason"]
                    existing.linked_mistake_subtype = capture["linked_mistake_subtype"]
                    existing.linked_mistake_title = capture["linked_mistake_title"]
                    existing.learned_status = VocabularyStatus.ACTIVE
                    existing.repetition_stage = max(0, existing.repetition_stage - 1)
                    existing.last_reviewed_at = None
                    saved.append(existing)
                    continue

                model = VocabularyItemModel(
                    id=f"vocab-capture-{uuid4().hex[:12]}",
                    user_id=user_id,
                    word=capture["word"],
                    translation=capture["translation"],
                    context=capture["context"],
                    category=capture["category"],
                    source_module=capture["source_module"],
                    review_reason=capture["review_reason"],
                    linked_mistake_subtype=capture["linked_mistake_subtype"],
                    linked_mistake_title=capture["linked_mistake_title"],
                    learned_status=VocabularyStatus.NEW,
                    repetition_stage=0,
                    last_reviewed_at=None,
                )
                session.add(model)
                saved.append(model)

            session.commit()
            for model in saved:
                session.refresh(model)
            return [to_review_item(model) for model in saved]
