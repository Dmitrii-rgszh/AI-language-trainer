from app.repositories.onboarding_repository import OnboardingRepository
from app.repositories.user_account_repository import UserAccountRepository
from app.schemas.onboarding import CompleteOnboardingRequest, CompleteOnboardingResponse, UserOnboarding
from app.services.profile_service.service import ProfileService


class OnboardingService:
    def __init__(
        self,
        user_repository: UserAccountRepository,
        onboarding_repository: OnboardingRepository,
        profile_service: ProfileService,
    ) -> None:
        self._user_repository = user_repository
        self._onboarding_repository = onboarding_repository
        self._profile_service = profile_service

    def get_onboarding(self, user_id: str) -> UserOnboarding | None:
        return self._onboarding_repository.get_onboarding(user_id)

    def complete_onboarding(self, payload: CompleteOnboardingRequest) -> CompleteOnboardingResponse:
        user = self._user_repository.resolve_user(payload.login, payload.email)
        onboarding = self._onboarding_repository.upsert_onboarding(user.id, payload.profile.onboarding_answers)
        profile = self._profile_service.update_profile(user.id, payload.profile)
        return CompleteOnboardingResponse(user=user, onboarding=onboarding, profile=profile)
