from __future__ import annotations

from pathlib import Path

from app.core.config import settings
from app.services.voice_service.service import VoiceService

WELCOME_REPLAY_PROMPTS: dict[str, str] = {
    "ru": "Как бы ты вежливо заказал кофе без сахара на английском языке?",
    "en": "How would you politely order a coffee without sugar in English?",
}

WELCOME_REPLAY_SPEAKER = "Daisy Studious"
WELCOME_REPLAY_STYLE = "warm"


def get_welcome_replay_audio_path(locale: str) -> Path:
    normalized_locale = "ru" if locale.lower().startswith("ru") else "en"
    configured_path = (
        settings.welcome_replay_audio_ru_path
        if normalized_locale == "ru"
        else settings.welcome_replay_audio_en_path
    )
    return Path(configured_path).resolve()


def ensure_welcome_replay_audio_cached(
    voice_service: VoiceService,
    *,
    locale: str,
) -> Path:
    normalized_locale = "ru" if locale.lower().startswith("ru") else "en"
    target_path = get_welcome_replay_audio_path(normalized_locale)
    if target_path.exists() and target_path.stat().st_size > 0:
        return target_path

    target_path.parent.mkdir(parents=True, exist_ok=True)
    audio_bytes = voice_service.synthesize(
        text=WELCOME_REPLAY_PROMPTS[normalized_locale],
        language=normalized_locale,
        speaker=WELCOME_REPLAY_SPEAKER,
        style=WELCOME_REPLAY_STYLE,
    )
    target_path.write_bytes(audio_bytes)
    return target_path
