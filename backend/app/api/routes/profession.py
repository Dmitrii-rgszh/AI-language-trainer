from fastapi import APIRouter

from app.core.dependencies import profession_service
from app.schemas.content import ProfessionTrackCard

router = APIRouter(prefix="/profession", tags=["profession"])


@router.get("/tracks", response_model=list[ProfessionTrackCard])
def get_profession_tracks() -> list[ProfessionTrackCard]:
    return profession_service.get_tracks()

