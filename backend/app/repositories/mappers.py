from __future__ import annotations

from app.models.lesson_run import LessonRun
from app.models.lesson_template import LessonBlock as LessonBlockModel
from app.models.lesson_template import LessonTemplate
from app.models.mistake_record import MistakeRecord
from app.models.progress_snapshot import ProgressSnapshot as ProgressSnapshotModel
from app.models.user_provider_preference import UserProviderPreference as UserProviderPreferenceModel
from app.models.user_profile import UserProfile as UserProfileModel
from app.schemas.lesson import Lesson, LessonBlock, LessonBlockRunState, LessonRecommendation, LessonRunState
from app.schemas.mistake import Mistake
from app.schemas.provider import ProviderPreference
from app.schemas.profile import UserProfile
from app.schemas.progress import LessonHistoryItem, ProgressSnapshot


SKILL_AREA_TO_PROGRESS_FIELD = {
    "grammar": "grammar_score",
    "speaking": "speaking_score",
    "listening": "listening_score",
    "pronunciation": "pronunciation_score",
    "writing": "writing_score",
    "profession_english": "profession_score",
    "regulation_eu": "regulation_score",
}


def to_user_profile(model: UserProfileModel) -> UserProfile:
    return UserProfile(
        id=model.id,
        name=model.name,
        native_language=model.native_language,
        current_level=model.current_level,
        target_level=model.target_level,
        profession_track=model.profession_track.value,
        preferred_ui_language=model.preferred_ui_language,
        preferred_explanation_language=model.preferred_explanation_language,
        lesson_duration=model.lesson_duration,
        speaking_priority=model.speaking_priority,
        grammar_priority=model.grammar_priority,
        profession_priority=model.profession_priority,
    )


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


def _focus_area(blocks: list[LessonBlockModel]) -> str:
    normalized = []
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
        focus_area=_focus_area(template.blocks),
    )


def to_lesson_history_item(model: LessonRun) -> LessonHistoryItem:
    return LessonHistoryItem(
        id=model.id,
        title=model.template.title if model.template else model.template_id,
        lesson_type=model.template.lesson_type.value if model.template else "mixed",
        completed_at=(model.completed_at or model.started_at).date().isoformat(),
        score=model.score or 0,
    )


def to_mistake(model: MistakeRecord) -> Mistake:
    return Mistake(
        id=model.id,
        category=model.category.value,
        subtype=model.subtype,
        source_module=model.source_module,
        original_text=model.original_text,
        corrected_text=model.corrected_text,
        explanation=model.explanation,
        repetition_count=model.repetition_count,
        last_seen_at=model.last_seen_at,
    )


def to_progress_snapshot(model: ProgressSnapshotModel, history: list[LessonHistoryItem]) -> ProgressSnapshot:
    values = {
        "grammar_score": 0,
        "speaking_score": 0,
        "listening_score": 0,
        "pronunciation_score": 0,
        "writing_score": 0,
        "profession_score": 0,
        "regulation_score": 0,
    }

    for skill_score in model.skill_scores:
        field_name = SKILL_AREA_TO_PROGRESS_FIELD.get(skill_score.area.value)
        if field_name:
            values[field_name] = skill_score.score

    return ProgressSnapshot(
        id=model.id,
        grammar_score=values["grammar_score"],
        speaking_score=values["speaking_score"],
        listening_score=values["listening_score"],
        pronunciation_score=values["pronunciation_score"],
        writing_score=values["writing_score"],
        profession_score=values["profession_score"],
        regulation_score=values["regulation_score"],
        streak=model.streak,
        daily_goal_minutes=model.daily_goal_minutes,
        minutes_completed_today=model.minutes_completed_today,
        history=history,
    )


def to_provider_preference(model: UserProviderPreferenceModel) -> ProviderPreference:
    return ProviderPreference(
        provider_type=model.provider_type.value,
        selected_provider=model.selected_provider,
        enabled=model.enabled,
        settings=model.settings or {},
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
