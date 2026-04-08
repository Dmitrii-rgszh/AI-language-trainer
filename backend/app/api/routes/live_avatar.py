from fastapi import APIRouter, Request, WebSocket
from fastapi.responses import FileResponse

from app.core.errors import NotFoundError
from app.core.config import BACKEND_DIR
from app.core.config import settings
from app.core.dependencies import live_avatar_service
from app.schemas.live_avatar import (
    LiveAvatarConfigResponse,
    LiveAvatarFallbackRequest,
    LiveAvatarFallbackResponse,
    LiveAvatarStatusResponse,
)

router = APIRouter(prefix="/live-avatar", tags=["live-avatar"])


@router.get("/config", response_model=LiveAvatarConfigResponse)
def get_live_avatar_config(request: Request) -> LiveAvatarConfigResponse:
    signaling_scheme = "wss" if request.url.scheme == "https" else "ws"
    signaling_url = str(request.base_url.replace(scheme=signaling_scheme)).rstrip("/") + f"{settings.api_prefix}/live-avatar/ws"
    return live_avatar_service.get_client_config(signaling_url=signaling_url)


@router.get("/status", response_model=LiveAvatarStatusResponse)
def get_live_avatar_status() -> LiveAvatarStatusResponse:
    return live_avatar_service.get_status()


@router.post("/fallback-render", response_model=LiveAvatarFallbackResponse)
def render_live_avatar_fallback(payload: LiveAvatarFallbackRequest) -> LiveAvatarFallbackResponse:
    result = live_avatar_service.render_fallback_response(
        user_text=payload.user_text,
        language=payload.language,
        avatar_key=payload.avatar_key,
    )
    clip_id = result.clip_path.stem
    return LiveAvatarFallbackResponse(
        transcript=result.transcript,
        assistant_text=result.assistant_text,
        clip_id=clip_id,
        clip_url=f"/api/live-avatar/fallback-render/{clip_id}",
    )


@router.get("/fallback-render/{clip_id}")
def get_live_avatar_fallback_clip(clip_id: str) -> FileResponse:
    clip_path = BACKEND_DIR / "generated" / "musetalk" / settings.musetalk_version / f"{clip_id}.mp4"
    if not clip_path.exists():
        raise NotFoundError(f"Fallback clip was not found: {clip_id}")
    return FileResponse(clip_path, media_type="video/mp4", filename=clip_path.name)


@router.get("/idle-loop")
def get_live_avatar_idle_loop(avatar_key: str | None = None) -> FileResponse:
    try:
        idle_loop_path = live_avatar_service.get_idle_loop_path(avatar_key=avatar_key)
    except ValueError as exc:
        raise NotFoundError(str(exc)) from exc
    if not idle_loop_path.exists():
        raise NotFoundError(f"Idle loop was not found for avatar: {avatar_key or settings.live_avatar_default_avatar_key}")
    return FileResponse(
        idle_loop_path,
        media_type="video/mp4",
        filename=idle_loop_path.name,
        headers={"Cache-Control": "no-store, no-cache, must-revalidate"},
    )


@router.get("/presence-video")
def get_live_avatar_presence_video(avatar_key: str | None = None) -> FileResponse:
    try:
        presence_video_path = live_avatar_service.get_presence_video_path(avatar_key=avatar_key)
    except ValueError as exc:
        raise NotFoundError(str(exc)) from exc
    except FileNotFoundError as exc:
        raise NotFoundError(str(exc)) from exc
    if not presence_video_path.exists():
        raise NotFoundError(
            f"Presence video was not found for avatar: {avatar_key or settings.live_avatar_default_avatar_key}"
        )
    return FileResponse(
        presence_video_path,
        media_type="video/mp4",
        filename=presence_video_path.name,
        headers={"Cache-Control": "no-store, no-cache, must-revalidate"},
    )


@router.websocket("/ws")
async def live_avatar_signaling(websocket: WebSocket) -> None:
    session = await live_avatar_service.create_session(websocket)
    try:
        await session.run()
    finally:
        await live_avatar_service.close_session(session.session_id)
