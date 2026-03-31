from fastapi import APIRouter

from app.api.dependencies import require_profile
from app.core.dependencies import diagnostic_service
from app.schemas.diagnostic import DiagnosticRoadmap
from app.schemas.lesson import LessonRunState

router = APIRouter(prefix="/diagnostic", tags=["diagnostic"])


@router.get("/roadmap", response_model=DiagnosticRoadmap)
def get_diagnostic_roadmap() -> DiagnosticRoadmap:
    return diagnostic_service.get_roadmap(require_profile())


@router.post("/checkpoint-run", response_model=LessonRunState)
def start_diagnostic_checkpoint() -> LessonRunState:
    return diagnostic_service.start_checkpoint_run(require_profile())
