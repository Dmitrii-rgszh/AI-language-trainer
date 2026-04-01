from __future__ import annotations

from app.core.errors import ServiceUnavailableError
from app.repositories.lesson_repository import LessonRepository
from app.repositories.lesson_runtime_repository import LessonRuntimeRepository
from app.repositories.mistake_repository import MistakeRepository
from app.repositories.progress_repository import ProgressRepository
from app.schemas.diagnostic import DiagnosticRoadmap, LevelMilestone
from app.schemas.lesson import LessonRunState
from app.schemas.profile import UserProfile


LEVEL_ORDER = ["A1", "A2", "B1", "B2", "C1", "C2"]
LEVEL_SCORE_THRESHOLDS = {
    "A1": 20,
    "A2": 35,
    "B1": 52,
    "B2": 70,
    "C1": 84,
    "C2": 94,
}
SKILL_LABELS = {
    "grammar": "grammar",
    "speaking": "speaking",
    "listening": "listening",
    "pronunciation": "pronunciation",
    "writing": "writing",
    "profession": "profession English",
}


class DiagnosticService:
    def __init__(
        self,
        lesson_repository: LessonRepository,
        lesson_runtime_repository: LessonRuntimeRepository,
        progress_repository: ProgressRepository,
        mistake_repository: MistakeRepository,
    ) -> None:
        self._lesson_repository = lesson_repository
        self._lesson_runtime_repository = lesson_runtime_repository
        self._progress_repository = progress_repository
        self._mistake_repository = mistake_repository

    def get_roadmap(self, profile: UserProfile) -> DiagnosticRoadmap:
        progress = self._progress_repository.get_latest_snapshot(profile.id)
        weak_spots = self._mistake_repository.list_weak_spots(profile.id, limit=3)

        skill_scores = {
            "grammar": progress.grammar_score if progress else 0,
            "speaking": progress.speaking_score if progress else 0,
            "listening": progress.listening_score if progress else 0,
            "pronunciation": progress.pronunciation_score if progress else 0,
            "writing": progress.writing_score if progress else 0,
            "profession": progress.profession_score if progress else 0,
        }
        measured_scores = [score for score in skill_scores.values() if score > 0]
        overall_score = round(
            sum(measured_scores if measured_scores else skill_scores.values())
            / max(len(measured_scores) if measured_scores else len(skill_scores), 1)
        )
        estimated_level = self._estimate_level(overall_score)
        weakest_skills = [
            SKILL_LABELS[name]
            for name, _ in sorted(skill_scores.items(), key=lambda item: item[1])[:3]
        ]
        next_focus = [spot.title for spot in weak_spots] or weakest_skills[:2]

        milestones = self._build_milestones(
            declared_current_level=profile.current_level,
            estimated_level=estimated_level,
            target_level=profile.target_level,
            overall_score=overall_score,
            weakest_skills=weakest_skills,
        )

        summary = self._build_summary(
            declared_current_level=profile.current_level,
            estimated_level=estimated_level,
            target_level=profile.target_level,
            weakest_skills=weakest_skills,
            next_focus=next_focus,
        )

        return DiagnosticRoadmap(
            declared_current_level=profile.current_level,
            estimated_level=estimated_level,
            target_level=profile.target_level,
            overall_score=overall_score,
            summary=summary,
            weakest_skills=weakest_skills,
            next_focus=next_focus,
            milestones=milestones,
        )

    def start_checkpoint_run(self, profile: UserProfile) -> LessonRunState:
        template = self._lesson_repository.create_diagnostic_template(
            profession_track=profile.profession_track,
            current_level=profile.current_level,
            target_level=profile.target_level,
        )
        lesson_run = self._lesson_runtime_repository.start_lesson_run(
            user_id=profile.id,
            profession_track=profile.profession_track,
            template_id=template.id,
        )
        if lesson_run is None:
            raise ServiceUnavailableError("Diagnostic checkpoint could not be started.")
        return lesson_run

    @staticmethod
    def _estimate_level(overall_score: int) -> str:
        estimated = "A1"
        for level in LEVEL_ORDER:
            if overall_score >= LEVEL_SCORE_THRESHOLDS[level]:
                estimated = level
        return estimated

    def _build_milestones(
        self,
        declared_current_level: str,
        estimated_level: str,
        target_level: str,
        overall_score: int,
        weakest_skills: list[str],
    ) -> list[LevelMilestone]:
        declared_index = LEVEL_ORDER.index(declared_current_level) if declared_current_level in LEVEL_ORDER else 1
        target_index = LEVEL_ORDER.index(target_level) if target_level in LEVEL_ORDER else min(declared_index + 2, len(LEVEL_ORDER) - 1)
        estimated_index = LEVEL_ORDER.index(estimated_level)

        milestones: list[LevelMilestone] = []
        for level in LEVEL_ORDER[max(1, declared_index) : target_index + 1]:
            required_score = LEVEL_SCORE_THRESHOLDS[level]
            if estimated_index > LEVEL_ORDER.index(level):
                status = "completed"
            elif estimated_level == level:
                status = "current"
            else:
                status = "upcoming"

            readiness = min(100, max(0, round((overall_score / max(required_score, 1)) * 100)))
            milestones.append(
                LevelMilestone(
                    level=level,
                    status=status,
                    readiness=readiness,
                    required_score=required_score,
                    current_score=overall_score,
                    description=self._describe_milestone(level),
                    focus_skills=weakest_skills[:2],
                )
            )

        return milestones

    @staticmethod
    def _describe_milestone(level: str) -> str:
        descriptions = {
            "A2": "Stabilize everyday grammar, short speaking turns and basic work vocabulary.",
            "B1": "Build longer explanations, better time control and more reliable listening coverage.",
            "B2": "Push fluency, nuanced feedback language and confident professional communication.",
            "C1": "Increase precision, flexibility and advanced structured argumentation.",
            "C2": "Refine near-native control, nuance and high-pressure communication.",
        }
        return descriptions.get(level, "Keep expanding control across core language skills.")

    @staticmethod
    def _build_summary(
        declared_current_level: str,
        estimated_level: str,
        target_level: str,
        weakest_skills: list[str],
        next_focus: list[str],
    ) -> str:
        mismatch_note = ""
        if declared_current_level != estimated_level:
            mismatch_note = f" Current profile says {declared_current_level}, but live progress looks closer to {estimated_level}."

        weakest = ", ".join(weakest_skills[:2]) if weakest_skills else "core skills"
        focus = ", ".join(next_focus[:2]) if next_focus else "the next adaptive lesson"
        return (
            f"Roadmap towards {target_level}: strengthen {weakest} first, then convert recovery work into longer lesson gains."
            f"{mismatch_note} Immediate focus: {focus}."
        )
