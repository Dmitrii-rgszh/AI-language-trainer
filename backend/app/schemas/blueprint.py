from enum import Enum
from typing import Annotated, Literal

from pydantic import Field

from .base import ApiModel


class LessonType(str, Enum):
    CORE = "core"
    DIAGNOSTIC = "diagnostic"
    GRAMMAR = "grammar"
    SPEAKING = "speaking"
    PRONUNCIATION = "pronunciation"
    WRITING = "writing"
    PROFESSIONAL = "professional"
    MIXED = "mixed"
    RECOVERY = "recovery"


class LessonRunStatus(str, Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class BlockRunStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class FeedbackMode(str, Enum):
    IMMEDIATE = "immediate"
    AFTER_BLOCK = "after_block"
    CRITICAL_ONLY = "critical_only"


class UserResponseType(str, Enum):
    NONE = "none"
    TEXT = "text"
    VOICE = "voice"
    MULTIPLE_CHOICE = "multiple_choice"


class MistakeCategory(str, Enum):
    GRAMMAR = "grammar"
    PRONUNCIATION = "pronunciation"
    VOCABULARY = "vocabulary"
    SPEAKING = "speaking"
    WRITING = "writing"
    PROFESSION = "profession"


class MistakeSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SkillArea(str, Enum):
    GRAMMAR = "grammar"
    SPEAKING = "speaking"
    LISTENING = "listening"
    READING = "reading"
    PRONUNCIATION = "pronunciation"
    WRITING = "writing"
    VOCABULARY = "vocabulary"
    INTERVIEW = "interview"
    PROFESSION_ENGLISH = "profession_english"
    INSURANCE_EU = "insurance_eu"
    BANKING_EU = "banking_eu"
    REGULATION_EU = "regulation_eu"
    AI_FOR_BUSINESS = "ai_for_business"


class VocabularyStatus(str, Enum):
    NEW = "new"
    ACTIVE = "active"
    MASTERED = "mastered"


class ProfessionDomain(str, Enum):
    INSURANCE = "insurance"
    BANKING = "banking"
    TRAINER_SKILLS = "trainer_skills"
    AI_BUSINESS = "ai_business"
    REGULATION = "regulation"
    CROSS_CULTURAL = "cross_cultural"


class UserProfileBlueprint(ApiModel):
    id: str
    name: str
    native_language: str
    current_level: str
    target_level: str
    profession_track: ProfessionDomain
    preferred_ui_language: str
    preferred_explanation_language: str
    lesson_duration: int = Field(ge=10, le=90)
    speaking_priority: int = Field(ge=1, le=10)
    grammar_priority: int = Field(ge=1, le=10)
    profession_priority: int = Field(ge=1, le=10)
    active_skill_focus: list[SkillArea] = Field(default_factory=list)
    created_at: str
    updated_at: str


class SkillScore(ApiModel):
    area: SkillArea
    score: int = Field(ge=0, le=100)
    confidence: int = Field(ge=0, le=100)
    updated_at: str


class IntroBlockPayload(ApiModel):
    lesson_goal: str
    warmup_prompt: str
    success_criteria: list[str]


class ReviewBlockPayload(ApiModel):
    source_mistake_ids: list[str]
    review_items: list[str]
    target_error_types: list[str]


class GrammarBlockPayload(ApiModel):
    topic_id: str
    focus_points: list[str]
    prompts: list[str]
    target_error_types: list[str]


class VocabBlockPayload(ApiModel):
    lexical_set: str
    vocabulary_ids: list[str]
    phrases: list[str]


class SpeakingBlockPayload(ApiModel):
    scenario_id: str
    mode: Literal["guided", "free", "roleplay"]
    prompts: list[str]
    expects_voice: bool
    feedback_focus: list[str]


class PronunciationBlockPayload(ApiModel):
    sound_focus: list[str]
    phrase_drills: list[str]
    minimal_pairs: list[str]
    shadowing_script: str | None = None


class ListeningBlockPayload(ApiModel):
    audio_asset_id: str
    transcript: str | None = None
    questions: list[str]
    slow_mode_allowed: bool = True


class ReadingBlockPayload(ApiModel):
    passage_title: str
    passage: str
    questions: list[str]
    answer_key: list[str] = Field(default_factory=list)


class WritingBlockPayload(ApiModel):
    task_id: str
    brief: str
    checklist: list[str]
    tone: str


class ProfessionBlockPayload(ApiModel):
    domain: ProfessionDomain
    topic_id: str
    scenario: str
    target_terms: list[str]


class ReflectionBlockPayload(ApiModel):
    prompts: list[str]
    capture_language: str


class SummaryBlockPayload(ApiModel):
    recap_prompts: list[str]
    next_step: str
    save_to_progress: bool = True


class LessonBlockCommon(ApiModel):
    id: str
    title: str
    instructions: str
    estimated_minutes: int = Field(ge=1, le=60)
    feedback_mode: FeedbackMode
    depends_on_block_ids: list[str] = Field(default_factory=list)


class IntroLessonBlock(LessonBlockCommon):
    block_type: Literal["intro_block"]
    payload: IntroBlockPayload


class ReviewLessonBlock(LessonBlockCommon):
    block_type: Literal["review_block"]
    payload: ReviewBlockPayload


class GrammarLessonBlock(LessonBlockCommon):
    block_type: Literal["grammar_block"]
    payload: GrammarBlockPayload


class VocabLessonBlock(LessonBlockCommon):
    block_type: Literal["vocab_block"]
    payload: VocabBlockPayload


class SpeakingLessonBlock(LessonBlockCommon):
    block_type: Literal["speaking_block"]
    payload: SpeakingBlockPayload


class PronunciationLessonBlock(LessonBlockCommon):
    block_type: Literal["pronunciation_block"]
    payload: PronunciationBlockPayload


class ListeningLessonBlock(LessonBlockCommon):
    block_type: Literal["listening_block"]
    payload: ListeningBlockPayload


class ReadingLessonBlock(LessonBlockCommon):
    block_type: Literal["reading_block"]
    payload: ReadingBlockPayload


class WritingLessonBlock(LessonBlockCommon):
    block_type: Literal["writing_block"]
    payload: WritingBlockPayload


class ProfessionLessonBlock(LessonBlockCommon):
    block_type: Literal["profession_block"]
    payload: ProfessionBlockPayload


class ReflectionLessonBlock(LessonBlockCommon):
    block_type: Literal["reflection_block"]
    payload: ReflectionBlockPayload


class SummaryLessonBlock(LessonBlockCommon):
    block_type: Literal["summary_block"]
    payload: SummaryBlockPayload


LessonBlockBlueprint = Annotated[
    IntroLessonBlock
    | ReviewLessonBlock
    | GrammarLessonBlock
    | VocabLessonBlock
    | SpeakingLessonBlock
    | PronunciationLessonBlock
    | ListeningLessonBlock
    | ReadingLessonBlock
    | WritingLessonBlock
    | ProfessionLessonBlock
    | ReflectionLessonBlock
    | SummaryLessonBlock,
    Field(discriminator="block_type"),
]


class LessonTemplateBlueprint(ApiModel):
    id: str
    lesson_type: LessonType
    title: str
    goal: str
    difficulty: str
    estimated_duration: int = Field(ge=5, le=120)
    blocks: list[LessonBlockBlueprint]
    enabled_tracks: list[ProfessionDomain] = Field(default_factory=list)
    generation_rules: list[str] = Field(default_factory=list)
    created_at: str
    updated_at: str


class LessonRunBlueprint(ApiModel):
    id: str
    user_id: str
    template_id: str
    status: LessonRunStatus
    recommended_by: str
    weak_spot_ids: list[str] = Field(default_factory=list)
    started_at: str
    completed_at: str | None = None
    score: int | None = Field(default=None, ge=0, le=100)


class LessonBlockRunBlueprint(ApiModel):
    id: str
    lesson_run_id: str
    block_id: str
    status: BlockRunStatus
    user_response_type: UserResponseType
    user_response: str | None = None
    transcript: str | None = None
    feedback_summary: str | None = None
    score: int | None = Field(default=None, ge=0, le=100)
    started_at: str
    completed_at: str | None = None


class MistakeRecordBlueprint(ApiModel):
    id: str
    user_id: str
    category: MistakeCategory
    subtype: str
    source_module: str
    source_block_run_id: str | None = None
    original_text: str
    corrected_text: str
    explanation: str
    severity: MistakeSeverity
    repetition_count: int = Field(ge=1)
    created_at: str
    last_seen_at: str


class ProgressSnapshotBlueprint(ApiModel):
    id: str
    user_id: str
    lesson_run_id: str | None = None
    snapshot_date: str
    skill_scores: list[SkillScore]
    daily_goal_minutes: int = Field(ge=0, le=180)
    minutes_completed_today: int = Field(ge=0, le=180)
    streak: int = Field(ge=0)


class VocabularyItemBlueprint(ApiModel):
    id: str
    user_id: str
    word: str
    translation: str
    context: str
    category: str
    learned_status: VocabularyStatus
    repetition_stage: int = Field(ge=0, le=10)
    last_reviewed_at: str | None = None


class ProfessionTopicBlueprint(ApiModel):
    id: str
    domain: ProfessionDomain
    title: str
    difficulty: str
    content: str
    examples: list[str]
    tags: list[str] = Field(default_factory=list)
