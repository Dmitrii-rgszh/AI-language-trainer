from __future__ import annotations

import io
import os
import re
import wave
from pathlib import Path
from typing import Any

import numpy as np

from app.core.config import settings
from app.providers.tts.base import BaseTTSProvider
from app.schemas.provider import ProviderAvailability, ProviderStatus


class XTTSProvider(BaseTTSProvider):
    def __init__(
        self,
        model_name: str | None = None,
        device: str | None = None,
        default_language: str | None = None,
        default_speaker: str | None = None,
        reference_wav: str | None = None,
    ) -> None:
        self._model_name = model_name or settings.xtts_model_name
        self._hf_repo_id = settings.xtts_hf_repo_id
        self._device = device or settings.xtts_device
        self._default_language = default_language or settings.xtts_default_language
        self._default_speaker = default_speaker or settings.xtts_default_speaker
        self._reference_wav = reference_wav or settings.xtts_reference_wav
        self._tts: Any | None = None

    def synthesize(
        self,
        text: str,
        language: str,
        speaker: str | None = None,
        style: str | None = None,
    ) -> bytes:
        tts = self._get_tts()
        normalized_text = self._prepare_text(text=text, language=language, style=style)
        if not normalized_text:
            raise ValueError("Text for speech synthesis cannot be empty.")

        kwargs: dict[str, Any] = {
            "text": normalized_text,
            "language": language or self._default_language,
            "split_sentences": True,
        }
        if self._reference_wav and os.path.exists(self._reference_wav):
            kwargs["speaker_wav"] = [self._reference_wav]
        else:
            kwargs["speaker"] = speaker or self._default_speaker

        wav = tts.tts(**kwargs)
        return _wav_to_bytes(wav)

    def _prepare_text(self, *, text: str, language: str, style: str | None) -> str:
        normalized_text = text.strip()
        if not normalized_text:
            return ""

        normalized_text = (
            normalized_text
            .replace("…", ", ")
            .replace("—", ", ")
            .replace("–", ", ")
            .replace(";", ", ")
            .replace(":", ", ")
            .replace("*", " ")
            .replace("`", " ")
            .replace("(", ", ")
            .replace(")", " ")
            .replace("[", ", ")
            .replace("]", " ")
            .replace("{", ", ")
            .replace("}", " ")
            .replace("/", " ")
            .replace("\\", " ")
        )
        normalized_text = re.sub(r"\.{2,}", ", ", normalized_text)
        normalized_text = re.sub(r'["“”«»]', "", normalized_text)

        sentence_parts = [
            re.sub(r"[.!?]+$", "", chunk.strip())
            for chunk in re.split(r"(?<=[.!?])\s+", normalized_text)
            if chunk.strip()
        ]
        if sentence_parts:
            joiner = ", " if style in {"coach", "warm"} else " "
            normalized_text = joiner.join(sentence_parts)

        normalized_text = re.sub(r"\s*,\s*", ", ", normalized_text)
        normalized_text = re.sub(r"\s+", " ", normalized_text).strip(" ,")

        return normalized_text

    def status(self) -> ProviderStatus:
        try:
            self._import_tts()
        except Exception as exc:
            return ProviderStatus(
                key="xtts_v2",
                name="XTTS v2 Voice Engine",
                type="tts",
                status=ProviderAvailability.OFFLINE,
                details=f"XTTS runtime is unavailable: {exc}",
            )

        details = (
            f"XTTS v2 is configured for {self._device} with default speaker "
            f"'{self._default_speaker}' and Russian support."
        )
        if self._reference_wav and os.path.exists(self._reference_wav):
            details = f"XTTS v2 is configured with custom reference voice at '{self._reference_wav}'."

        return ProviderStatus(
            key="xtts_v2",
            name="XTTS v2 Voice Engine",
            type="tts",
            status=ProviderAvailability.READY,
            details=details,
        )

    def _get_tts(self) -> Any:
        if self._tts is not None:
            return self._tts

        if settings.coqui_tos_agreed:
            os.environ.setdefault("COQUI_TOS_AGREED", "1")

        self._patch_torch_checkpoint_loading()
        tts_api = self._import_tts()
        gpu = self._should_use_gpu()
        model_dir = self._download_model_snapshot()
        self._tts = tts_api.TTS(
            model_path=str(model_dir),
            config_path=str(model_dir / "config.json"),
            gpu=gpu,
            progress_bar=False,
        )
        return self._tts

    @staticmethod
    def _import_tts() -> Any:
        from TTS import api as tts_api

        return tts_api

    def _should_use_gpu(self) -> bool:
        requested_device = self._device.lower()
        if requested_device == "cpu":
            return False

        try:
            import torch

            return torch.cuda.is_available()
        except Exception:
            return False

    def _download_model_snapshot(self) -> Path:
        from huggingface_hub import snapshot_download

        local_dir = snapshot_download(
            repo_id=self._hf_repo_id,
            allow_patterns=[
                "config.json",
                "dvae.pth",
                "mel_stats.pth",
                "model.pth",
                "speakers_xtts.pth",
                "vocab.json",
            ],
        )
        return Path(local_dir)

    @staticmethod
    def _patch_torch_checkpoint_loading() -> None:
        import TTS.tts.models.xtts as xtts_module
        import TTS.utils.io as io_module
        import fsspec
        import torch
        from TTS.utils.generic_utils import get_user_data_dir

        def load_fsspec_compat(
            path: str,
            map_location: Any = None,
            cache: bool = True,
            **kwargs: Any,
        ) -> Any:
            kwargs.setdefault("weights_only", False)
            is_local = os.path.isdir(path) or os.path.isfile(path)
            if cache and not is_local:
                with fsspec.open(
                    f"filecache::{path}",
                    filecache={"cache_storage": str(get_user_data_dir("tts_cache"))},
                    mode="rb",
                ) as file_handle:
                    return torch.load(file_handle, map_location=map_location, **kwargs)

            with fsspec.open(path, "rb") as file_handle:
                return torch.load(file_handle, map_location=map_location, **kwargs)

        io_module.load_fsspec = load_fsspec_compat
        xtts_module.load_fsspec = load_fsspec_compat


def _wav_to_bytes(wav_data: list[float] | np.ndarray, sample_rate: int = 24000) -> bytes:
    audio = np.asarray(wav_data, dtype=np.float32)
    audio = np.clip(audio, -1.0, 1.0)
    pcm16 = (audio * 32767.0).astype(np.int16)

    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm16.tobytes())

    return buffer.getvalue()
