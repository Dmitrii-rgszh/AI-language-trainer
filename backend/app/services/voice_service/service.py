from __future__ import annotations

from app.core.errors import AppError, BadGatewayError, ServiceUnavailableError
from app.providers.tts.base import BaseTTSProvider


class VoiceService:
    def __init__(self, provider: BaseTTSProvider | None) -> None:
        self._provider = provider

    def synthesize(
        self,
        text: str,
        language: str,
        speaker: str | None = None,
        style: str | None = None,
    ) -> bytes:
        if self._provider is None:
            raise ServiceUnavailableError("TTS provider is not configured.")

        try:
            return self._provider.synthesize(
                text=text,
                language=language,
                speaker=speaker,
                style=style,
            )
        except AppError:
            raise
        except Exception as exc:
            raise BadGatewayError(f"Speech synthesis failed: {exc}") from exc
