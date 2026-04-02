from __future__ import annotations

import re

from app.schemas.mistake_extraction import ExtractedMistake


def build_capture(mistake: ExtractedMistake) -> dict[str, str] | None:
    if mistake.subtype == "irregular-past":
        corrected = extract_irregular_past_target(
            original_text=mistake.original_text,
            corrected_text=mistake.corrected_text,
        )
        if not corrected:
            return None
        return {
            "word": corrected.lower(),
            "translation": "неправильная форма прошедшего времени",
            "context": f"{mistake.original_text} -> {mistake.corrected_text}",
            "category": "mistake_irregular_verbs",
            "source_module": mistake.source_module,
            "review_reason": "Captured from repeated irregular past correction.",
            "linked_mistake_subtype": mistake.subtype,
            "linked_mistake_title": "Irregular Past Forms",
        }

    if mistake.subtype == "subject-verb-agreement":
        corrected = extract_agreement_target(mistake.corrected_text)
        if not corrected:
            return None
        return {
            "word": corrected.lower(),
            "translation": "согласование подлежащего и сказуемого",
            "context": f"{mistake.original_text} -> {mistake.corrected_text}",
            "category": "mistake_agreement_patterns",
            "source_module": mistake.source_module,
            "review_reason": "Captured from subject-verb agreement correction.",
            "linked_mistake_subtype": mistake.subtype,
            "linked_mistake_title": "Subject-Verb Agreement",
        }

    if mistake.subtype == "comparative-form":
        corrected = extract_first_token(mistake.corrected_text)
        if not corrected:
            return None
        return {
            "word": corrected.lower(),
            "translation": "правильная сравнительная форма",
            "context": f"{mistake.original_text} -> {mistake.corrected_text}",
            "category": "mistake_comparatives",
            "source_module": mistake.source_module,
            "review_reason": "Captured from comparative form correction.",
            "linked_mistake_subtype": mistake.subtype,
            "linked_mistake_title": "Comparative Forms",
        }

    if mistake.subtype == "feedback-language":
        phrase = extract_feedback_phrase(mistake.corrected_text)
        if not phrase:
            return None
        return {
            "word": phrase,
            "translation": "мягкая формулировка для professional feedback",
            "context": f"{mistake.original_text} -> {mistake.corrected_text}",
            "category": "mistake_feedback_language",
            "source_module": mistake.source_module,
            "review_reason": "Captured from professional feedback phrasing correction.",
            "linked_mistake_subtype": mistake.subtype,
            "linked_mistake_title": "Feedback language for workshops",
        }

    if mistake.subtype == "tense-choice":
        phrase = extract_present_perfect_phrase(mistake.corrected_text)
        if not phrase:
            return None
        return {
            "word": phrase,
            "translation": "паттерн Present Perfect для опыта и периода с since",
            "context": f"{mistake.original_text} -> {mistake.corrected_text}",
            "category": "mistake_tense_patterns",
            "source_module": mistake.source_module,
            "review_reason": "Captured from tense correction for active reuse.",
            "linked_mistake_subtype": mistake.subtype,
            "linked_mistake_title": "Present Perfect vs Past Simple",
        }

    return None


def extract_first_token(text: str) -> str | None:
    match = re.search(r"\b([A-Za-z']+)\b", text)
    return match.group(1) if match else None


def extract_irregular_past_target(original_text: str, corrected_text: str) -> str | None:
    original_tokens = re.findall(r"[A-Za-z']+", original_text.lower())
    corrected_tokens = re.findall(r"[A-Za-z']+", corrected_text)
    for token in corrected_tokens:
        if token.lower() not in original_tokens:
            return token
    return extract_first_token(corrected_text)


def extract_agreement_target(text: str) -> str | None:
    match = re.search(r"\b(?:people|participants|managers|trainers|teams)\s+([A-Za-z']+)\b", text, flags=re.IGNORECASE)
    return match.group(1) if match else extract_first_token(text)


def extract_feedback_phrase(text: str) -> str | None:
    lowered = " ".join(text.split())
    return lowered[:80] if lowered else None


def extract_present_perfect_phrase(text: str) -> str | None:
    match = re.search(
        r"\b(?:I|We|They|He|She)\s+(?:have|has)\s+[A-Za-z']+(?:\s+[A-Za-z']+){0,4}",
        text,
        flags=re.IGNORECASE,
    )
    if match:
        return match.group(0)
    compact = " ".join(text.split())
    return compact[:80] if compact else None
