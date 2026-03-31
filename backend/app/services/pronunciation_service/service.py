from __future__ import annotations

from fastapi import UploadFile

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
        user_id: str,
        target_text: str,
        audio: UploadFile,
        drill_id: str | None = None,
        sound_focus: str | None = None,
    ) -> PronunciationAssessment:
        transcript = await self._stt_service.transcribe_upload(audio)
        scoring = self._scoring_provider.score_pronunciation(target_text, transcript)
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
