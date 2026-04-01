from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import inspect

from app.content.bootstrap import bootstrap_content
from app.db.session import SessionLocal, engine
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


def _bootstrap_content_if_ready() -> None:
    existing_tables = set(inspect(engine).get_table_names())
    required_content_tables = {
        "lesson_templates",
        "lesson_blocks",
        "profession_topics",
        "grammar_topics",
        "profession_tracks",
        "speaking_scenarios",
        "pronunciation_drills",
        "writing_tasks",
    }
    if required_content_tables.issubset(existing_tables):
        with SessionLocal() as bootstrap_session:
            bootstrap_content(bootstrap_session)
            bootstrap_session.commit()


def build_runtime() -> AppRuntime:
    _bootstrap_content_if_ready()
    provider_registry = ProviderRegistry()

    profile_repository = ProfileRepository(SessionLocal)
    content_repository = ContentRepository(SessionLocal)
    lesson_repository = LessonRepository(SessionLocal)
    lesson_runtime_repository = LessonRuntimeRepository(SessionLocal)
    listening_repository = ListeningRepository(SessionLocal)
    progress_repository = ProgressRepository(SessionLocal, lesson_repository)
    mistake_repository = MistakeRepository(SessionLocal)
    onboarding_repository = OnboardingRepository(SessionLocal)
    user_account_repository = UserAccountRepository(SessionLocal)
    provider_preference_repository = ProviderPreferenceRepository(SessionLocal)
    speaking_attempt_repository = SpeakingAttemptRepository(SessionLocal)
    pronunciation_attempt_repository = PronunciationAttemptRepository(SessionLocal)
    writing_attempt_repository = WritingAttemptRepository(SessionLocal)
    vocabulary_repository = VocabularyRepository(SessionLocal)
    recommendation_repository = RecommendationRepository(lesson_repository, mistake_repository, vocabulary_repository)
    mistake_extraction_service = MistakeExtractionService()
    ai_orchestrator = AIOrchestrator(provider_registry.llm_provider)
    stt_service = STTService(provider_registry.stt_provider)

    profile_bootstrap_service = ProfileBootstrapService(SessionLocal)
    profile_service = ProfileService(profile_repository, profile_bootstrap_service)

    return AppRuntime(
        adaptive_study_service=AdaptiveStudyService(
            lesson_repository,
            lesson_runtime_repository,
            recommendation_repository,
            mistake_repository,
            progress_repository,
            vocabulary_repository,
        ),
        diagnostic_service=DiagnosticService(
            lesson_repository,
            lesson_runtime_repository,
            progress_repository,
            mistake_repository,
        ),
        grammar_service=GrammarService(content_repository),
        lesson_runtime_service=LessonRuntimeService(
            lesson_runtime_repository,
            progress_repository,
            mistake_repository,
            mistake_extraction_service,
        ),
        lesson_service=LessonService(lesson_repository),
        listening_service=ListeningService(listening_repository),
        mistake_service=MistakeService(mistake_repository),
        onboarding_service=OnboardingService(user_account_repository, onboarding_repository, profile_service),
        profile_service=profile_service,
        profession_service=ProfessionService(content_repository),
        progress_service=ProgressService(progress_repository),
        pronunciation_service=PronunciationService(
            content_repository,
            stt_service,
            provider_registry.scoring_provider,
            pronunciation_attempt_repository,
        ),
        provider_service=ProviderService(provider_preference_repository, provider_registry),
        recommendation_service=RecommendationService(recommendation_repository),
        speaking_service=SpeakingService(
            content_repository,
            ai_orchestrator,
            speaking_attempt_repository,
            mistake_repository,
            vocabulary_repository,
            mistake_extraction_service,
        ),
        stt_service=stt_service,
        user_service=UserService(user_account_repository),
        voice_service=VoiceService(provider_registry.tts_provider),
        writing_service=WritingService(
            content_repository,
            ai_orchestrator,
            writing_attempt_repository,
            mistake_repository,
            vocabulary_repository,
            mistake_extraction_service,
        ),
    )
