from .base import ApiModel
from .lesson import LessonRecommendation
from .mistake import WeakSpot


class VocabularyReviewItem(ApiModel):
    id: str
    word: str
    translation: str
    context: str
    category: str
    source_module: str
    review_reason: str
    linked_mistake_subtype: str | None = None
    linked_mistake_title: str | None = None
    learned_status: str
    repetition_stage: int
    due_now: bool


class MistakeVocabularyBacklink(ApiModel):
    weak_spot_title: str
    weak_spot_category: str
    due_count: int
    active_count: int
    example_words: list[str]
    source_modules: list[str]


class MistakeResolutionSignal(ApiModel):
    weak_spot_title: str
    weak_spot_category: str
    status: str
    repetition_count: int
    last_seen_days_ago: int
    linked_vocabulary_count: int
    resolution_hint: str


class VocabularyLoopSummary(ApiModel):
    due_count: int
    new_count: int
    active_count: int
    mastered_count: int
    weakest_category: str | None = None


class AdaptiveLoopStep(ApiModel):
    id: str
    title: str
    description: str
    route: str
    step_type: str


class ModuleRotationItem(ApiModel):
    module_key: str
    title: str
    reason: str
    route: str
    priority: int


class AdaptiveStrategyAlignment(ApiModel):
    focus_area: str
    route_title: str
    route_seed_source: str
    route_seed_detail: str
    why_now: str
    next_best_action: str
    carry_over_signal_label: str | None = None
    watch_signal_label: str | None = None
    recommended_module_key: str | None = None
    recommended_module_reason: str | None = None


class AdaptiveStudyLoop(ApiModel):
    focus_area: str
    headline: str
    summary: str
    recommendation: LessonRecommendation
    weak_spots: list[WeakSpot]
    due_vocabulary: list[VocabularyReviewItem]
    vocabulary_backlinks: list[MistakeVocabularyBacklink]
    mistake_resolution: list[MistakeResolutionSignal]
    module_rotation: list[ModuleRotationItem]
    vocabulary_summary: VocabularyLoopSummary
    listening_focus: str | None = None
    generation_rationale: list[str]
    next_steps: list[AdaptiveLoopStep]
    strategy_alignment: AdaptiveStrategyAlignment | None = None


class VocabularyHub(ApiModel):
    summary: VocabularyLoopSummary
    due_items: list[VocabularyReviewItem]
    recent_items: list[VocabularyReviewItem]
    mistake_backlinks: list[MistakeVocabularyBacklink]


class VocabularyReviewUpdateRequest(ApiModel):
    successful: bool = True
