from __future__ import annotations

from app.core.app_runtime_types import AppRepositories, AppRuntime, AppRuntimeDependencies
from app.core.config import settings
from app.live_avatar.avatar.avatar_profile import load_avatar_asset_profile_from_settings
from app.live_avatar.dialogue.service import LiveAvatarDialogueService
from app.live_avatar.lipsync.musetalk.engine import MuseTalkLiveEngine
from app.live_avatar.tts.qwen3.engine import Qwen3LiveTTSAdapter
from app.services.adaptive_study_service.service import AdaptiveStudyService
from app.services.diagnostic_service.service import DiagnosticService
from app.services.grammar_service.service import GrammarService
from app.services.journey_service.service import JourneyService
from app.services.lesson_runtime_service.service import LessonRuntimeService
from app.services.lesson_service.service import LessonService
from app.services.listening_service.service import ListeningService
from app.services.live_avatar_service.service import LiveAvatarService
from app.services.mistake_service.service import MistakeService
from app.services.onboarding_service.service import OnboardingService
from app.services.pronunciation_service.service import PronunciationService
from app.services.profession_service.service import ProfessionService
from app.services.progress_service.service import ProgressService
from app.services.provider_service.service import ProviderService
from app.services.recommendation_service.service import RecommendationService
from app.services.speaking_service.service import SpeakingService
from app.services.user_service.service import UserService
from app.services.welcome_tutor_service.service import WelcomeTutorService
from app.services.voice_service.service import VoiceService
from app.services.writing_service.service import WritingService


def build_app_runtime(
    repositories: AppRepositories,
    dependencies: AppRuntimeDependencies,
) -> AppRuntime:
    voice_service = VoiceService(dependencies.provider_registry.tts_provider)
    welcome_tutor_service = WelcomeTutorService(voice_service)
    dialogue_service = LiveAvatarDialogueService(dependencies.provider_registry.llm_provider)
    live_tts_adapter = Qwen3LiveTTSAdapter()
    live_lipsync_engine = MuseTalkLiveEngine()
    live_avatar_profile = load_avatar_asset_profile_from_settings(
        avatar_key=settings.live_avatar_default_avatar_key,
    )
    recommendation_service = RecommendationService(
        repositories.lesson_repository,
        repositories.mistake_repository,
        repositories.vocabulary_repository,
        repositories.progress_repository,
        repositories.journey_repository,
    )
    journey_service = JourneyService(
        repositories.journey_repository,
        repositories.lesson_repository,
        repositories.lesson_runtime_repository,
        recommendation_service,
        repositories.mistake_repository,
        repositories.vocabulary_repository,
        repositories.progress_repository,
    )

    return AppRuntime(
        adaptive_study_service=AdaptiveStudyService(
            repositories.lesson_repository,
            repositories.lesson_runtime_repository,
            recommendation_service,
            repositories.mistake_repository,
            repositories.progress_repository,
            repositories.vocabulary_repository,
            repositories.journey_repository,
        ),
        diagnostic_service=DiagnosticService(
            repositories.lesson_repository,
            repositories.lesson_runtime_repository,
            repositories.progress_repository,
            repositories.mistake_repository,
        ),
        grammar_service=GrammarService(repositories.content_repository),
        journey_service=journey_service,
        lesson_runtime_service=LessonRuntimeService(
            repositories.lesson_runtime_repository,
            repositories.progress_repository,
            repositories.mistake_repository,
            dependencies.mistake_extraction_service,
            journey_service,
        ),
        lesson_service=LessonService(repositories.lesson_repository),
        listening_service=ListeningService(repositories.listening_repository),
        live_avatar_service=LiveAvatarService(
            dialogue_service=dialogue_service,
            tts_adapter=live_tts_adapter,
            lipsync_engine=live_lipsync_engine,
            stt_provider=dependencies.provider_registry.stt_provider,
            welcome_tutor_service=welcome_tutor_service,
            avatar_profile=live_avatar_profile,
        ),
        mistake_service=MistakeService(repositories.mistake_repository),
        onboarding_service=OnboardingService(
            repositories.user_account_repository,
            repositories.onboarding_repository,
            dependencies.profile_service,
            journey_service,
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
        welcome_tutor_service=welcome_tutor_service,
        voice_service=voice_service,
        writing_service=WritingService(
            repositories.content_repository,
            dependencies.ai_orchestrator,
            repositories.writing_attempt_repository,
            repositories.mistake_repository,
            repositories.vocabulary_repository,
            dependencies.mistake_extraction_service,
        ),
    )
