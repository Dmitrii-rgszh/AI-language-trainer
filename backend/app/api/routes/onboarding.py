from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import require_active_user_id
from app.core.dependencies import onboarding_service
from app.schemas.onboarding import CompleteOnboardingRequest, CompleteOnboardingResponse, UserOnboarding

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@router.get("/current", response_model=UserOnboarding)
def get_current_onboarding(user_id: Annotated[str, Depends(require_active_user_id)]) -> UserOnboarding:
    return onboarding_service.get_onboarding(user_id)


@router.post("/complete", response_model=CompleteOnboardingResponse)
def complete_onboarding(payload: CompleteOnboardingRequest) -> CompleteOnboardingResponse:
    return onboarding_service.complete_onboarding(payload)
