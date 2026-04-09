from app.providers.tts.qwen3_tts_provider import Qwen3TTSProvider
from app.providers.tts.xtts_provider import XTTSProvider


def test_qwen_prepare_text_preserves_sentence_end_punctuation() -> None:
    prepared = Qwen3TTSProvider._prepare_text(
        text='How are you? "I am fine!"',
        style=None,
    )

    assert prepared == "How are you? I am fine!"


def test_qwen_prepare_text_keeps_question_tone_for_warm_style() -> None:
    prepared = Qwen3TTSProvider._prepare_text(
        text="Could you say that again? I want to be sure.",
        style="warm",
    )

    assert prepared == "Could you say that again? I want to be sure."


def test_xtts_prepare_text_preserves_sentence_end_punctuation() -> None:
    provider = XTTSProvider()

    prepared = provider._prepare_text(
        text='Where should we start? "Right here!"',
        language="en",
        style=None,
    )

    assert prepared == "Where should we start? Right here!"
