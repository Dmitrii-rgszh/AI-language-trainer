from abc import ABC, abstractmethod

from app.schemas.provider import ProviderStatus


class BaseSTTProvider(ABC):
    @abstractmethod
    def transcribe(self, audio_path: str, language: str | None = None) -> str:
        raise NotImplementedError

    def transcribe_detailed(self, audio_path: str, language: str | None = None) -> dict[str, object]:
        return {
            "transcript": self.transcribe(audio_path, language=language),
            "words": [],
            "average_logprob": None,
            "no_speech_prob": None,
        }

    @abstractmethod
    def status(self) -> ProviderStatus:
        raise NotImplementedError
