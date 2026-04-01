from __future__ import annotations

from dataclasses import dataclass

from app.schemas.blueprint import MistakeCategory, MistakeSeverity


@dataclass
class ExtractedMistake:
    category: MistakeCategory
    subtype: str
    source_module: str
    original_text: str
    corrected_text: str
    explanation: str
    severity: MistakeSeverity
