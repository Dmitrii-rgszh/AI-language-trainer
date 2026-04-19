from fastapi import APIRouter, Depends

from app.api.dependencies import require_profile
from app.core.dependencies import diagnostic_service
from app.schemas.diagnostic import DiagnosticRoadmap
from app.schemas.lesson import LessonRunState
from app.schemas.profile import UserProfile

router = APIRouter(prefix="/diagnostic", tags=["diagnostic"])


@router.get("/roadmap", response_model=DiagnosticRoadmap)
def get_diagnostic_roadmap(profile: UserProfile = Depends(require_profile)) -> DiagnosticRoadmap:
    return diagnostic_service.get_roadmap(profile)


@router.post("/checkpoint-run", response_model=LessonRunState)
def start_diagnostic_checkpoint(profile: UserProfile = Depends(require_profile)) -> LessonRunState:
    return diagnostic_service.start_checkpoint_run(profile)
