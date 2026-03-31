from app.repositories.content_repository import ContentRepository
from app.schemas.content import ProfessionTrackCard


class ProfessionService:
    def __init__(self, repository: ContentRepository) -> None:
        self._repository = repository

    def get_tracks(self) -> list[ProfessionTrackCard]:
        return self._repository.list_profession_tracks()
