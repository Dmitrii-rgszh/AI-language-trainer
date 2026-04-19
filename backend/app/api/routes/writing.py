from fastapi import APIRouter, Depends

from app.api.dependencies import require_profile
from app.core.dependencies import writing_service
from app.schemas.content import WritingTask
from app.schemas.feedback import AITextFeedback, WritingAttempt, WritingReviewRequest
from app.schemas.profile import UserProfile

router = APIRouter(prefix="/writing", tags=["writing"])


@router.get("/task", response_model=WritingTask)
def get_writing_task() -> WritingTask:
    return writing_service.get_task()


@router.post("/review", response_model=AITextFeedback)
def review_writing(
    payload: WritingReviewRequest,
    profile: UserProfile = Depends(require_profile),
) -> AITextFeedback:
    return writing_service.review_draft(
        user_id=profile.id,
        task_id=payload.task_id,
        draft=payload.draft,
        feedback_language=payload.feedback_language,
    )


@router.get("/attempts", response_model=list[WritingAttempt])
def get_writing_attempts(profile: UserProfile = Depends(require_profile)) -> list[WritingAttempt]:
    return writing_service.list_attempts(profile.id)
