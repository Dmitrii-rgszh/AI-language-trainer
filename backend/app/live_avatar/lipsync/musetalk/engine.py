from __future__ import annotations

import base64
import io
import json
from collections.abc import AsyncIterator

import httpx
import numpy as np
from PIL import Image

from app.core.config import settings


class MuseTalkLiveEngine:
    def __init__(self) -> None:
        self._base_url = settings.musetalk_live_base_url.rstrip("/")
        self._default_avatar_key = settings.live_avatar_default_avatar_key
        self._avatar_images = {
            settings.live_avatar_default_avatar_key: settings.musetalk_avatar_verba_tutor_image,
        }

    async def warmup(self) -> None:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{self._base_url}/health")
            response.raise_for_status()
            await self.prepare_avatar(self._default_avatar_key)

    def check_health(self) -> tuple[bool, str]:
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(f"{self._base_url}/health")
                response.raise_for_status()
        except Exception as exc:
            return False, f"MuseTalk live runtime is unavailable: {exc}"
        return True, "MuseTalk live runtime is ready."

    async def prepare_avatar(self, avatar_key: str) -> None:
        avatar_image = self._avatar_images.get(avatar_key)
        if not avatar_image:
            raise RuntimeError(f"Unknown live avatar key: {avatar_key}")

        payload = {
            "avatar_id": avatar_key,
            "image_path": avatar_image,
        }
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(f"{self._base_url}/prepare-avatar", json=payload)
            response.raise_for_status()

    async def stream_frames(
        self,
        *,
        audio_path: str,
        avatar_key: str,
        fps: int,
    ) -> AsyncIterator[np.ndarray]:
        payload = {
            "avatar_id": avatar_key,
            "audio_path": audio_path,
            "fps": fps,
        }
        timeout = httpx.Timeout(connect=30.0, read=600.0, write=60.0, pool=30.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream(
                "POST",
                f"{self._base_url}/render-stream",
                json=payload,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    payload = json.loads(line)
                    event_type = payload.get("type")
                    if event_type == "meta":
                        continue
                    if event_type == "error":
                        raise RuntimeError(payload.get("detail", "MuseTalk live stream failed."))
                    if event_type != "frame":
                        continue

                    image_bytes = base64.b64decode(payload["data"])
                    with Image.open(io.BytesIO(image_bytes)) as image:
                        yield np.array(image.convert("RGB"), dtype=np.uint8)
