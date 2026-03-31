from __future__ import annotations

from io import BytesIO

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.core.dependencies import voice_service
from app.schemas.voice import SynthesizeSpeechRequest

router = APIRouter(prefix="/voice", tags=["voice"])


@router.post("/synthesize")
def synthesize_speech(payload: SynthesizeSpeechRequest) -> StreamingResponse:
    audio_bytes = voice_service.synthesize(
        text=payload.text,
        language=payload.language,
        speaker=payload.speaker,
    )
    return StreamingResponse(
        BytesIO(audio_bytes),
        media_type="audio/wav",
        headers={"Content-Disposition": "inline; filename=voice.wav"},
    )

