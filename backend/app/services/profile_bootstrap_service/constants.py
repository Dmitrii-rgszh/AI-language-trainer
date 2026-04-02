from __future__ import annotations

from app.schemas.blueprint import SkillArea


BASELINE_PREFIX = "bootstrap-"
LEGACY_LESSON_RUN_IDS = {"run-1"}
LEGACY_MISTAKE_IDS = {"mistake-1", "mistake-3"}
LEGACY_PROGRESS_IDS = {"snapshot-1"}
LEGACY_VOCAB_IDS = {"vocab-1"}

LEVEL_BASE_SCORES = {
    "A1": 34,
    "A2": 46,
    "B1": 58,
    "B2": 71,
    "C1": 82,
    "C2": 91,
}

TRACK_SCORE_ADJUSTMENTS = {
    "trainer_skills": {
        SkillArea.GRAMMAR: 2,
        SkillArea.SPEAKING: 4,
        SkillArea.LISTENING: 0,
        SkillArea.PRONUNCIATION: 1,
        SkillArea.WRITING: 1,
        SkillArea.PROFESSION_ENGLISH: 6,
        SkillArea.REGULATION_EU: 0,
    },
    "insurance": {
        SkillArea.GRAMMAR: 2,
        SkillArea.SPEAKING: 2,
        SkillArea.LISTENING: 3,
        SkillArea.PRONUNCIATION: 0,
        SkillArea.WRITING: 1,
        SkillArea.PROFESSION_ENGLISH: 6,
        SkillArea.REGULATION_EU: 2,
    },
    "banking": {
        SkillArea.GRAMMAR: 2,
        SkillArea.SPEAKING: 2,
        SkillArea.LISTENING: 2,
        SkillArea.PRONUNCIATION: 0,
        SkillArea.WRITING: 2,
        SkillArea.PROFESSION_ENGLISH: 6,
        SkillArea.REGULATION_EU: 1,
    },
    "ai_business": {
        SkillArea.GRAMMAR: 3,
        SkillArea.SPEAKING: 2,
        SkillArea.LISTENING: 1,
        SkillArea.PRONUNCIATION: 0,
        SkillArea.WRITING: 3,
        SkillArea.PROFESSION_ENGLISH: 6,
        SkillArea.REGULATION_EU: 0,
    },
    "cross_cultural": {
        SkillArea.GRAMMAR: 1,
        SkillArea.SPEAKING: 4,
        SkillArea.LISTENING: 2,
        SkillArea.PRONUNCIATION: 1,
        SkillArea.WRITING: 0,
        SkillArea.PROFESSION_ENGLISH: 1,
        SkillArea.REGULATION_EU: 0,
    },
}
