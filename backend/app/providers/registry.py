from app.core.config import settings
from app.providers.llm.lmstudio_provider import LMStudioProvider
from app.providers.llm.mock_provider import MockLLMProvider
from app.providers.scoring.rule_based_provider import RuleBasedScoringProvider
from app.providers.stt.faster_whisper_provider import FasterWhisperProvider
from app.providers.tts.xtts_provider import XTTSProvider
from app.schemas.provider import ProviderStatus


class ProviderRegistry:
    def __init__(self) -> None:
        self.mock_llm_provider = MockLLMProvider()
        self.lmstudio_llm_provider = LMStudioProvider()
        self.faster_whisper_provider = FasterWhisperProvider()
        self.xtts_provider = XTTSProvider()
        self.rule_based_scoring_provider = RuleBasedScoringProvider()
        self.llm_provider = self._resolve_default_llm_provider()
        self.stt_provider = self._resolve_default_stt_provider()
        self.tts_provider = self._resolve_default_tts_provider()
        self.scoring_provider = self.rule_based_scoring_provider

    def _resolve_default_llm_provider(self):
        if settings.llm_provider == "lmstudio":
            status = self.lmstudio_llm_provider.status()
            if status.status == "ready":
                return self.lmstudio_llm_provider

        return self.mock_llm_provider

    def _resolve_default_tts_provider(self):
        if settings.tts_provider == "xtts":
            status = self.xtts_provider.status()
            if status.status == "ready":
                return self.xtts_provider

        return None

    def _resolve_default_stt_provider(self):
        if settings.stt_provider == "faster_whisper":
            status = self.faster_whisper_provider.status()
            if status.status == "ready":
                return self.faster_whisper_provider

        return None

    def get_statuses(self) -> list[ProviderStatus]:
        llm_status = self.lmstudio_llm_provider.status()
        if settings.llm_provider != "lmstudio":
            llm_status = self.mock_llm_provider.status()
        elif llm_status.status != "ready":
            llm_status = ProviderStatus(
                key="mock_llm",
                name="Mock LLM Provider",
                type="llm",
                status="mock",
                details="LM Studio is unavailable, so backend fell back to mock LLM.",
            )

        tts_status = self.xtts_provider.status()
        if settings.tts_provider != "xtts":
            tts_status = ProviderStatus(
                key="tts_disabled",
                name="TTS Engine",
                type="tts",
                status="offline",
                details="TTS provider is disabled in configuration.",
            )
        stt_status = self.faster_whisper_provider.status()
        if settings.stt_provider != "faster_whisper":
            stt_status = ProviderStatus(
                key="stt_disabled",
                name="STT Engine",
                type="stt",
                status="offline",
                details="STT provider is disabled in configuration.",
            )

        return [
            llm_status,
            stt_status,
            tts_status,
            self.rule_based_scoring_provider.status(),
        ]
