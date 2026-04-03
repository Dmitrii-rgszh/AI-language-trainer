from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path

from app.core.config import settings
from app.live_avatar.dialogue.service import LiveAvatarDialogueService
from app.live_avatar.lipsync.musetalk.engine import MuseTalkLiveEngine
from app.live_avatar.rtc.session_manager import LiveAvatarSessionManager
from app.live_avatar.tts.qwen3.engine import Qwen3LiveTTSAdapter
from app.schemas.live_avatar import LiveAvatarConfigResponse, LiveAvatarIceServer, LiveAvatarStatusResponse
from app.services.welcome_tutor_service.service import WelcomeTutorService

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LiveAvatarFallbackRenderResult:
    transcript: str
    assistant_text: str
    clip_path: Path


class LiveAvatarService:
    def __init__(
        self,
        *,
        dialogue_service: LiveAvatarDialogueService,
        tts_adapter: Qwen3LiveTTSAdapter,
        lipsync_engine: MuseTalkLiveEngine,
        stt_provider,
        welcome_tutor_service: WelcomeTutorService,
    ) -> None:
        self._dialogue_service = dialogue_service
        self._tts_adapter = tts_adapter
        self._lipsync_engine = lipsync_engine
        self._welcome_tutor_service = welcome_tutor_service
        self._session_manager = LiveAvatarSessionManager(
            dialogue_service=dialogue_service,
            tts_adapter=tts_adapter,
            lipsync_engine=lipsync_engine,
            stt_provider=stt_provider,
        )
        self._warmup_error: str | None = None

    async def warmup(self) -> None:
        if not settings.live_avatar_enabled:
            self._warmup_error = "Live avatar mode is disabled in configuration."
            return

        try:
            await asyncio.to_thread(self._tts_adapter.warmup)
            await self._lipsync_engine.warmup()
            self._warmup_error = None
        except Exception as exc:
            self._warmup_error = str(exc)
            logger.warning("Live avatar warmup failed: %s", exc)

    def get_client_config(self, *, signaling_url: str) -> LiveAvatarConfigResponse:
        return LiveAvatarConfigResponse(
            enabled=settings.live_avatar_enabled,
            signaling_path=f"{settings.api_prefix}/live-avatar/ws",
            signaling_url=signaling_url,
            default_avatar_key=settings.live_avatar_default_avatar_key,
            default_voice_profile_id=settings.live_avatar_default_voice_profile_id,
            fallback_mode_available=True,
            ice_servers=self._build_ice_servers(),
            details="Live avatar mode uses WebRTC with Qwen3-TTS and MuseTalk streaming adapters.",
        )

    def get_status(self) -> LiveAvatarStatusResponse:
        if not settings.live_avatar_enabled:
            return LiveAvatarStatusResponse(
                enabled=False,
                ready=False,
                mode="disabled",
                details="Live avatar mode is disabled in configuration.",
            )

        tts_ready, tts_detail = self._tts_adapter.check_health()
        lipsync_ready, lipsync_detail = self._lipsync_engine.check_health()
        if tts_ready and lipsync_ready:
            return LiveAvatarStatusResponse(
                enabled=True,
                ready=True,
                mode="live",
                details="Live avatar signaling and streaming runtimes are ready.",
            )

        fallback_details = " ".join(
            detail for ready, detail in ((tts_ready, tts_detail), (lipsync_ready, lipsync_detail)) if not ready
        ).strip()
        if self._warmup_error:
            fallback_details = f"{fallback_details} Warmup: {self._warmup_error}".strip()

        return LiveAvatarStatusResponse(
            enabled=True,
            ready=False,
            mode="fallback",
            details=fallback_details or "Live avatar is not ready. Fallback render mode is available.",
        )

    async def create_session(self, websocket):
        return await self._session_manager.create_session(websocket)

    async def close_session(self, session_id: str) -> None:
        await self._session_manager.close_session(session_id)

    async def shutdown(self) -> None:
        await self._session_manager.shutdown()

    def render_fallback_response(
        self,
        *,
        user_text: str,
        language: str,
        avatar_key: str,
    ) -> LiveAvatarFallbackRenderResult:
        assistant_text = self._dialogue_service.generate_reply(user_text=user_text, language=language)
        clip_path = self._welcome_tutor_service.render_clip(
            text=assistant_text,
            language=language,
            avatar_key=avatar_key,
        )
        return LiveAvatarFallbackRenderResult(
            transcript=user_text.strip(),
            assistant_text=assistant_text,
            clip_path=clip_path,
        )

    @staticmethod
    def _build_ice_servers() -> list[LiveAvatarIceServer]:
        servers: list[LiveAvatarIceServer] = []
        if settings.webrtc_stun_urls:
            servers.append(LiveAvatarIceServer(urls=settings.webrtc_stun_urls))
        if settings.webrtc_turn_urls:
            servers.append(
                LiveAvatarIceServer(
                    urls=settings.webrtc_turn_urls,
                    username=settings.webrtc_turn_username or None,
                    credential=settings.webrtc_turn_password or None,
                )
            )
        return servers
