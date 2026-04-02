from __future__ import annotations

from sqlalchemy.orm import Session

from app.content.grammar.catalog import GRAMMAR_TOPIC_CATALOG
from app.content.profession.catalog import PROFESSION_TOPIC_CATALOG, PROFESSION_TRACK_CATALOG
from app.content.pronunciation.catalog import PRONUNCIATION_DRILL_CATALOG
from app.content.speaking.catalog import SPEAKING_SCENARIO_CATALOG
from app.content.writing.catalog import WRITING_TASK_CATALOG
from app.models.grammar_topic import GrammarTopic
from app.models.pronunciation_drill import PronunciationDrill
from app.models.profession_topic import ProfessionTopic
from app.models.profession_track import ProfessionTrack
from app.models.speaking_scenario import SpeakingScenario
from app.models.writing_task import WritingTask


def upsert_grammar_topics(session: Session) -> dict[str, GrammarTopic]:
    persisted: dict[str, GrammarTopic] = {}
    for spec in GRAMMAR_TOPIC_CATALOG:
        model = session.get(GrammarTopic, spec["id"])
        if not model:
            model = GrammarTopic(id=spec["id"])
            session.add(model)

        model.title = spec["title"]
        model.level = spec["level"]
        model.mastery = spec["mastery"]
        model.explanation = spec["explanation"]
        model.checkpoints = spec["checkpoints"]
        persisted[model.id] = model
    return persisted


def upsert_profession_tracks(session: Session) -> None:
    for spec in PROFESSION_TRACK_CATALOG:
        model = session.get(ProfessionTrack, spec["id"])
        if not model:
            model = ProfessionTrack(id=spec["id"])
            session.add(model)

        model.title = spec["title"]
        model.domain = spec["domain"]
        model.summary = spec["summary"]
        model.lesson_focus = spec["lesson_focus"]


def upsert_profession_topics(session: Session) -> dict[str, ProfessionTopic]:
    persisted: dict[str, ProfessionTopic] = {}
    for spec in PROFESSION_TOPIC_CATALOG:
        model = session.get(ProfessionTopic, spec["id"])
        if not model:
            model = ProfessionTopic(id=spec["id"])
            session.add(model)

        model.domain = spec["domain"]
        model.title = spec["title"]
        model.difficulty = spec["difficulty"]
        model.content = spec["content"]
        model.examples = spec["examples"]
        model.tags = spec["tags"]
        persisted[model.id] = model
    return persisted


def upsert_speaking_scenarios(session: Session) -> None:
    for spec in SPEAKING_SCENARIO_CATALOG:
        model = session.get(SpeakingScenario, spec["id"])
        if not model:
            model = SpeakingScenario(id=spec["id"])
            session.add(model)

        model.title = spec["title"]
        model.mode = spec["mode"]
        model.goal = spec["goal"]
        model.prompt = spec["prompt"]
        model.feedback_hint = spec["feedback_hint"]


def upsert_pronunciation_drills(session: Session) -> None:
    for spec in PRONUNCIATION_DRILL_CATALOG:
        model = session.get(PronunciationDrill, spec["id"])
        if not model:
            model = PronunciationDrill(id=spec["id"])
            session.add(model)

        model.title = spec["title"]
        model.sound = spec["sound"]
        model.focus = spec["focus"]
        model.phrases = spec["phrases"]
        model.difficulty = spec["difficulty"]


def upsert_writing_tasks(session: Session) -> None:
    for spec in WRITING_TASK_CATALOG:
        model = session.get(WritingTask, spec["id"])
        if not model:
            model = WritingTask(id=spec["id"])
            session.add(model)

        model.title = spec["title"]
        model.brief = spec["brief"]
        model.tone = spec["tone"]
        model.checklist = spec["checklist"]
        model.improved_version_preview = spec["improved_version_preview"]
