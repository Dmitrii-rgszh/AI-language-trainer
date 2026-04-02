from __future__ import annotations

"""Compatibility layer for legacy mapper imports.

Repository code should import domain-specific mapper modules directly.
This module stays as a thin bridge so older imports keep working while
we finish the modular split.
"""

from app.repositories.account_mappers import (
    to_provider_preference,
    to_user_account,
    to_user_onboarding,
)
from app.repositories.lesson_mappers import (
    focus_area as _focus_area,
    to_lesson,
    to_lesson_block,
    to_lesson_history_item,
    to_lesson_recommendation,
    to_lesson_run_state,
)
from app.repositories.mistake_mappers import to_mistake
from app.repositories.profile_mappers import to_user_profile
from app.repositories.progress_mappers import (
    SKILL_AREA_TO_PROGRESS_FIELD,
    to_progress_snapshot,
)

__all__ = [
    "SKILL_AREA_TO_PROGRESS_FIELD",
    "_focus_area",
    "to_lesson",
    "to_lesson_block",
    "to_lesson_history_item",
    "to_lesson_recommendation",
    "to_lesson_run_state",
    "to_mistake",
    "to_progress_snapshot",
    "to_provider_preference",
    "to_user_account",
    "to_user_onboarding",
    "to_user_profile",
]
