from __future__ import annotations

import threading
from collections import deque
from typing import ClassVar

import cv2
import numpy as np
from PIL import Image

from app.live_avatar.avatar.avatar_profile import AvatarAssetProfile
from app.live_avatar.avatar.presence_track_source import PresenceTrackSource


class AvatarMotionManager:
    _source_frame_cache: ClassVar[dict[str, np.ndarray]] = {}
    _source_frame_cache_lock: ClassVar[threading.Lock] = threading.Lock()

    def __init__(
        self,
        avatar_profile: AvatarAssetProfile,
        *,
        return_blend_ms: int,
    ) -> None:
        self._avatar_profile = avatar_profile
        self._return_blend_ms = max(0, return_blend_ms)
        self._source_frame: np.ndarray | None = None
        self._presence_source: PresenceTrackSource | None = None
        self._speaking_frames: deque[np.ndarray] = deque()
        self._blend_frames: deque[np.ndarray] = deque()
        self._last_speaking_frame: np.ndarray | None = None
        self._speaking_active = False
        self._speaking_start_idle_index = 0
        self._speaking_frame_count = 0
        self._lock = threading.Lock()
        self._is_warmed = False

    @property
    def avatar_profile(self) -> AvatarAssetProfile:
        return self._avatar_profile

    def warmup(self) -> None:
        if self._is_warmed:
            return

        source_cache_key = self._build_source_cache_key()
        with self._source_frame_cache_lock:
            source_frame = self._source_frame_cache.get(source_cache_key)
            if source_frame is None:
                source_frame = self._load_source_frame()
                self._source_frame_cache[source_cache_key] = source_frame

        self._source_frame = source_frame
        motion_video_path = self._avatar_profile.motion_video_path
        if motion_video_path.exists():
            self._presence_source = PresenceTrackSource(
                video_path=motion_video_path,
                frame_size=self._avatar_profile.frame_size,
            )
            self._presence_source.warmup()
        self._is_warmed = True

    def next_frame(self) -> np.ndarray:
        self.warmup()
        with self._lock:
            if self._speaking_frames:
                frame = self._speaking_frames.popleft()
                self._last_speaking_frame = frame
                return frame

            if self._speaking_active and self._last_speaking_frame is not None:
                return self._last_speaking_frame

            if self._blend_frames:
                return self._blend_frames.popleft()

            return self._next_presence_frame_locked()

    def get_current_idle_index(self) -> int:
        self.warmup()
        with self._lock:
            if self._presence_source is None:
                return 0
            return self._presence_source.get_current_index()

    def start_speaking(self, *, start_idle_index: int | None = None) -> int:
        self.warmup()
        with self._lock:
            cycle_length = self._get_cycle_length_locked()
            current_idle_index = self._presence_source.get_current_index() if self._presence_source is not None else 0
            normalized_index = (start_idle_index if start_idle_index is not None else current_idle_index) % cycle_length
            self._seek_presence_locked(normalized_index)
            self._speaking_start_idle_index = normalized_index
            self._speaking_active = True
            self._speaking_frames.clear()
            self._blend_frames.clear()
            self._speaking_frame_count = 0
            return normalized_index

    def enqueue_speaking_frame(self, frame_array: np.ndarray) -> None:
        self.warmup()
        with self._lock:
            self._speaking_active = True
            self._speaking_frames.append(self._resize_frame(frame_array))
            self._speaking_frame_count += 1

    def finish_speaking(self) -> None:
        self.warmup()
        with self._lock:
            self._speaking_active = False
            self._speaking_frames.clear()
            cycle_length = self._get_cycle_length_locked()
            next_index = (self._speaking_start_idle_index + self._speaking_frame_count) % cycle_length
            self._seek_presence_locked(next_index)
            self._prepare_return_blend_locked()
            self._speaking_frame_count = 0

    def clear(self) -> None:
        self.warmup()
        with self._lock:
            self._speaking_active = False
            self._speaking_frames.clear()
            self._blend_frames.clear()
            self._last_speaking_frame = None
            self._speaking_frame_count = 0

    def _next_presence_frame_locked(self) -> np.ndarray:
        if self._presence_source is None:
            return self._source_frame.copy()
        return self._presence_source.next_frame()

    def _prepare_return_blend_locked(self) -> None:
        if self._last_speaking_frame is None:
            return

        blend_frame_count = max(
            1,
            int(round((self._return_blend_ms / 1000) * self._avatar_profile.idle_fps)),
        )
        target_frame = self._next_presence_frame_locked()
        blend_frames: list[np.ndarray] = []
        for index in range(1, blend_frame_count + 1):
            alpha = index / (blend_frame_count + 1)
            blended_frame = cv2.addWeighted(
                self._last_speaking_frame,
                1.0 - alpha,
                target_frame,
                alpha,
                0.0,
            )
            blend_frames.append(blended_frame.astype(np.uint8))

        self._blend_frames = deque(blend_frames)
        self._last_speaking_frame = None

    def _seek_presence_locked(self, frame_index: int) -> None:
        if self._presence_source is None:
            return
        self._presence_source.seek(frame_index)

    def _get_cycle_length_locked(self) -> int:
        if self._presence_source is None or self._presence_source.frame_count <= 0:
            return 1
        return self._presence_source.frame_count

    def _load_source_frame(self) -> np.ndarray:
        with Image.open(self._avatar_profile.source_image_path) as source_image:
            image = source_image.convert("RGB")
            crop = self._avatar_profile.face_crop
            cropped = image.crop(
                (
                    crop.x,
                    crop.y,
                    crop.x + crop.width,
                    crop.y + crop.height,
                )
            )
            if cropped.size != self._avatar_profile.frame_size:
                cropped = cropped.resize(self._avatar_profile.frame_size, Image.Resampling.LANCZOS)
            return np.array(cropped, dtype=np.uint8)

    def _resize_frame(self, frame_array: np.ndarray) -> np.ndarray:
        target_width, target_height = self._avatar_profile.frame_size
        if frame_array.shape[1] == target_width and frame_array.shape[0] == target_height:
            return frame_array.astype(np.uint8)
        resized = cv2.resize(
            frame_array.astype(np.uint8),
            (target_width, target_height),
            interpolation=cv2.INTER_LANCZOS4,
        )
        return resized.astype(np.uint8)

    def _build_source_cache_key(self) -> str:
        return self._build_file_signature(self._avatar_profile.source_image_path)

    @staticmethod
    def _build_file_signature(path) -> str:
        try:
            stat = path.stat()
            return f"{path.as_posix()}:{stat.st_mtime_ns}:{stat.st_size}"
        except FileNotFoundError:
            return f"{path.as_posix()}:missing"
