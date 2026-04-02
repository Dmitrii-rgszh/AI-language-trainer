from sqlalchemy import select

from app.content.bootstrap import bootstrap_content
from app.models.lesson_run import LessonRun
from app.models.mistake_record import MistakeRecord
from app.models.progress_snapshot import ProgressSnapshot
from app.models.pronunciation_attempt import PronunciationAttempt
from app.models.user_profile import UserProfile as UserProfileModel
from app.models.vocabulary_item import VocabularyItem
from app.schemas.profile import OnboardingAnswers, UserProfile
from app.services.profile_bootstrap_service.service import ProfileBootstrapService


def _build_profile() -> UserProfile:
    return UserProfile(
        id="user-bootstrap-service-1",
        name="Nina",
        native_language="ru",
        current_level="B1",
        target_level="B2",
        profession_track="trainer_skills",
        preferred_ui_language="ru",
        preferred_explanation_language="ru",
        lesson_duration=20,
        speaking_priority=7,
        grammar_priority=6,
        profession_priority=8,
        onboarding_answers=OnboardingAnswers(),
    )


def test_profile_bootstrap_service_syncs_missing_runtime_data(empty_session_factory) -> None:
    profile = _build_profile()

    with empty_session_factory() as session:
        bootstrap_content(session)
        session.add(
            UserProfileModel(
                id=profile.id,
                name=profile.name,
                native_language=profile.native_language,
                current_level=profile.current_level,
                target_level=profile.target_level,
                profession_track=profile.profession_track,
                preferred_ui_language=profile.preferred_ui_language,
                preferred_explanation_language=profile.preferred_explanation_language,
                lesson_duration=profile.lesson_duration,
                speaking_priority=profile.speaking_priority,
                grammar_priority=profile.grammar_priority,
                profession_priority=profile.profession_priority,
                onboarding_answers=profile.onboarding_answers.model_dump(mode="json"),
            )
        )
        session.commit()

    service = ProfileBootstrapService(empty_session_factory)
    service.sync_profile_runtime(profile)

    with empty_session_factory() as session:
        runs = session.scalars(select(LessonRun).where(LessonRun.user_id == profile.id)).all()
        mistakes = session.scalars(select(MistakeRecord).where(MistakeRecord.user_id == profile.id)).all()
        snapshots = session.scalars(select(ProgressSnapshot).where(ProgressSnapshot.user_id == profile.id)).all()
        vocabulary = session.scalars(select(VocabularyItem).where(VocabularyItem.user_id == profile.id)).all()
        attempts = session.scalars(
            select(PronunciationAttempt).where(PronunciationAttempt.user_id == profile.id)
        ).all()

    assert len(runs) == 1
    assert runs[0].recommended_by == "profile_bootstrap"
    assert len(mistakes) == 2
    assert len(snapshots) == 1
    assert len(vocabulary) >= 1
    assert len(attempts) == 1
