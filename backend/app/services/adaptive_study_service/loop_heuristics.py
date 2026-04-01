from __future__ import annotations

from collections.abc import Sequence

from app.schemas.mistake import WeakSpot
from app.schemas.progress import ProgressSnapshot
from app.services.shared.recovery_signals import build_mistake_resolution


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
