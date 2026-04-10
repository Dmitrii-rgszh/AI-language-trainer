from io import BytesIO

import pytest
from fastapi import UploadFile

from app.services.pronunciation_service.service import PronunciationService


class StubContentRepository:
    def list_pronunciation_drills(self) -> list[object]:
        return []


class RecordingSTTService:
    def __init__(self) -> None:
        self.last_language: str | None = None

    def transcribe_path_detailed(
        self,
        audio_path: str,
        language: str | None = None,
    ) -> dict[str, object]:
        self.last_language = language
        return {
            "transcript": "I'd like a coffee without sugar",
            "word_timestamps": [],
        }


class StubScoringProvider:
    def score_pronunciation(
        self,
        target_text: str,
        transcript: str,
        acoustic_signals: dict[str, object] | None = None,
    ) -> dict[str, object]:
        return {
            "score": 88,
            "matched_tokens": ["i'd", "like", "coffee", "without", "sugar"],
            "missed_tokens": [],
            "feedback": "Mostly clear.",
            "weakest_words": [],
            "word_assessments": [],
            "focus_assessments": [],
        }


class RecordingAttemptRepository:
    def __init__(self) -> None:
        self.calls = 0

    def create_attempt(self, **kwargs) -> None:
        self.calls += 1


@pytest.mark.anyio
async def test_assess_upload_passes_language_to_stt() -> None:
    stt_service = RecordingSTTService()
    attempt_repository = RecordingAttemptRepository()
    service = PronunciationService(
        repository=StubContentRepository(),
        stt_service=stt_service,
        scoring_provider=StubScoringProvider(),
        attempt_repository=attempt_repository,
    )
    upload = UploadFile(filename="welcome-proof-lesson.webm", file=BytesIO(b"test-audio"))

    assessment = await service.assess_upload(
        user_id=None,
        target_text="I'd like a coffee without sugar.",
        audio=upload,
        language="en",
        persist_attempt=False,
    )

    assert assessment.transcript == "I'd like a coffee without sugar"
    assert stt_service.last_language == "en"
    assert attempt_repository.calls == 0
