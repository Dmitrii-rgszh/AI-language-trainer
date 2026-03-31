from fastapi import APIRouter, HTTPException

from app.api.dependencies import require_profile
from app.core.dependencies import recommendation_service
from app.schemas.lesson import LessonRecommendation

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/next", response_model=LessonRecommendation)
def get_next_recommendation() -> LessonRecommendation:
    recommendation = recommendation_service.get_next_step(require_profile())
    if not recommendation:
        raise HTTPException(status_code=503, detail="Recommendation content is not initialized.")

    return recommendation
