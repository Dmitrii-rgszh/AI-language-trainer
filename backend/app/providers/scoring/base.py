from abc import ABC, abstractmethod

from app.schemas.provider import ProviderStatus


class BaseScoringProvider(ABC):
    @abstractmethod
    def score(self, content: str) -> int:
        raise NotImplementedError

    @abstractmethod
    def score_pronunciation(
        self,
        target_text: str,
        transcript: str,
        acoustic_signals: dict[str, object] | None = None,
    ) -> dict[str, object]:
        raise NotImplementedError

    @abstractmethod
    def status(self) -> ProviderStatus:
        raise NotImplementedError
