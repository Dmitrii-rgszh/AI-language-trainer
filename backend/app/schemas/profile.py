from .base import ApiModel


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


class ProfileUpdateRequest(UserProfile):
    pass

