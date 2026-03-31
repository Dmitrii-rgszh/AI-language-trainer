from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session, sessionmaker

from app.content.bootstrap import bootstrap_content
from app.db.session import SessionLocal
from app.models.user_account import UserAccount as UserAccountModel
from app.models.user_onboarding import UserOnboarding as UserOnboardingModel
from app.models.user_profile import UserProfile as UserProfileModel
from app.schemas.blueprint import ProfessionDomain
from app.schemas.profile import OnboardingAnswers, UserProfile
from app.services.profile_bootstrap_service.service import ProfileBootstrapService


def build_seed_onboarding_answers() -> OnboardingAnswers:
    return OnboardingAnswers(
        learner_persona="professional_learner",
        age_group="adult",
        learning_context="career_growth",
        primary_goal="work_communication",
        secondary_goals=["speaking_confidence", "grammar_accuracy"],
        active_skill_focus=["speaking", "grammar", "vocabulary"],
        study_preferences=["structured_plan", "short_sessions", "gentle_feedback"],
        interest_topics=["work_and_business", "technology", "culture"],
        support_needs=["clear_examples", "confidence_support"],
        notes="Initial seeded profile for the local fullstack demo.",
    )


def seed_user(session: Session) -> UserProfileModel:
    seed_answers = build_seed_onboarding_answers()
    user_account = session.get(UserAccountModel, "user-local-1")
    if user_account is None:
        user_account = UserAccountModel(
            id="user-local-1",
            login="learner",
            email="learner@local.test",
        )
        session.add(user_account)
    else:
        user_account.login = "learner"
        user_account.email = "learner@local.test"

    onboarding = session.get(UserOnboardingModel, "onboarding-user-local-1")
    if onboarding is None:
        onboarding = UserOnboardingModel(
            id="onboarding-user-local-1",
            user_id="user-local-1",
            answers=seed_answers.model_dump(mode="json"),
            completed_at=datetime.utcnow(),
        )
        session.add(onboarding)
    else:
        onboarding.user_id = "user-local-1"
        onboarding.answers = seed_answers.model_dump(mode="json")
        onboarding.completed_at = datetime.utcnow()

    user = session.get(UserProfileModel, "user-local-1")
    if user:
        user.onboarding_answers = seed_answers.model_dump(mode="json")
        return user

    user = UserProfileModel(
        id="user-local-1",
        name="Learner",
        native_language="ru",
        current_level="A2",
        target_level="B2",
        profession_track=ProfessionDomain.TRAINER_SKILLS,
        preferred_ui_language="ru",
        preferred_explanation_language="ru",
        lesson_duration=25,
        speaking_priority=8,
        grammar_priority=7,
        profession_priority=9,
        onboarding_answers=seed_answers.model_dump(mode="json"),
    )
    session.add(user)
    session.flush()
    return user


def to_profile_schema(model: UserProfileModel) -> UserProfile:
    return UserProfile(
        id=model.id,
        name=model.name,
        native_language=model.native_language,
        current_level=model.current_level,
        target_level=model.target_level,
        profession_track=model.profession_track.value,
        preferred_ui_language=model.preferred_ui_language,
        preferred_explanation_language=model.preferred_explanation_language,
        lesson_duration=model.lesson_duration,
        speaking_priority=model.speaking_priority,
        grammar_priority=model.grammar_priority,
        profession_priority=model.profession_priority,
        onboarding_answers=model.onboarding_answers or {},
    )


def seed_runtime_data(session: Session, user: UserProfileModel, template=None) -> None:
    del template

    bind = session.get_bind()
    if bind is None:
        raise RuntimeError("A bound SQLAlchemy session is required to seed runtime data.")

    session.commit()
    session.refresh(user)

    factory = sessionmaker(bind=bind, autoflush=False, autocommit=False, future=True, class_=Session)
    ProfileBootstrapService(factory).sync_profile_runtime(to_profile_schema(user))
    session.expire_all()


def main() -> None:
    with SessionLocal() as session:
        bootstrap_content(session)
        session.flush()
        user = seed_user(session)
        session.commit()
        session.refresh(user)
        profile = to_profile_schema(user)

    ProfileBootstrapService(SessionLocal).sync_profile_runtime(profile)
    print("Profile and baseline runtime data seeded successfully.")


if __name__ == "__main__":
    main()
