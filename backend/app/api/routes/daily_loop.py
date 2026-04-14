from fastapi import APIRouter

from app.api.dependencies import require_profile
from app.core.dependencies import journey_service
from app.schemas.journey import DailyLoopPlan
from app.schemas.lesson import LessonRunState

router = APIRouter(prefix="/daily-loop", tags=["daily-loop"])


@router.get("/today", response_model=DailyLoopPlan)
def get_today_daily_loop() -> DailyLoopPlan:
    return journey_service.get_today_plan(require_profile())


@router.post("/today/start", response_model=LessonRunState)
def start_today_daily_loop() -> LessonRunState:
    return journey_service.start_today_session(require_profile())
