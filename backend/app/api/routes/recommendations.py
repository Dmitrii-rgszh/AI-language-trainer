from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import require_profile
from app.core.dependencies import recommendation_service
from app.schemas.lesson import LessonRecommendation
from app.schemas.profile import UserProfile

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/next", response_model=LessonRecommendation)
def get_next_recommendation(profile: UserProfile = Depends(require_profile)) -> LessonRecommendation:
    recommendation = recommendation_service.get_next_step(profile)
    if not recommendation:
        raise HTTPException(status_code=503, detail="Recommendation content is not initialized.")

    return recommendation
