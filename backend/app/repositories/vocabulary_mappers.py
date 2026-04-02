from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta

from app.models.vocabulary_item import VocabularyItem as VocabularyItemModel
from app.schemas.adaptive import MistakeVocabularyBacklink, VocabularyLoopSummary, VocabularyReviewItem
from app.schemas.blueprint import VocabularyStatus


def is_due(model: VocabularyItemModel) -> bool:
    if model.learned_status != VocabularyStatus.MASTERED:
        return True
    if model.last_reviewed_at is None:
        return True
    return model.last_reviewed_at <= datetime.utcnow() - timedelta(days=7)


def to_review_item(model: VocabularyItemModel) -> VocabularyReviewItem:
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
        due_now=is_due(model),
    )


def build_summary(models: list[VocabularyItemModel]) -> VocabularyLoopSummary:
    due_items = [model for model in models if is_due(model)]
    categories = Counter(model.category for model in due_items)
    return VocabularyLoopSummary(
        due_count=len(due_items),
        new_count=len([model for model in models if model.learned_status == VocabularyStatus.NEW]),
        active_count=len([model for model in models if model.learned_status == VocabularyStatus.ACTIVE]),
        mastered_count=len([model for model in models if model.learned_status == VocabularyStatus.MASTERED]),
        weakest_category=categories.most_common(1)[0][0] if categories else None,
    )


def build_mistake_backlinks(
    models: list[VocabularyItemModel],
    limit: int = 6,
) -> list[MistakeVocabularyBacklink]:
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
        if is_due(model):
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
