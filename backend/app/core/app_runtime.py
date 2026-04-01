from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from app.db.session import SessionLocal
from app.providers.registry import ProviderRegistry
from app.repositories.content_repository import ContentRepository
from app.repositories.lesson_repository import LessonRepository
from app.repositories.lesson_runtime_repository import LessonRuntimeRepository
from app.repositories.listening_repository import ListeningRepository
from app.repositories.mistake_repository import MistakeRepository
from app.repositories.onboarding_repository import OnboardingRepository
from app.repositories.profile_repository import ProfileRepository
from app.repositories.progress_repository import ProgressRepository
from app.repositories.provider_preference_repository import ProviderPreferenceRepository
from app.repositories.pronunciation_attempt_repository import PronunciationAttemptRepository
from app.repositories.recommendation_repository import RecommendationRepository
from app.repositories.speaking_attempt_repository import SpeakingAttemptRepository
from app.repositories.user_account_repository import UserAccountRepository
from app.repositories.vocabulary_repository import VocabularyRepository
from app.repositories.writing_attempt_repository import WritingAttemptRepository
from app.services.adaptive_study_service.service import AdaptiveStudyService
from app.services.ai_orchestrator import AIOrchestrator
from app.services.diagnostic_service.service import DiagnosticService
from app.services.grammar_service.service import GrammarService
from app.services.lesson_runtime_service.service import LessonRuntimeService
from app.services.lesson_service.service import LessonService
from app.services.listening_service.service import ListeningService
from app.services.mistake_extraction_service.service import MistakeExtractionService
from app.services.mistake_service.service import MistakeService
from app.services.onboarding_service.service import OnboardingService
from app.services.pronunciation_service.service import PronunciationService
from app.services.profile_bootstrap_service.service import ProfileBootstrapService
from app.services.profile_service.service import ProfileService
from app.services.profession_service.service import ProfessionService
from app.services.progress_service.service import ProgressService
from app.services.provider_service.service import ProviderService
from app.services.recommendation_service.service import RecommendationService
from app.services.speaking_service.service import SpeakingService
from app.services.stt_service.service import STTService
from app.services.user_service.service import UserService
from app.services.voice_service.service import VoiceService
from app.services.writing_service.service import WritingService

SessionFactory = Callable[[], Any]


@dataclass(frozen=True)
class AppRepositories:
    content_repository: ContentRepository
    lesson_repository: LessonRepository
    lesson_runtime_repository: LessonRuntimeRepository
    listening_repository: ListeningRepository
    mistake_repository: MistakeRepository
    onboarding_repository: OnboardingRepository
    profile_repository: ProfileRepository
    progress_repository: ProgressRepository
    provider_preference_repository: ProviderPreferenceRepository
    pronunciation_attempt_repository: PronunciationAttemptRepository
    recommendation_repository: RecommendationRepository
    speaking_attempt_repository: SpeakingAttemptRepository
    user_account_repository: UserAccountRepository
    vocabulary_repository: VocabularyRepository
    writing_attempt_repository: WritingAttemptRepository


@dataclass(frozen=True)
class AppRuntimeDependencies:
    ai_orchestrator: AIOrchestrator
    mistake_extraction_service: MistakeExtractionService
    profile_service: ProfileService
    provider_registry: ProviderRegistry
    stt_service: STTService


@dataclass(frozen=True)
class AppRuntime:
    adaptive_study_service: AdaptiveStudyService
    diagnostic_service: DiagnosticService
    grammar_service: GrammarService
    lesson_runtime_service: LessonRuntimeService
    lesson_service: LessonService
    listening_service: ListeningService
    mistake_service: MistakeService
    onboarding_service: OnboardingService
    profile_service: ProfileService
    profession_service: ProfessionService
    progress_service: ProgressService
    pronunciation_service: PronunciationService
    provider_service: ProviderService
    recommendation_service: RecommendationService
    speaking_service: SpeakingService
    stt_service: STTService
    user_service: UserService
    voice_service: VoiceService
    writing_service: WritingService


def build_app_repositories(session_factory: SessionFactory = SessionLocal) -> AppRepositories:
    lesson_repository = LessonRepository(session_factory)
    mistake_repository = MistakeRepository(session_factory)
    vocabulary_repository = VocabularyRepository(session_factory)

    return AppRepositories(
        content_repository=ContentRepository(session_factory),
        lesson_repository=lesson_repository,
        lesson_runtime_repository=LessonRuntimeRepository(session_factory),
        listening_repository=ListeningRepository(session_factory),
        mistake_repository=mistake_repository,
        onboarding_repository=OnboardingRepository(session_factory),
        profile_repository=ProfileRepository(session_factory),
        progress_repository=ProgressRepository(session_factory, lesson_repository),
        provider_preference_repository=ProviderPreferenceRepository(session_factory),
        pronunciation_attempt_repository=PronunciationAttemptRepository(session_factory),
        recommendation_repository=RecommendationRepository(
            lesson_repository,
            mistake_repository,
            vocabulary_repository,
        ),
        speaking_attempt_repository=SpeakingAttemptRepository(session_factory),
        user_account_repository=UserAccountRepository(session_factory),
        vocabulary_repository=vocabulary_repository,
        writing_attempt_repository=WritingAttemptRepository(session_factory),
    )


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


def build_app_runtime(
    repositories: AppRepositories,
    dependencies: AppRuntimeDependencies,
) -> AppRuntime:
    recommendation_service = RecommendationService(
        repositories.lesson_repository,
        repositories.mistake_repository,
        repositories.vocabulary_repository,
    )

    return AppRuntime(
        adaptive_study_service=AdaptiveStudyService(
            repositories.lesson_repository,
            repositories.lesson_runtime_repository,
            recommendation_service,
            repositories.mistake_repository,
            repositories.progress_repository,
            repositories.vocabulary_repository,
        ),
        diagnostic_service=DiagnosticService(
            repositories.lesson_repository,
            repositories.lesson_runtime_repository,
            repositories.progress_repository,
            repositories.mistake_repository,
        ),
        grammar_service=GrammarService(repositories.content_repository),
        lesson_runtime_service=LessonRuntimeService(
            repositories.lesson_runtime_repository,
            repositories.progress_repository,
            repositories.mistake_repository,
            dependencies.mistake_extraction_service,
        ),
        lesson_service=LessonService(repositories.lesson_repository),
        listening_service=ListeningService(repositories.listening_repository),
        mistake_service=MistakeService(repositories.mistake_repository),
        onboarding_service=OnboardingService(
            repositories.user_account_repository,
            repositories.onboarding_repository,
            dependencies.profile_service,
        ),
        profile_service=dependencies.profile_service,
        profession_service=ProfessionService(repositories.content_repository),
        progress_service=ProgressService(repositories.progress_repository),
        pronunciation_service=PronunciationService(
            repositories.content_repository,
            dependencies.stt_service,
            dependencies.provider_registry.scoring_provider,
            repositories.pronunciation_attempt_repository,
        ),
        provider_service=ProviderService(
            repositories.provider_preference_repository,
            dependencies.provider_registry,
        ),
        recommendation_service=recommendation_service,
        speaking_service=SpeakingService(
            repositories.content_repository,
            dependencies.ai_orchestrator,
            repositories.speaking_attempt_repository,
            repositories.mistake_repository,
            repositories.vocabulary_repository,
            dependencies.mistake_extraction_service,
        ),
        stt_service=dependencies.stt_service,
        user_service=UserService(repositories.user_account_repository),
        voice_service=VoiceService(dependencies.provider_registry.tts_provider),
        writing_service=WritingService(
            repositories.content_repository,
            dependencies.ai_orchestrator,
            repositories.writing_attempt_repository,
            repositories.mistake_repository,
            repositories.vocabulary_repository,
            dependencies.mistake_extraction_service,
        ),
    )
