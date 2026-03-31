from app.services.ai_orchestrator import AIOrchestrator
from app.repositories.content_repository import ContentRepository
from app.repositories.mistake_repository import MistakeRepository
from app.repositories.vocabulary_repository import VocabularyRepository
from app.repositories.writing_attempt_repository import WritingAttemptRepository
from app.services.mistake_extraction_service.service import MistakeExtractionService
from app.schemas.content import WritingTask
from app.schemas.feedback import AITextFeedback, WritingAttempt


class WritingService:
    def __init__(
        self,
        repository: ContentRepository,
        ai_orchestrator: AIOrchestrator,
        writing_attempt_repository: WritingAttemptRepository,
        mistake_repository: MistakeRepository,
        vocabulary_repository: VocabularyRepository,
        mistake_extraction_service: MistakeExtractionService,
    ) -> None:
        self._repository = repository
        self._ai_orchestrator = ai_orchestrator
        self._writing_attempt_repository = writing_attempt_repository
        self._mistake_repository = mistake_repository
        self._vocabulary_repository = vocabulary_repository
        self._mistake_extraction_service = mistake_extraction_service

    def get_task(self) -> WritingTask:
        task = self._repository.get_primary_writing_task()
        if task:
            return task

        return WritingTask(
            id="writing-empty",
            title="Writing task is not available yet",
            brief="Content bootstrap has not populated writing tasks.",
            tone="neutral",
            checklist=[],
            improved_version_preview="",
        )

    def review_draft(self, user_id: str, task_id: str, draft: str, feedback_language: str) -> AITextFeedback:
        task = self._repository.get_primary_writing_task()
        if task is None or task.id != task_id:
            return AITextFeedback(
                source="mock",
                summary="Письменное задание не найдено. Обнови страницу и попробуй ещё раз.",
                voice_text="Не удалось найти writing задание. Давай обновим задачу и продолжим.",
                voice_language="ru",
            )

        prompt = (
            "Role: supportive English writing tutor.\n"
            f"Feedback language: {feedback_language}.\n"
            "Reply briefly and concretely.\n"
            "Structure:\n"
            "1. One short strength.\n"
            "2. Main grammar or wording issues.\n"
            "3. A polished improved version.\n"
            "4. One next revision goal.\n"
            "Keep the improved version natural and professional.\n\n"
            f"Task title: {task.title}\n"
            f"Brief: {task.brief}\n"
            f"Tone: {task.tone}\n"
            f"Checklist: {', '.join(task.checklist)}\n"
            f"Learner draft:\n{draft}"
        )
        summary = self._ai_orchestrator.generate_stub("writing", prompt)
        voice_text = self._build_voice_text(summary=summary, feedback_language=feedback_language, task_title=task.title)

        feedback = AITextFeedback(
            source="mock" if self._ai_orchestrator.is_mock() else "ai",
            summary=summary,
            voice_text=voice_text,
            voice_language=feedback_language if feedback_language in {"ru", "en"} else "ru",
        )
        self._writing_attempt_repository.create_attempt(
            user_id=user_id,
            task_id=task.id,
            draft=draft,
            feedback=feedback,
        )
        extracted_mistakes = self._mistake_extraction_service.extract_from_review(
            source_module="writing",
            learner_text=draft,
            feedback_summary=feedback.summary,
        )
        self._mistake_repository.apply_extracted_mistakes(user_id, {}, extracted_mistakes)
        self._vocabulary_repository.capture_from_mistakes(user_id, extracted_mistakes)
        return feedback

    def list_attempts(self, user_id: str) -> list[WritingAttempt]:
        return self._writing_attempt_repository.list_attempts(user_id)

    @staticmethod
    def _build_voice_text(summary: str, feedback_language: str, task_title: str) -> str:
        compact_summary = " ".join(summary.split())
        if feedback_language == "en":
            return f"Writing feedback for {task_title}. {compact_summary} Revise the draft and submit one more version."

        return (
            f"Разбор writing-задачи {task_title}. {compact_summary} "
            "Теперь внеси правки и попробуй отправить ещё одну версию."
        )
