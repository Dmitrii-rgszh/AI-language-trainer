from app.schemas.blueprint import SkillArea
from app.schemas.profile import OnboardingAnswers, UserProfile
from app.services.profile_bootstrap_service.baselines import TRACK_BASELINES
from app.services.profile_bootstrap_service.scoring import block_baseline, run_score, skill_score_map
from app.services.profile_bootstrap_service.selectors import baseline_key, mistake_id


def build_profile(**overrides) -> UserProfile:
    payload = {
        "id": "user-bootstrap-1",
        "name": "Nina",
        "native_language": "ru",
        "current_level": "B1",
        "target_level": "B2",
        "profession_track": "unknown_track",
        "preferred_ui_language": "ru",
        "preferred_explanation_language": "ru",
        "lesson_duration": 20,
        "speaking_priority": 7,
        "grammar_priority": 6,
        "profession_priority": 8,
        "onboarding_answers": OnboardingAnswers(),
    }
    payload.update(overrides)
    return UserProfile(**payload)


def test_profile_bootstrap_scoring_uses_default_track_adjustments() -> None:
    profile = build_profile()

    scores = skill_score_map(profile)

    assert run_score(profile) == 75
    assert scores[SkillArea.GRAMMAR] == 62
    assert scores[SkillArea.SPEAKING] == 66
    assert scores[SkillArea.PROFESSION_ENGLISH] == 70


def test_profile_bootstrap_helper_ids_are_stable_and_prefixed() -> None:
    generated_key = baseline_key("user-bootstrap-1")

    assert generated_key == baseline_key("user-bootstrap-1")
    assert len(generated_key) == 10
    assert mistake_id(generated_key, "grammar").startswith("bootstrap-mistake-")


def test_profile_bootstrap_block_baseline_uses_track_content() -> None:
    spec = TRACK_BASELINES["insurance"]

    response_text, feedback_summary, score = block_baseline("profession_block", spec)

    assert response_text == spec["profession"]["corrected_text"]
    assert "client-friendly" in feedback_summary
    assert score == 79
