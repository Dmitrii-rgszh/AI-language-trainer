from __future__ import annotations

from app.live_avatar.dialogue.service import LiveAvatarDialogueService
from app.live_avatar.lipsync.musetalk.engine import MuseTalkLiveEngine
from app.live_avatar.rtc.session import LiveAvatarSession
from app.live_avatar.tts.qwen3.engine import Qwen3LiveTTSAdapter
from app.providers.stt.base import BaseSTTProvider
from app.live_avatar.avatar.avatar_profile import AvatarAssetProfile


class LiveAvatarSessionManager:
    def __init__(
        self,
        *,
        dialogue_service: LiveAvatarDialogueService,
        tts_adapter: Qwen3LiveTTSAdapter,
        lipsync_engine: MuseTalkLiveEngine,
        stt_provider: BaseSTTProvider | None,
        avatar_profile: AvatarAssetProfile,
    ) -> None:
        self._dialogue_service = dialogue_service
        self._tts_adapter = tts_adapter
        self._lipsync_engine = lipsync_engine
        self._stt_provider = stt_provider
        self._avatar_profile = avatar_profile
        self._sessions: dict[str, LiveAvatarSession] = {}

    async def create_session(self, websocket) -> LiveAvatarSession:
        session = LiveAvatarSession(
            websocket=websocket,
            dialogue_service=self._dialogue_service,
            tts_adapter=self._tts_adapter,
            lipsync_engine=self._lipsync_engine,
            stt_provider=self._stt_provider,
            avatar_profile=self._avatar_profile,
        )
        self._sessions[session.session_id] = session
        await session.accept()
        return session

    async def close_session(self, session_id: str) -> None:
        session = self._sessions.pop(session_id, None)
        if session is not None:
            await session.close()

    async def shutdown(self) -> None:
        for session_id in list(self._sessions):
            await self.close_session(session_id)
