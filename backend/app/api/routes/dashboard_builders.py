from __future__ import annotations

from app.schemas.journey import DailyLoopPlan, LearnerJourneyState
from app.schemas.adaptive import AdaptiveStudyLoop
from app.schemas.content import DashboardData, QuickAction, ResumeLessonCard
from app.schemas.lesson import LessonRecommendation, LessonRunState
from app.schemas.mistake import WeakSpot
from app.schemas.profile import UserProfile
from app.schemas.progress import ProgressSnapshot


def build_quick_actions(
    profile: UserProfile,
    weak_spots: list[WeakSpot],
    due_vocabulary_count: int,
) -> list[QuickAction]:
    actions: list[QuickAction] = []
    seen_routes: set[str] = set()
    primary_focus = weak_spots[0].category if weak_spots else None

    def push(action: QuickAction) -> None:
        if action.route in seen_routes:
            return
        actions.append(action)
        seen_routes.add(action.route)

    category_actions = {
        "grammar": QuickAction(
            id="quick-grammar",
            title="Grammar Sprint",
            description="Tight review of the current grammar weak spot before the next full lesson.",
            route="/grammar",
        ),
        "speaking": QuickAction(
            id="quick-speaking",
            title="Speaking Check-in",
            description="Short guided speaking with focused feedback before the next full lesson.",
            route="/speaking",
        ),
        "profession": QuickAction(
            id="quick-profession",
            title="Profession Hub",
            description=profession_hub_description(profile.profession_track),
            route="/profession",
        ),
        "pronunciation": QuickAction(
            id="quick-pronunciation",
            title="Pronunciation Lab",
            description="Clear the top weak sound and keep your speech more stable before the next speaking block.",
            route="/pronunciation",
        ),
        "writing": QuickAction(
            id="quick-writing",
            title="Writing Coach",
            description="Tighten wording, structure and tone in a short guided writing pass.",
            route="/writing",
        ),
        "vocabulary": QuickAction(
            id="quick-vocabulary",
            title="Vocabulary Hub",
            description="Review due words linked to recent mistakes and keep the queue under control.",
            route="/vocabulary",
        ),
    }

    if primary_focus and primary_focus in category_actions:
        push(category_actions[primary_focus])

    prioritized_modules = sorted(
        [
            ("speaking", profile.speaking_priority),
            ("grammar", profile.grammar_priority),
            ("profession", profile.profession_priority),
        ],
        key=lambda item: item[1],
        reverse=True,
    )
    for module_key, _ in prioritized_modules:
        action = category_actions[module_key]
        if action.route not in seen_routes:
            push(action)
        if len(actions) >= 2:
            break

    push(
        QuickAction(
            id="quick-profession-track",
            title="Profession Hub",
            description=profession_hub_description(profile.profession_track),
            route="/profession",
        )
    )

    if due_vocabulary_count > 0:
        push(category_actions["vocabulary"])
    else:
        push(
            QuickAction(
                id="quick-adaptive",
                title="Adaptive Loop",
                description="Recovery focus, vocabulary repetition and next study step in one flow.",
                route="/activity",
            )
        )

    if len(actions) < 4:
        push(
            QuickAction(
                id="quick-activity",
                title="Adaptive Loop",
                description="Recovery focus, vocabulary repetition and next study step in one flow.",
                route="/activity",
            )
        )

    return actions[:4]


def profession_hub_description(profession_track: str) -> str:
    return {
        "trainer_skills": "Feedback language, facilitation phrasing and workshop English for your current track.",
        "insurance": "Protection language, needs analysis and client follow-up for your current track.",
        "banking": "Product explanations, transfer updates and client-friendly banking phrasing.",
        "ai_business": "Workflow explanations, guardrails and business-facing AI language for your current track.",
    }.get(profession_track, "Professional English for the current track.")


def build_resume_lesson_card(active_run: LessonRunState | None) -> ResumeLessonCard | None:
    if active_run is None:
        return None

    completed_blocks = sum(1 for block in active_run.block_runs if block.status == "completed")
    current_index = min(completed_blocks, max(len(active_run.lesson.blocks) - 1, 0))
    return ResumeLessonCard(
        run_id=active_run.run_id,
        title=active_run.lesson.title,
        current_block_title=active_run.lesson.blocks[current_index].title,
        completed_blocks=completed_blocks,
        total_blocks=len(active_run.lesson.blocks),
        route="/lesson-runner",
    )


def build_dashboard_data(
    profile: UserProfile,
    progress: ProgressSnapshot,
    weak_spots: list[WeakSpot],
    recommendation: LessonRecommendation,
    study_loop: AdaptiveStudyLoop | None,
    daily_loop_plan: DailyLoopPlan | None,
    journey_state: LearnerJourneyState | None,
    active_run: LessonRunState | None,
) -> DashboardData:
    return DashboardData(
        profile=profile,
        progress=progress,
        weak_spots=weak_spots,
        recommendation=recommendation,
        study_loop=study_loop,
        daily_loop_plan=daily_loop_plan,
        journey_state=journey_state,
        quick_actions=build_quick_actions(
            profile=profile,
            weak_spots=weak_spots,
            due_vocabulary_count=study_loop.vocabulary_summary.due_count if study_loop else 0,
        ),
        resume_lesson=build_resume_lesson_card(active_run),
    )
