from __future__ import annotations

import os
import tempfile
from pathlib import Path

from fastapi import UploadFile

from app.core.errors import AppError, BadGatewayError, ServiceUnavailableError
from app.providers.stt.base import BaseSTTProvider


class STTService:
    def __init__(self, provider: BaseSTTProvider | None) -> None:
        self._provider = provider

    def transcribe_path(self, audio_path: str, language: str | None = None) -> str:
        details = self.transcribe_path_detailed(audio_path, language=language)
        transcript = str(details.get("transcript") or "").strip()
        if not transcript:
            raise BadGatewayError("Speech transcription returned an empty transcript.")
        return transcript

    def transcribe_path_detailed(self, audio_path: str, language: str | None = None) -> dict[str, object]:
        if self._provider is None:
            raise ServiceUnavailableError("STT provider is not configured.")

        try:
            return self._provider.transcribe_detailed(audio_path, language=language)
        except AppError:
            raise
        except Exception as exc:
            raise BadGatewayError(f"Speech transcription failed: {exc}") from exc

    async def transcribe_upload(self, upload: UploadFile, language: str | None = None) -> str:
        details = await self.transcribe_upload_detailed(upload, language=language)
        transcript = str(details.get("transcript") or "").strip()
        if not transcript:
            raise BadGatewayError("Speech transcription returned an empty transcript.")
        return transcript

    async def transcribe_upload_detailed(self, upload: UploadFile, language: str | None = None) -> dict[str, object]:
        suffix = Path(upload.filename or "audio.webm").suffix or ".webm"
        temp_path: str | None = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temporary_file:
                temp_path = temporary_file.name
                while True:
                    chunk = await upload.read(1024 * 1024)
                    if not chunk:
                        break
                    temporary_file.write(chunk)

            return self.transcribe_path_detailed(temp_path, language=language)
        except AppError:
            raise
        finally:
            await upload.close()
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
