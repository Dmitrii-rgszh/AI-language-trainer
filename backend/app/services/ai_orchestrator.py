from app.prompts.grammar_prompts import GRAMMAR_EXPLANATION_PROMPT
from app.prompts.profession_prompts import PROFESSION_COACH_PROMPT
from app.prompts.speaking_prompts import SPEAKING_FEEDBACK_PROMPT
from app.prompts.writing_prompts import WRITING_REVIEW_PROMPT
from app.providers.llm.base import BaseLLMProvider


class AIOrchestrator:
    def __init__(self, llm_provider: BaseLLMProvider) -> None:
        self._llm_provider = llm_provider

    def generate_stub(self, domain: str, content: str) -> str:
        prompt_map = {
            "grammar": GRAMMAR_EXPLANATION_PROMPT,
            "speaking": SPEAKING_FEEDBACK_PROMPT,
            "writing": WRITING_REVIEW_PROMPT,
            "profession": PROFESSION_COACH_PROMPT,
        }
        prompt = prompt_map.get(domain, "Provide a concise helpful response.")
        return self._llm_provider.generate(f"{prompt}\n\nCONTENT:\n{content}")

    def is_mock(self) -> bool:
        return self._llm_provider.__class__.__name__ == "MockLLMProvider"
