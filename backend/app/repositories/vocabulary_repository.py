from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta
import re
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.models.vocabulary_item import VocabularyItem as VocabularyItemModel
from app.schemas.blueprint import VocabularyStatus
from app.schemas.adaptive import MistakeVocabularyBacklink, VocabularyLoopSummary, VocabularyReviewItem
from app.services.mistake_extraction_service.service import ExtractedMistake


class VocabularyRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def list_due_items(self, user_id: str, limit: int = 5) -> list[VocabularyReviewItem]:
        with self._session_factory() as session:
            statement = (
                select(VocabularyItemModel)
                .where(VocabularyItemModel.user_id == user_id)
                .order_by(VocabularyItemModel.repetition_stage.asc(), VocabularyItemModel.word.asc())
            )
            models = session.scalars(statement).all()
            due_items = [self._to_review_item(model) for model in models if self._is_due(model)]
            return due_items[:limit]

    def review_item(self, user_id: str, item_id: str, successful: bool) -> VocabularyReviewItem | None:
        with self._session_factory() as session:
            model = session.scalar(
                select(VocabularyItemModel).where(
                    VocabularyItemModel.user_id == user_id,
                    VocabularyItemModel.id == item_id,
                )
            )
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
            return self._to_review_item(model)

    def get_summary(self, user_id: str) -> VocabularyLoopSummary:
        with self._session_factory() as session:
            models = session.scalars(select(VocabularyItemModel).where(VocabularyItemModel.user_id == user_id)).all()
            due_items = [model for model in models if self._is_due(model)]
            categories = Counter(model.category for model in due_items)
            return VocabularyLoopSummary(
                due_count=len(due_items),
                new_count=len([model for model in models if model.learned_status == VocabularyStatus.NEW]),
                active_count=len([model for model in models if model.learned_status == VocabularyStatus.ACTIVE]),
                mastered_count=len([model for model in models if model.learned_status == VocabularyStatus.MASTERED]),
                weakest_category=categories.most_common(1)[0][0] if categories else None,
            )

    def list_recent_items(self, user_id: str, limit: int = 8) -> list[VocabularyReviewItem]:
        with self._session_factory() as session:
            statement = (
                select(VocabularyItemModel)
                .where(VocabularyItemModel.user_id == user_id)
                .order_by(VocabularyItemModel.last_reviewed_at.desc().nullslast(), VocabularyItemModel.word.asc())
                .limit(limit)
            )
            return [self._to_review_item(model) for model in session.scalars(statement).all()]

    def list_mistake_backlinks(self, user_id: str, limit: int = 6) -> list[MistakeVocabularyBacklink]:
        with self._session_factory() as session:
            models = session.scalars(select(VocabularyItemModel).where(VocabularyItemModel.user_id == user_id)).all()

        grouped: dict[str, dict[str, object]] = {}
        for model in models:
            if not model.linked_mistake_title:
                continue

            bucket = grouped.setdefault(
                model.linked_mistake_title,
                {
                    "weak_spot_title": model.linked_mistake_title,
                    "weak_spot_category": model.category,
                    "due_count": 0,
                    "active_count": 0,
                    "example_words": [],
                    "source_modules": [],
                },
            )
            if self._is_due(model):
                bucket["due_count"] = int(bucket["due_count"]) + 1
            bucket["active_count"] = int(bucket["active_count"]) + 1
            if model.word not in bucket["example_words"] and len(bucket["example_words"]) < 3:
                cast_list = bucket["example_words"]
                assert isinstance(cast_list, list)
                cast_list.append(model.word)
            if model.source_module not in bucket["source_modules"]:
                source_list = bucket["source_modules"]
                assert isinstance(source_list, list)
                source_list.append(model.source_module)

        ranked = sorted(
            grouped.values(),
            key=lambda item: (int(item["due_count"]), int(item["active_count"])),
            reverse=True,
        )[:limit]
        return [
            MistakeVocabularyBacklink(
                weak_spot_title=str(item["weak_spot_title"]),
                weak_spot_category=str(item["weak_spot_category"]),
                due_count=int(item["due_count"]),
                active_count=int(item["active_count"]),
                example_words=list(item["example_words"]),
                source_modules=list(item["source_modules"]),
            )
            for item in ranked
        ]

    def capture_from_mistakes(self, user_id: str, mistakes: list[ExtractedMistake]) -> list[VocabularyReviewItem]:
        captures = [capture for mistake in mistakes if (capture := self._build_capture(mistake)) is not None]
        if not captures:
            return []

        with self._session_factory() as session:
            saved: list[VocabularyItemModel] = []
            for capture in captures:
                existing = session.scalar(
                    select(VocabularyItemModel).where(
                        VocabularyItemModel.user_id == user_id,
                        VocabularyItemModel.word == capture["word"],
                    )
                )
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
            return [self._to_review_item(model) for model in saved]

    @staticmethod
    def _is_due(model: VocabularyItemModel) -> bool:
        if model.learned_status != VocabularyStatus.MASTERED:
            return True
        if model.last_reviewed_at is None:
            return True
        return model.last_reviewed_at <= datetime.utcnow() - timedelta(days=7)

    @staticmethod
    def _to_review_item(model: VocabularyItemModel) -> VocabularyReviewItem:
        return VocabularyReviewItem(
            id=model.id,
            word=model.word,
            translation=model.translation,
            context=model.context,
            category=model.category,
            source_module=model.source_module,
            review_reason=model.review_reason,
            linked_mistake_subtype=model.linked_mistake_subtype,
            linked_mistake_title=model.linked_mistake_title,
            learned_status=model.learned_status.value,
            repetition_stage=model.repetition_stage,
            due_now=VocabularyRepository._is_due(model),
        )

    @staticmethod
    def _build_capture(mistake: ExtractedMistake) -> dict[str, str] | None:
        if mistake.subtype == "irregular-past":
            corrected = VocabularyRepository._extract_irregular_past_target(
                original_text=mistake.original_text,
                corrected_text=mistake.corrected_text,
            )
            if not corrected:
                return None
            return {
                "word": corrected.lower(),
                "translation": "неправильная форма прошедшего времени",
                "context": f"{mistake.original_text} -> {mistake.corrected_text}",
                "category": "mistake_irregular_verbs",
                "source_module": mistake.source_module,
                "review_reason": "Captured from repeated irregular past correction.",
                "linked_mistake_subtype": mistake.subtype,
                "linked_mistake_title": "Irregular Past Forms",
            }

        if mistake.subtype == "subject-verb-agreement":
            corrected = VocabularyRepository._extract_agreement_target(mistake.corrected_text)
            if not corrected:
                return None
            return {
                "word": corrected.lower(),
                "translation": "согласование подлежащего и сказуемого",
                "context": f"{mistake.original_text} -> {mistake.corrected_text}",
                "category": "mistake_agreement_patterns",
                "source_module": mistake.source_module,
                "review_reason": "Captured from subject-verb agreement correction.",
                "linked_mistake_subtype": mistake.subtype,
                "linked_mistake_title": "Subject-Verb Agreement",
            }

        if mistake.subtype == "comparative-form":
            corrected = VocabularyRepository._extract_first_token(mistake.corrected_text)
            if not corrected:
                return None
            return {
                "word": corrected.lower(),
                "translation": "правильная сравнительная форма",
                "context": f"{mistake.original_text} -> {mistake.corrected_text}",
                "category": "mistake_comparatives",
                "source_module": mistake.source_module,
                "review_reason": "Captured from comparative form correction.",
                "linked_mistake_subtype": mistake.subtype,
                "linked_mistake_title": "Comparative Forms",
            }

        if mistake.subtype == "feedback-language":
            phrase = VocabularyRepository._extract_feedback_phrase(mistake.corrected_text)
            if not phrase:
                return None
            return {
                "word": phrase,
                "translation": "мягкая формулировка для professional feedback",
                "context": f"{mistake.original_text} -> {mistake.corrected_text}",
                "category": "mistake_feedback_language",
                "source_module": mistake.source_module,
                "review_reason": "Captured from professional feedback phrasing correction.",
                "linked_mistake_subtype": mistake.subtype,
                "linked_mistake_title": "Feedback language for workshops",
            }

        if mistake.subtype == "tense-choice":
            phrase = VocabularyRepository._extract_present_perfect_phrase(mistake.corrected_text)
            if not phrase:
                return None
            return {
                "word": phrase,
                "translation": "паттерн Present Perfect для опыта и периода с since",
                "context": f"{mistake.original_text} -> {mistake.corrected_text}",
                "category": "mistake_tense_patterns",
                "source_module": mistake.source_module,
                "review_reason": "Captured from tense correction for active reuse.",
                "linked_mistake_subtype": mistake.subtype,
                "linked_mistake_title": "Present Perfect vs Past Simple",
            }

        return None

    @staticmethod
    def _extract_first_token(text: str) -> str | None:
        match = re.search(r"\b([A-Za-z']+)\b", text)
        return match.group(1) if match else None

    @staticmethod
    def _extract_irregular_past_target(original_text: str, corrected_text: str) -> str | None:
        original_tokens = re.findall(r"[A-Za-z']+", original_text.lower())
        corrected_tokens = re.findall(r"[A-Za-z']+", corrected_text)
        for token in corrected_tokens:
            if token.lower() not in original_tokens:
                return token
        return VocabularyRepository._extract_first_token(corrected_text)

    @staticmethod
    def _extract_agreement_target(text: str) -> str | None:
        match = re.search(r"\b(?:people|participants|managers|trainers|teams)\s+([A-Za-z']+)\b", text, flags=re.IGNORECASE)
        return match.group(1) if match else VocabularyRepository._extract_first_token(text)

    @staticmethod
    def _extract_feedback_phrase(text: str) -> str | None:
        lowered = " ".join(text.split())
        return lowered[:80] if lowered else None

    @staticmethod
    def _extract_present_perfect_phrase(text: str) -> str | None:
        match = re.search(
            r"\b(?:I|We|They|He|She)\s+(?:have|has)\s+[A-Za-z']+(?:\s+[A-Za-z']+){0,4}",
            text,
            flags=re.IGNORECASE,
        )
        if match:
            return match.group(0)
        compact = " ".join(text.split())
        return compact[:80] if compact else None
