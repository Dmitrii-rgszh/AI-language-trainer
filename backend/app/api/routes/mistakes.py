from fastapi import APIRouter, Depends

from app.api.dependencies import require_profile
from app.core.dependencies import mistake_service
from app.schemas.mistake import Mistake
from app.schemas.profile import UserProfile

router = APIRouter(prefix="/mistakes", tags=["mistakes"])


@router.get("", response_model=list[Mistake])
def get_mistakes(profile: UserProfile = Depends(require_profile)) -> list[Mistake]:
    return mistake_service.list_mistakes(profile.id)
