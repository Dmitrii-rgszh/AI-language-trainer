from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import require_profile
from app.core.dependencies import adaptive_study_service
from app.schemas.adaptive import (
    AdaptiveStudyLoop,
    VocabularyHub,
    VocabularyJournalCaptureRequest,
    VocabularyReviewItem,
    VocabularyReviewUpdateRequest,
)
from app.schemas.lesson import LessonRunState
from app.schemas.profile import UserProfile

router = APIRouter(prefix="/adaptive", tags=["adaptive"])


@router.get("/loop", response_model=AdaptiveStudyLoop)
def get_adaptive_loop(profile: UserProfile = Depends(require_profile)) -> AdaptiveStudyLoop:
    loop = adaptive_study_service.get_loop(profile)
    if loop is None:
        raise HTTPException(status_code=503, detail="Adaptive study loop is not available.")

    return loop


@router.get("/vocabulary/hub", response_model=VocabularyHub)
def get_vocabulary_hub(profile: UserProfile = Depends(require_profile)) -> VocabularyHub:
    return adaptive_study_service.get_vocabulary_hub(profile.id)


@router.post("/vocabulary/{item_id}/review", response_model=VocabularyReviewItem)
def review_vocabulary_item(
    item_id: str,
    payload: VocabularyReviewUpdateRequest,
    profile: UserProfile = Depends(require_profile),
) -> VocabularyReviewItem:
    reviewed = adaptive_study_service.review_vocabulary(profile.id, item_id, payload.successful)
    if reviewed is None:
        raise HTTPException(status_code=404, detail="Vocabulary item not found.")

    return reviewed


@router.post("/vocabulary/journal-capture", response_model=VocabularyReviewItem)
def capture_vocabulary_journal_item(
    payload: VocabularyJournalCaptureRequest,
    profile: UserProfile = Depends(require_profile),
) -> VocabularyReviewItem:
    return adaptive_study_service.capture_word_journal(
        profile.id,
        phrase=payload.phrase,
        translation=payload.translation,
        context=payload.context,
    )


@router.post("/recovery-run", response_model=LessonRunState)
def start_recovery_run(profile: UserProfile = Depends(require_profile)) -> LessonRunState:
    return adaptive_study_service.start_recovery_run(profile)
