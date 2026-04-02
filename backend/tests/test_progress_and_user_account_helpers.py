from app.repositories.progress_state import apply_diagnostic_delta, build_area_score_map
from app.repositories.user_account_policies import build_login_candidates, normalize_login_candidate
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


def test_build_login_candidates_normalizes_and_deduplicates() -> None:
    normalized = normalize_login_candidate("  Nina Dev!  ")
    candidates = build_login_candidates("  Nina Dev!  ")

    assert normalized == "nina_dev"
    assert candidates
    assert all(candidate.lower() != normalized for candidate in candidates)
    assert len(candidates) == len({candidate.lower() for candidate in candidates})
