from __future__ import annotations

from app.models.lesson_run import LessonRun
from app.models.lesson_template import LessonBlock as LessonBlockModel
from app.models.lesson_template import LessonTemplate
from app.schemas.lesson import Lesson, LessonBlock, LessonBlockRunState, LessonRecommendation, LessonRunState
from app.schemas.progress import LessonHistoryItem


def to_lesson_block(model: LessonBlockModel) -> LessonBlock:
    return LessonBlock(
        id=model.id,
        block_type=model.block_type,
        title=model.title,
        instructions=model.instructions,
        estimated_minutes=model.estimated_minutes,
        payload=model.payload,
    )


def to_lesson(template: LessonTemplate) -> Lesson:
    blocks = [to_lesson_block(block) for block in template.blocks]
    return Lesson(
        id=template.id,
        lesson_type=template.lesson_type.value,
        title=template.title,
        goal=template.goal,
        difficulty=template.difficulty,
        duration=template.estimated_duration,
        modules=[block.block_type for block in blocks],
        blocks=blocks,
        completed=False,
        score=None,
    )


def focus_area(blocks: list[LessonBlockModel]) -> str:
    normalized: list[str] = []
    for block in blocks:
        value = block.block_type.replace("_block", "")
        if value not in {"review", "summary", "intro", "reflection"} and value not in normalized:
            normalized.append(value)
    return ",".join(normalized)


def to_lesson_recommendation(template: LessonTemplate) -> LessonRecommendation:
    return LessonRecommendation(
        id=template.id,
        title=template.title,
        lesson_type=template.lesson_type.value,
        goal=template.goal,
        duration=template.estimated_duration,
        focus_area=focus_area(template.blocks),
    )


def to_lesson_history_item(model: LessonRun) -> LessonHistoryItem:
    return LessonHistoryItem(
        id=model.id,
        title=model.template.title if model.template else model.template_id,
        lesson_type=model.template.lesson_type.value if model.template else "mixed",
        completed_at=(model.completed_at or model.started_at).date().isoformat(),
        score=model.score or 0,
    )


def to_lesson_run_state(model: LessonRun) -> LessonRunState:
    if not model.template:
        raise ValueError("LessonRunState requires template relationship to be loaded.")

    return LessonRunState(
        run_id=model.id,
        status=model.status.value,
        started_at=model.started_at.isoformat(),
        completed_at=model.completed_at.isoformat() if model.completed_at else None,
        score=model.score,
        lesson=to_lesson(model.template),
        block_runs=[
            LessonBlockRunState(
                id=block_run.id,
                block_id=block_run.block_id,
                status=block_run.status.value,
                user_response_type=block_run.user_response_type.value,
                user_response=block_run.user_response,
                transcript=block_run.transcript,
                feedback_summary=block_run.feedback_summary,
                score=block_run.score,
            )
            for block_run in sorted(model.block_runs, key=lambda item: item.started_at)
        ],
    )
