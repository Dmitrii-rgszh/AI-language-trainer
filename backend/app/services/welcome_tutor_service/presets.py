from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

PromptKind = Literal["intro", "replay", "clarity_intro", "clarity_model"]

WELCOME_PRESET_REVISION = "welcome-presets-v6-presence-01-forced"
WELCOME_CLARITY_PRESET_REVISION = "welcome-presets-v7-stable-coach"


@dataclass(frozen=True)
class WelcomeTutorPreset:
    locale: Literal["ru", "en"]
    render_language: Literal["ru", "en"]
    kind: PromptKind
    variant: int
    text: str
    filename: str
    revision: str


WELCOME_TUTOR_PRESETS: tuple[WelcomeTutorPreset, ...] = (
    WelcomeTutorPreset(
        locale="ru",
        render_language="ru",
        kind="intro",
        variant=0,
        text="Привет, я Лиза. Я помогу тебе говорить по-английски естественно и уверенно. Для начала скажи: Как бы ты вежливо заказал кофе без сахара на английском языке?",
        filename="ru-intro-1.mp4",
        revision=WELCOME_PRESET_REVISION,
    ),
    WelcomeTutorPreset(
        locale="ru",
        render_language="ru",
        kind="intro",
        variant=1,
        text="Привет, я Лиза, и мы будем учиться через реальные ситуации. Представь, что ты в кафе: Как бы ты вежливо заказал кофе без сахара на английском языке?",
        filename="ru-intro-2.mp4",
        revision=WELCOME_PRESET_REVISION,
    ),
    WelcomeTutorPreset(
        locale="ru",
        render_language="ru",
        kind="intro",
        variant=2,
        text="Привет, я Лиза. Здесь мы тренируем не отдельные слова, а живую речь. Первая ситуация: Как бы ты вежливо заказал кофе без сахара на английском языке?",
        filename="ru-intro-3.mp4",
        revision=WELCOME_PRESET_REVISION,
    ),
    WelcomeTutorPreset(
        locale="ru",
        render_language="ru",
        kind="replay",
        variant=0,
        text="Как бы ты вежливо заказал кофе без сахара на английском языке?",
        filename="ru-replay.mp4",
        revision=WELCOME_PRESET_REVISION,
    ),
    WelcomeTutorPreset(
        locale="ru",
        render_language="ru",
        kind="clarity_intro",
        variant=0,
        text="Послушай, как эта фраза звучит у носителя английского языка.",
        filename="ru-clarity-intro.mp4",
        revision=WELCOME_CLARITY_PRESET_REVISION,
    ),
    WelcomeTutorPreset(
        locale="en",
        render_language="en",
        kind="intro",
        variant=0,
        text="Hi, I am Liza. I will help you speak English naturally and confidently. To begin, tell me: How would you politely order a coffee without sugar in English?",
        filename="en-intro-1.mp4",
        revision=WELCOME_PRESET_REVISION,
    ),
    WelcomeTutorPreset(
        locale="en",
        render_language="en",
        kind="intro",
        variant=1,
        text="Hi, I am Liza, and we will learn through real-life situations. Imagine you are in a cafe: How would you politely order a coffee without sugar in English?",
        filename="en-intro-2.mp4",
        revision=WELCOME_PRESET_REVISION,
    ),
    WelcomeTutorPreset(
        locale="en",
        render_language="en",
        kind="intro",
        variant=2,
        text="Hi, I am Liza. Here we train real speech, not isolated words. First situation: How would you politely order a coffee without sugar in English?",
        filename="en-intro-3.mp4",
        revision=WELCOME_PRESET_REVISION,
    ),
    WelcomeTutorPreset(
        locale="en",
        render_language="en",
        kind="replay",
        variant=0,
        text="How would you politely order a coffee without sugar in English?",
        filename="en-replay.mp4",
        revision=WELCOME_PRESET_REVISION,
    ),
    WelcomeTutorPreset(
        locale="en",
        render_language="en",
        kind="clarity_intro",
        variant=0,
        text="Listen to how this phrase sounds from a native English speaker.",
        filename="en-clarity-intro.mp4",
        revision=WELCOME_CLARITY_PRESET_REVISION,
    ),
    WelcomeTutorPreset(
        locale="ru",
        render_language="en",
        kind="clarity_model",
        variant=0,
        text="I'd like a coffee without sugar.",
        filename="ru-clarity-model.mp4",
        revision=WELCOME_CLARITY_PRESET_REVISION,
    ),
    WelcomeTutorPreset(
        locale="en",
        render_language="en",
        kind="clarity_model",
        variant=0,
        text="I'd like a coffee without sugar.",
        filename="en-clarity-model.mp4",
        revision=WELCOME_CLARITY_PRESET_REVISION,
    ),
)


def iter_welcome_tutor_presets() -> tuple[WelcomeTutorPreset, ...]:
    return WELCOME_TUTOR_PRESETS


def resolve_welcome_tutor_preset(
    *,
    locale: str,
    kind: PromptKind,
    variant: int = 0,
) -> WelcomeTutorPreset:
    normalized_locale: Literal["ru", "en"] = "ru" if locale.lower().startswith("ru") else "en"
    for preset in WELCOME_TUTOR_PRESETS:
        if preset.locale == normalized_locale and preset.kind == kind and preset.variant == variant:
            return preset
    raise ValueError(f"Unknown welcome tutor preset: locale={normalized_locale} kind={kind} variant={variant}")


def build_welcome_tutor_preset_path(base_dir: Path, preset: WelcomeTutorPreset) -> Path:
    return (base_dir / preset.revision / preset.filename).resolve()
