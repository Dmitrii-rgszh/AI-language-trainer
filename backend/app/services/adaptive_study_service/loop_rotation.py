from __future__ import annotations

"""Compatibility facade for adaptive loop rotation builders."""

from app.services.adaptive_study_service.next_steps_builder import build_next_steps
from app.services.adaptive_study_service.rotation_builder import build_module_rotation

__all__ = [
    "build_module_rotation",
    "build_next_steps",
]
