from __future__ import annotations

from app.schemas.blueprint import SkillArea
from app.schemas.profile import UserProfile

from .constants import LEVEL_BASE_SCORES, TRACK_SCORE_ADJUSTMENTS
from .types import TrackBaselineSpec


def block_baseline(block_type: str, spec: TrackBaselineSpec) -> tuple[str, str, int]:
    if block_type == "review_block":
        return (
            "I reviewed the corrected versions and repeated the stronger patterns before the next task.",
            "Good reset. The corrected patterns are now easier to activate in context.",
            78,
        )
    if block_type == "grammar_block":
        return (
            spec["grammar"]["corrected_text"],
            "Grammar pattern is clearer. Keep the corrected form active in your next response.",
            74,
        )
    if block_type == "speaking_block":
        return (
            spec["speaking_response"],
            "The answer is clearer and more structured. Keep the same pattern under slight time pressure.",
            76,
        )
    if block_type == "profession_block":
        return (
            spec["profession"]["corrected_text"],
            "Professional tone is stronger now. Keep this phrasing natural and client-friendly.",
            79,
        )
    if block_type == "summary_block":
        return (
            spec["summary_response"],
            "Good wrap-up. One rule and one phrase are now ready to reuse in the next practice round.",
            82,
        )
    return (
        "I completed the block and kept the response concise.",
        "Solid completion. Keep the same level of clarity in the next step.",
        75,
    )


def level_base(level: str) -> int:
    return LEVEL_BASE_SCORES.get(level.upper(), LEVEL_BASE_SCORES["A2"])


def run_score(profile: UserProfile) -> int:
    weighted_priority = round(
        (profile.speaking_priority + profile.grammar_priority + profile.profession_priority) / 3
    )
    return max(62, min(88, level_base(profile.current_level) + weighted_priority + 10))


def skill_score_map(profile: UserProfile) -> dict[SkillArea, int]:
    base = level_base(profile.current_level)
    adjustments = TRACK_SCORE_ADJUSTMENTS.get(
        profile.profession_track, TRACK_SCORE_ADJUSTMENTS["trainer_skills"]
    )
    raw_scores = {
        SkillArea.GRAMMAR: base + adjustments[SkillArea.GRAMMAR] + (profile.grammar_priority - 5) * 2,
        SkillArea.SPEAKING: base + adjustments[SkillArea.SPEAKING] + (profile.speaking_priority - 5) * 2,
        SkillArea.LISTENING: base - 3 + adjustments[SkillArea.LISTENING],
        SkillArea.PRONUNCIATION: base - 5 + adjustments[SkillArea.PRONUNCIATION],
        SkillArea.WRITING: base - 2 + adjustments[SkillArea.WRITING],
        SkillArea.PROFESSION_ENGLISH: base
        + adjustments[SkillArea.PROFESSION_ENGLISH]
        + (profile.profession_priority - 5) * 2,
        SkillArea.REGULATION_EU: base - 10 + adjustments[SkillArea.REGULATION_EU],
    }
    return {area: max(18, min(95, value)) for area, value in raw_scores.items()}
