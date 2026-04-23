from app.repositories.journey_repository import JourneyRepository
from app.repositories.lesson_repository import LessonRepository
from app.repositories.lesson_runtime_repository import LessonRuntimeRepository
from app.repositories.mistake_repository import MistakeRepository
from app.repositories.profile_repository import ProfileRepository
from app.repositories.progress_repository import ProgressRepository
from app.repositories.recommendation_repository import RecommendationRepository
from app.repositories.vocabulary_repository import VocabularyRepository
from app.services.adaptive_study_service.service import AdaptiveStudyService
from app.services.journey_service.service import JourneyService
from app.services.recommendation_service.service import RecommendationService


def test_word_journal_capture_feeds_vocabulary_hub_and_daily_ritual(seeded_session_factory) -> None:
    profile_repository = ProfileRepository(seeded_session_factory)
    lesson_repository = LessonRepository(seeded_session_factory)
    lesson_runtime_repository = LessonRuntimeRepository(seeded_session_factory)
    mistake_repository = MistakeRepository(seeded_session_factory)
    progress_repository = ProgressRepository(seeded_session_factory, lesson_repository)
    vocabulary_repository = VocabularyRepository(seeded_session_factory)
    journey_repository = JourneyRepository(seeded_session_factory)
    recommendation_repository = RecommendationRepository(
        lesson_repository,
        mistake_repository,
        vocabulary_repository,
        progress_repository,
        journey_repository,
    )
    adaptive_service = AdaptiveStudyService(
        lesson_repository,
        lesson_runtime_repository,
        recommendation_repository,
        mistake_repository,
        progress_repository,
        vocabulary_repository,
        journey_repository,
    )
    recommendation_service = RecommendationService(
        lesson_repository,
        mistake_repository,
        vocabulary_repository,
        journey_repository=journey_repository,
    )
    journey_service = JourneyService(
        journey_repository,
        lesson_repository,
        lesson_runtime_repository,
        recommendation_service,
        mistake_repository,
        vocabulary_repository,
        progress_repository,
    )

    saved_profile = profile_repository.get_profile("user-local-1")
    assert saved_profile is not None
    profile = saved_profile.model_copy(
        update={
            "onboarding_answers": saved_profile.onboarding_answers.model_copy(
                update={"ritual_elements": ["daily_word_journal", "gentle_daily_consistency"]}
            )
        }
    )

    captured = adaptive_service.capture_word_journal(
        profile.id,
        phrase="keep it light",
        translation="держать это легко",
        context="A real-life phrase to reuse in speaking and writing after reading You & English.",
    )

    assert captured.source_module == "word_journal"
    assert captured.category == "word_journal"
    assert "daily word journal" in captured.review_reason.lower()

    hub = adaptive_service.get_vocabulary_hub(profile.id)
    assert any(item.word == "keep it light" for item in hub.journal_items)
    assert any(item.source_module == "word_journal" for item in hub.due_items)

    plan = journey_service.get_today_plan(profile)

    assert plan.ritual is not None
    assert "word journal" in plan.ritual.promise.lower()
