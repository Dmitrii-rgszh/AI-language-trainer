from fastapi import APIRouter, Depends

from app.api.dependencies import require_profile
from app.core.dependencies import journey_service
from app.schemas.journey import DailyLoopPlan
from app.schemas.lesson import LessonRunState
from app.schemas.profile import UserProfile

router = APIRouter(prefix="/daily-loop", tags=["daily-loop"])


@router.get("/today", response_model=DailyLoopPlan)
def get_today_daily_loop(profile: UserProfile = Depends(require_profile)) -> DailyLoopPlan:
    return journey_service.get_today_plan(profile)


@router.post("/today/start", response_model=LessonRunState)
def start_today_daily_loop(profile: UserProfile = Depends(require_profile)) -> LessonRunState:
    return journey_service.start_today_session(profile)
