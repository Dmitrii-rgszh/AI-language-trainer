from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class QwenVoiceProfile:
    profile_id: str
    display_name: str
    reference_audio_path: str
    reference_text: str | None
    reference_text_file: str | None
    avatar_key: str
    language: str
    temperature: float
    top_p: float
    top_k: int
    repetition_penalty: float
    max_new_tokens: int
    sample_rate: int
