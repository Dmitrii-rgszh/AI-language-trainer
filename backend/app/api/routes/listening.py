from fastapi import APIRouter, Depends

from app.api.dependencies import require_profile
from app.core.dependencies import listening_service
from app.schemas.listening import ListeningAttempt, ListeningTrend
from app.schemas.profile import UserProfile

router = APIRouter(prefix="/listening", tags=["listening"])


@router.get("/history", response_model=list[ListeningAttempt])
def get_listening_history(profile: UserProfile = Depends(require_profile)) -> list[ListeningAttempt]:
    return listening_service.list_attempts(profile.id)


@router.get("/trends", response_model=ListeningTrend)
def get_listening_trends(profile: UserProfile = Depends(require_profile)) -> ListeningTrend:
    return listening_service.get_trends(profile.id)
