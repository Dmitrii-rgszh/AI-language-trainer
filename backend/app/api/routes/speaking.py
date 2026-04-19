from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.api.dependencies import require_profile
from app.core.dependencies import speaking_service, stt_service
from app.schemas.content import SpeakingScenario
from app.schemas.feedback import AITextFeedback, SpeakingAttempt, SpeakingFeedbackRequest, SpeakingVoiceFeedback
from app.schemas.profile import UserProfile

router = APIRouter(prefix="/speaking", tags=["speaking"])


@router.get("/scenarios", response_model=list[SpeakingScenario])
def get_speaking_scenarios() -> list[SpeakingScenario]:
    return speaking_service.get_scenarios()


@router.post("/feedback", response_model=AITextFeedback)
def get_speaking_feedback(
    payload: SpeakingFeedbackRequest,
    profile: UserProfile = Depends(require_profile),
) -> AITextFeedback:
    return speaking_service.get_feedback(
        user_id=profile.id,
        scenario_id=payload.scenario_id,
        transcript=payload.transcript,
        feedback_language=payload.feedback_language,
        input_mode="text",
    )


@router.post("/voice-feedback", response_model=SpeakingVoiceFeedback)
async def get_speaking_voice_feedback(
    scenario_id: str = Form(...),
    feedback_language: str = Form("ru"),
    audio: UploadFile = File(...),
    profile: UserProfile = Depends(require_profile),
) -> SpeakingVoiceFeedback:
    transcript = await stt_service.transcribe_upload(audio)
    feedback = speaking_service.get_feedback(
        user_id=profile.id,
        scenario_id=scenario_id,
        transcript=transcript,
        feedback_language=feedback_language,
        input_mode="voice",
    )
    return SpeakingVoiceFeedback(transcript=transcript, feedback=feedback)


@router.get("/attempts", response_model=list[SpeakingAttempt])
def get_speaking_attempts(profile: UserProfile = Depends(require_profile)) -> list[SpeakingAttempt]:
    return speaking_service.list_attempts(profile.id)
