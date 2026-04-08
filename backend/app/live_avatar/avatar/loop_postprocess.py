from __future__ import annotations

import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from app.core.config import settings


@dataclass(frozen=True)
class LoopWindowSelection:
    start_index: int
    frame_count: int
    score: float


class IdleLoopPostprocessor:
    def normalize_loop(
        self,
        *,
        input_video_path: Path,
        output_video_path: Path,
        fps: int,
        size: int,
        loop_duration_sec: float,
        blend_frames: int,
    ) -> Path:
        frames = self._read_frames(input_video_path, size=size)
        if not frames:
            raise RuntimeError(f"Idle loop postprocess could not read frames from: {input_video_path}")

        target_frame_count = max(1, int(round(loop_duration_sec * fps)))
        normalized_frames = self._select_loop_frames(frames, target_frame_count)
        softened_frames = self._soften_loop(normalized_frames, blend_frames=blend_frames)
        self._write_video(
            frames=softened_frames,
            output_video_path=output_video_path,
            fps=fps,
            size=size,
        )
        return output_video_path

    def _read_frames(self, video_path: Path, *, size: int) -> list[np.ndarray]:
        capture = cv2.VideoCapture(video_path.as_posix())
        frames: list[np.ndarray] = []
        try:
            while True:
                success, frame = capture.read()
                if not success:
                    break
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                if frame.shape[0] != size or frame.shape[1] != size:
                    frame = cv2.resize(frame, (size, size), interpolation=cv2.INTER_LANCZOS4)
                frames.append(frame.astype(np.uint8))
        finally:
            capture.release()
        return frames

    def _select_loop_frames(
        self,
        frames: list[np.ndarray],
        target_frame_count: int,
    ) -> list[np.ndarray]:
        if len(frames) == 1:
            return [frames[0].copy() for _ in range(target_frame_count)]

        selection = self._select_best_loop_window(frames, target_frame_count)
        if len(frames) >= target_frame_count:
            return self._slice_loop_window(
                frames,
                start_index=selection.start_index,
                frame_count=selection.frame_count,
            )

        if len(frames) == target_frame_count:
            return [frame.copy() for frame in frames]
        if len(frames) > target_frame_count:
            indices = np.linspace(0, len(frames) - 1, num=target_frame_count, dtype=np.float32)
            return [frames[int(round(index))].copy() for index in indices]

        repeated_frames: list[np.ndarray] = []
        while len(repeated_frames) < target_frame_count:
            for frame in frames:
                repeated_frames.append(frame.copy())
                if len(repeated_frames) >= target_frame_count:
                    break
        return repeated_frames

    def _select_best_loop_window(
        self,
        frames: list[np.ndarray],
        target_frame_count: int,
    ) -> LoopWindowSelection:
        if len(frames) <= 1:
            return LoopWindowSelection(start_index=0, frame_count=max(1, target_frame_count), score=0.0)

        if len(frames) < target_frame_count:
            return LoopWindowSelection(start_index=0, frame_count=target_frame_count, score=0.0)

        best_selection: LoopWindowSelection | None = None

        if len(frames) == target_frame_count:
            candidate_starts = range(len(frames))
        else:
            candidate_starts = range(0, len(frames) - target_frame_count + 1)

        for start_index in candidate_starts:
            candidate_frames = self._slice_loop_window(
                frames,
                start_index=start_index,
                frame_count=target_frame_count,
            )
            score = self._score_loop_candidate(candidate_frames)
            if best_selection is None or score < best_selection.score:
                best_selection = LoopWindowSelection(
                    start_index=start_index,
                    frame_count=target_frame_count,
                    score=score,
                )

        return best_selection or LoopWindowSelection(start_index=0, frame_count=target_frame_count, score=0.0)

    def _slice_loop_window(
        self,
        frames: list[np.ndarray],
        *,
        start_index: int,
        frame_count: int,
    ) -> list[np.ndarray]:
        if len(frames) >= frame_count and start_index + frame_count <= len(frames):
            return [frame.copy() for frame in frames[start_index : start_index + frame_count]]

        sliced_frames: list[np.ndarray] = []
        for frame_offset in range(frame_count):
            cycle_index = (start_index + frame_offset) % len(frames)
            sliced_frames.append(frames[cycle_index].copy())
        return sliced_frames

    def _score_loop_candidate(self, frames: list[np.ndarray]) -> float:
        if len(frames) <= 2:
            return 0.0

        motion_diffs = self._compute_motion_diffs(frames)
        if not motion_diffs:
            return 0.0

        seam_diff = self._frame_diff(frames[-1], frames[0])
        seam_context_radius = max(2, min(6, len(frames) // 12))
        seam_context = float(
            np.mean(
                [
                    self._frame_diff(frames[-seam_context_radius + index], frames[index])
                    for index in range(seam_context_radius)
                ]
            )
        )
        eye_seam_diff = self._frame_diff(self._upper_face_band(frames[-1]), self._upper_face_band(frames[0]))
        tail_velocity = frames[-1].astype(np.float32) - frames[-2].astype(np.float32)
        head_velocity = frames[1].astype(np.float32) - frames[0].astype(np.float32)
        seam_velocity = float(np.mean(np.abs(tail_velocity - head_velocity)))
        motion_median = float(np.median(motion_diffs))
        motion_peak = float(np.max(motion_diffs))
        motion_spike_penalty = motion_peak / max(motion_median, 1e-3)

        return (
            seam_diff * 0.44
            + seam_context * 0.24
            + eye_seam_diff * 0.18
            + seam_velocity * 0.1
            + motion_spike_penalty * 0.04
        )

    def _compute_motion_diffs(self, frames: list[np.ndarray]) -> list[float]:
        return [
            self._frame_diff(frames[index - 1], frames[index])
            for index in range(1, len(frames))
        ]

    def _upper_face_band(self, frame: np.ndarray) -> np.ndarray:
        height = frame.shape[0]
        top = int(round(height * 0.12))
        bottom = int(round(height * 0.52))
        return frame[top:bottom, :, :]

    def _frame_diff(self, first: np.ndarray, second: np.ndarray) -> float:
        return float(
            np.mean(
                np.abs(first.astype(np.float32) - second.astype(np.float32))
            )
        )

    def _soften_loop(
        self,
        frames: list[np.ndarray],
        *,
        blend_frames: int,
    ) -> list[np.ndarray]:
        if len(frames) <= 2:
            return frames

        output_frames = [frame.copy() for frame in frames]
        effective_blend_frames = max(0, min(blend_frames, len(output_frames) // 4))
        for index in range(effective_blend_frames):
            alpha = (index + 1) / (effective_blend_frames + 1)
            tail_index = len(output_frames) - effective_blend_frames + index
            output_frames[tail_index] = cv2.addWeighted(
                output_frames[tail_index],
                1.0 - alpha,
                output_frames[index],
                alpha,
                0.0,
            ).astype(np.uint8)
        return output_frames

    def _write_video(
        self,
        *,
        frames: list[np.ndarray],
        output_video_path: Path,
        fps: int,
        size: int,
    ) -> None:
        temp_output_path = create_temp_video_path(prefix="idle-loop-browser-source")
        try:
            self._write_video_raw(
                frames=frames,
                output_video_path=temp_output_path,
                fps=fps,
                size=size,
            )
            self._transcode_to_browser_mp4(
                input_video_path=temp_output_path,
                output_video_path=output_video_path,
            )
        finally:
            temp_output_path.unlink(missing_ok=True)

    def _write_video_raw(
        self,
        *,
        frames: list[np.ndarray],
        output_video_path: Path,
        fps: int,
        size: int,
    ) -> None:
        output_video_path.parent.mkdir(parents=True, exist_ok=True)
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(output_video_path.as_posix(), fourcc, fps, (size, size))
        if not writer.isOpened():
            raise RuntimeError(f"Could not open idle loop writer for: {output_video_path}")

        try:
            for frame in frames:
                writer.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
        finally:
            writer.release()

    def _transcode_to_browser_mp4(
        self,
        *,
        input_video_path: Path,
        output_video_path: Path,
    ) -> None:
        ffmpeg_path = self._resolve_ffmpeg_path()
        if ffmpeg_path is None:
            shutil.copy2(input_video_path, output_video_path)
            return

        output_video_path.parent.mkdir(parents=True, exist_ok=True)
        temp_browser_path = create_temp_video_path(prefix="idle-loop-browser-final")
        try:
            command = [
                ffmpeg_path,
                "-y",
                "-i",
                input_video_path.as_posix(),
                "-an",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "+faststart",
                temp_browser_path.as_posix(),
            ]
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
            )
            if completed.returncode != 0 or not temp_browser_path.exists() or temp_browser_path.stat().st_size <= 0:
                raise RuntimeError(
                    "Idle loop ffmpeg transcode failed. "
                    f"stdout: {completed.stdout.strip()} stderr: {completed.stderr.strip()}"
                )

            shutil.copy2(temp_browser_path, output_video_path)
        finally:
            temp_browser_path.unlink(missing_ok=True)

    def _resolve_ffmpeg_path(self) -> str | None:
        configured_path = settings.live_avatar_ffmpeg_path.strip()
        if not configured_path:
            return None

        if Path(configured_path).is_absolute():
            return configured_path if Path(configured_path).exists() else None

        resolved = shutil.which(configured_path)
        if resolved:
            return resolved
        return configured_path if shutil.which(configured_path) else None


def create_temp_video_path(prefix: str = "idle-loop", suffix: str = ".mp4") -> Path:
    with tempfile.NamedTemporaryFile(prefix=prefix, suffix=suffix, delete=False) as temporary_file:
        return Path(temporary_file.name)
