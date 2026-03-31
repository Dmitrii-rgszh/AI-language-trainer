from fastapi import APIRouter

from app.api.dependencies import require_profile
from app.core.dependencies import (
    adaptive_study_service,
    lesson_runtime_service,
    mistake_service,
    progress_service,
    recommendation_service,
)
from app.schemas.content import DashboardData, QuickAction, ResumeLessonCard

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardData)
def get_dashboard() -> DashboardData:
    profile = require_profile()
    active_run = lesson_runtime_service.get_active_run(profile)
    resume_lesson = None
    if active_run:
        completed_blocks = sum(1 for block in active_run.block_runs if block.status == "completed")
        current_index = min(completed_blocks, max(len(active_run.lesson.blocks) - 1, 0))
        resume_lesson = ResumeLessonCard(
            run_id=active_run.run_id,
            title=active_run.lesson.title,
            current_block_title=active_run.lesson.blocks[current_index].title,
            completed_blocks=completed_blocks,
            total_blocks=len(active_run.lesson.blocks),
            route="/lesson-runner",
        )

    return DashboardData(
        profile=profile,
        progress=progress_service.get_snapshot(profile.id),
        weak_spots=mistake_service.list_weak_spots(profile.id),
        recommendation=recommendation_service.get_next_step(profile),
        study_loop=adaptive_study_service.get_loop(profile),
        quick_actions=[
            QuickAction(
                id="action-1",
                title="Grammar Sprint",
                description="10 минут на ключевую тему и быстрый drill.",
                route="/grammar",
            ),
            QuickAction(
                id="action-2",
                title="Speaking Check-in",
                description="Короткий guided speaking с фидбеком.",
                route="/speaking",
            ),
            QuickAction(
                id="action-3",
                title="Profession Hub",
                description="Профессиональный английский по текущему треку.",
                route="/profession",
            ),
            QuickAction(
                id="action-4",
                title="Adaptive Loop",
                description="Recovery focus, vocabulary repetition and next study step in one flow.",
                route="/activity",
            ),
        ],
        resume_lesson=resume_lesson,
    )
