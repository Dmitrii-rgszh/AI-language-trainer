from __future__ import annotations

import os
import tempfile
from pathlib import Path

from fastapi import UploadFile

from app.core.errors import AppError, BadGatewayError
from app.providers.scoring.base import BaseScoringProvider
from app.repositories.content_repository import ContentRepository
from app.repositories.pronunciation_attempt_repository import PronunciationAttemptRepository
from app.schemas.content import PronunciationDrill
from app.schemas.pronunciation import PronunciationAssessment, PronunciationAttempt, PronunciationTrend
from app.services.stt_service.service import STTService


class PronunciationService:
    def __init__(
        self,
        repository: ContentRepository,
        stt_service: STTService,
        scoring_provider: BaseScoringProvider,
        attempt_repository: PronunciationAttemptRepository,
    ) -> None:
        self._repository = repository
        self._stt_service = stt_service
        self._scoring_provider = scoring_provider
        self._attempt_repository = attempt_repository

    def get_drills(self) -> list[PronunciationDrill]:
        return self._repository.list_pronunciation_drills()

    def list_attempts(self, user_id: str) -> list[PronunciationAttempt]:
        return self._attempt_repository.list_attempts(user_id)

    def get_trends(self, user_id: str) -> PronunciationTrend:
        return self._attempt_repository.get_trends(user_id)

    async def assess_upload(
        self,
        *,
        user_id: str | None,
        target_text: str,
        audio: UploadFile,
        drill_id: str | None = None,
        sound_focus: str | None = None,
        language: str | None = None,
        persist_attempt: bool = True,
    ) -> PronunciationAssessment:
        suffix = Path(audio.filename or "pronunciation.webm").suffix or ".webm"
        temp_path: str | None = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temporary_file:
                temp_path = temporary_file.name
                while True:
                    chunk = await audio.read(1024 * 1024)
                    if not chunk:
                        break
                    temporary_file.write(chunk)

            transcription = self._stt_service.transcribe_path_detailed(
                temp_path,
                language=language,
            )
            transcript = str(transcription.get("transcript") or "").strip()
            scoring = self._scoring_provider.score_pronunciation(
                target_text,
                transcript,
                acoustic_signals={**transcription, "audio_path": temp_path},
            )
            assessment = PronunciationAssessment(
                target_text=target_text,
                transcript=transcript,
                score=int(scoring["score"]),
                matched_tokens=list(scoring["matched_tokens"]),
                missed_tokens=list(scoring["missed_tokens"]),
                feedback=str(scoring["feedback"]),
                weakest_words=list(scoring["weakest_words"]),
                word_assessments=list(scoring["word_assessments"]),
                focus_assessments=list(scoring["focus_assessments"]),
            )
            if persist_attempt and user_id:
                self._attempt_repository.create_attempt(
                    user_id=user_id,
                    drill_id=drill_id,
                    target_text=target_text,
                    sound_focus=sound_focus,
                    transcript=assessment.transcript,
                    score=assessment.score,
                    feedback=assessment.feedback,
                    weakest_words=assessment.weakest_words,
                    focus_issues=[item.focus for item in assessment.focus_assessments if item.status != "stable"],
                )
            return assessment
        except AppError:
            raise
        except Exception as exc:
            raise BadGatewayError(f"Pronunciation assessment failed: {exc}") from exc
        finally:
            await audio.close()
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
