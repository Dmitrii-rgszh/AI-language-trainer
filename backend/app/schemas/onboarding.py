from .base import ApiModel
from .profile import OnboardingAnswers, ProfileUpdateRequest, UserProfile
from .user_account import UserAccount


class UserOnboarding(ApiModel):
    id: str
    user_id: str
    answers: OnboardingAnswers
    completed_at: str
    created_at: str
    updated_at: str


class CompleteOnboardingRequest(ApiModel):
    login: str
    email: str
    session_id: str | None = None
    profile: ProfileUpdateRequest


class CompleteOnboardingResponse(ApiModel):
    user: UserAccount
    onboarding: UserOnboarding
    profile: UserProfile
