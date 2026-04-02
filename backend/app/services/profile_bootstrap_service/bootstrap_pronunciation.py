from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.pronunciation_attempt import PronunciationAttempt
from app.schemas.profile import UserProfile

from .constants import BASELINE_PREFIX
from .scoring import level_base
from .types import TrackBaselineSpec


def ensure_pronunciation_attempt(
    session: Session,
    profile: UserProfile,
    spec: TrackBaselineSpec,
    baseline_key: str,
) -> None:
    attempt_id = f"{BASELINE_PREFIX}pronunciation-{baseline_key}"
    pronunciation_spec = spec["pronunciation"]
    attempt = session.get(PronunciationAttempt, attempt_id)
    if attempt is None:
        attempt = PronunciationAttempt(
            id=attempt_id,
            user_id=profile.id,
            drill_id="pronunciation-soft-th-control",
            target_text=pronunciation_spec["target_text"],
            sound_focus="th",
            transcript=pronunciation_spec["transcript"],
            score=max(58, level_base(profile.current_level) + 6),
            feedback=pronunciation_spec["feedback"],
            weakest_words=list(pronunciation_spec["weakest_words"]),
            focus_issues=list(pronunciation_spec["focus_issues"]),
        )
        session.add(attempt)
        return

    attempt.user_id = profile.id
    attempt.drill_id = "pronunciation-soft-th-control"
    attempt.target_text = pronunciation_spec["target_text"]
    attempt.sound_focus = "th"
    attempt.transcript = pronunciation_spec["transcript"]
    attempt.score = max(58, level_base(profile.current_level) + 6)
    attempt.feedback = pronunciation_spec["feedback"]
    attempt.weakest_words = list(pronunciation_spec["weakest_words"])
    attempt.focus_issues = list(pronunciation_spec["focus_issues"])
