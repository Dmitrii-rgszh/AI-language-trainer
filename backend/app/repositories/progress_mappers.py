from __future__ import annotations

from app.models.progress_snapshot import ProgressSnapshot as ProgressSnapshotModel
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


def to_progress_snapshot(
    model: ProgressSnapshotModel, history: list[LessonHistoryItem]
) -> ProgressSnapshot:
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
