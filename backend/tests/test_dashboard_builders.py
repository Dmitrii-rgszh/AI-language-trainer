from app.api.routes.dashboard_builders import (
    build_dashboard_data,
    build_quick_actions,
    build_resume_lesson_card,
    profession_hub_description,
)
from app.schemas.adaptive import AdaptiveStudyLoop, AdaptiveStudyLoop, AdaptiveStudyLoop
from app.schemas.adaptive import (
    AdaptiveLoopStep,
    MistakeResolutionSignal,
    MistakeVocabularyBacklink,
    ModuleRotationItem,
    VocabularyLoopSummary,
    VocabularyReviewItem,
)
from app.schemas.content import DashboardData
from app.schemas.journey import DailyLoopPlan, DailyLoopStep, LearnerJourneyState
from app.schemas.lesson import (
    Lesson,
    LessonBlock,
    LessonBlockRunState,
    LessonRecommendation,
    LessonRunState,
)
from app.schemas.mistake import WeakSpot
from app.schemas.profile import OnboardingAnswers, UserProfile
from app.schemas.progress import ProgressSnapshot


def _build_profile() -> UserProfile:
    return UserProfile(
        id="user-1",
        name="Nina",
        native_language="ru",
        current_level="A2",
        target_level="B2",
        profession_track="trainer_skills",
        preferred_ui_language="ru",
        preferred_explanation_language="ru",
        lesson_duration=20,
        speaking_priority=9,
        grammar_priority=7,
        profession_priority=8,
        onboarding_answers=OnboardingAnswers(),
    )


def _build_progress() -> ProgressSnapshot:
    return ProgressSnapshot(
        id="snapshot-1",
        grammar_score=52,
        speaking_score=58,
        listening_score=49,
        pronunciation_score=46,
        writing_score=54,
        profession_score=61,
        regulation_score=0,
        streak=3,
        daily_goal_minutes=20,
        minutes_completed_today=12,
        history=[],
    )


def _build_study_loop() -> AdaptiveStudyLoop:
    return AdaptiveStudyLoop(
        focus_area="grammar",
        headline="Focus",
        summary="Summary",
        recommendation=LessonRecommendation(
            id="lesson-1",
            title="Recovery lesson",
            lesson_type="recovery",
            goal="Fix recurring mistakes.",
            duration=20,
            focus_area="grammar",
        ),
        weak_spots=[],
        due_vocabulary=[
            VocabularyReviewItem(
                id="vocab-1",
                word="have worked",
                translation="pattern",
                context="I have worked here since 2022.",
                category="mistake_tense_patterns",
                source_module="speaking",
                review_reason="reason",
                linked_mistake_subtype="tense-choice",
                linked_mistake_title="Present Perfect vs Past Simple",
                learned_status="active",
                repetition_stage=2,
                due_now=True,
            )
        ],
        vocabulary_backlinks=[
            MistakeVocabularyBacklink(
                weak_spot_title="Present Perfect vs Past Simple",
                weak_spot_category="grammar",
                due_count=1,
                active_count=1,
                example_words=["have worked"],
                source_modules=["speaking"],
            )
        ],
        mistake_resolution=[
            MistakeResolutionSignal(
                weak_spot_title="Present Perfect vs Past Simple",
                weak_spot_category="grammar",
                status="recovering",
                repetition_count=2,
                last_seen_days_ago=2,
                linked_vocabulary_count=1,
                resolution_hint="Pattern is easing.",
            )
        ],
        module_rotation=[
            ModuleRotationItem(
                module_key="recovery",
                title="Recovery",
                reason="Recent weak spots",
                route="/activity",
                priority=1,
            )
        ],
        vocabulary_summary=VocabularyLoopSummary(
            due_count=1,
            new_count=0,
            active_count=3,
            mastered_count=1,
            weakest_category="grammar",
        ),
        listening_focus="audio_comprehension",
        generation_rationale=["Reason"],
        next_steps=[
            AdaptiveLoopStep(
                id="next-1",
                title="Start",
                description="Continue",
                route="/activity",
                step_type="recovery",
            )
        ],
    )


def _build_active_run() -> LessonRunState:
    return LessonRunState(
        run_id="run-1",
        status="in_progress",
        started_at="2026-04-02T10:00:00",
        lesson=Lesson(
            id="lesson-1",
            lesson_type="recovery",
            title="Recovery lesson",
            goal="Fix recurring mistakes.",
            difficulty="A2",
            duration=20,
            modules=["review_block", "grammar_block"],
            blocks=[
                LessonBlock(
                    id="block-1",
                    block_type="review_block",
                    title="Review",
                    instructions="Review",
                    estimated_minutes=5,
                    payload={},
                ),
                LessonBlock(
                    id="block-2",
                    block_type="grammar_block",
                    title="Grammar",
                    instructions="Practice",
                    estimated_minutes=10,
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
                user_response="Done",
                transcript=None,
                feedback_summary=None,
                score=80,
            ),
            LessonBlockRunState(
                id="run-block-2",
                block_id="block-2",
                status="active",
                user_response_type="text",
                user_response=None,
                transcript=None,
                feedback_summary=None,
                score=None,
            ),
        ],
    )


def _build_daily_loop_plan() -> DailyLoopPlan:
    return DailyLoopPlan(
        id="daily-loop-1",
        plan_date_key="2026-04-13",
        status="planned",
        stage="first_path",
        session_kind="recommended",
        focus_area="grammar",
        headline="Nina, your daily loop is ready.",
        summary="A focused first loop around grammar and speaking.",
        why_this_now="The current plan keeps the first path simple and connected.",
        next_step_hint="Start the loop and finish one guided session.",
        preferred_mode="mixed",
        time_budget_minutes=20,
        estimated_minutes=20,
        recommended_lesson_type="recovery",
        recommended_lesson_title="Recovery lesson",
        lesson_run_id=None,
        completed_at=None,
        steps=[
            DailyLoopStep(
                id="warm-start",
                skill="coach",
                title="Warm start",
                description="Liza frames the session.",
                duration_minutes=2,
            )
        ],
    )


def _build_journey_state() -> LearnerJourneyState:
    return LearnerJourneyState(
        user_id="user-1",
        stage="daily_loop_ready",
        source="proof_lesson",
        preferred_mode="mixed",
        diagnostic_readiness="soft_start",
        time_budget_minutes=20,
        current_focus_area="grammar",
        current_strategy_summary="Keep the next step focused on grammar first, then widen into speaking.",
        next_best_action="Open the daily loop and complete one guided session.",
        last_daily_plan_id="daily-loop-1",
        proof_lesson_handoff=None,
        strategy_snapshot={"focusArea": "grammar"},
        onboarding_completed_at="2026-04-13T10:00:00",
        created_at="2026-04-13T10:00:00",
        updated_at="2026-04-13T10:00:00",
    )


def test_build_quick_actions_prioritizes_focus_and_avoids_duplicate_routes() -> None:
    actions = build_quick_actions(
        profile=_build_profile(),
        weak_spots=[
            WeakSpot(
                id="weak-1",
                title="Present Perfect vs Past Simple",
                category="grammar",
                recommendation="Review tense contrast.",
            )
        ],
        due_vocabulary_count=1,
    )

    assert actions
    assert actions[0].route == "/grammar"
    assert len({action.route for action in actions}) == len(actions)


def test_build_resume_lesson_card_points_to_current_block() -> None:
    card = build_resume_lesson_card(_build_active_run())

    assert card is not None
    assert card.completed_blocks == 1
    assert card.current_block_title == "Grammar"


def test_build_dashboard_data_wraps_all_sections() -> None:
    data = build_dashboard_data(
        profile=_build_profile(),
        progress=_build_progress(),
        weak_spots=[],
        recommendation=LessonRecommendation(
            id="lesson-1",
            title="Recovery lesson",
            lesson_type="recovery",
            goal="Fix recurring mistakes.",
            duration=20,
            focus_area="grammar",
        ),
        study_loop=_build_study_loop(),
        daily_loop_plan=_build_daily_loop_plan(),
        journey_state=_build_journey_state(),
        active_run=_build_active_run(),
    )

    assert isinstance(data, DashboardData)
    assert data.resume_lesson is not None
    assert data.quick_actions
    assert data.daily_loop_plan is not None
    assert data.journey_state is not None
    assert profession_hub_description("trainer_skills").startswith("Feedback language")
