from fastapi import APIRouter, File, Form, UploadFile

from app.api.dependencies import require_profile
from app.core.dependencies import pronunciation_service
from app.schemas.content import PronunciationDrill
from app.schemas.pronunciation import PronunciationAssessment, PronunciationAttempt, PronunciationTrend

router = APIRouter(prefix="/pronunciation", tags=["pronunciation"])


@router.get("/drills", response_model=list[PronunciationDrill])
def get_pronunciation_drills() -> list[PronunciationDrill]:
    return pronunciation_service.get_drills()


@router.get("/attempts", response_model=list[PronunciationAttempt])
def get_pronunciation_attempts() -> list[PronunciationAttempt]:
    return pronunciation_service.list_attempts(require_profile().id)


@router.get("/trends", response_model=PronunciationTrend)
def get_pronunciation_trends() -> PronunciationTrend:
    return pronunciation_service.get_trends(require_profile().id)


@router.post("/assess", response_model=PronunciationAssessment)
async def assess_pronunciation(
    target_text: str = Form(...),
    drill_id: str | None = Form(None),
    sound_focus: str | None = Form(None),
    audio: UploadFile = File(...),
) -> PronunciationAssessment:
    return await pronunciation_service.assess_upload(
        user_id=require_profile().id,
        target_text=target_text,
        drill_id=drill_id,
        sound_focus=sound_focus,
        audio=audio,
    )
