from pydantic import Field

from .base import ApiModel


class OnboardingAnswers(ApiModel):
    learner_persona: str = "self_learner"
    age_group: str = "adult"
    learning_context: str = "general_english"
    primary_goal: str = "everyday_communication"
    secondary_goals: list[str] = Field(
        default_factory=lambda: ["speaking_confidence", "vocabulary_growth"]
    )
    active_skill_focus: list[str] = Field(
        default_factory=lambda: ["speaking", "vocabulary", "grammar"]
    )
    study_preferences: list[str] = Field(
        default_factory=lambda: ["structured_plan", "short_sessions", "gentle_feedback"]
    )
    interest_topics: list[str] = Field(default_factory=lambda: ["daily_life", "travel", "culture"])
    support_needs: list[str] = Field(default_factory=lambda: ["clear_examples"])
    notes: str = ""


class UserProfile(ApiModel):
    id: str
    name: str
    native_language: str
    current_level: str
    target_level: str
    profession_track: str
    preferred_ui_language: str
    preferred_explanation_language: str
    lesson_duration: int
    speaking_priority: int
    grammar_priority: int
    profession_priority: int
    onboarding_answers: OnboardingAnswers = Field(default_factory=OnboardingAnswers)


class ProfileUpdateRequest(UserProfile):
    pass
