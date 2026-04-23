from app.schemas.learning_blueprint import LearningBlueprint
from app.schemas.profile import OnboardingAnswers, UserProfile
from app.services.journey_service.service import JourneyService
from app.services.learning_blueprint_service.service import LearningBlueprintService


def _build_profile() -> UserProfile:
    return UserProfile(
        id="user-relationship-1",
        name="Mila",
        native_language="ru",
        current_level="A2",
        target_level="B1",
        profession_track="cross_cultural",
        preferred_ui_language="ru",
        preferred_explanation_language="ru",
        lesson_duration=18,
        speaking_priority=7,
        grammar_priority=6,
        profession_priority=4,
        onboarding_answers=OnboardingAnswers(
            primary_goal="everyday_communication",
            preferred_mode="mixed",
            english_relationship_goal="freedom_and_lightness",
            emotional_barriers=["fear_of_mistakes", "perfectionism"],
            ritual_elements=["daily_word_journal", "reading_for_pleasure"],
        ),
    )


def test_learning_blueprint_service_builds_relationship_guardrails() -> None:
    blueprint = LearningBlueprintService.build(
        profile=_build_profile(),
        focus_area="speaking",
        journey_stage="daily_loop_ready",
        current_strategy_summary="Keep English alive and usable.",
        next_best_action="Open the next route step.",
        recommendation=None,
    )

    assert isinstance(blueprint, LearningBlueprint)
    assert "freedom and lightness" in blueprint.north_star
    assert any(pillar.id == "relationship" for pillar in blueprint.focus_pillars)
    assert any("word journal" in item.lower() for item in blueprint.rhythm_contract)
    assert any("mistakes as progress" in item.lower() or "mistakes as progress signals" in item.lower() for item in blueprint.guardrails)


def test_journey_service_infers_reading_lane_from_relationship_ritual() -> None:
    profile = _build_profile()

    assert JourneyService._infer_input_lane(profile) == "reading"
    assert JourneyService._infer_output_lane(profile) == "writing"
