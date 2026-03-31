from fastapi import APIRouter

from app.api.dependencies import require_profile
from app.core.dependencies import mistake_service
from app.schemas.mistake import Mistake

router = APIRouter(prefix="/mistakes", tags=["mistakes"])


@router.get("", response_model=list[Mistake])
def get_mistakes() -> list[Mistake]:
    return mistake_service.list_mistakes(require_profile().id)
