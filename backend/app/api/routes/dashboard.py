from fastapi import APIRouter, Depends

from app.api.dependencies import require_profile
from app.api.routes.dashboard_builders import build_dashboard_data
from app.core.dependencies import (
    adaptive_study_service,
    journey_service,
    lesson_runtime_service,
    mistake_service,
    progress_service,
    recommendation_service,
)
from app.schemas.content import DashboardData
from app.schemas.profile import UserProfile

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardData)
def get_dashboard(profile: UserProfile = Depends(require_profile)) -> DashboardData:
    active_run = lesson_runtime_service.get_active_run(profile)
    progress = progress_service.get_snapshot(profile.id)
    weak_spots = mistake_service.list_weak_spots(profile.id)
    recommendation = recommendation_service.get_next_step(profile)
    study_loop = adaptive_study_service.get_loop(profile)
    daily_loop_plan = journey_service.get_today_plan(profile)
    journey_state = journey_service.get_journey_state(profile)
    return build_dashboard_data(
        profile=profile,
        progress=progress,
        weak_spots=weak_spots,
        recommendation=recommendation,
        study_loop=study_loop,
        daily_loop_plan=daily_loop_plan,
        journey_state=journey_state,
        active_run=active_run,
    )
