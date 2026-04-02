from __future__ import annotations

from app.schemas.diagnostic import DiagnosticRoadmap, LevelMilestone
from app.schemas.profile import UserProfile
from app.schemas.progress import ProgressSnapshot
from app.schemas.mistake import WeakSpot
from app.services.diagnostic_service.constants import (
    LEVEL_ORDER,
    LEVEL_SCORE_THRESHOLDS,
    MILESTONE_DESCRIPTIONS,
    SKILL_LABELS,
)


def build_diagnostic_roadmap(
    profile: UserProfile,
    progress: ProgressSnapshot | None,
    weak_spots: list[WeakSpot],
) -> DiagnosticRoadmap:
    skill_scores = extract_skill_scores(progress)
    overall_score = calculate_overall_score(skill_scores)
    estimated_level = estimate_level(overall_score)
    weakest_skills = resolve_weakest_skills(skill_scores)
    next_focus = [spot.title for spot in weak_spots] or weakest_skills[:2]

    milestones = build_milestones(
        declared_current_level=profile.current_level,
        estimated_level=estimated_level,
        target_level=profile.target_level,
        overall_score=overall_score,
        weakest_skills=weakest_skills,
    )
    summary = build_summary(
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


def extract_skill_scores(progress: ProgressSnapshot | None) -> dict[str, int]:
    return {
        "grammar": progress.grammar_score if progress else 0,
        "speaking": progress.speaking_score if progress else 0,
        "listening": progress.listening_score if progress else 0,
        "pronunciation": progress.pronunciation_score if progress else 0,
        "writing": progress.writing_score if progress else 0,
        "profession": progress.profession_score if progress else 0,
    }


def calculate_overall_score(skill_scores: dict[str, int]) -> int:
    measured_scores = [score for score in skill_scores.values() if score > 0]
    active_scores = measured_scores if measured_scores else list(skill_scores.values())
    return round(sum(active_scores) / max(len(active_scores), 1))


def estimate_level(overall_score: int) -> str:
    estimated = "A1"
    for level in LEVEL_ORDER:
        if overall_score >= LEVEL_SCORE_THRESHOLDS[level]:
            estimated = level
    return estimated


def resolve_weakest_skills(skill_scores: dict[str, int]) -> list[str]:
    return [SKILL_LABELS[name] for name, _ in sorted(skill_scores.items(), key=lambda item: item[1])[:3]]


def build_milestones(
    declared_current_level: str,
    estimated_level: str,
    target_level: str,
    overall_score: int,
    weakest_skills: list[str],
) -> list[LevelMilestone]:
    declared_index = LEVEL_ORDER.index(declared_current_level) if declared_current_level in LEVEL_ORDER else 1
    target_index = (
        LEVEL_ORDER.index(target_level)
        if target_level in LEVEL_ORDER
        else min(declared_index + 2, len(LEVEL_ORDER) - 1)
    )
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
                description=describe_milestone(level),
                focus_skills=weakest_skills[:2],
            )
        )

    return milestones


def describe_milestone(level: str) -> str:
    return MILESTONE_DESCRIPTIONS.get(level, "Keep expanding control across core language skills.")


def build_summary(
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
