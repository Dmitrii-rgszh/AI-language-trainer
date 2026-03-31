from app.repositories.content_repository import ContentRepository
from app.schemas.content import GrammarTopic


class GrammarService:
    def __init__(self, repository: ContentRepository) -> None:
        self._repository = repository

    def get_topics(self) -> list[GrammarTopic]:
        return self._repository.list_grammar_topics()
