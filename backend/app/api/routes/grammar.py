from fastapi import APIRouter

from app.core.dependencies import grammar_service
from app.schemas.content import GrammarTopic

router = APIRouter(prefix="/grammar", tags=["grammar"])


@router.get("/topics", response_model=list[GrammarTopic])
def get_grammar_topics() -> list[GrammarTopic]:
    return grammar_service.get_topics()

