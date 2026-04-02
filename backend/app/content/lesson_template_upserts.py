from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.content.lessons.catalog import LESSON_TEMPLATE_CATALOG
from app.models.grammar_topic import GrammarTopic
from app.models.lesson_template import LessonBlock, LessonTemplate
from app.models.profession_topic import ProfessionTopic


def upsert_lesson_templates(
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
            profession_topics[topic_id]
            for topic_id in spec.get("profession_topic_ids", [])
            if topic_id in profession_topics
        ]

        existing_blocks = {
            block.id: block
            for block in session.scalars(
                select(LessonBlock).where(LessonBlock.lesson_template_id == template.id)
            ).all()
        }

        for block_spec in spec["blocks"]:
            ensure_referenced_content_exists(
                block_spec["payload"], grammar_topics, profession_topics
            )

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


def ensure_referenced_content_exists(
    payload: dict,
    grammar_topics: dict[str, GrammarTopic],
    profession_topics: dict[str, ProfessionTopic],
) -> None:
    topic_id = payload.get("topicId")
    domain = payload.get("domain")

    if domain and topic_id and topic_id not in profession_topics:
        raise ValueError(
            f"Profession topic '{topic_id}' referenced in lesson block but not found in catalog."
        )

    if topic_id and topic_id.startswith("grammar-") and topic_id not in grammar_topics:
        raise ValueError(
            f"Grammar topic '{topic_id}' referenced in lesson block but not found in catalog."
        )
