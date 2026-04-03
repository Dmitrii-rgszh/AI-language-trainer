from __future__ import annotations

import asyncio
import contextlib
import io
import tempfile
import wave
from pathlib import Path
from typing import Any
from uuid import uuid4

from aiortc import RTCIceCandidate, RTCPeerConnection, RTCSessionDescription
from aiortc.sdp import candidate_from_sdp, candidate_to_sdp
from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect

from app.core.config import settings
from app.live_avatar.audio.utterance_recorder import CapturedUtterance, UtteranceRecorder
from app.live_avatar.dialogue.service import LiveAvatarDialogueService
from app.live_avatar.rtc.ice import build_rtc_configuration
from app.live_avatar.lipsync.musetalk.engine import MuseTalkLiveEngine
from app.live_avatar.rtc.tracks import AvatarAudioTrack, AvatarVideoTrack
from app.live_avatar.tts.qwen3.engine import Qwen3LiveTTSAdapter
from app.live_avatar.tts.qwen3.voice_profile import QwenVoiceProfile
from app.providers.stt.base import BaseSTTProvider


class LiveAvatarSession:
    def __init__(
        self,
        *,
        websocket: WebSocket,
        dialogue_service: LiveAvatarDialogueService,
        tts_adapter: Qwen3LiveTTSAdapter,
        lipsync_engine: MuseTalkLiveEngine,
        stt_provider: BaseSTTProvider | None,
    ) -> None:
        self.session_id = uuid4().hex
        self._websocket = websocket
        self._dialogue_service = dialogue_service
        self._tts_adapter = tts_adapter
        self._lipsync_engine = lipsync_engine
        self._stt_provider = stt_provider
        self._peer_connection: RTCPeerConnection | None = None
        self._audio_track = AvatarAudioTrack(chunk_ms=settings.live_avatar_audio_chunk_ms)
        self._video_track = AvatarVideoTrack(
            avatar_image_path=settings.musetalk_avatar_verba_tutor_image,
            fps=settings.live_avatar_idle_video_fps,
        )
        self._recorder = UtteranceRecorder(
            start_threshold=settings.live_avatar_vad_start_threshold,
            continue_threshold=settings.live_avatar_vad_continue_threshold,
            min_speech_ms=settings.live_avatar_min_speech_ms,
            trailing_silence_ms=settings.live_avatar_trailing_silence_ms,
            max_utterance_ms=settings.live_avatar_max_utterance_ms,
            preroll_ms=settings.live_avatar_preroll_ms,
        )
        self._send_lock = asyncio.Lock()
        self._processing_lock = asyncio.Lock()
        self._consume_audio_task: asyncio.Task[None] | None = None
        self._has_input_audio_track = False
        self._closed = False

    async def accept(self) -> None:
        await self._websocket.accept()
        await self._send_json(
            {
                "type": "session-ready",
                "sessionId": self.session_id,
                "status": "connecting",
            }
        )

    async def run(self) -> None:
        try:
            while True:
                message = await self._websocket.receive_json()
                await self.handle_message(message)
        except WebSocketDisconnect:
            return
        finally:
            await self.close()

    async def handle_message(self, message: dict[str, Any]) -> None:
        message_type = str(message.get("type", "")).strip()
        if message_type == "offer":
            await self._handle_offer(message)
            return
        if message_type == "ice-candidate":
            await self._handle_ice_candidate(message)
            return
        if message_type == "force-end-turn":
            await self.force_finalize_turn()
            return
        if message_type == "speak-text":
            await self._handle_speak_text(message)
            return
        if message_type == "disconnect":
            await self.close()

    async def force_finalize_turn(self) -> None:
        utterance = self._recorder.force_finalize()
        if utterance is not None:
            asyncio.create_task(self._process_utterance(utterance))

    async def _handle_speak_text(self, message: dict[str, Any]) -> None:
        text = str(message.get("text", "")).strip()
        language = str(message.get("language", "ru")).strip() or "ru"
        if not text:
            return
        asyncio.create_task(self._speak_text(text=text, language=language))

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        if self._consume_audio_task is not None:
            self._consume_audio_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._consume_audio_task
        if self._peer_connection is not None:
            await self._peer_connection.close()

    async def _handle_offer(self, message: dict[str, Any]) -> None:
        peer_connection = await self._ensure_peer_connection()
        offer = RTCSessionDescription(sdp=message["sdp"], type="offer")
        await peer_connection.setRemoteDescription(offer)
        answer = await peer_connection.createAnswer()
        await peer_connection.setLocalDescription(answer)
        await self._send_json(
            {
                "type": "answer",
                "sdp": peer_connection.localDescription.sdp,
            }
        )
        await self._send_status("connected", "Соединение установлено")

    async def _handle_ice_candidate(self, message: dict[str, Any]) -> None:
        if self._peer_connection is None:
            return
        candidate_payload = message.get("candidate")
        if not isinstance(candidate_payload, dict):
            return
        candidate_sdp = candidate_payload.get("candidate")
        if not candidate_sdp:
            return
        candidate = candidate_from_sdp(candidate_sdp)
        candidate.sdpMid = candidate_payload.get("sdpMid")
        candidate.sdpMLineIndex = candidate_payload.get("sdpMLineIndex")
        await self._peer_connection.addIceCandidate(candidate)

    async def _ensure_peer_connection(self) -> RTCPeerConnection:
        if self._peer_connection is not None:
            return self._peer_connection

        peer_connection = RTCPeerConnection(configuration=build_rtc_configuration())
        peer_connection.addTrack(self._audio_track)
        peer_connection.addTrack(self._video_track)

        @peer_connection.on("track")
        def on_track(track: Any) -> None:
            if track.kind != "audio":
                return
            self._has_input_audio_track = True
            if self._consume_audio_task is not None:
                self._consume_audio_task.cancel()
            self._consume_audio_task = asyncio.create_task(self._consume_audio(track))

        @peer_connection.on("icecandidate")
        def on_icecandidate(candidate: RTCIceCandidate | None) -> None:
            if candidate is None:
                return
            asyncio.create_task(
                self._send_json(
                    {
                        "type": "ice-candidate",
                        "candidate": {
                            "candidate": candidate_to_sdp(candidate),
                            "sdpMid": candidate.sdpMid,
                            "sdpMLineIndex": candidate.sdpMLineIndex,
                        },
                    }
                )
            )

        @peer_connection.on("connectionstatechange")
        async def on_connectionstatechange() -> None:
            state = peer_connection.connectionState
            if state == "connected" and self._has_input_audio_track:
                await self._send_status("microphone_active", "Микрофон активен")
                await self._send_status("listening", "Слушаю…")
            elif state in {"failed", "closed", "disconnected"}:
                await self._send_status("connection_error", "Ошибка соединения")

        self._peer_connection = peer_connection
        return peer_connection

    async def _consume_audio(self, track: Any) -> None:
        await self._send_status("listening", "Слушаю…")
        while not self._closed:
            frame = await track.recv()
            if self._processing_lock.locked():
                continue

            utterance = self._recorder.process_frame(frame)
            if utterance is None:
                continue
            asyncio.create_task(self._process_utterance(utterance))

    async def _process_utterance(self, utterance: CapturedUtterance) -> None:
        if self._processing_lock.locked():
            return

        async with self._processing_lock:
            try:
                await self._send_status("processing", "Обрабатываю…")
                transcript = await asyncio.to_thread(self._transcribe_utterance, utterance)
                if not transcript:
                    await self._send_status("listening", "Слушаю…")
                    return

                await self._send_json({"type": "user-transcript", "text": transcript})
                await self._send_status("thinking", "Обрабатываю…")
                reply_text = await asyncio.to_thread(
                    self._dialogue_service.generate_reply,
                    user_text=transcript,
                    language="ru",
                )
                await self._send_json({"type": "assistant-text", "text": reply_text})
                await self._send_status("processing", "Лиза готовит голос…")

                voice_profile = self._tts_adapter.load_voice_profile(settings.live_avatar_default_voice_profile_id)
                wav_bytes = await asyncio.to_thread(
                    self._tts_adapter.synthesize,
                    reply_text,
                    voice_profile,
                    language="ru",
                )
                await self._send_status("speaking", "Лиза отвечает…")
                await self._play_response(wav_bytes=wav_bytes, voice_profile=voice_profile)
                await self._send_status("listening", "Слушаю…")
            except Exception as exc:
                await self._send_status("connection_error", f"Ошибка live-avatar: {exc}")

    async def _speak_text(self, *, text: str, language: str) -> None:
        if self._processing_lock.locked():
            return

        async with self._processing_lock:
            try:
                await self._send_json({"type": "assistant-text", "text": text})
                await self._send_status("processing", "Лиза готовит live-реплику…")
                voice_profile = self._tts_adapter.load_voice_profile(settings.live_avatar_default_voice_profile_id)
                wav_bytes = await asyncio.to_thread(
                    self._tts_adapter.synthesize,
                    text,
                    voice_profile,
                    language=language,
                )
                await self._send_status("speaking", "Лиза говорит вживую…")
                await self._play_response(wav_bytes=wav_bytes, voice_profile=voice_profile)
                await self._send_status("connected", "Соединение установлено")
            except Exception as exc:
                await self._send_status("connection_error", f"Ошибка live-avatar: {exc}")

    def _transcribe_utterance(self, utterance: CapturedUtterance) -> str:
        if self._stt_provider is None:
            return ""

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temporary_file:
            temp_path = Path(temporary_file.name)
        try:
            temp_path.write_bytes(utterance.wav_bytes)
            return self._stt_provider.transcribe(str(temp_path)).strip()
        finally:
            temp_path.unlink(missing_ok=True)

    async def _play_response(self, *, wav_bytes: bytes, voice_profile: QwenVoiceProfile) -> None:
        audio_duration_seconds = self._measure_wav_duration(wav_bytes)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temporary_file:
            temp_path = Path(temporary_file.name)
        temp_path.write_bytes(wav_bytes)
        self._audio_track.clear()
        self._video_track.clear()

        first_frame_ready = asyncio.Event()

        async def feed_video() -> None:
            try:
                await self._lipsync_engine.prepare_avatar(voice_profile.avatar_key)
                async for frame_array in self._lipsync_engine.stream_frames(
                    audio_path=temp_path.as_posix(),
                    avatar_key=voice_profile.avatar_key,
                    fps=settings.musetalk_fps,
                ):
                    await self._video_track.enqueue_frame(frame_array)
                    if not first_frame_ready.is_set():
                        first_frame_ready.set()
            except Exception:
                await self._send_status("fallback_mode", "Fallback mode")
                first_frame_ready.set()

        video_task = asyncio.create_task(feed_video())
        try:
            await asyncio.wait_for(first_frame_ready.wait(), timeout=10.0)
        except asyncio.TimeoutError:
            await self._send_status("fallback_mode", "Fallback mode")
        self._audio_track.set_response_audio(wav_bytes)
        await asyncio.sleep(audio_duration_seconds + 0.25)
        await video_task
        temp_path.unlink(missing_ok=True)

    async def _send_status(self, status: str, detail: str) -> None:
        await self._send_json({"type": "status", "status": status, "detail": detail})

    async def _send_json(self, payload: dict[str, Any]) -> None:
        if self._closed:
            return
        async with self._send_lock:
            await self._websocket.send_json(payload)

    @staticmethod
    def _measure_wav_duration(wav_bytes: bytes) -> float:
        with wave.open(io.BytesIO(wav_bytes), "rb") as wav_file:
            sample_rate = wav_file.getframerate()
            frame_count = wav_file.getnframes()
        if sample_rate <= 0:
            return 0.0
        return frame_count / sample_rate
