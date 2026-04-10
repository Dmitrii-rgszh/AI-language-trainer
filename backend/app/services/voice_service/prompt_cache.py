from __future__ import annotations

from pathlib import Path
from typing import Literal

from app.core.config import settings
from app.services.voice_service.service import VoiceService

WelcomeProofLessonCue = Literal["feedback", "clarity", "retry", "result"]

WELCOME_REPLAY_PROMPTS: dict[str, str] = {
    "ru": "Как бы ты вежливо заказал кофе без сахара на английском языке?",
    "en": "How would you politely order a coffee without sugar in English?",
}

WELCOME_PROOF_LESSON_CUE_PROMPTS: dict[str, dict[WelcomeProofLessonCue, str]] = {
    "ru": {
        "feedback": "Смотри, я сохранила твою мысль и сделала фразу естественнее.",
        "clarity": "Теперь быстро посмотрим, насколько легко тебя понять в этой фразе.",
        "retry": "Теперь сразу перенесём этот шаблон в новую фразу.",
        "result": "Смотри, за пару минут у тебя уже появился рабочий речевой шаблон.",
    },
    "en": {
        "feedback": "Let me keep your meaning and make the phrase sound more natural.",
        "clarity": "Now let us quickly check how easy this phrase is to understand.",
        "retry": "Now let us move this pattern straight into a new phrase.",
        "result": "Look, in just a couple of minutes you already have a working speech pattern.",
    },
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


def get_welcome_proof_lesson_cue_audio_path(
    locale: str,
    cue: WelcomeProofLessonCue,
) -> Path:
    normalized_locale = "ru" if locale.lower().startswith("ru") else "en"
    base_dir = Path(settings.welcome_audio_cache_dir).resolve()
    return (base_dir / f"welcome_proof_lesson_{normalized_locale}_{cue}.wav").resolve()


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


def iter_welcome_proof_lesson_cues() -> tuple[WelcomeProofLessonCue, ...]:
    return ("feedback", "clarity", "retry", "result")


def ensure_welcome_proof_lesson_cue_audio_cached(
    voice_service: VoiceService,
    *,
    locale: str,
    cue: WelcomeProofLessonCue,
) -> Path:
    normalized_locale = "ru" if locale.lower().startswith("ru") else "en"
    target_path = get_welcome_proof_lesson_cue_audio_path(normalized_locale, cue)
    if target_path.exists() and target_path.stat().st_size > 0:
        return target_path

    target_path.parent.mkdir(parents=True, exist_ok=True)
    audio_bytes = voice_service.synthesize(
        text=WELCOME_PROOF_LESSON_CUE_PROMPTS[normalized_locale][cue],
        language=normalized_locale,
        speaker=WELCOME_REPLAY_SPEAKER,
        style=WELCOME_REPLAY_STYLE,
    )
    target_path.write_bytes(audio_bytes)
    return target_path
