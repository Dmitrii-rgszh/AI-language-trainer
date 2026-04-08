from fastapi import APIRouter, Query
from fastapi.responses import FileResponse

from app.core.dependencies import welcome_tutor_service
from app.schemas.avatar_lipsync import WelcomeTutorClipRequest, WelcomeTutorStatusResponse

router = APIRouter(prefix="/welcome", tags=["welcome"])


@router.get("/ai-tutor/status", response_model=WelcomeTutorStatusResponse)
def get_welcome_ai_tutor_status() -> WelcomeTutorStatusResponse:
    status = welcome_tutor_service.get_status()
    return WelcomeTutorStatusResponse(
        available=status.available,
        mode="musetalk" if status.available else "fallback",
        details=status.details,
    )


@router.post("/ai-tutor/video")
def render_welcome_ai_tutor_video(payload: WelcomeTutorClipRequest) -> FileResponse:
    clip_path = welcome_tutor_service.render_clip(
        text=payload.text,
        language=payload.language,
        avatar_key=payload.avatar_key,
    )
    return FileResponse(
        clip_path,
        media_type="video/mp4",
        filename=clip_path.name,
    )


@router.get("/ai-tutor/preset-video")
def get_welcome_ai_tutor_preset_video(
    locale: str = Query(default="ru"),
    kind: str = Query(default="intro"),
    variant: int = Query(default=0, ge=0),
    rev: str | None = Query(default=None),
) -> FileResponse:
    clip_path = welcome_tutor_service.ensure_preset_clip(
        locale=locale,
        kind=kind,
        variant=variant,
        avatar_key="verba_tutor",
    )
    return FileResponse(
        clip_path,
        media_type="video/mp4",
        filename=clip_path.name,
        headers={"Cache-Control": "public, max-age=31536000, immutable"},
    )
