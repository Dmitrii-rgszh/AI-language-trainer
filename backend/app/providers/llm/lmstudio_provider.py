from __future__ import annotations

from typing import Any

import httpx

from app.core.config import settings
from app.providers.llm.base import BaseLLMProvider
from app.schemas.provider import ProviderAvailability, ProviderStatus


class LMStudioProvider(BaseLLMProvider):
    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        api_key: str | None = None,
        timeout: float | None = None,
    ) -> None:
        self._base_url = (base_url or settings.lmstudio_base_url).rstrip("/")
        self._model = model or settings.lmstudio_model
        self._api_key = api_key or settings.lmstudio_api_key
        self._timeout = timeout or settings.lmstudio_timeout_seconds

    def generate(self, prompt: str) -> str:
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": "You are a concise, helpful English trainer assistant."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }
        response = self._request("POST", "/chat/completions", json=payload)
        choices = response.get("choices", [])
        if not choices:
            raise RuntimeError("LM Studio returned no choices.")

        message = choices[0].get("message", {})
        content = message.get("content")
        if not content:
            raise RuntimeError("LM Studio returned an empty message.")

        return str(content).strip()

    def status(self) -> ProviderStatus:
        try:
            response = self._request("GET", "/models")
            models = response.get("data", [])
            resolved_model = self._model
            if models:
                resolved_model = str(models[0].get("id", self._model))

            return ProviderStatus(
                key="lmstudio_llm",
                name="LM Studio LLM",
                type="llm",
                status=ProviderAvailability.READY,
                details=f"Connected to {self._base_url} with model '{resolved_model}'.",
            )
        except Exception as exc:
            return ProviderStatus(
                key="lmstudio_llm",
                name="LM Studio LLM",
                type="llm",
                status=ProviderAvailability.OFFLINE,
                details=f"LM Studio server is unavailable at {self._base_url}: {exc}",
            )

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self._api_key}"
        with httpx.Client(base_url=self._base_url, timeout=self._timeout) as client:
            response = client.request(method, path, headers=headers, **kwargs)
            response.raise_for_status()
            return response.json()
