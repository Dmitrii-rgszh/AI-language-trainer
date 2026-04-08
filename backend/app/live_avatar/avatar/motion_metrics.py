from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

import cv2
import numpy as np


@dataclass(frozen=True)
class VideoMotionMetrics:
    video_path: str
    frame_count: int
    fps: float
    duration_sec: float
    motion_mean: float
    motion_median: float
    motion_peak: float
    motion_spike_ratio: float
    seam_diff: float
    eye_seam_diff: float
    seam_velocity: float

    def to_dict(self) -> dict[str, float | int | str]:
        return asdict(self)


def read_frames(video_path: Path) -> tuple[list[np.ndarray], float]:
    capture = cv2.VideoCapture(video_path.as_posix())
    if not capture.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    fps = capture.get(cv2.CAP_PROP_FPS) or 0.0
    frames: list[np.ndarray] = []
    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB).astype(np.uint8))
    finally:
        capture.release()
    return frames, float(fps)


def frame_diff(first: np.ndarray, second: np.ndarray) -> float:
    return float(np.mean(np.abs(first.astype(np.float32) - second.astype(np.float32))))


def upper_face_band(frame: np.ndarray) -> np.ndarray:
    height = frame.shape[0]
    top = int(round(height * 0.12))
    bottom = int(round(height * 0.52))
    return frame[top:bottom, :, :]


def analyze_video(video_path: Path) -> VideoMotionMetrics:
    frames, fps = read_frames(video_path)
    if not frames:
        raise RuntimeError(f"No frames in video: {video_path}")

    motion_diffs = analyze_motion_diffs(frames)
    seam_diff = frame_diff(frames[-1], frames[0]) if len(frames) > 1 else 0.0
    eye_seam_diff = (
        frame_diff(upper_face_band(frames[-1]), upper_face_band(frames[0]))
        if len(frames) > 1
        else 0.0
    )

    if len(frames) > 2:
        tail_velocity = frames[-1].astype(np.float32) - frames[-2].astype(np.float32)
        head_velocity = frames[1].astype(np.float32) - frames[0].astype(np.float32)
        seam_velocity = float(np.mean(np.abs(tail_velocity - head_velocity)))
    else:
        seam_velocity = 0.0

    motion_mean = float(np.mean(motion_diffs)) if motion_diffs else 0.0
    motion_median = float(np.median(motion_diffs)) if motion_diffs else 0.0
    motion_peak = float(np.max(motion_diffs)) if motion_diffs else 0.0
    motion_spike_ratio = motion_peak / max(motion_median, 1e-3)

    return VideoMotionMetrics(
        video_path=video_path.as_posix(),
        frame_count=len(frames),
        fps=fps,
        duration_sec=len(frames) / fps if fps > 0 else 0.0,
        motion_mean=motion_mean,
        motion_median=motion_median,
        motion_peak=motion_peak,
        motion_spike_ratio=motion_spike_ratio,
        seam_diff=seam_diff,
        eye_seam_diff=eye_seam_diff,
        seam_velocity=seam_velocity,
    )


def analyze_motion_diffs(frames: list[np.ndarray]) -> list[float]:
    return [
        frame_diff(frames[index - 1], frames[index])
        for index in range(1, len(frames))
    ]
