from __future__ import annotations

from app.core.app_runtime_types import AppRepositories, SessionFactory
from app.db.session import SessionLocal
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
