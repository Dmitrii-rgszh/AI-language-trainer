from __future__ import annotations

from sqlalchemy.orm import Session

from app.content.bootstrap import bootstrap_content
from app.db.session import SessionLocal
from app.models.user_profile import UserProfile as UserProfileModel
from app.schemas.blueprint import ProfessionDomain
from app.schemas.profile import UserProfile
from app.services.profile_bootstrap_service.service import ProfileBootstrapService


def seed_user(session: Session) -> UserProfileModel:
    user = session.get(UserProfileModel, "user-local-1")
    if user:
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
    )


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
