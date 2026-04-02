from __future__ import annotations

"""Compatibility facade for adaptive loop copy builders."""

from app.services.adaptive_study_service.headline_builder import build_headline
from app.services.adaptive_study_service.rationale_builder import build_generation_rationale
from app.services.adaptive_study_service.summary_builder import build_summary

__all__ = [
    "build_generation_rationale",
    "build_headline",
    "build_summary",
]
