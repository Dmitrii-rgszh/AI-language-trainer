from __future__ import annotations

from typing import TypedDict


class MistakeSpec(TypedDict):
    subtype: str
    source_module: str
    original_text: str
    corrected_text: str
    explanation: str
    repetition_count: int


class VocabularySpecRequired(TypedDict):
    code: str
    word: str
    translation: str
    context: str
    category: str
    source_module: str
    review_reason: str
    repetition_stage: int


class VocabularySpec(VocabularySpecRequired, total=False):
    linked_mistake_subtype: str
    linked_mistake_title: str


class PronunciationSpec(TypedDict):
    target_text: str
    transcript: str
    feedback: str
    weakest_words: list[str]
    focus_issues: list[str]


class TrackBaselineSpec(TypedDict):
    template_id: str
    grammar: MistakeSpec
    profession: MistakeSpec
    vocabulary: list[VocabularySpec]
    speaking_response: str
    summary_response: str
    pronunciation: PronunciationSpec
