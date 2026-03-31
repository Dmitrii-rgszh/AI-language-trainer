from fastapi import APIRouter, HTTPException

from app.api.dependencies import require_profile
from app.core.dependencies import lesson_runtime_service, lesson_service
from app.schemas.lesson import (
    CompleteLessonRunRequest,
    CompleteLessonRunResponse,
    Lesson,
    LessonRunState,
    SubmitBlockResultRequest,
    StartLessonRunRequest,
)

router = APIRouter(prefix="/lessons", tags=["lessons"])


@router.get("/recommended", response_model=Lesson)
def get_recommended_lesson() -> Lesson:
    lesson = lesson_service.build_recommended_lesson(require_profile())
    if not lesson:
        raise HTTPException(status_code=503, detail="Lesson content is not initialized.")

    return lesson


@router.post("/runs/start", response_model=LessonRunState)
def start_lesson_run(payload: StartLessonRunRequest) -> LessonRunState:
    return lesson_runtime_service.start_run(require_profile(), payload)


@router.get("/runs/active", response_model=LessonRunState | None)
def get_active_lesson_run() -> LessonRunState | None:
    return lesson_runtime_service.get_active_run(require_profile())


@router.delete("/runs/{run_id}", status_code=204)
def discard_lesson_run(run_id: str) -> None:
    lesson_runtime_service.discard_run(require_profile(), run_id)


@router.post("/runs/{run_id}/restart", response_model=LessonRunState)
def restart_lesson_run(run_id: str) -> LessonRunState:
    return lesson_runtime_service.restart_run(require_profile(), run_id)


@router.post("/runs/{run_id}/blocks/submit", response_model=LessonRunState)
def submit_block_result(run_id: str, payload: SubmitBlockResultRequest) -> LessonRunState:
    return lesson_runtime_service.submit_block_result(require_profile(), run_id, payload)


@router.post("/runs/{run_id}/complete", response_model=CompleteLessonRunResponse)
def complete_lesson_run(run_id: str, payload: CompleteLessonRunRequest) -> CompleteLessonRunResponse:
    return lesson_runtime_service.complete_run(require_profile(), run_id, payload)
