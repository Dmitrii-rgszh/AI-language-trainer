from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from app.repositories.mistake_repository import WEAK_SPOT_TITLE_MAP
from app.schemas.adaptive import MistakeResolutionSignal, MistakeVocabularyBacklink
from app.schemas.mistake import Mistake, WeakSpot
from app.schemas.progress import ProgressSnapshot


def detect_listening_focus(
    progress: ProgressSnapshot | None,
    weak_spots: Sequence[WeakSpot],
) -> str | None:
    if any(getattr(spot, "category", "") == "listening" for spot in weak_spots):
        return "audio_comprehension"
    if progress is None:
        return None
    if progress.listening_score <= 55:
        return "audio_comprehension"
    if progress.listening_score < min(progress.speaking_score or 100, progress.writing_score or 100):
        return "detail_capture"
    return None


def build_mistake_resolution(
    mistakes: Sequence[Mistake],
    vocabulary_backlinks: Sequence[MistakeVocabularyBacklink],
    limit: int = 4,
) -> list[MistakeResolutionSignal]:
    if not mistakes:
        return []

    backlink_map = {item.weak_spot_title: item for item in vocabulary_backlinks}
    now = datetime.utcnow()
    ranked = sorted(mistakes, key=lambda item: item.repetition_count, reverse=True)[:limit]
    signals: list[MistakeResolutionSignal] = []

    for mistake in ranked:
        title = WEAK_SPOT_TITLE_MAP.get(mistake.subtype, mistake.subtype.replace("-", " ").title())
        backlink = backlink_map.get(title)
        linked_vocabulary_count = backlink.active_count if backlink else 0
        last_seen_days_ago = max(0, (now - mistake.last_seen_at.replace(tzinfo=None)).days)

        if linked_vocabulary_count >= 2 and last_seen_days_ago >= 5:
            status = "stabilizing"
            hint = "This weak spot has moved into vocabulary review and has not resurfaced recently."
        elif linked_vocabulary_count >= 1 and last_seen_days_ago >= 2:
            status = "recovering"
            hint = "The pattern is still being reviewed, but it is appearing less often in fresh corrections."
        else:
            status = "active"
            hint = "This weak spot is still repeating often enough that it should stay in active recovery."

        signals.append(
            MistakeResolutionSignal(
                weak_spot_title=title,
                weak_spot_category=mistake.category,
                status=status,
                repetition_count=mistake.repetition_count,
                last_seen_days_ago=last_seen_days_ago,
                linked_vocabulary_count=linked_vocabulary_count,
                resolution_hint=hint,
            )
        )

    return signals
