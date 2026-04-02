from __future__ import annotations

from io import BytesIO

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import StreamingResponse

from app.core.dependencies import stt_service, voice_service
from app.schemas.voice import SynthesizeSpeechRequest, TranscribeSpeechResponse

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


@router.post("/transcribe", response_model=TranscribeSpeechResponse)
async def transcribe_speech(audio: UploadFile = File(...)) -> TranscribeSpeechResponse:
    transcript = await stt_service.transcribe_upload(audio)
    return TranscribeSpeechResponse(transcript=transcript)
