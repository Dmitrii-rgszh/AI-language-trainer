from datetime import date

from app.models.progress_snapshot import ProgressSkillScore, ProgressSnapshot
from app.repositories.progress_state import (
    apply_diagnostic_delta,
    apply_guided_delta,
    build_area_score_map,
    build_progress_snapshot_model,
)
from app.schemas.blueprint import SkillArea
from app.repositories.user_account_policies import build_login_candidates, normalize_login_candidate
from app.schemas.profile import OnboardingAnswers, UserProfile
from app.schemas.lesson import Lesson, LessonBlock, LessonBlockRunState, LessonRunState


def test_build_area_score_map_groups_scores_by_skill_area() -> None:
    lesson_run = LessonRunState(
        run_id="run-1",
        status="completed",
        started_at="2026-04-02T10:00:00",
        completed_at="2026-04-02T10:10:00",
        score=80,
        lesson=Lesson(
            id="lesson-1",
            lesson_type="mixed",
            title="Test lesson",
            goal="Goal",
            difficulty="A2",
            duration=10,
            modules=["grammar_block", "speaking_block"],
            blocks=[
                LessonBlock(
                    id="block-1",
                    block_type="grammar_block",
                    title="Grammar",
                    instructions="",
                    estimated_minutes=5,
                    payload={},
                ),
                LessonBlock(
                    id="block-2",
                    block_type="speaking_block",
                    title="Speaking",
                    instructions="",
                    estimated_minutes=5,
                    payload={},
                ),
            ],
            completed=False,
            score=None,
        ),
        block_runs=[
            LessonBlockRunState(
                id="run-block-1",
                block_id="block-1",
                status="completed",
                user_response_type="text",
                user_response="Example",
                transcript=None,
                feedback_summary=None,
                score=72,
            ),
            LessonBlockRunState(
                id="run-block-2",
                block_id="block-2",
                status="completed",
                user_response_type="text",
                user_response="Example",
                transcript=None,
                feedback_summary=None,
                score=84,
            ),
        ],
    )

    score_map = build_area_score_map(lesson_run)

    assert score_map["grammar"] == 72
    assert score_map["speaking"] == 84


def test_apply_diagnostic_delta_handles_high_and_low_scores() -> None:
    assert apply_diagnostic_delta(50, 50, 82) == (55, 58)
    assert apply_diagnostic_delta(50, 50, 40) == (47, 45)


def test_apply_guided_delta_rewards_strong_signal_and_penalizes_fragile_one() -> None:
    assert apply_guided_delta(50, 50, 86, signal_count=2) == (55, 57)
    assert apply_guided_delta(50, 50, 44, signal_count=1) == (48, 47)


def test_build_progress_snapshot_model_uses_area_scores_per_skill() -> None:
    lesson_run = LessonRunState(
        run_id="run-2",
        status="completed",
        started_at="2026-04-02T10:00:00",
        completed_at="2026-04-02T10:16:00",
        score=74,
        lesson=Lesson(
            id="lesson-2",
            lesson_type="mixed",
            title="Guided route",
            goal="Goal",
            difficulty="A2",
            duration=16,
            modules=["grammar_block", "speaking_block", "speaking_block"],
            blocks=[
                LessonBlock(
                    id="block-1",
                    block_type="grammar_block",
                    title="Grammar",
                    instructions="",
                    estimated_minutes=5,
                    payload={},
                ),
                LessonBlock(
                    id="block-2",
                    block_type="speaking_block",
                    title="Speaking 1",
                    instructions="",
                    estimated_minutes=5,
                    payload={},
                ),
                LessonBlock(
                    id="block-3",
                    block_type="speaking_block",
                    title="Speaking 2",
                    instructions="",
                    estimated_minutes=6,
                    payload={},
                ),
            ],
            completed=False,
            score=None,
        ),
        block_runs=[
            LessonBlockRunState(
                id="run-block-1",
                block_id="block-1",
                status="completed",
                user_response_type="text",
                user_response="Example",
                transcript=None,
                feedback_summary=None,
                score=49,
            ),
            LessonBlockRunState(
                id="run-block-2",
                block_id="block-2",
                status="completed",
                user_response_type="voice",
                user_response="Example",
                transcript="Example",
                feedback_summary=None,
                score=82,
            ),
            LessonBlockRunState(
                id="run-block-3",
                block_id="block-3",
                status="completed",
                user_response_type="voice",
                user_response="Example",
                transcript="Example",
                feedback_summary=None,
                score=86,
            ),
        ],
    )
    profile = UserProfile(
        id="user-test",
        name="Nina",
        native_language="ru",
        current_level="A2",
        target_level="B1",
        profession_track="trainer_skills",
        preferred_ui_language="ru",
        preferred_explanation_language="ru",
        lesson_duration=20,
        speaking_priority=75,
        grammar_priority=70,
        profession_priority=62,
        onboarding_answers=OnboardingAnswers(
            primary_goal="work",
            preferred_mode="voice_first",
            diagnostic_readiness="soft_start",
            active_skill_focus=["speaking", "grammar"],
        ),
    )
    latest_snapshot = ProgressSnapshot(
        id="snapshot-previous",
        user_id=profile.id,
        lesson_run_id="run-prev",
        snapshot_date=date.today(),
        daily_goal_minutes=20,
        minutes_completed_today=10,
        streak=3,
    )
    latest_snapshot.skill_scores = [
        ProgressSkillScore(area=SkillArea.GRAMMAR, score=55, confidence=55),
        ProgressSkillScore(area=SkillArea.SPEAKING, score=55, confidence=55),
    ]

    snapshot = build_progress_snapshot_model(profile, lesson_run, latest_snapshot)
    scores = {item.area: (item.score, item.confidence) for item in snapshot.skill_scores}

    assert scores[SkillArea.SPEAKING][0] > scores[SkillArea.GRAMMAR][0]
    assert scores[SkillArea.SPEAKING][1] > scores[SkillArea.GRAMMAR][1]
    assert scores[SkillArea.GRAMMAR][0] <= 55
    assert snapshot.minutes_completed_today >= 26


def test_build_login_candidates_normalizes_and_deduplicates() -> None:
    normalized = normalize_login_candidate("  Nina Dev!  ")
    candidates = build_login_candidates("  Nina Dev!  ")

    assert normalized == "nina_dev"
    assert candidates
    assert all(candidate.lower() != normalized for candidate in candidates)
    assert len(candidates) == len({candidate.lower() for candidate in candidates})
