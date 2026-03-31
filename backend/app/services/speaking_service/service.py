from app.services.ai_orchestrator import AIOrchestrator
from app.repositories.mistake_repository import MistakeRepository
from app.repositories.content_repository import ContentRepository
from app.repositories.speaking_attempt_repository import SpeakingAttemptRepository
from app.repositories.vocabulary_repository import VocabularyRepository
from app.services.mistake_extraction_service.service import MistakeExtractionService
from app.schemas.content import SpeakingScenario
from app.schemas.feedback import AITextFeedback, SpeakingAttempt


class SpeakingService:
    def __init__(
        self,
        repository: ContentRepository,
        ai_orchestrator: AIOrchestrator,
        speaking_attempt_repository: SpeakingAttemptRepository,
        mistake_repository: MistakeRepository,
        vocabulary_repository: VocabularyRepository,
        mistake_extraction_service: MistakeExtractionService,
    ) -> None:
        self._repository = repository
        self._ai_orchestrator = ai_orchestrator
        self._speaking_attempt_repository = speaking_attempt_repository
        self._mistake_repository = mistake_repository
        self._vocabulary_repository = vocabulary_repository
        self._mistake_extraction_service = mistake_extraction_service

    def get_scenarios(self) -> list[SpeakingScenario]:
        return self._repository.list_speaking_scenarios()

    def get_feedback(
        self,
        *,
        user_id: str | None,
        scenario_id: str,
        transcript: str,
        feedback_language: str,
        input_mode: str = "text",
    ) -> AITextFeedback:
        scenario = next((item for item in self._repository.list_speaking_scenarios() if item.id == scenario_id), None)
        if scenario is None:
            return AITextFeedback(
                source="mock",
                summary="Не удалось найти speaking scenario для анализа. Проверь выбор упражнения.",
                voice_text="Давай выберем корректный speaking сценарий и попробуем ещё раз.",
                voice_language="ru",
            )

        prompt = (
            "Role: supportive English speaking tutor.\n"
            f"Feedback language: {feedback_language}.\n"
            "Reply briefly and concretely.\n"
            "Structure:\n"
            "1. One short strength.\n"
            "2. 2-3 corrections with better phrasing.\n"
            "3. One next-step speaking drill.\n"
            "Keep English examples short and natural.\n\n"
            f"Scenario title: {scenario.title}\n"
            f"Goal: {scenario.goal}\n"
            f"Prompt: {scenario.prompt}\n"
            f"Feedback hint: {scenario.feedback_hint}\n"
            f"Learner transcript:\n{transcript}"
        )
        summary = self._ai_orchestrator.generate_stub("speaking", prompt)
        voice_text = self._build_voice_text(
            summary=summary,
            feedback_language=feedback_language,
            scenario_title=scenario.title,
        )
        feedback = AITextFeedback(
            source="mock" if self._ai_orchestrator.is_mock() else "ai",
            summary=summary,
            voice_text=voice_text,
            voice_language=feedback_language if feedback_language in {"ru", "en"} else "ru",
        )
        if user_id:
            self._speaking_attempt_repository.create_attempt(
                user_id=user_id,
                scenario_id=scenario_id,
                input_mode=input_mode,
                transcript=transcript,
                feedback=feedback,
            )
            extracted_mistakes = self._mistake_extraction_service.extract_from_review(
                source_module="speaking",
                learner_text=transcript,
                feedback_summary=feedback.summary,
            )
            self._mistake_repository.apply_extracted_mistakes(user_id, {}, extracted_mistakes)
            self._vocabulary_repository.capture_from_mistakes(user_id, extracted_mistakes)

        return feedback

    def list_attempts(self, user_id: str, limit: int = 12) -> list[SpeakingAttempt]:
        return self._speaking_attempt_repository.list_attempts(user_id=user_id, limit=limit)

    @staticmethod
    def _build_voice_text(summary: str, feedback_language: str, scenario_title: str) -> str:
        compact_summary = " ".join(summary.split())
        if feedback_language == "en":
            return (
                f"Speaking feedback for {scenario_title}. {compact_summary} "
                "Repeat the improved sentence out loud once more."
            )

        return (
            f"Разбор speaking-сценария {scenario_title}. {compact_summary} "
            "Теперь повтори улучшенную фразу вслух ещё один раз."
        )
