from __future__ import annotations

import re

from app.schemas.mistake_extraction import ExtractedMistake
from app.schemas.blueprint import MistakeCategory, MistakeSeverity
from app.schemas.lesson import BlockResultSubmission, Lesson


class MistakeExtractionService:
    def extract_from_block_results(
        self,
        lesson: Lesson,
        block_results: list[BlockResultSubmission],
    ) -> list[ExtractedMistake]:
        lesson_blocks = {block.id: block for block in lesson.blocks}
        extracted: list[ExtractedMistake] = []

        for result in block_results:
            response_text = (result.user_response or result.transcript or "").strip()
            if not response_text:
                continue

            block = lesson_blocks.get(result.block_id)
            if not block:
                continue

            lowered = response_text.lower()

            if "since" in lowered and "have" not in lowered and block.block_type in {"grammar_block", "speaking_block"}:
                extracted.append(
                    ExtractedMistake(
                        category=MistakeCategory.GRAMMAR,
                        subtype="tense-choice",
                        source_module=block.block_type.replace("_block", ""),
                        original_text=response_text,
                        corrected_text=self._insert_have_fix(response_text),
                        explanation="Для действий с since обычно нужен Present Perfect.",
                        severity=MistakeSeverity.MEDIUM,
                    )
                )

            if any(token in lowered for token in ["is wrong", "wrong.", "wrong,"]) and block.block_type == "profession_block":
                extracted.append(
                    ExtractedMistake(
                        category=MistakeCategory.PROFESSION,
                        subtype="feedback-language",
                        source_module="profession",
                        original_text=response_text,
                        corrected_text=response_text.replace("is wrong", "could be clearer").replace("wrong", "clearer"),
                        explanation="В professional feedback лучше использовать более мягкие формулировки.",
                        severity=MistakeSeverity.MEDIUM,
                    )
                )

            if "/s/" in lowered or "sink" in lowered and block.block_type == "pronunciation_block":
                extracted.append(
                    ExtractedMistake(
                        category=MistakeCategory.PRONUNCIATION,
                        subtype="th-sound",
                        source_module="pronunciation",
                        original_text=response_text,
                        corrected_text=response_text.replace("sink", "think"),
                        explanation="Для /th/ нужен другой артикуляционный паттерн, чем для /s/.",
                        severity=MistakeSeverity.LOW,
                    )
                )

        return extracted

    def extract_from_review(
        self,
        *,
        source_module: str,
        learner_text: str,
        feedback_summary: str = "",
    ) -> list[ExtractedMistake]:
        response_text = learner_text.strip()
        if not response_text:
            return []

        lowered = response_text.lower()
        feedback_lowered = feedback_summary.lower()
        extracted: list[ExtractedMistake] = []

        if "since" in lowered and not re.search(r"\b(have|has)\b", lowered):
            extracted.append(
                ExtractedMistake(
                    category=MistakeCategory.GRAMMAR,
                    subtype="tense-choice",
                    source_module=source_module,
                    original_text=response_text,
                    corrected_text=self._insert_have_fix(response_text),
                    explanation="Для периода с since обычно нужен Present Perfect.",
                    severity=MistakeSeverity.MEDIUM,
                )
            )

        if "goed" in lowered:
            extracted.append(
                ExtractedMistake(
                    category=MistakeCategory.GRAMMAR,
                    subtype="irregular-past",
                    source_module=source_module,
                    original_text=response_text,
                    corrected_text=re.sub(r"\bgoed\b", "went", response_text, flags=re.IGNORECASE),
                    explanation="Глагол go образует Past Simple как went, а не goed.",
                    severity=MistakeSeverity.MEDIUM,
                )
            )

        if re.search(r"\b(people|participants|managers|trainers|teams)\s+feels\b", lowered) or (
            "agreement" in feedback_lowered and "feels" in lowered
        ):
            extracted.append(
                ExtractedMistake(
                    category=MistakeCategory.GRAMMAR,
                    subtype="subject-verb-agreement",
                    source_module=source_module,
                    original_text=response_text,
                    corrected_text=re.sub(r"\bfeels\b", "feel", response_text, flags=re.IGNORECASE),
                    explanation="После plural subject нужен feel, а не feels.",
                    severity=MistakeSeverity.MEDIUM,
                )
            )

        if re.search(r"\bmore (better|clearer|easier|stronger)\b", lowered):
            extracted.append(
                ExtractedMistake(
                    category=MistakeCategory.WRITING if source_module == "writing" else MistakeCategory.GRAMMAR,
                    subtype="comparative-form",
                    source_module=source_module,
                    original_text=response_text,
                    corrected_text=re.sub(
                        r"\bmore (better|clearer|easier|stronger)\b",
                        lambda match: match.group(1),
                        response_text,
                        flags=re.IGNORECASE,
                    ),
                    explanation="Такие comparative forms не требуют more перед better/clearer/easier/stronger.",
                    severity=MistakeSeverity.LOW,
                )
            )

        return extracted

    @staticmethod
    def _insert_have_fix(text: str) -> str:
        if text.lower().startswith("i "):
            return f"I have {text[2:].lstrip()}"
        if text.lower().startswith("we "):
            return f"We have {text[3:].lstrip()}"
        return f"Have {text}"
