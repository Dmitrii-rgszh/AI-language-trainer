from __future__ import annotations

"""Compatibility facade for app runtime builder functions."""

from app.core.app_dependency_builders import build_app_runtime_dependencies
from app.core.app_repository_builders import build_app_repositories
from app.core.app_service_builders import build_app_runtime

__all__ = [
    "build_app_repositories",
    "build_app_runtime_dependencies",
    "build_app_runtime",
]
