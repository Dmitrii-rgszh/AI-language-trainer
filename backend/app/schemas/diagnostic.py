from .base import ApiModel


class LevelMilestone(ApiModel):
    level: str
    status: str
    readiness: int
    required_score: int
    current_score: int
    description: str
    focus_skills: list[str]


class DiagnosticRoadmap(ApiModel):
    declared_current_level: str
    estimated_level: str
    target_level: str
    overall_score: int
    summary: str
    weakest_skills: list[str]
    next_focus: list[str]
    milestones: list[LevelMilestone]
