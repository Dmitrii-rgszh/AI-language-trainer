from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.models.grammar_topic import GrammarTopic as GrammarTopicModel
from app.models.pronunciation_drill import PronunciationDrill as PronunciationDrillModel
from app.models.profession_track import ProfessionTrack as ProfessionTrackModel
from app.models.speaking_scenario import SpeakingScenario as SpeakingScenarioModel
from app.models.writing_task import WritingTask as WritingTaskModel
from app.schemas.content import GrammarTopic, ProfessionTrackCard, PronunciationDrill, SpeakingScenario, WritingTask


class ContentRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def list_grammar_topics(self) -> list[GrammarTopic]:
        with self._session_factory() as session:
            statement = select(GrammarTopicModel).order_by(GrammarTopicModel.title.asc())
            models = session.scalars(statement).all()
            return [
                GrammarTopic(
                    id=model.id,
                    title=model.title,
                    level=model.level,
                    mastery=model.mastery,
                    explanation=model.explanation,
                    checkpoints=model.checkpoints,
                )
                for model in models
            ]

    def list_profession_tracks(self) -> list[ProfessionTrackCard]:
        with self._session_factory() as session:
            statement = select(ProfessionTrackModel).order_by(ProfessionTrackModel.title.asc())
            models = session.scalars(statement).all()
            return [
                ProfessionTrackCard(
                    id=model.id,
                    title=model.title,
                    domain=model.domain.value,
                    summary=model.summary,
                    lesson_focus=model.lesson_focus,
                )
                for model in models
            ]

    def list_speaking_scenarios(self) -> list[SpeakingScenario]:
        with self._session_factory() as session:
            statement = select(SpeakingScenarioModel).order_by(SpeakingScenarioModel.title.asc())
            models = session.scalars(statement).all()
            return [
                SpeakingScenario(
                    id=model.id,
                    title=model.title,
                    mode=model.mode,
                    goal=model.goal,
                    prompt=model.prompt,
                    feedback_hint=model.feedback_hint,
                )
                for model in models
            ]

    def list_pronunciation_drills(self) -> list[PronunciationDrill]:
        with self._session_factory() as session:
            statement = select(PronunciationDrillModel).order_by(PronunciationDrillModel.title.asc())
            models = session.scalars(statement).all()
            return [
                PronunciationDrill(
                    id=model.id,
                    title=model.title,
                    sound=model.sound,
                    focus=model.focus,
                    phrases=model.phrases,
                    difficulty=model.difficulty,
                )
                for model in models
            ]

    def get_primary_writing_task(self) -> WritingTask | None:
        with self._session_factory() as session:
            statement = select(WritingTaskModel).order_by(WritingTaskModel.title.asc()).limit(1)
            model = session.scalar(statement)
            if not model:
                return None

            return WritingTask(
                id=model.id,
                title=model.title,
                brief=model.brief,
                tone=model.tone,
                checklist=model.checklist,
                improved_version_preview=model.improved_version_preview,
            )
