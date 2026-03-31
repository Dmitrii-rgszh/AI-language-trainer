from __future__ import annotations

from datetime import date, datetime

from sqlalchemy.orm import Session

from app.content.bootstrap import bootstrap_content
from app.db.session import SessionLocal
from app.models.lesson_run import LessonBlockRun, LessonRun
from app.models.lesson_template import LessonTemplate
from app.models.mistake_record import MistakeRecord
from app.models.progress_snapshot import ProgressSkillScore, ProgressSnapshot
from app.models.user_profile import UserProfile
from app.models.vocabulary_item import VocabularyItem
from app.schemas.blueprint import (
    BlockRunStatus,
    LessonRunStatus,
    MistakeCategory,
    MistakeSeverity,
    ProfessionDomain,
    SkillArea,
    UserResponseType,
    VocabularyStatus,
)


def seed_user(session: Session) -> UserProfile:
    user = session.get(UserProfile, "user-local-1")
    if user:
        return user

    user = UserProfile(
        id="user-local-1",
        name="Alex",
        native_language="ru",
        current_level="A2",
        target_level="B2",
        profession_track=ProfessionDomain.TRAINER_SKILLS,
        preferred_ui_language="ru",
        preferred_explanation_language="ru",
        lesson_duration=25,
        speaking_priority=8,
        grammar_priority=7,
        profession_priority=9,
    )
    session.add(user)
    return user


def seed_runtime_data(session: Session, user: UserProfile, template: LessonTemplate) -> None:
    lesson_run = session.get(LessonRun, "run-1")
    if not lesson_run:
        lesson_run = LessonRun(
            id="run-1",
            user_id=user.id,
            template_id=template.id,
            status=LessonRunStatus.COMPLETED,
            recommended_by="recommendation_engine_v1",
            weak_spot_ids=["mistake-1", "mistake-3"],
            started_at=datetime(2026, 3, 19, 18, 0, 0),
            completed_at=datetime(2026, 3, 19, 18, 24, 0),
            score=78,
        )
        session.add(lesson_run)

    if not session.get(LessonBlockRun, "block-run-1"):
        session.add_all(
            [
                LessonBlockRun(
                    id="block-run-1",
                    lesson_run_id="run-1",
                    block_id="block-review-1",
                    status=BlockRunStatus.COMPLETED,
                    user_response_type=UserResponseType.TEXT,
                    user_response="Reviewed previous mistakes and repeated correct versions.",
                    transcript=None,
                    feedback_summary="Good recall. Keep tense consistency in work updates.",
                    score=80,
                    started_at=datetime(2026, 3, 19, 18, 0, 0),
                    completed_at=datetime(2026, 3, 19, 18, 4, 0),
                ),
                LessonBlockRun(
                    id="block-run-2",
                    lesson_run_id="run-1",
                    block_id="block-speaking-1",
                    status=BlockRunStatus.COMPLETED,
                    user_response_type=UserResponseType.TEXT,
                    user_response="I have improved my workshop openings and I have added more examples for managers.",
                    transcript=None,
                    feedback_summary="Strong clarity. Watch Present Perfect with time references.",
                    score=76,
                    started_at=datetime(2026, 3, 19, 18, 10, 0),
                    completed_at=datetime(2026, 3, 19, 18, 17, 0),
                ),
            ]
        )

    if not session.get(MistakeRecord, "mistake-1"):
        session.add_all(
            [
                MistakeRecord(
                    id="mistake-1",
                    user_id=user.id,
                    category=MistakeCategory.GRAMMAR,
                    subtype="tense-choice",
                    source_module="speaking",
                    source_block_run_id="block-run-2",
                    original_text="I work with this team since 2022.",
                    corrected_text="I have worked with this team since 2022.",
                    explanation="Нужен Present Perfect, потому что действие началось в прошлом и продолжается сейчас.",
                    severity=MistakeSeverity.MEDIUM,
                    repetition_count=4,
                    created_at=datetime(2026, 3, 10, 18, 0, 0),
                    last_seen_at=datetime(2026, 3, 19, 18, 15, 0),
                ),
                MistakeRecord(
                    id="mistake-3",
                    user_id=user.id,
                    category=MistakeCategory.PROFESSION,
                    subtype="feedback-language",
                    source_module="profession",
                    source_block_run_id="block-run-2",
                    original_text="This part is wrong.",
                    corrected_text="This part could be clearer for the audience.",
                    explanation="Для trainer context лучше использовать мягкие формулировки.",
                    severity=MistakeSeverity.MEDIUM,
                    repetition_count=3,
                    created_at=datetime(2026, 3, 11, 19, 0, 0),
                    last_seen_at=datetime(2026, 3, 19, 18, 19, 0),
                ),
            ]
        )

    if not session.get(ProgressSnapshot, "snapshot-1"):
        snapshot = ProgressSnapshot(
            id="snapshot-1",
            user_id=user.id,
            lesson_run_id="run-1",
            snapshot_date=date(2026, 3, 19),
            daily_goal_minutes=25,
            minutes_completed_today=24,
            streak=6,
        )
        snapshot.skill_scores = [
            ProgressSkillScore(
                area=SkillArea.GRAMMAR,
                score=54,
                confidence=72,
                updated_at=datetime(2026, 3, 19, 18, 24, 0),
            ),
            ProgressSkillScore(
                area=SkillArea.SPEAKING,
                score=48,
                confidence=64,
                updated_at=datetime(2026, 3, 19, 18, 24, 0),
            ),
            ProgressSkillScore(
                area=SkillArea.PROFESSION_ENGLISH,
                score=46,
                confidence=58,
                updated_at=datetime(2026, 3, 19, 18, 24, 0),
            ),
        ]
        session.add(snapshot)

    if not session.get(VocabularyItem, "vocab-1"):
        session.add(
            VocabularyItem(
                id="vocab-1",
                user_id=user.id,
                word="stakeholder",
                translation="заинтересованная сторона",
                context="Our stakeholders have asked for a shorter training format.",
                category="trainer_skills",
                learned_status=VocabularyStatus.ACTIVE,
                repetition_stage=2,
                last_reviewed_at=datetime(2026, 3, 19, 18, 25, 0),
            )
        )


def main() -> None:
    with SessionLocal() as session:
        bootstrap_content(session)
        session.flush()
        user = seed_user(session)
        template = session.get(LessonTemplate, "template-trainer-daily-flow")
        if not template:
            raise RuntimeError("Expected content bootstrap to create template-trainer-daily-flow.")
        seed_runtime_data(session, user, template)
        session.commit()
        print("Demo data seeded successfully.")


if __name__ == "__main__":
    main()
