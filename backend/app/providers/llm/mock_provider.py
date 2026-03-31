import re

from app.providers.llm.base import BaseLLMProvider
from app.schemas.provider import ProviderStatus


class MockLLMProvider(BaseLLMProvider):
    DISPLAY_NAME = "Fallback LLM"
    STATUS_DETAILS = "Local fallback responses stay available during development and whenever LM Studio is unavailable."
    UNAVAILABLE_DETAILS = "LM Studio is unavailable, so the app is using local fallback responses."

    def generate(self, prompt: str) -> str:
        feedback_language = self._extract_feedback_language(prompt)
        learner_text = self._extract_learner_text(prompt)
        normalized_text = self._normalize_text(learner_text)

        if "Learner draft:" in prompt:
            return self._build_writing_feedback(feedback_language, normalized_text)

        if "Learner transcript:" in prompt:
            return self._build_speaking_feedback(feedback_language, normalized_text)

        if feedback_language == "en":
            return (
                "Strength: The main idea is clear. "
                "Corrections: Keep the response shorter, cleaner, and more consistent in tense. "
                "Next step: Repeat the idea once more with one concrete example."
            )

        return (
            "Сильная сторона: основная мысль понятна. "
            "Что поправить: сделай ответ короче, чище и стабильнее по временам. "
            "Следующий шаг: повтори ту же идею ещё раз и добавь один конкретный пример."
        )

    def status(self) -> ProviderStatus:
        return ProviderStatus(
            key="mock_llm",
            name=self.DISPLAY_NAME,
            type="llm",
            status="mock",
            details=self.STATUS_DETAILS,
        )

    @staticmethod
    def _extract_feedback_language(prompt: str) -> str:
        match = re.search(r"Feedback language:\s*(ru|en)\b", prompt)
        return match.group(1) if match else "ru"

    @staticmethod
    def _extract_learner_text(prompt: str) -> str:
        for marker in ("Learner draft:", "Learner transcript:"):
            if marker in prompt:
                return prompt.split(marker, maxsplit=1)[1].strip()
        return ""

    @staticmethod
    def _normalize_text(text: str) -> str:
        compact = " ".join(text.split())
        if not compact:
            return ""

        normalized = compact[0].upper() + compact[1:] if len(compact) > 1 else compact.upper()
        if normalized[-1] not in ".!?":
            normalized = f"{normalized}."
        if len(normalized) > 220:
            normalized = normalized[:217].rsplit(" ", maxsplit=1)[0].rstrip(",.;:") + "..."
        return normalized

    @classmethod
    def _build_speaking_feedback(cls, feedback_language: str, normalized_text: str) -> str:
        if feedback_language == "en":
            phrasing = (
                f"Natural phrasing: {normalized_text}"
                if normalized_text
                else "Natural phrasing: Keep the answer in 2-3 short sentences with one concrete detail."
            )
            return (
                "Strength: The answer stays on topic and is easy to follow.\n"
                "Corrections: Keep one main tense pattern, shorten long clauses, and use clearer linking words.\n"
                f"{phrasing}\n"
                "Next step: Repeat the answer once more out loud and add one specific example."
            )

        phrasing = (
            f"Более естественная формулировка: {normalized_text}"
            if normalized_text
            else "Более естественная формулировка: собери ответ в 2-3 короткие фразы и добавь одну конкретную деталь."
        )
        return (
            "Сильная сторона: ответ по теме и его легко понять.\n"
            "Что поправить: держи одно основное время, укорачивай длинные куски и добавляй более ясные связки.\n"
            f"{phrasing}\n"
            "Следующий шаг: повтори ответ вслух ещё раз и добавь один конкретный пример."
        )

    @classmethod
    def _build_writing_feedback(cls, feedback_language: str, normalized_text: str) -> str:
        if feedback_language == "en":
            revision = (
                f"Improved version: {normalized_text}"
                if normalized_text
                else "Improved version: Rewrite the draft in 2-3 clean sentences with one concrete example."
            )
            return (
                "Strength: The draft stays on topic and the main point is visible.\n"
                "Corrections: Check tense consistency, article choice, and shorter sentence structure.\n"
                f"{revision}\n"
                "Next step: Submit one revised version with a clearer closing line."
            )

        revision = (
            f"Более чистый вариант: {normalized_text}"
            if normalized_text
            else "Более чистый вариант: перепиши текст в 2-3 аккуратных предложениях и добавь один конкретный пример."
        )
        return (
            "Сильная сторона: текст остаётся по теме, и основная мысль читается.\n"
            "Что поправить: проверь согласование времён, артикли и более короткую структуру предложений.\n"
            f"{revision}\n"
            "Следующий шаг: отправь ещё одну версию с более ясным завершающим предложением."
        )
