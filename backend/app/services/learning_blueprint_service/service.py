from __future__ import annotations

from datetime import datetime

from app.schemas.learning_blueprint import (
    LearningBlueprint,
    LearningBlueprintCheckpoint,
    LearningBlueprintPillar,
)
from app.schemas.lesson import LessonRecommendation
from app.schemas.profile import UserProfile


RELATIONSHIP_GOAL_LABELS = {
    "freedom_and_lightness": "freedom and lightness",
    "spontaneous_speaking": "spontaneous speaking",
    "self_expression": "self-expression",
    "calm_confidence": "calm confidence",
}

EMOTIONAL_BARRIER_LABELS = {
    "fear_of_mistakes": "fear of mistakes",
    "fear_of_judgment": "fear of judgment",
    "perfectionism": "perfectionism",
    "voice_shyness": "voice shyness",
    "english_feels_heavy": "a heavy relationship with English",
    "uncertainty_stress": "stress from uncertainty",
}

RITUAL_ELEMENT_RULES = {
    "daily_word_journal": "Keep a living word journal from real life and only capture 1-3 phrases that feel personally useful.",
    "reading_for_pleasure": "Protect 5-10 minutes of reading for pleasure, not for finishing hard material or proving discipline.",
    "spontaneous_voice_notes": "Use short spontaneous voice notes so the learner hears and accepts their own voice without over-preparing.",
    "highlight_lowlight_reflection": "Use a short highlight/lowlight reflection so English keeps touching real life instead of abstract drills.",
    "playful_contact": "Keep one playful real-life contact point where English can stay curious, social, and alive.",
    "gentle_daily_consistency": "Prefer a little English every day over heavy catch-up sessions that drain energy.",
}


class LearningBlueprintService:
    @classmethod
    def build(
        cls,
        *,
        profile: UserProfile,
        focus_area: str,
        journey_stage: str,
        current_strategy_summary: str,
        next_best_action: str,
        recommendation: LessonRecommendation | None,
        route_recovery_memory: dict | None = None,
        route_follow_up_memory: dict | None = None,
        skill_trajectory: dict | None = None,
        strategy_memory: dict | None = None,
        weak_spots: list[dict] | None = None,
        daily_loop_plan: dict | None = None,
    ) -> LearningBlueprint:
        answers = profile.onboarding_answers
        phase_key, phase_label = cls._resolve_phase(journey_stage, route_recovery_memory)
        route_mode = cls._resolve_route_mode(answers.preferred_mode, route_recovery_memory, daily_loop_plan)
        north_star = cls._build_north_star(profile, focus_area)
        learner_snapshot = cls._build_learner_snapshot(profile)
        success_signal = cls._build_success_signal(
            focus_area=focus_area,
            next_best_action=next_best_action,
            route_follow_up_memory=route_follow_up_memory,
            recommendation=recommendation,
        )
        pillars = cls._build_focus_pillars(
            profile=profile,
            focus_area=focus_area,
            route_recovery_memory=route_recovery_memory,
            route_follow_up_memory=route_follow_up_memory,
            skill_trajectory=skill_trajectory,
            strategy_memory=strategy_memory,
            weak_spots=weak_spots,
        )
        checkpoints = cls._build_checkpoints(
            focus_area=focus_area,
            next_best_action=next_best_action,
            route_recovery_memory=route_recovery_memory,
            route_follow_up_memory=route_follow_up_memory,
            recommendation=recommendation,
        )
        rhythm_contract = cls._build_rhythm_contract(profile, daily_loop_plan, route_recovery_memory)
        guardrails = cls._build_guardrails(profile, focus_area, route_recovery_memory)
        liza_role = cls._build_liza_role(profile, route_recovery_memory, route_follow_up_memory, focus_area)

        return LearningBlueprint(
            generated_at=datetime.utcnow().isoformat(),
            headline=f"{profile.name}'s learning blueprint",
            north_star=north_star,
            strategic_summary=current_strategy_summary,
            learner_snapshot=learner_snapshot,
            route_mode=route_mode,
            current_phase=phase_key,
            current_phase_label=phase_label,
            current_focus=focus_area,
            success_signal=success_signal,
            liza_role=liza_role,
            focus_pillars=pillars,
            checkpoints=checkpoints,
            rhythm_contract=rhythm_contract,
            guardrails=guardrails,
        )

    @staticmethod
    def _resolve_phase(journey_stage: str, route_recovery_memory: dict | None) -> tuple[str, str]:
        if route_recovery_memory and route_recovery_memory.get("phase"):
            phase = str(route_recovery_memory["phase"])
            label_map = {
                "route_rebuild": "Route rebuild",
                "protected_return": "Protected return",
                "skill_repair_cycle": "Skill repair cycle",
                "targeted_stabilization": "Targeted stabilization",
                "support_reopen_arc": "Support reopen arc",
            }
            return phase, label_map.get(phase, phase.replace("_", " ").title())

        label_map = {
            "first_path": "First path",
            "daily_loop_ready": "Daily loop ready",
            "daily_loop_active": "Route in motion",
            "daily_loop_completed": "Route review",
        }
        return journey_stage, label_map.get(journey_stage, journey_stage.replace("_", " ").title())

    @staticmethod
    def _resolve_route_mode(
        preferred_mode: str,
        route_recovery_memory: dict | None,
        daily_loop_plan: dict | None,
    ) -> str:
        session_shape = (
            str(route_recovery_memory.get("sessionShape"))
            if route_recovery_memory and route_recovery_memory.get("sessionShape")
            else None
        )
        estimated_minutes = (
            int(daily_loop_plan.get("estimatedMinutes") or daily_loop_plan.get("estimated_minutes"))
            if daily_loop_plan
            and (
                daily_loop_plan.get("estimatedMinutes") is not None
                or daily_loop_plan.get("estimated_minutes") is not None
            )
            else None
        )
        compactness = "compact" if estimated_minutes is not None and estimated_minutes <= 18 else "full"
        if session_shape:
            return f"{session_shape.replace('_', ' ')} · {preferred_mode} · {compactness}"
        return f"{preferred_mode} · {compactness}"

    @staticmethod
    def _build_north_star(profile: UserProfile, focus_area: str) -> str:
        goal = profile.onboarding_answers.primary_goal.replace("_", " ")
        relationship_goal = RELATIONSHIP_GOAL_LABELS.get(
            profile.onboarding_answers.english_relationship_goal,
            profile.onboarding_answers.english_relationship_goal.replace("_", " "),
        )
        return (
            f"Move from {profile.current_level} toward {profile.target_level} by making {goal} "
            f"feel usable through a connected route led by {focus_area}, while English becomes a source of {relationship_goal}."
        )

    @staticmethod
    def _build_learner_snapshot(profile: UserProfile) -> str:
        answers = profile.onboarding_answers
        context = answers.learning_context.replace("_", " ")
        persona = answers.learner_persona.replace("_", " ")
        return (
            f"{answers.age_group.replace('_', ' ')} {persona} in {context}, "
            f"prefers {answers.preferred_mode.replace('_', ' ')} study and {profile.lesson_duration}-minute sessions."
        )

    @staticmethod
    def _build_success_signal(
        *,
        focus_area: str,
        next_best_action: str,
        route_follow_up_memory: dict | None,
        recommendation: LessonRecommendation | None,
    ) -> str:
        if route_follow_up_memory and route_follow_up_memory.get("summary"):
            return str(route_follow_up_memory["summary"])
        if recommendation and recommendation.goal:
            return recommendation.goal
        return f"Keep {focus_area} stable enough that the next step can widen without losing route continuity. {next_best_action}"

    @classmethod
    def _build_focus_pillars(
        cls,
        *,
        profile: UserProfile,
        focus_area: str,
        route_recovery_memory: dict | None,
        route_follow_up_memory: dict | None,
        skill_trajectory: dict | None,
        strategy_memory: dict | None,
        weak_spots: list[dict] | None,
    ) -> list[LearningBlueprintPillar]:
        pillars: list[LearningBlueprintPillar] = [
            LearningBlueprintPillar(
                id="goal",
                title="Goal-led route",
                reason=(
                    f"The route should keep serving {profile.onboarding_answers.primary_goal.replace('_', ' ')} "
                    f"instead of splitting into disconnected drills."
                ),
                source="onboarding_goal",
            ),
            LearningBlueprintPillar(
                id="relationship",
                title="English relationship first",
                reason=cls._build_relationship_reason(profile),
                source="english_relationship",
            ),
            LearningBlueprintPillar(
                id="focus",
                title=f"{focus_area.title()} leads first",
                reason=(
                    f"{focus_area.title()} is the current lead signal, so the route should organize the next session around it "
                    "before widening to adjacent skills."
                ),
                source="current_focus",
            ),
        ]

        if route_recovery_memory and route_recovery_memory.get("summary"):
            pillars.append(
                LearningBlueprintPillar(
                    id="recovery",
                    title="Recovery arc protection",
                    reason=str(route_recovery_memory["summary"]),
                    source="route_recovery_memory",
                )
            )
        elif strategy_memory and strategy_memory.get("summary"):
            pillars.append(
                LearningBlueprintPillar(
                    id="memory",
                    title="Long-memory pressure",
                    reason=str(strategy_memory["summary"]),
                    source="strategy_memory",
                )
            )
        elif skill_trajectory and skill_trajectory.get("summary"):
            pillars.append(
                LearningBlueprintPillar(
                    id="trajectory",
                    title="Multi-day trajectory",
                    reason=str(skill_trajectory["summary"]),
                    source="skill_trajectory",
                )
            )
        elif weak_spots:
            weak_spot_title = str(weak_spots[0].get("title") or weak_spots[0].get("category") or "the current weak signal")
            pillars.append(
                LearningBlueprintPillar(
                    id="repair",
                    title="Weak-signal repair",
                    reason=f"The route still needs to protect {weak_spot_title} so it does not reappear as the main blocker.",
                    source="weak_spot",
                )
            )

        if route_follow_up_memory and route_follow_up_memory.get("summary"):
            pillars.append(
                LearningBlueprintPillar(
                    id="follow-up",
                    title="Follow-up governance",
                    reason=str(route_follow_up_memory["summary"]),
                    source="route_follow_up_memory",
                )
            )

        return pillars[:4]

    @staticmethod
    def _build_checkpoints(
        *,
        focus_area: str,
        next_best_action: str,
        route_recovery_memory: dict | None,
        route_follow_up_memory: dict | None,
        recommendation: LessonRecommendation | None,
    ) -> list[LearningBlueprintCheckpoint]:
        checkpoints = [
            LearningBlueprintCheckpoint(
                id="today",
                title="Land today's route cleanly",
                summary=next_best_action,
                success_signal=(
                    recommendation.goal
                    if recommendation and recommendation.goal
                    else f"The route stays coherent around {focus_area} instead of breaking into detached modules."
                ),
            )
        ]
        if route_recovery_memory and route_recovery_memory.get("nextPhaseHint"):
            checkpoints.append(
                LearningBlueprintCheckpoint(
                    id="recovery",
                    title="Protect the current recovery arc",
                    summary=str(route_recovery_memory["actionHint"] or route_recovery_memory["summary"]),
                    success_signal=str(route_recovery_memory["nextPhaseHint"]),
                )
            )
        if route_follow_up_memory and route_follow_up_memory.get("followUpLabel"):
            checkpoints.append(
                LearningBlueprintCheckpoint(
                    id="follow-up",
                    title=f"Open {route_follow_up_memory.get('followUpLabel')}",
                    summary=str(route_follow_up_memory.get("summary") or next_best_action),
                    success_signal="The learner should see one obvious step after the current surface rather than needing to guess.",
                )
            )
        return checkpoints[:3]

    @staticmethod
    def _build_rhythm_contract(
        profile: UserProfile,
        daily_loop_plan: dict | None,
        route_recovery_memory: dict | None,
    ) -> list[str]:
        estimated_minutes = (
            int(daily_loop_plan.get("estimatedMinutes") or daily_loop_plan.get("estimated_minutes"))
            if daily_loop_plan
            and (
                daily_loop_plan.get("estimatedMinutes") is not None
                or daily_loop_plan.get("estimated_minutes") is not None
            )
            else profile.lesson_duration
        )
        contract = [
            RITUAL_ELEMENT_RULES[item]
            for item in profile.onboarding_answers.ritual_elements
            if item in RITUAL_ELEMENT_RULES
        ]
        contract.extend(
            [
                f"Keep sessions around {estimated_minutes} minutes so the route stays repeatable.",
                f"Use {profile.onboarding_answers.preferred_mode.replace('_', ' ')} as the default lane unless the recovery arc needs a calmer shape.",
            ]
        )
        if route_recovery_memory and route_recovery_memory.get("actionHint"):
            contract.append(str(route_recovery_memory["actionHint"]))
        return contract[:4]

    @staticmethod
    def _build_guardrails(
        profile: UserProfile,
        focus_area: str,
        route_recovery_memory: dict | None,
    ) -> list[str]:
        guardrails = [
            item
            for barrier in profile.onboarding_answers.emotional_barriers
            if (item := LearningBlueprintService._map_barrier_to_guardrail(barrier)) is not None
        ]
        guardrails.extend(
            [
                "Do not fragment the day into unrelated drills.",
                f"Keep {focus_area} visible as the lead signal before widening.",
            ]
        )
        if "gentle_feedback" in profile.onboarding_answers.study_preferences:
            guardrails.append("Feedback should stay calm and corrective, not overwhelming.")
        if "clear_examples" in profile.onboarding_answers.support_needs:
            guardrails.append("Every harder step should still come with a clear example or anchor.")
        if route_recovery_memory and route_recovery_memory.get("phase") == "support_reopen_arc":
            guardrails.append("Reopen support inside the main route instead of letting it become a detached side path.")
        return guardrails[:4]

    @staticmethod
    def _build_liza_role(
        profile: UserProfile,
        route_recovery_memory: dict | None,
        route_follow_up_memory: dict | None,
        focus_area: str,
    ) -> str:
        emotional_barriers = set(profile.onboarding_answers.emotional_barriers)
        if emotional_barriers & {"fear_of_mistakes", "fear_of_judgment", "voice_shyness", "perfectionism"}:
            return (
                f"Liza should lower shame, normalize mistakes, and help {focus_area} feel safe enough for spontaneity before asking for more polish."
            )
        if route_recovery_memory and route_recovery_memory.get("phase") == "support_reopen_arc":
            return (
                f"Liza should protect the reopen arc, explain why {focus_area} still leads, and keep the learner from treating support work as a separate product."
            )
        if route_follow_up_memory and route_follow_up_memory.get("followUpLabel"):
            return (
                f"Liza should clarify the current step and make the transition into {route_follow_up_memory.get('followUpLabel')} feel inevitable and calm."
            )
        return f"Liza should keep {focus_area} connected to the learner's main goal and always make the next step obvious."

    @staticmethod
    def _map_barrier_to_guardrail(barrier: str) -> str | None:
        mapping = {
            "fear_of_mistakes": "Treat mistakes as progress signals, not as proof that the learner is failing.",
            "fear_of_judgment": "Keep more low-stakes speaking and self-expression before public-performance pressure.",
            "perfectionism": "Do not wait for perfect grammar before speaking or writing.",
            "voice_shyness": "Let the learner hear and accept their own voice before pushing polish.",
            "english_feels_heavy": "If the route stops feeling alive, lighten it before adding more cognitive load.",
            "uncertainty_stress": "Use clearer next steps and smaller experiments when uncertainty starts creating freeze.",
        }
        return mapping.get(barrier)

    @classmethod
    def _build_relationship_reason(cls, profile: UserProfile) -> str:
        answers = profile.onboarding_answers
        goal_label = RELATIONSHIP_GOAL_LABELS.get(
            answers.english_relationship_goal,
            answers.english_relationship_goal.replace("_", " "),
        )
        barriers = [
            EMOTIONAL_BARRIER_LABELS.get(item, item.replace("_", " "))
            for item in answers.emotional_barriers[:2]
        ]
        if barriers:
            return (
                f"The route should move English toward {goal_label}, while softening {', '.join(barriers)} enough for real self-expression."
            )
        return (
            f"The route should make English feel like {goal_label}, not only like a subject to manage."
        )
