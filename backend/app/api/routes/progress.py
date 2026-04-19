from fastapi import APIRouter, Depends

from app.api.dependencies import require_profile
from app.core.dependencies import progress_service
from app.schemas.progress import ProgressSnapshot
from app.schemas.profile import UserProfile

router = APIRouter(prefix="/progress", tags=["progress"])


@router.get("", response_model=ProgressSnapshot)
def get_progress(profile: UserProfile = Depends(require_profile)) -> ProgressSnapshot:
    return progress_service.get_snapshot(profile.id)
