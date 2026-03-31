from __future__ import annotations

from typing import Any

from app.core.config import settings
from app.providers.stt.base import BaseSTTProvider
from app.schemas.provider import ProviderAvailability, ProviderStatus


class FasterWhisperProvider(BaseSTTProvider):
    def __init__(
        self,
        model_name: str | None = None,
        device: str | None = None,
        compute_type: str | None = None,
    ) -> None:
        self._model_name = model_name or settings.faster_whisper_model
        self._device = device or settings.faster_whisper_device
        self._compute_type = compute_type or settings.faster_whisper_compute_type
        self._model: Any | None = None

    def transcribe(self, audio_path: str) -> str:
        model = self._get_model()
        segments, _ = model.transcribe(
            audio=audio_path,
            beam_size=5,
            vad_filter=True,
            condition_on_previous_text=False,
        )
        transcript = " ".join(segment.text.strip() for segment in segments).strip()
        if not transcript:
            raise RuntimeError("No speech was recognized in the uploaded audio.")
        return transcript

    def status(self) -> ProviderStatus:
        try:
            self._import_whisper_model()
        except Exception as exc:
            return ProviderStatus(
                key="faster_whisper_stt",
                name="Faster Whisper STT",
                type="stt",
                status=ProviderAvailability.OFFLINE,
                details=f"Faster Whisper runtime is unavailable: {exc}",
            )

        return ProviderStatus(
            key="faster_whisper_stt",
            name="Faster Whisper STT",
            type="stt",
            status=ProviderAvailability.READY,
            details=(
                f"Configured with model '{self._model_name}' on device "
                f"'{self._resolve_device()}' using compute type '{self._resolve_compute_type()}'."
            ),
        )

    def _get_model(self) -> Any:
        if self._model is not None:
            return self._model

        whisper_module = self._import_whisper_model()
        self._model = whisper_module.WhisperModel(
            self._model_name,
            device=self._resolve_device(),
            compute_type=self._resolve_compute_type(),
        )
        return self._model

    @staticmethod
    def _import_whisper_model() -> Any:
        import faster_whisper

        return faster_whisper

    def _resolve_device(self) -> str:
        requested_device = self._device.lower()
        if requested_device != "auto":
            return requested_device

        try:
            import torch

            return "cuda" if torch.cuda.is_available() else "cpu"
        except Exception:
            return "cpu"

    def _resolve_compute_type(self) -> str:
        requested_compute_type = self._compute_type.lower()
        if requested_compute_type != "auto":
            return requested_compute_type

        return "float16" if self._resolve_device() == "cuda" else "int8"

