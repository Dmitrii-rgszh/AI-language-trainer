from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import require_active_user_id
from app.core.dependencies import onboarding_service
from app.repositories.user_account_repository import UserIdentityConflictError
from app.schemas.onboarding import CompleteOnboardingRequest, CompleteOnboardingResponse, UserOnboarding

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@router.get("/current", response_model=UserOnboarding)
def get_current_onboarding(user_id: Annotated[str, Depends(require_active_user_id)]) -> UserOnboarding:
    onboarding = onboarding_service.get_onboarding(user_id)
    if not onboarding:
        raise HTTPException(status_code=404, detail="Onboarding is not initialized.")

    return onboarding


@router.post("/complete", response_model=CompleteOnboardingResponse)
def complete_onboarding(payload: CompleteOnboardingRequest) -> CompleteOnboardingResponse:
    try:
        return onboarding_service.complete_onboarding(payload)
    except UserIdentityConflictError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
