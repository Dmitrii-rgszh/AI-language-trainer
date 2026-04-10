from pathlib import Path

from app.services.voice_service.prompt_cache import (
    ensure_welcome_proof_lesson_cue_audio_cached,
)


class StubVoiceService:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str | None, str | None]] = []

    def synthesize(
        self,
        text: str,
        language: str,
        speaker: str | None = None,
        style: str | None = None,
    ) -> bytes:
        self.calls.append((text, language, speaker, style))
        return b"wav-bytes"


def test_ensure_welcome_proof_lesson_cue_audio_cached_writes_audio_once(
    monkeypatch,
    tmp_path: Path,
) -> None:
    from app.core.config import settings

    voice_service = StubVoiceService()
    monkeypatch.setattr(settings, "welcome_audio_cache_dir", tmp_path.as_posix(), raising=False)

    first_path = ensure_welcome_proof_lesson_cue_audio_cached(
        voice_service,
        locale="ru",
        cue="feedback",
    )
    second_path = ensure_welcome_proof_lesson_cue_audio_cached(
        voice_service,
        locale="ru",
        cue="feedback",
    )

    assert first_path == second_path
    assert first_path.exists()
    assert first_path.read_bytes() == b"wav-bytes"
    assert len(voice_service.calls) == 1
