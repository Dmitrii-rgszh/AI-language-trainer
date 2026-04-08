from __future__ import annotations

import threading
from pathlib import Path

import cv2
import numpy as np


class PresenceTrackSource:
    def __init__(self, *, video_path: Path, frame_size: tuple[int, int]) -> None:
        self._video_path = video_path
        self._frame_size = frame_size
        self._capture: cv2.VideoCapture | None = None
        self._frame_count = 0
        self._current_index = 0
        self._lock = threading.Lock()

    @property
    def frame_count(self) -> int:
        return self._frame_count

    def warmup(self) -> None:
        with self._lock:
            self._open_capture_locked(reset=True)

    def close(self) -> None:
        with self._lock:
            self._close_capture_locked()

    def get_current_index(self) -> int:
        with self._lock:
            return self._current_index % max(1, self._frame_count)

    def seek(self, frame_index: int) -> None:
        with self._lock:
            if self._frame_count <= 0:
                self._current_index = 0
                return
            target_index = frame_index % self._frame_count
            self._open_capture_locked(reset=False)
            assert self._capture is not None
            self._capture.set(cv2.CAP_PROP_POS_FRAMES, float(target_index))
            self._current_index = target_index

    def next_frame(self) -> np.ndarray:
        with self._lock:
            self._open_capture_locked(reset=False)
            assert self._capture is not None
            success, frame = self._capture.read()
            if not success:
                self._open_capture_locked(reset=True)
                success, frame = self._capture.read()
            if not success:
                raise RuntimeError(f"Presence source could not read frame from: {self._video_path}")

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            target_width, target_height = self._frame_size
            if frame_rgb.shape[1] != target_width or frame_rgb.shape[0] != target_height:
                frame_rgb = cv2.resize(frame_rgb, (target_width, target_height), interpolation=cv2.INTER_LANCZOS4)

            if self._frame_count > 0:
                self._current_index = (self._current_index + 1) % self._frame_count
            return frame_rgb.astype(np.uint8)

    def _open_capture_locked(self, *, reset: bool) -> None:
        if reset or self._capture is None or not self._capture.isOpened():
            self._close_capture_locked()
            self._capture = cv2.VideoCapture(self._video_path.as_posix())
            if not self._capture.isOpened():
                raise RuntimeError(f"Could not open presence video source: {self._video_path}")
            self._frame_count = max(0, int(self._capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0))
            self._current_index = 0

    def _close_capture_locked(self) -> None:
        if self._capture is not None:
            self._capture.release()
            self._capture = None
