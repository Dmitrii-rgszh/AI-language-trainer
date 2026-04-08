from __future__ import annotations

from io import BytesIO

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import FileResponse, StreamingResponse

from app.core.dependencies import stt_service, voice_service
from app.schemas.voice import SynthesizeSpeechRequest, TranscribeSpeechResponse
from app.services.voice_service.prompt_cache import ensure_welcome_replay_audio_cached

router = APIRouter(prefix="/voice", tags=["voice"])


@router.post("/synthesize")
def synthesize_speech(payload: SynthesizeSpeechRequest) -> StreamingResponse:
    audio_bytes = voice_service.synthesize(
        text=payload.text,
        language=payload.language,
        speaker=payload.speaker,
        style=payload.style,
    )
    return StreamingResponse(
        BytesIO(audio_bytes),
        media_type="audio/wav",
        headers={"Content-Disposition": "inline; filename=voice.wav"},
    )


@router.get("/welcome-replay")
def get_welcome_replay_audio(locale: str = "ru") -> FileResponse:
    audio_path = ensure_welcome_replay_audio_cached(voice_service, locale=locale)
    return FileResponse(
        audio_path,
        media_type="audio/wav",
        filename=audio_path.name,
        headers={"Cache-Control": "public, max-age=31536000, immutable"},
    )


@router.post("/transcribe", response_model=TranscribeSpeechResponse)
async def transcribe_speech(audio: UploadFile = File(...)) -> TranscribeSpeechResponse:
    transcript = await stt_service.transcribe_upload(audio)
    return TranscribeSpeechResponse(transcript=transcript)
