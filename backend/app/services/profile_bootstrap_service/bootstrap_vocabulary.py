from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.vocabulary_item import VocabularyItem
from app.schemas.blueprint import VocabularyStatus
from app.schemas.profile import UserProfile

from .constants import BASELINE_PREFIX
from .types import TrackBaselineSpec


def ensure_vocabulary(
    session: Session,
    profile: UserProfile,
    spec: TrackBaselineSpec,
    baseline_key: str,
) -> None:
    legacy_item = session.get(VocabularyItem, "vocab-1")
    for index, item_spec in enumerate(spec["vocabulary"]):
        item_id = f"{BASELINE_PREFIX}vocab-{baseline_key}-{item_spec['code']}"
        model = (
            legacy_item
            if index == 0 and legacy_item is not None and legacy_item.user_id == profile.id
            else session.get(VocabularyItem, item_id)
        )
        if model is None:
            model = VocabularyItem(
                id=item_id,
                user_id=profile.id,
                word=item_spec["word"],
                translation=item_spec["translation"],
                context=item_spec["context"],
                category=item_spec["category"],
                source_module=item_spec["source_module"],
                review_reason=item_spec["review_reason"],
                linked_mistake_subtype=item_spec.get("linked_mistake_subtype"),
                linked_mistake_title=item_spec.get("linked_mistake_title"),
                learned_status=VocabularyStatus.ACTIVE,
                repetition_stage=item_spec["repetition_stage"],
                last_reviewed_at=datetime.utcnow() - timedelta(days=max(1, index)),
            )
            session.add(model)
            continue

        model.user_id = profile.id
        model.word = item_spec["word"]
        model.translation = item_spec["translation"]
        model.context = item_spec["context"]
        model.category = item_spec["category"]
        model.source_module = item_spec["source_module"]
        model.review_reason = item_spec["review_reason"]
        model.linked_mistake_subtype = item_spec.get("linked_mistake_subtype")
        model.linked_mistake_title = item_spec.get("linked_mistake_title")
        model.learned_status = VocabularyStatus.ACTIVE
        model.repetition_stage = item_spec["repetition_stage"]
        model.last_reviewed_at = datetime.utcnow() - timedelta(days=max(1, index))
