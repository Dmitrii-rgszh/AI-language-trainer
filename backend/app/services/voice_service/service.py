from __future__ import annotations

from fastapi import HTTPException

from app.providers.tts.base import BaseTTSProvider


class VoiceService:
    def __init__(self, provider: BaseTTSProvider | None) -> None:
        self._provider = provider

    def synthesize(self, text: str, language: str, speaker: str | None = None) -> bytes:
        if self._provider is None:
            raise HTTPException(status_code=503, detail="TTS provider is not configured.")

        try:
            return self._provider.synthesize(text=text, language=language, speaker=speaker)
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Speech synthesis failed: {exc}") from exc

