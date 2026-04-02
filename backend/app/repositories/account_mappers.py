from __future__ import annotations

from app.models.user_account import UserAccount as UserAccountModel
from app.models.user_onboarding import UserOnboarding as UserOnboardingModel
from app.models.user_provider_preference import UserProviderPreference as UserProviderPreferenceModel
from app.schemas.onboarding import UserOnboarding
from app.schemas.profile import OnboardingAnswers
from app.schemas.provider import ProviderPreference
from app.schemas.user_account import UserAccount


def to_provider_preference(model: UserProviderPreferenceModel) -> ProviderPreference:
    return ProviderPreference(
        provider_type=model.provider_type.value,
        selected_provider=model.selected_provider,
        enabled=model.enabled,
        settings=model.settings or {},
    )


def to_user_account(model: UserAccountModel) -> UserAccount:
    return UserAccount(
        id=model.id,
        login=model.login,
        email=model.email,
        created_at=model.created_at.isoformat(),
        updated_at=model.updated_at.isoformat(),
    )


def to_user_onboarding(model: UserOnboardingModel) -> UserOnboarding:
    return UserOnboarding(
        id=model.id,
        user_id=model.user_id,
        answers=OnboardingAnswers.model_validate(model.answers or {}),
        completed_at=model.completed_at.isoformat(),
        created_at=model.created_at.isoformat(),
        updated_at=model.updated_at.isoformat(),
    )
