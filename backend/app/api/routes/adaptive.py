from fastapi import APIRouter, HTTPException

from app.api.dependencies import require_profile
from app.core.dependencies import adaptive_study_service
from app.schemas.adaptive import AdaptiveStudyLoop, VocabularyHub, VocabularyReviewItem, VocabularyReviewUpdateRequest
from app.schemas.lesson import LessonRunState

router = APIRouter(prefix="/adaptive", tags=["adaptive"])


@router.get("/loop", response_model=AdaptiveStudyLoop)
def get_adaptive_loop() -> AdaptiveStudyLoop:
    loop = adaptive_study_service.get_loop(require_profile())
    if loop is None:
        raise HTTPException(status_code=503, detail="Adaptive study loop is not available.")

    return loop


@router.get("/vocabulary/hub", response_model=VocabularyHub)
def get_vocabulary_hub() -> VocabularyHub:
    return adaptive_study_service.get_vocabulary_hub(require_profile().id)


@router.post("/vocabulary/{item_id}/review", response_model=VocabularyReviewItem)
def review_vocabulary_item(item_id: str, payload: VocabularyReviewUpdateRequest) -> VocabularyReviewItem:
    reviewed = adaptive_study_service.review_vocabulary(require_profile().id, item_id, payload.successful)
    if reviewed is None:
        raise HTTPException(status_code=404, detail="Vocabulary item not found.")

    return reviewed


@router.post("/recovery-run", response_model=LessonRunState)
def start_recovery_run() -> LessonRunState:
    return adaptive_study_service.start_recovery_run(require_profile())
