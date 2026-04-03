from __future__ import annotations

from app.providers.llm.base import BaseLLMProvider


class LiveAvatarDialogueService:
    def __init__(self, llm_provider: BaseLLMProvider | None) -> None:
        self._llm_provider = llm_provider

    def generate_reply(self, *, user_text: str, language: str = "ru") -> str:
        normalized_text = user_text.strip()
        if not normalized_text:
            return ""

        if self._llm_provider is None:
            return self._build_fallback_reply(normalized_text, language)

        prompt = (
            "You are Liza, a warm smiling English coach in a live avatar conversation.\n"
            "Reply in the same language as the user unless the user clearly asks otherwise.\n"
            "Keep the answer concise, friendly, and natural for spoken delivery.\n"
            "Avoid markdown, bullet points, and long lists.\n"
            "Use at most 3 short sentences.\n\n"
            f"User language hint: {language}\n"
            f"User message: {normalized_text}\n\n"
            "Assistant reply:"
        )

        try:
            reply = self._llm_provider.generate(prompt).strip()
        except Exception:
            return self._build_fallback_reply(normalized_text, language)

        return reply or self._build_fallback_reply(normalized_text, language)

    @staticmethod
    def _build_fallback_reply(user_text: str, language: str) -> str:
        if language == "ru":
            return (
                "Я услышала тебя. Давай разберём это спокойно и коротко. "
                f"Твоя реплика была: {user_text}"
            )

        return (
            "I heard you. Let us keep it simple and friendly. "
            f"Your message was: {user_text}"
        )
