from __future__ import annotations

from app.core.errors import NotFoundError, ServiceUnavailableError
from app.repositories.lesson_runtime_repository import LessonRuntimeRepository
from app.repositories.mistake_repository import MistakeRepository
from app.repositories.progress_repository import ProgressRepository
from app.services.mistake_extraction_service.service import MistakeExtractionService
from app.schemas.lesson import (
    CompleteLessonRunRequest,
    CompleteLessonRunResponse,
    LessonRunState,
    SubmitBlockResultRequest,
    StartLessonRunRequest,
)
from app.schemas.profile import UserProfile


class LessonRuntimeService:
    def __init__(
        self,
        repository: LessonRuntimeRepository,
        progress_repository: ProgressRepository,
        mistake_repository: MistakeRepository,
        mistake_extraction_service: MistakeExtractionService,
    ) -> None:
        self._repository = repository
        self._progress_repository = progress_repository
        self._mistake_repository = mistake_repository
        self._mistake_extraction_service = mistake_extraction_service

    def start_run(self, profile: UserProfile, payload: StartLessonRunRequest) -> LessonRunState:
        lesson_run = self._repository.start_lesson_run(
            user_id=profile.id,
            profession_track=profile.profession_track,
            template_id=payload.template_id,
        )
        if not lesson_run:
            raise ServiceUnavailableError("Lesson content is not initialized.")

        return lesson_run

    def get_active_run(self, profile: UserProfile) -> LessonRunState | None:
        return self._repository.get_active_lesson_run(profile.id)

    def discard_run(self, profile: UserProfile, run_id: str) -> None:
        discarded = self._repository.discard_lesson_run(profile.id, run_id)
        if not discarded:
            raise NotFoundError("Active lesson run was not found.")

    def submit_block_result(
        self,
        profile: UserProfile,
        run_id: str,
        payload: SubmitBlockResultRequest,
    ) -> LessonRunState:
        lesson_run = self._repository.submit_block_result(profile.id, run_id, payload)
        if not lesson_run:
            raise NotFoundError("Lesson run or block was not found.")

        return lesson_run

    def restart_run(self, profile: UserProfile, run_id: str) -> LessonRunState:
        self.discard_run(profile, run_id)
        return self.start_run(profile, StartLessonRunRequest())

    def complete_run(
        self,
        profile: UserProfile,
        run_id: str,
        payload: CompleteLessonRunRequest,
    ) -> CompleteLessonRunResponse:
        lesson_run = self._repository.complete_lesson_run(profile.id, run_id, payload.score, payload.block_results)
        if not lesson_run:
            raise NotFoundError("Lesson run was not found.")

        block_type_by_id = {block.id: block.block_type.replace("_block", "") for block in lesson_run.lesson.blocks}
        block_run_module_map = {
            block_type_by_id.get(block_run.block_id, block_run.block_id): block_run.id
            for block_run in lesson_run.block_runs
        }
        extracted_mistakes = self._mistake_extraction_service.extract_from_block_results(
            lesson_run.lesson,
            payload.block_results,
        )
        mistakes = self._mistake_repository.apply_extracted_mistakes(
            profile.id,
            block_run_module_map,
            extracted_mistakes,
        )
        progress = self._progress_repository.create_snapshot_for_completed_lesson(
            profile=profile,
            lesson_run=lesson_run,
            minutes_completed=payload.minutes_completed,
        )
        return CompleteLessonRunResponse(lesson_run=lesson_run, progress=progress, mistakes=mistakes)
