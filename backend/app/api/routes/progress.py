from fastapi import APIRouter

from app.api.dependencies import require_profile
from app.core.dependencies import progress_service
from app.schemas.progress import ProgressSnapshot

router = APIRouter(prefix="/progress", tags=["progress"])


@router.get("", response_model=ProgressSnapshot)
def get_progress() -> ProgressSnapshot:
    return progress_service.get_snapshot(require_profile().id)
