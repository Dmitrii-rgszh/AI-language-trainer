from fastapi import APIRouter, Depends

from app.api.dependencies import require_profile
from app.core.dependencies import journey_service
from app.schemas.journey import (
    CompleteTaskDrivenStepRequest,
    CompleteRouteReentrySupportStepRequest,
    LearnerJourneyState,
    OnboardingSession,
    RegisterRitualSignalRequest,
    RegisterRouteEntryRequest,
    SaveOnboardingSessionDraftRequest,
    StartOnboardingSessionRequest,
)
from app.schemas.profile import UserProfile

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


@router.post("/reentry-support-step", response_model=LearnerJourneyState)
def complete_route_reentry_support_step(
    payload: CompleteRouteReentrySupportStepRequest,
    profile: UserProfile = Depends(require_profile),
) -> LearnerJourneyState:
    return journey_service.register_route_reentry_support_step(
        profile=profile,
        route=payload.route,
    )


@router.post("/task-driven-step", response_model=LearnerJourneyState)
def complete_task_driven_step(
    payload: CompleteTaskDrivenStepRequest,
    profile: UserProfile = Depends(require_profile),
) -> LearnerJourneyState:
    return journey_service.register_task_driven_step(
        profile=profile,
        input_route=payload.input_route,
        response_route=payload.response_route,
    )


@router.post("/route-entry", response_model=LearnerJourneyState)
def register_route_entry(
    payload: RegisterRouteEntryRequest,
    profile: UserProfile = Depends(require_profile),
) -> LearnerJourneyState:
    return journey_service.register_route_entry(
        profile=profile,
        route=payload.route,
        source=payload.source,
    )


@router.post("/ritual-signal", response_model=LearnerJourneyState)
def register_ritual_signal(
    payload: RegisterRitualSignalRequest,
    profile: UserProfile = Depends(require_profile),
) -> LearnerJourneyState:
    return journey_service.register_ritual_signal(
        profile=profile,
        signal_type=payload.signal_type,
        route=payload.route,
        label=payload.label,
        summary=payload.summary,
    )
