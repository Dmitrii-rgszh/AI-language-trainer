from __future__ import annotations

from app.models.user_profile import UserProfile as UserProfileModel
from app.schemas.profile import OnboardingAnswers, UserProfile


def to_user_profile(model: UserProfileModel) -> UserProfile:
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
        onboarding_answers=OnboardingAnswers.model_validate(model.onboarding_answers or {}),
    )
