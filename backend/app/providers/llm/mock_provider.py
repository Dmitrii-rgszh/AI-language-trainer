from app.providers.llm.base import BaseLLMProvider
from app.schemas.provider import ProviderStatus


class MockLLMProvider(BaseLLMProvider):
    def generate(self, prompt: str) -> str:
        snippet = prompt.strip().splitlines()[0] if prompt.strip() else "prompt"
        return f"Mock response generated for: {snippet}"

    def status(self) -> ProviderStatus:
        return ProviderStatus(
            key="mock_llm",
            name="Mock LLM Provider",
            type="llm",
            status="mock",
            details="Готов для локальной разработки и fallback, пока реальный LM Studio provider не активен.",
        )
