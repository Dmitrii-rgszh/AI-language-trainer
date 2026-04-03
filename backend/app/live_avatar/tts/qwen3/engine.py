from __future__ import annotations

import hashlib
from collections.abc import Iterator

import httpx

from app.core.config import settings
from app.live_avatar.tts.qwen3.streaming import WavAudioChunk, iter_wav_audio_chunks
from app.live_avatar.tts.qwen3.voice_profile import QwenVoiceProfile
from app.providers.tts.qwen3_tts_provider import Qwen3TTSProvider


class Qwen3LiveTTSAdapter:
    def __init__(self) -> None:
        self._base_url = settings.qwen_tts_base_url.rstrip("/")
        self._timeout_seconds = settings.qwen_tts_timeout_seconds
        self._profiles: dict[str, QwenVoiceProfile] = {}
        self.register_voice_profile(
            profile_id=settings.live_avatar_default_voice_profile_id,
            display_name=settings.live_avatar_default_voice_name,
            reference_audio=settings.qwen_tts_ref_audio_path or settings.qwen_tts_reference_wav,
            reference_text=settings.qwen_tts_ref_text or settings.qwen_tts_reference_text or None,
            reference_text_file=settings.qwen_tts_reference_text_file or None,
            avatar_key=settings.live_avatar_default_avatar_key,
            language="ru",
        )

    def warmup(self) -> None:
        with httpx.Client(timeout=5.0) as client:
            response = client.get(f"{self._base_url}/health")
            response.raise_for_status()

    def check_health(self) -> tuple[bool, str]:
        try:
            self.warmup()
        except Exception as exc:
            return False, f"Qwen3-TTS runtime is unavailable: {exc}"
        return True, "Qwen3-TTS runtime is ready."

    def register_voice_profile(
        self,
        *,
        profile_id: str,
        display_name: str,
        reference_audio: str,
        reference_text: str | None = None,
        reference_text_file: str | None = None,
        avatar_key: str = "verba_tutor",
        language: str = "ru",
    ) -> QwenVoiceProfile:
        profile = QwenVoiceProfile(
            profile_id=profile_id,
            display_name=display_name,
            reference_audio_path=reference_audio,
            reference_text=reference_text,
            reference_text_file=reference_text_file,
            avatar_key=avatar_key,
            language=language,
            temperature=settings.qwen_tts_temperature,
            top_p=settings.qwen_tts_top_p,
            top_k=settings.qwen_tts_top_k,
            repetition_penalty=settings.qwen_tts_repetition_penalty,
            max_new_tokens=settings.qwen_tts_max_new_tokens,
            sample_rate=settings.qwen_tts_sample_rate,
        )
        self._profiles[profile_id] = profile
        return profile

    def load_voice_profile(self, profile_id: str) -> QwenVoiceProfile:
        return self._profiles[profile_id]

    def synthesize(
        self,
        text: str,
        voice_profile: QwenVoiceProfile,
        *,
        language: str | None = None,
    ) -> bytes:
        reference_text = self._resolve_reference_text(voice_profile)
        payload = {
            "text": text.strip(),
            "language": Qwen3TTSProvider._map_language(language or voice_profile.language),
            "ref_audio": voice_profile.reference_audio_path,
            "ref_text": reference_text,
            "x_vector_only_mode": False,
            "cache_key": self._build_cache_key(voice_profile, reference_text),
            "temperature": voice_profile.temperature,
            "top_p": voice_profile.top_p,
            "top_k": voice_profile.top_k,
            "repetition_penalty": voice_profile.repetition_penalty,
            "max_new_tokens": voice_profile.max_new_tokens,
        }
        response = httpx.post(
            f"{self._base_url}/synthesize",
            json=payload,
            timeout=self._timeout_seconds,
        )
        response.raise_for_status()
        return response.content

    def stream_synthesize(
        self,
        text: str,
        voice_profile: QwenVoiceProfile,
        *,
        language: str | None = None,
        chunk_ms: int = 120,
    ) -> Iterator[WavAudioChunk]:
        wav_bytes = self.synthesize(text, voice_profile, language=language)
        yield from iter_wav_audio_chunks(wav_bytes, chunk_ms=chunk_ms)

    @staticmethod
    def _build_cache_key(voice_profile: QwenVoiceProfile, reference_text: str) -> str:
        payload = "|".join(
            [
                voice_profile.profile_id,
                voice_profile.reference_audio_path,
                reference_text,
            ]
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @staticmethod
    def _resolve_reference_text(voice_profile: QwenVoiceProfile) -> str:
        provider = Qwen3TTSProvider(
            reference_wav=voice_profile.reference_audio_path,
            reference_text=voice_profile.reference_text or "",
            reference_text_file=voice_profile.reference_text_file or "",
        )
        return provider._load_reference_text()
