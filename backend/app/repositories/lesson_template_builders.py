from __future__ import annotations

"""Compatibility facade for dynamic lesson template builders."""

from app.repositories.diagnostic_template_builder import create_diagnostic_template
from app.repositories.recovery_template_builder import create_recovery_template

__all__ = [
    "create_diagnostic_template",
    "create_recovery_template",
]
