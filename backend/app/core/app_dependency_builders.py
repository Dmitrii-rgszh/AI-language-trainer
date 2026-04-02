from __future__ import annotations

from app.core.app_runtime_types import AppRepositories, AppRuntimeDependencies, SessionFactory
from app.db.session import SessionLocal
from app.providers.registry import ProviderRegistry
from app.services.ai_orchestrator import AIOrchestrator
from app.services.mistake_extraction_service.service import MistakeExtractionService
from app.services.profile_bootstrap_service.service import ProfileBootstrapService
from app.services.profile_service.service import ProfileService
from app.services.stt_service.service import STTService


def build_app_runtime_dependencies(
    repositories: AppRepositories,
    session_factory: SessionFactory = SessionLocal,
    provider_registry: ProviderRegistry | None = None,
) -> AppRuntimeDependencies:
    runtime_provider_registry = provider_registry or ProviderRegistry()
    profile_bootstrap_service = ProfileBootstrapService(session_factory)

    return AppRuntimeDependencies(
        ai_orchestrator=AIOrchestrator(runtime_provider_registry.llm_provider),
        mistake_extraction_service=MistakeExtractionService(),
        profile_service=ProfileService(repositories.profile_repository, profile_bootstrap_service),
        provider_registry=runtime_provider_registry,
        stt_service=STTService(runtime_provider_registry.stt_provider),
    )
