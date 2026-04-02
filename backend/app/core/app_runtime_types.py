from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

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
from app.services.profile_service.service import ProfileService
from app.services.profession_service.service import ProfessionService
from app.services.progress_service.service import ProgressService
from app.services.provider_service.service import ProviderService
from app.services.recommendation_service.service import RecommendationService
from app.services.speaking_service.service import SpeakingService
from app.services.stt_service.service import STTService
from app.services.user_service.service import UserService
from app.services.welcome_tutor_service.service import WelcomeTutorService
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
    welcome_tutor_service: WelcomeTutorService
    voice_service: VoiceService
    writing_service: WritingService
