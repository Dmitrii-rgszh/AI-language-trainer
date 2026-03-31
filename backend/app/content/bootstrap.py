from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.content.grammar.catalog import GRAMMAR_TOPIC_CATALOG
from app.content.lessons.catalog import LESSON_TEMPLATE_CATALOG
from app.content.pronunciation.catalog import PRONUNCIATION_DRILL_CATALOG
from app.content.profession.catalog import PROFESSION_TOPIC_CATALOG, PROFESSION_TRACK_CATALOG
from app.content.speaking.catalog import SPEAKING_SCENARIO_CATALOG
from app.content.writing.catalog import WRITING_TASK_CATALOG
from app.models.grammar_topic import GrammarTopic
from app.models.lesson_template import LessonBlock, LessonTemplate
from app.models.pronunciation_drill import PronunciationDrill
from app.models.profession_topic import ProfessionTopic
from app.models.profession_track import ProfessionTrack
from app.models.speaking_scenario import SpeakingScenario
from app.models.writing_task import WritingTask


def bootstrap_content(session: Session) -> None:
    grammar_topics = _upsert_grammar_topics(session)
    profession_topics = _upsert_profession_topics(session)
    _upsert_profession_tracks(session)
    _upsert_speaking_scenarios(session)
    _upsert_pronunciation_drills(session)
    _upsert_writing_tasks(session)
    _upsert_lesson_templates(session, grammar_topics=grammar_topics, profession_topics=profession_topics)


def _upsert_grammar_topics(session: Session) -> dict[str, GrammarTopic]:
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


def _upsert_profession_tracks(session: Session) -> None:
    for spec in PROFESSION_TRACK_CATALOG:
        model = session.get(ProfessionTrack, spec["id"])
        if not model:
            model = ProfessionTrack(id=spec["id"])
            session.add(model)

        model.title = spec["title"]
        model.domain = spec["domain"]
        model.summary = spec["summary"]
        model.lesson_focus = spec["lesson_focus"]


def _upsert_profession_topics(session: Session) -> dict[str, ProfessionTopic]:
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


def _upsert_speaking_scenarios(session: Session) -> None:
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


def _upsert_pronunciation_drills(session: Session) -> None:
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


def _upsert_writing_tasks(session: Session) -> None:
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


def _upsert_lesson_templates(
    session: Session,
    grammar_topics: dict[str, GrammarTopic],
    profession_topics: dict[str, ProfessionTopic],
) -> None:
    for spec in LESSON_TEMPLATE_CATALOG:
        template = session.get(LessonTemplate, spec["id"])
        if not template:
            template = LessonTemplate(id=spec["id"])
            session.add(template)

        template.lesson_type = spec["lesson_type"]
        template.title = spec["title"]
        template.goal = spec["goal"]
        template.difficulty = spec["difficulty"]
        template.estimated_duration = spec["estimated_duration"]
        template.enabled_tracks = spec["enabled_tracks"]
        template.generation_rules = spec["generation_rules"]
        template.profession_topics = [
            profession_topics[topic_id] for topic_id in spec.get("profession_topic_ids", []) if topic_id in profession_topics
        ]

        existing_blocks = {
            block.id: block
            for block in session.scalars(select(LessonBlock).where(LessonBlock.lesson_template_id == template.id)).all()
        }

        for block_spec in spec["blocks"]:
            _ensure_referenced_content_exists(block_spec["payload"], grammar_topics, profession_topics)

            block = existing_blocks.get(block_spec["id"])
            if not block:
                block = LessonBlock(id=block_spec["id"], lesson_template=template)
                session.add(block)

            block.lesson_template = template
            block.position = block_spec["position"]
            block.block_type = block_spec["block_type"]
            block.title = block_spec["title"]
            block.instructions = block_spec["instructions"]
            block.estimated_minutes = block_spec["estimated_minutes"]
            block.feedback_mode = block_spec["feedback_mode"]
            block.depends_on_block_ids = block_spec["depends_on_block_ids"]
            block.payload = block_spec["payload"]


def _ensure_referenced_content_exists(
    payload: dict,
    grammar_topics: dict[str, GrammarTopic],
    profession_topics: dict[str, ProfessionTopic],
) -> None:
    topic_id = payload.get("topicId")
    domain = payload.get("domain")

    if domain and topic_id and topic_id not in profession_topics:
        raise ValueError(f"Profession topic '{topic_id}' referenced in lesson block but not found in catalog.")

    if topic_id and topic_id.startswith("grammar-") and topic_id not in grammar_topics:
        raise ValueError(f"Grammar topic '{topic_id}' referenced in lesson block but not found in catalog.")
