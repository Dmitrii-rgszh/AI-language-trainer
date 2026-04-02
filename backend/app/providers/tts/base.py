from abc import ABC, abstractmethod

from app.schemas.provider import ProviderStatus


class BaseTTSProvider(ABC):
    @abstractmethod
    def synthesize(
        self,
        text: str,
        language: str,
        speaker: str | None = None,
        style: str | None = None,
    ) -> bytes:
        raise NotImplementedError

    @abstractmethod
    def status(self) -> ProviderStatus:
        raise NotImplementedError
