from __future__ import annotations

import os
import tempfile
from pathlib import Path

from fastapi import HTTPException, UploadFile

from app.providers.stt.base import BaseSTTProvider


class STTService:
    def __init__(self, provider: BaseSTTProvider | None) -> None:
        self._provider = provider

    async def transcribe_upload(self, upload: UploadFile) -> str:
        if self._provider is None:
            raise HTTPException(status_code=503, detail="STT provider is not configured.")

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

            return self._provider.transcribe(temp_path)
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Speech transcription failed: {exc}") from exc
        finally:
            await upload.close()
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

