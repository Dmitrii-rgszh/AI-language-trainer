from __future__ import annotations

from datetime import datetime

from app.repositories.lesson_repository import LessonRepository
from app.repositories.mistake_repository import MistakeRepository, WEAK_SPOT_TITLE_MAP
from app.repositories.vocabulary_repository import VocabularyRepository
from app.schemas.adaptive import MistakeVocabularyBacklink
from app.schemas.lesson import LessonRecommendation
from app.schemas.mistake import Mistake
from app.schemas.profile import UserProfile


class RecommendationRepository:
    def __init__(
        self,
        lesson_repository: LessonRepository,
        mistake_repository: MistakeRepository,
        vocabulary_repository: VocabularyRepository,
    ) -> None:
        self._lesson_repository = lesson_repository
        self._mistake_repository = mistake_repository
        self._vocabulary_repository = vocabulary_repository

    def get_next_step(self, profile: UserProfile) -> LessonRecommendation | None:
        weak_spots = self._mistake_repository.list_weak_spots(profile.id, limit=2)
        mistakes = self._mistake_repository.list_mistakes(profile.id)
        due_vocabulary = self._vocabulary_repository.list_due_items(profile.id, limit=3)
        vocabulary_backlinks = self._vocabulary_repository.list_mistake_backlinks(profile.id, limit=6)
        latest_completed = self._lesson_repository.list_recent_completed_lessons(profile.id, limit=1)
        latest_lesson_type = latest_completed[0].lesson_type if latest_completed else None
        resolution_map = self._build_resolution_map(mistakes, vocabulary_backlinks)

        if latest_lesson_type == "recovery":
            recommendation = self._lesson_repository.get_recommendation(profile.profession_track)
            if not recommendation:
                return None

            recommendation.goal = self._build_recovery_completed_goal(
                weak_spots=weak_spots,
                profession_track=profile.profession_track,
                due_vocabulary_count=len(due_vocabulary),
            )
            return recommendation

        top_resolution_states = [
            resolution_map.get(spot.title, "active")
            for spot in weak_spots
        ]
        recovering_or_stable = [state for state in top_resolution_states if state in {"recovering", "stabilizing"}]
        active_count = len([state for state in top_resolution_states if state == "active"])
        should_soften_recovery = bool(weak_spots) and bool(top_resolution_states) and (
            top_resolution_states[0] in {"recovering", "stabilizing"} and active_count <= 1
        )

        if should_soften_recovery:
            recommendation = self._lesson_repository.get_recommendation(profile.profession_track)
            if not recommendation:
                return None

            recommendation.goal = self._build_softened_goal(
                base_goal=recommendation.goal,
                weak_spots=weak_spots,
                resolution_map=resolution_map,
                due_vocabulary_count=len(due_vocabulary),
                latest_lesson_type=latest_lesson_type,
            )
            return recommendation

        if weak_spots or due_vocabulary:
            priority_text = ", ".join(
                f"{spot.title} ({resolution_map.get(spot.title, 'active')})"
                for spot in weak_spots
            )
            return LessonRecommendation(
                id="adaptive-recovery-recommendation",
                title="Adaptive Recovery Loop",
                lesson_type="recovery",
                goal=self._build_recovery_goal(
                    weak_spots=weak_spots,
                    priority_text=priority_text,
                    due_vocabulary_count=len(due_vocabulary),
                    latest_lesson_type=latest_lesson_type,
                    profession_track=profile.profession_track,
                ),
                duration=18 if not due_vocabulary else 22,
                focus_area=weak_spots[0].category if weak_spots else "vocabulary",
            )

        recommendation = self._lesson_repository.get_recommendation(profile.profession_track)
        if not recommendation:
            return None

        if weak_spots:
            recommendation.goal = self._append_weak_spot_context(
                base_goal=recommendation.goal,
                weak_spots=weak_spots,
                resolution_map=resolution_map,
                due_vocabulary_count=len(due_vocabulary),
            )

        return recommendation

    @classmethod
    def _build_recovery_completed_goal(
        cls,
        weak_spots: list,
        profession_track: str,
        due_vocabulary_count: int,
    ) -> str:
        carry_forward = ", ".join(spot.title for spot in weak_spots) or "recent fixes"
        opener = cls._pick_variant(
            [
                "Recovery loop completed. Return to the main track and apply the corrected patterns in a fuller lesson.",
                "The focused repair pass is done. Step back into the main lesson flow and keep the corrected forms active in context.",
                "Recovery work is finished for now. Rejoin the broader lesson track so the fixed patterns stay alive in real usage.",
            ],
            profession_track,
            due_vocabulary_count,
            carry_forward,
        )
        carry_line = cls._pick_variant(
            [
                f"Carry forward: {carry_forward}.",
                f"Keep these repairs in play: {carry_forward}.",
                f"Do not let these fixes go cold: {carry_forward}.",
            ],
            carry_forward,
            due_vocabulary_count,
            profession_track,
        )
        return f"{opener} {carry_line}"

    @classmethod
    def _build_softened_goal(
        cls,
        base_goal: str,
        weak_spots: list,
        resolution_map: dict[str, str],
        due_vocabulary_count: int,
        latest_lesson_type: str | None,
    ) -> str:
        resolution_summary = ", ".join(
            f"{spot.title} is {resolution_map.get(spot.title, 'active')}"
            for spot in weak_spots
        )
        bridge = cls._pick_variant(
            [
                "Recovery pressure is easing:",
                "The recovery load is starting to soften:",
                "Targeted repair no longer needs to dominate the plan:",
            ],
            resolution_summary,
            due_vocabulary_count,
            latest_lesson_type or "none",
        )
        closer = cls._pick_variant(
            [
                "Keep these patterns alive inside the main lesson flow instead of restarting a hard recovery loop.",
                "Let the main lesson track carry the correction forward rather than forcing another full recovery pass.",
                "Use the broader lesson flow to stabilize these fixes before opening another hard recovery cycle.",
            ],
            resolution_summary,
            due_vocabulary_count,
            latest_lesson_type or "none",
        )
        return f"{base_goal} {bridge} {resolution_summary}. {closer}"

    @classmethod
    def _build_recovery_goal(
        cls,
        weak_spots: list,
        priority_text: str,
        due_vocabulary_count: int,
        latest_lesson_type: str | None,
        profession_track: str,
    ) -> str:
        opener = cls._pick_variant(
            [
                "Short personalized recovery lesson before the next full module.",
                "Use one compact recovery pass before you jump back into the larger lesson track.",
                "Take a focused repair lesson now so the next main module lands on cleaner ground.",
            ],
            priority_text,
            due_vocabulary_count,
            latest_lesson_type or "none",
            profession_track,
        )
        parts = [opener]
        if weak_spots:
            weak_spot_line = cls._pick_variant(
                [
                    f"Priority weak spots: {priority_text}.",
                    f"Main repair targets right now: {priority_text}.",
                    f"These patterns need the first pass of attention: {priority_text}.",
                ],
                priority_text,
                due_vocabulary_count,
                profession_track,
            )
            parts.append(weak_spot_line)
        if due_vocabulary_count:
            vocab_line = cls._pick_variant(
                [
                    f"Vocabulary due now: {due_vocabulary_count} item{'s' if due_vocabulary_count != 1 else ''}.",
                    f"Vocabulary review queue waiting here: {due_vocabulary_count} item{'s' if due_vocabulary_count != 1 else ''}.",
                    f"Fold in {due_vocabulary_count} due vocabulary item{'s' if due_vocabulary_count != 1 else ''} while the repair lesson is still warm.",
                ],
                due_vocabulary_count,
                priority_text,
                latest_lesson_type or "none",
            )
            parts.append(vocab_line)
        return " ".join(parts).strip()

    @classmethod
    def _append_weak_spot_context(
        cls,
        base_goal: str,
        weak_spots: list,
        resolution_map: dict[str, str],
        due_vocabulary_count: int,
    ) -> str:
        priority_line = ", ".join(
            f"{spot.title} ({resolution_map.get(spot.title, 'active')})"
            for spot in weak_spots
        )
        suffix = cls._pick_variant(
            [
                f"Priority weak spots: {priority_line}.",
                f"Keep an eye on these weak spots during the lesson: {priority_line}.",
                f"Use this lesson to hold these patterns steady: {priority_line}.",
            ],
            priority_line,
            due_vocabulary_count,
            len(weak_spots),
        )
        return f"{base_goal} {suffix}"

    @staticmethod
    def _build_resolution_map(
        mistakes: list[Mistake],
        vocabulary_backlinks: list[MistakeVocabularyBacklink],
    ) -> dict[str, str]:
        backlink_map = {item.weak_spot_title: item for item in vocabulary_backlinks}
        resolution: dict[str, str] = {}
        for mistake in mistakes:
            title = WEAK_SPOT_TITLE_MAP.get(mistake.subtype, mistake.subtype.replace("-", " ").title())
            backlink = backlink_map.get(title)
            linked_count = backlink.active_count if backlink else 0
            last_seen_days_ago = max(0, (datetime.utcnow() - mistake.last_seen_at.replace(tzinfo=None)).days)
            if linked_count >= 2 and last_seen_days_ago >= 5:
                resolution[title] = "stabilizing"
            elif linked_count >= 1 and last_seen_days_ago >= 2:
                resolution[title] = "recovering"
            else:
                resolution[title] = "active"
        return resolution

    @staticmethod
    def _pick_variant(variants: list[str], *seed_parts: object) -> str:
        if not variants:
            return ""
        seed = "|".join(str(part) for part in seed_parts if part is not None)
        if not seed:
            return variants[0]
        weighted_seed = sum((index + 1) * ord(char) for index, char in enumerate(seed))
        index = (weighted_seed + len(seed_parts) * 17) % len(variants)
        return variants[index]
