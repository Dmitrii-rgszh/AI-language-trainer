from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path

import httpx

from app.core.config import BACKEND_DIR, settings
from app.providers.stt.faster_whisper_provider import FasterWhisperProvider
from app.providers.tts.base import BaseTTSProvider
from app.schemas.provider import ProviderAvailability, ProviderStatus

QWEN_LANGUAGE_MAP = {
    "auto": "Auto",
    "zh": "Chinese",
    "cn": "Chinese",
    "en": "English",
    "ja": "Japanese",
    "jp": "Japanese",
    "ko": "Korean",
    "de": "German",
    "fr": "French",
    "ru": "Russian",
    "pt": "Portuguese",
    "es": "Spanish",
    "it": "Italian",
}


class Qwen3TTSProvider(BaseTTSProvider):
    def __init__(
        self,
        *,
        base_url: str | None = None,
        reference_wav: str | None = None,
        reference_text: str | None = None,
        reference_text_file: str | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        self._base_url = (base_url or settings.qwen_tts_base_url).rstrip("/")
        self._reference_wav = reference_wav or settings.qwen_tts_reference_wav or settings.xtts_reference_wav
        self._reference_text = (reference_text or settings.qwen_tts_reference_text).strip()
        self._reference_text_file = reference_text_file or settings.qwen_tts_reference_text_file
        self._timeout_seconds = timeout_seconds or settings.qwen_tts_timeout_seconds
        self._reference_text_cache: str | None = self._reference_text or None

    def synthesize(
        self,
        text: str,
        language: str,
        speaker: str | None = None,
        style: str | None = None,
    ) -> bytes:
        del speaker

        normalized_text = self._prepare_text(text=text, style=style)
        if not normalized_text:
            raise ValueError("Text for speech synthesis cannot be empty.")

        reference_wav = self._resolve_reference_wav()
        reference_text, x_vector_only_mode = self._resolve_reference_prompt()
        sampling = self._resolve_sampling_params(style)
        payload = {
            "text": normalized_text,
            "language": self._map_language(language),
            "ref_audio": reference_wav,
            "ref_text": reference_text,
            "x_vector_only_mode": x_vector_only_mode,
            "cache_key": self._build_cache_key(reference_wav=reference_wav, reference_text=reference_text),
            "temperature": sampling["temperature"],
            "top_p": sampling["top_p"],
            "top_k": sampling["top_k"],
            "repetition_penalty": sampling["repetition_penalty"],
            "max_new_tokens": settings.qwen_tts_max_new_tokens,
        }

        try:
            response = httpx.post(
                f"{self._base_url}/synthesize",
                json=payload,
                timeout=self._timeout_seconds,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            message = self._extract_error_message(exc.response)
            raise RuntimeError(f"Qwen3-TTS synthesis failed: {message}") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Qwen3-TTS runtime is unavailable: {exc}") from exc

        return response.content

    def status(self) -> ProviderStatus:
        try:
            reference_wav = self._resolve_reference_wav()
        except Exception as exc:
            return ProviderStatus(
                key="qwen3_tts",
                name="Qwen3-TTS Voice Clone",
                type="tts",
                status=ProviderAvailability.OFFLINE,
                details=str(exc),
            )

        try:
            response = httpx.get(f"{self._base_url}/health", timeout=2.0)
            response.raise_for_status()
        except Exception as exc:
            return ProviderStatus(
                key="qwen3_tts",
                name="Qwen3-TTS Voice Clone",
                type="tts",
                status=ProviderAvailability.OFFLINE,
                details=f"Qwen3-TTS runtime is unavailable at '{self._base_url}': {exc}",
            )
        payload = response.json()
        if not payload.get("model_loaded"):
            return ProviderStatus(
                key="qwen3_tts",
                name="Qwen3-TTS Voice Clone",
                type="tts",
                status=ProviderAvailability.OFFLINE,
                details=f"Qwen3-TTS runtime is still warming up at '{self._base_url}'.",
            )

        return ProviderStatus(
            key="qwen3_tts",
            name="Qwen3-TTS Voice Clone",
            type="tts",
            status=ProviderAvailability.READY,
            details=f"Qwen3-TTS clone runtime is active at '{self._base_url}' with reference voice '{reference_wav}'.",
        )

    def _resolve_reference_wav(self) -> str:
        if self._reference_wav and os.path.exists(self._reference_wav):
            return self._reference_wav
        raise FileNotFoundError(
            "Qwen3-TTS reference voice file was not found. Set QWEN_TTS_REFERENCE_WAV to a valid WAV path."
        )

    def _resolve_reference_prompt(self) -> tuple[str, bool]:
        try:
            reference_text = self._load_reference_text()
        except Exception:
            return "", True

        return reference_text, False

    def _load_reference_text(self) -> str:
        if self._reference_text_cache:
            return self._reference_text_cache

        for candidate in self._reference_text_candidates():
            if candidate and candidate.exists():
                text = candidate.read_text(encoding="utf-8").strip()
                if text:
                    self._reference_text_cache = text
                    return text

        stt_provider = FasterWhisperProvider()
        transcript = stt_provider.transcribe(self._resolve_reference_wav()).strip()
        if not transcript:
            raise RuntimeError("Reference audio transcript is empty.")

        cache_path = self._generated_reference_text_path()
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(transcript, encoding="utf-8")
        self._reference_text_cache = transcript
        return transcript

    def _reference_text_candidates(self) -> list[Path]:
        reference_path = Path(self._resolve_reference_wav())
        candidates: list[Path] = []
        if self._reference_text_file:
            candidates.append(Path(self._reference_text_file))
        candidates.append(reference_path.with_suffix(".txt"))
        candidates.append(reference_path.with_name(f"{reference_path.stem}.transcript.txt"))
        candidates.append(self._generated_reference_text_path())
        return candidates

    def _generated_reference_text_path(self) -> Path:
        reference_path = Path(self._resolve_reference_wav())
        return BACKEND_DIR / "generated" / "qwen_tts" / "reference" / f"{reference_path.stem}.transcript.txt"

    @staticmethod
    def _map_language(language: str) -> str:
        normalized = (language or "").strip()
        if not normalized:
            return "Auto"

        compact = normalized.lower()
        compact = compact.split("-", 1)[0]
        return QWEN_LANGUAGE_MAP.get(compact, normalized.title())

    @staticmethod
    def _prepare_text(*, text: str, style: str | None) -> str:
        normalized_text = text.strip()
        if not normalized_text:
            return ""

        normalized_text = (
            normalized_text
            .replace("…", ", ")
            .replace("—", ", ")
            .replace("–", ", ")
            .replace(";", ", ")
            .replace("*", " ")
            .replace("`", " ")
        )
        normalized_text = re.sub(r'["“”«»]', "", normalized_text)
        normalized_text = re.sub(r"\s+", " ", normalized_text).strip()

        sentence_parts = [chunk.strip() for chunk in re.split(r"(?<=[.!?])\s+", normalized_text) if chunk.strip()]
        if sentence_parts:
            normalized_text = " ".join(sentence_parts)

        return normalized_text.strip(" ,")

    @staticmethod
    def _resolve_sampling_params(style: str | None) -> dict[str, float | int]:
        normalized_style = (style or "").strip().lower()
        if normalized_style == "coach":
            return {
                "temperature": 0.12,
                "top_p": 0.55,
                "top_k": 8,
                "repetition_penalty": 1.02,
            }
        if normalized_style == "neutral":
            return {
                "temperature": 0.2,
                "top_p": 0.65,
                "top_k": 12,
                "repetition_penalty": 1.03,
            }
        return {
            "temperature": settings.qwen_tts_temperature,
            "top_p": settings.qwen_tts_top_p,
            "top_k": settings.qwen_tts_top_k,
            "repetition_penalty": settings.qwen_tts_repetition_penalty,
        }

    @staticmethod
    def _build_cache_key(*, reference_wav: str, reference_text: str) -> str:
        payload = f"{reference_wav}|{reference_text}".encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    @staticmethod
    def _extract_error_message(response: httpx.Response) -> str:
        try:
            payload = response.json()
        except Exception:
            return response.text.strip() or f"HTTP {response.status_code}"

        if isinstance(payload, dict):
            detail = payload.get("detail")
            if isinstance(detail, str) and detail.strip():
                return detail.strip()

        return response.text.strip() or f"HTTP {response.status_code}"
