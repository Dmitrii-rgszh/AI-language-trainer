from __future__ import annotations

import asyncio
import io
import os
import threading
from typing import Any
from pathlib import Path

import numpy as np
import soundfile as soundfile
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

app = FastAPI(title="Qwen3-TTS Sidecar", version="0.1.0")

SUPPORTED_LANGUAGE_ALIASES = {
    "auto": "Auto",
    "zh": "Chinese",
    "cn": "Chinese",
    "chinese": "Chinese",
    "en": "English",
    "english": "English",
    "fr": "French",
    "french": "French",
    "de": "German",
    "german": "German",
    "it": "Italian",
    "italian": "Italian",
    "ja": "Japanese",
    "jp": "Japanese",
    "japanese": "Japanese",
    "ko": "Korean",
    "korean": "Korean",
    "pt": "Portuguese",
    "portuguese": "Portuguese",
    "ru": "Russian",
    "russian": "Russian",
    "es": "Spanish",
    "spanish": "Spanish",
}


class SynthesizeRequest(BaseModel):
    text: str = Field(min_length=1, max_length=4000)
    language: str = Field(default="Auto", min_length=1, max_length=40)
    ref_audio: str = Field(min_length=1, max_length=1000)
    ref_text: str = Field(default="", max_length=4000)
    x_vector_only_mode: bool = False
    cache_key: str | None = Field(default=None, max_length=128)
    temperature: float = Field(default=0.35, ge=0.0, le=2.0)
    top_p: float = Field(default=0.82, ge=0.0, le=1.0)
    top_k: int = Field(default=20, ge=1, le=200)
    repetition_penalty: float = Field(default=1.05, ge=0.5, le=2.0)
    max_new_tokens: int = Field(default=1200, ge=1, le=4000)


class QwenTTSRuntime:
    def __init__(self) -> None:
        self._model_id = os.getenv("QWEN_TTS_MODEL_ID", "Qwen/Qwen3-TTS-12Hz-1.7B-Base")
        self._device = os.getenv("QWEN_TTS_DEVICE", "cuda:0")
        self._dtype_name = os.getenv("QWEN_TTS_DTYPE", "float16").strip().lower()
        self._attn_implementation = os.getenv("QWEN_TTS_ATTN_IMPLEMENTATION", "").strip()
        self._default_ref_audio = (
            os.getenv("QWEN_TTS_REF_AUDIO_PATH", "").strip()
            or os.getenv("QWEN_TTS_REFERENCE_WAV", "").strip()
        )
        self._default_ref_text = os.getenv("QWEN_TTS_REF_TEXT", "").strip()
        self._default_ref_text_file = os.getenv("QWEN_TTS_REFERENCE_TEXT_FILE", "").strip()
        self._model: Any | None = None
        self._startup_error: str | None = None
        self._model_lock = threading.Lock()
        self._prompt_cache: dict[str, Any] = {}
        self._prompt_lock = threading.Lock()

    def health(self) -> dict[str, Any]:
        return {
            "status": "ok" if self._model is not None and not self._startup_error else "warming",
            "model_loaded": self._model is not None,
            "model_id": self._model_id,
            "device": self._device,
            "dtype": self._dtype_name,
            "startup_error": self._startup_error,
        }

    def synthesize(self, payload: SynthesizeRequest) -> bytes:
        if not os.path.exists(payload.ref_audio):
            raise FileNotFoundError(f"Reference audio file not found: {payload.ref_audio}")

        if not payload.x_vector_only_mode and not payload.ref_text.strip():
            raise ValueError("ref_text is required unless x_vector_only_mode=True.")

        model = self._get_model()
        voice_clone_prompt = self._get_or_create_prompt(model=model, payload=payload)
        wavs, sample_rate = model.generate_voice_clone(
            text=payload.text,
            language=_normalize_language(payload.language),
            voice_clone_prompt=voice_clone_prompt,
            temperature=payload.temperature,
            top_p=payload.top_p,
            top_k=payload.top_k,
            repetition_penalty=payload.repetition_penalty,
            max_new_tokens=payload.max_new_tokens,
        )
        return _waveform_to_wav_bytes(wavs[0], sample_rate)

    def warmup(self) -> None:
        model = self._get_model()
        if self._default_ref_audio:
            try:
                default_ref_text = self._resolve_default_ref_text()
                if default_ref_text:
                    self._get_or_create_prompt(
                        model=model,
                        payload=SynthesizeRequest(
                            text="warmup",
                            language="Russian",
                            ref_audio=self._default_ref_audio,
                            ref_text=default_ref_text,
                            x_vector_only_mode=False,
                            cache_key="startup-default-voice-clone",
                        ),
                    )
            except Exception:
                # Model warmup is still useful even if prompt warmup cannot be completed.
                return

    def _get_model(self) -> Any:
        if self._model is not None:
            return self._model

        with self._model_lock:
            if self._model is not None:
                return self._model

            import torch
            from qwen_tts import Qwen3TTSModel

            kwargs: dict[str, Any] = {
                "device_map": self._device,
            }
            dtype = getattr(torch, self._dtype_name, None)
            if dtype is not None:
                kwargs["dtype"] = dtype
            if self._attn_implementation:
                kwargs["attn_implementation"] = self._attn_implementation

            self._model = Qwen3TTSModel.from_pretrained(self._model_id, **kwargs)
            return self._model

    def _get_or_create_prompt(self, *, model: Any, payload: SynthesizeRequest) -> Any:
        cache_key = payload.cache_key or f"{payload.ref_audio}|{payload.ref_text}|{payload.x_vector_only_mode}"
        prompt = self._prompt_cache.get(cache_key)
        if prompt is not None:
            return prompt

        with self._prompt_lock:
            prompt = self._prompt_cache.get(cache_key)
            if prompt is not None:
                return prompt

            prompt = model.create_voice_clone_prompt(
                ref_audio=payload.ref_audio,
                ref_text=payload.ref_text or None,
                x_vector_only_mode=payload.x_vector_only_mode,
            )
            self._prompt_cache[cache_key] = prompt
            return prompt

    def _resolve_default_ref_text(self) -> str:
        if self._default_ref_text:
            return self._default_ref_text
        if self._default_ref_text_file and os.path.exists(self._default_ref_text_file):
            return Path(self._default_ref_text_file).read_text(encoding="utf-8").strip()
        return ""


runtime = QwenTTSRuntime()


@app.get("/health")
def health() -> dict[str, Any]:
    payload = runtime.health()
    if not payload["model_loaded"] or payload.get("startup_error"):
        raise HTTPException(status_code=503, detail=payload)
    return payload


@app.post("/synthesize")
def synthesize(payload: SynthesizeRequest) -> Response:
    try:
        audio_bytes = runtime.synthesize(payload)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return Response(content=audio_bytes, media_type="audio/wav")


@app.on_event("startup")
async def warmup_runtime() -> None:
    try:
        await asyncio.to_thread(runtime.warmup)
        runtime._startup_error = None
    except Exception as exc:
        runtime._startup_error = str(exc)


def _waveform_to_wav_bytes(wav_data: Any, sample_rate: int) -> bytes:
    audio = np.asarray(wav_data, dtype=np.float32)
    buffer = io.BytesIO()
    soundfile.write(buffer, audio, sample_rate, format="WAV")
    return buffer.getvalue()


def _normalize_language(language: str) -> str:
    normalized = (language or "").strip()
    if not normalized:
        return "Auto"

    compact = normalized.lower().split("-", 1)[0]
    return SUPPORTED_LANGUAGE_ALIASES.get(compact, normalized.title())
