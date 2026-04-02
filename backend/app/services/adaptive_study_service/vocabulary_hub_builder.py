from __future__ import annotations

from app.schemas.adaptive import (
    MistakeVocabularyBacklink,
    VocabularyHub,
    VocabularyLoopSummary,
    VocabularyReviewItem,
)


def build_vocabulary_hub(
    summary: VocabularyLoopSummary,
    due_items: list[VocabularyReviewItem],
    recent_items: list[VocabularyReviewItem],
    mistake_backlinks: list[MistakeVocabularyBacklink],
) -> VocabularyHub:
    return VocabularyHub(
        summary=summary,
        due_items=due_items,
        recent_items=recent_items,
        mistake_backlinks=mistake_backlinks,
    )
