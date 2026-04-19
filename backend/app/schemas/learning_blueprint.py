from pydantic import Field

from .base import ApiModel


class LearningBlueprintPillar(ApiModel):
    id: str
    title: str
    reason: str
    source: str


class LearningBlueprintCheckpoint(ApiModel):
    id: str
    title: str
    summary: str
    success_signal: str


class LearningBlueprint(ApiModel):
    version: str = "v1"
    generated_at: str
    headline: str
    north_star: str
    strategic_summary: str
    learner_snapshot: str
    route_mode: str
    current_phase: str
    current_phase_label: str
    current_focus: str
    success_signal: str
    liza_role: str
    focus_pillars: list[LearningBlueprintPillar] = Field(default_factory=list)
    checkpoints: list[LearningBlueprintCheckpoint] = Field(default_factory=list)
    rhythm_contract: list[str] = Field(default_factory=list)
    guardrails: list[str] = Field(default_factory=list)
