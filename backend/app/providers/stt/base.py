from abc import ABC, abstractmethod

from app.schemas.provider import ProviderStatus


class BaseSTTProvider(ABC):
    @abstractmethod
    def transcribe(self, audio_path: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def status(self) -> ProviderStatus:
        raise NotImplementedError

