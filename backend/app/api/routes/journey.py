from fastapi import APIRouter

from app.core.dependencies import journey_service
from app.schemas.journey import (
    OnboardingSession,
    SaveOnboardingSessionDraftRequest,
    StartOnboardingSessionRequest,
)

router = APIRouter(prefix="/journey", tags=["journey"])


@router.post("/onboarding-session", response_model=OnboardingSession)
def start_onboarding_session(payload: StartOnboardingSessionRequest) -> OnboardingSession:
    return journey_service.start_onboarding_session(payload)


@router.get("/onboarding-session/{session_id}", response_model=OnboardingSession)
def get_onboarding_session(session_id: str) -> OnboardingSession:
    return journey_service.get_onboarding_session(session_id)


@router.put("/onboarding-session/{session_id}/draft", response_model=OnboardingSession)
def save_onboarding_session_draft(
    session_id: str,
    payload: SaveOnboardingSessionDraftRequest,
) -> OnboardingSession:
    return journey_service.save_onboarding_draft(session_id, payload)
