from fastapi import APIRouter

from app.api.dependencies import require_profile
from app.core.dependencies import listening_service
from app.schemas.listening import ListeningAttempt, ListeningTrend

router = APIRouter(prefix="/listening", tags=["listening"])


@router.get("/history", response_model=list[ListeningAttempt])
def get_listening_history() -> list[ListeningAttempt]:
    return listening_service.list_attempts(require_profile().id)


@router.get("/trends", response_model=ListeningTrend)
def get_listening_trends() -> ListeningTrend:
    return listening_service.get_trends(require_profile().id)
