from app.schemas.diagnostic import DiagnosticRoadmap
from app.schemas.mistake import WeakSpot
from app.schemas.profile import OnboardingAnswers, UserProfile
from app.schemas.progress import ProgressSnapshot
from app.services.diagnostic_service.roadmap import (
    build_diagnostic_roadmap,
    build_summary,
    calculate_overall_score,
    estimate_level,
    extract_skill_scores,
)


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
        speaking_priority=7,
        grammar_priority=6,
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


def test_diagnostic_score_helpers_extract_average_and_estimate_level() -> None:
    skill_scores = extract_skill_scores(_build_progress())

    assert skill_scores["grammar"] == 52
    assert calculate_overall_score(skill_scores) == 53
    assert estimate_level(53) == "B1"


def test_diagnostic_summary_mentions_mismatch_and_focus() -> None:
    summary = build_summary(
        declared_current_level="A2",
        estimated_level="B1",
        target_level="B2",
        weakest_skills=["pronunciation", "listening"],
        next_focus=["Present Perfect vs Past Simple", "pronunciation"],
    )

    assert "Roadmap towards B2" in summary
    assert "Current profile says A2" in summary
    assert "Immediate focus" in summary


def test_build_diagnostic_roadmap_returns_consistent_structure() -> None:
    roadmap = build_diagnostic_roadmap(
        _build_profile(),
        _build_progress(),
        [
            WeakSpot(
                id="weak-1",
                title="Present Perfect vs Past Simple",
                category="grammar",
                recommendation="Review tense contrast.",
            )
        ],
    )

    assert isinstance(roadmap, DiagnosticRoadmap)
    assert roadmap.estimated_level == "B1"
    assert roadmap.target_level == "B2"
    assert roadmap.milestones
    assert roadmap.milestones[0].level == "A2"
    assert roadmap.next_focus[0] == "Present Perfect vs Past Simple"
