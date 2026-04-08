from __future__ import annotations

import json
import math
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2

from app.core.config import settings
from app.live_avatar.avatar.avatar_profile import AvatarAssetProfile
from app.live_avatar.avatar.liveportrait_adapter import LivePortraitAdapter, LivePortraitRenderRequest
from app.live_avatar.avatar.loop_postprocess import IdleLoopPostprocessor
from app.live_avatar.avatar.motion_metrics import VideoMotionMetrics, analyze_video


@dataclass(frozen=True)
class IdleDriverCandidate:
    candidate_id: str
    source_path: Path
    start_sec: float
    duration_sec: float
    score_bias: float = 0.0


@dataclass(frozen=True)
class IdleDriverSelection:
    candidate: IdleDriverCandidate
    score: float
    metrics: VideoMotionMetrics
    report_path: Path
    canonical_driving_video_path: Path


_DEFAULT_DRIVER_CANDIDATES: tuple[dict[str, float | str], ...] = (
    {"candidate_id": "d9_08_14", "source_path": "assets/examples/driving/d9.mp4", "start_sec": 8.0, "duration_sec": 6.0},
    {"candidate_id": "d9_10_16", "source_path": "assets/examples/driving/d9.mp4", "start_sec": 10.0, "duration_sec": 6.0},
    {"candidate_id": "d10_03_09", "source_path": "assets/examples/driving/d10.mp4", "start_sec": 3.0, "duration_sec": 6.0},
    {"candidate_id": "d11_01_07", "source_path": "assets/examples/driving/d11.mp4", "start_sec": 1.0, "duration_sec": 6.0},
    {"candidate_id": "d12_00_06", "source_path": "assets/examples/driving/d12.mp4", "start_sec": 0.0, "duration_sec": 6.0},
    {"candidate_id": "d20_00_06", "source_path": "assets/examples/driving/d20.mp4", "start_sec": 0.0, "duration_sec": 6.0, "score_bias": -3.0},
)


class IdleDriverSelector:
    def __init__(
        self,
        *,
        liveportrait_adapter: LivePortraitAdapter | None = None,
        postprocessor: IdleLoopPostprocessor | None = None,
    ) -> None:
        self._liveportrait_adapter = liveportrait_adapter or LivePortraitAdapter()
        self._postprocessor = postprocessor or IdleLoopPostprocessor()
        self._project_dir = Path(settings.live_avatar_liveportrait_project_dir).resolve()
        self._asset_dir = Path(settings.live_avatar_asset_dir).resolve()
        self._manifest_path = Path(settings.live_avatar_idle_driver_candidates_path).resolve()

    def select_driver(
        self,
        avatar_profile: AvatarAssetProfile,
        *,
        generated_dir: Path,
    ) -> IdleDriverSelection:
        candidates = self._load_candidates()
        if not candidates:
            raise RuntimeError("Idle driver selector did not find any usable driver candidates.")

        selection_dir = generated_dir / "driver_selection"
        inputs_dir = selection_dir / "inputs"
        raw_dir = selection_dir / "render_raw"
        loops_dir = selection_dir / "loops"
        inputs_dir.mkdir(parents=True, exist_ok=True)
        raw_dir.mkdir(parents=True, exist_ok=True)
        loops_dir.mkdir(parents=True, exist_ok=True)

        report_entries: list[dict[str, Any]] = []
        best_result: IdleDriverSelection | None = None

        for candidate in candidates:
            entry: dict[str, Any] = {
                "candidate_id": candidate.candidate_id,
                "source_path": candidate.source_path.as_posix(),
                "start_sec": candidate.start_sec,
                "duration_sec": candidate.duration_sec,
                "score_bias": candidate.score_bias,
            }
            try:
                driving_segment_path = inputs_dir / f"{candidate.candidate_id}.mp4"
                raw_render_path = raw_dir / f"{candidate.candidate_id}.mp4"
                loop_path = loops_dir / f"{candidate.candidate_id}.mp4"
                if not self._is_usable_video(loop_path):
                    self._clip_video_segment(
                        input_video_path=candidate.source_path,
                        output_video_path=driving_segment_path,
                        start_sec=candidate.start_sec,
                        duration_sec=candidate.duration_sec,
                    )

                    self._liveportrait_adapter.render_idle_raw(
                        LivePortraitRenderRequest(
                            source_image_path=avatar_profile.source_image_path,
                            driving_video_path=driving_segment_path,
                            output_video_path=raw_render_path,
                        )
                    )

                    self._postprocessor.normalize_loop(
                        input_video_path=raw_render_path,
                        output_video_path=loop_path,
                        fps=avatar_profile.idle_fps,
                        size=avatar_profile.idle_size,
                        loop_duration_sec=settings.live_avatar_idle_loop_duration_sec,
                        blend_frames=settings.live_avatar_idle_loop_blend_frames,
                    )
                metrics = analyze_video(loop_path)
                score = self._score_candidate(candidate, metrics)
                entry.update(
                    {
                        "status": "ok",
                        "score": score,
                        "metrics": metrics.to_dict(),
                        "driving_segment_path": driving_segment_path.as_posix(),
                        "raw_render_path": raw_render_path.as_posix(),
                        "loop_path": loop_path.as_posix(),
                    }
                )
                if best_result is None or score < best_result.score:
                    best_result = IdleDriverSelection(
                        candidate=candidate,
                        score=score,
                        metrics=metrics,
                        report_path=selection_dir / "selection_report.json",
                        canonical_driving_video_path=Path(settings.live_avatar_idle_driving_video).resolve(),
                    )
                    shutil.copy2(driving_segment_path, best_result.canonical_driving_video_path)
            except Exception as exc:  # noqa: BLE001 - keep candidate sweep resilient
                entry.update(
                    {
                        "status": "error",
                        "error": str(exc),
                    }
                )
            report_entries.append(entry)

        if best_result is None:
            report_path = selection_dir / "selection_report.json"
            report_path.write_text(
                json.dumps({"status": "error", "candidates": report_entries}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            raise RuntimeError(f"Idle driver selector could not render any usable candidate. See: {report_path}")

        report_payload = {
            "status": "ok",
            "selected_candidate_id": best_result.candidate.candidate_id,
            "selected_score": best_result.score,
            "selected_metrics": best_result.metrics.to_dict(),
            "canonical_driving_video_path": best_result.canonical_driving_video_path.as_posix(),
            "candidates": report_entries,
        }
        best_result.report_path.write_text(
            json.dumps(report_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return best_result

    def _load_candidates(self) -> list[IdleDriverCandidate]:
        if self._manifest_path.exists():
            payload = json.loads(self._manifest_path.read_text(encoding="utf-8"))
            candidate_payloads = payload.get("candidates") if isinstance(payload, dict) else payload
        else:
            candidate_payloads = list(_DEFAULT_DRIVER_CANDIDATES)

        candidates: list[IdleDriverCandidate] = []
        for index, raw_candidate in enumerate(candidate_payloads or []):
            if not isinstance(raw_candidate, dict):
                continue
            raw_id = str(raw_candidate.get("candidate_id") or f"candidate_{index + 1}").strip()
            raw_source = raw_candidate.get("source_path")
            if not raw_id or not raw_source:
                continue
            source_path = self._resolve_source_path(str(raw_source))
            if source_path is None or not source_path.exists():
                continue
            candidates.append(
                IdleDriverCandidate(
                    candidate_id=raw_id,
                    source_path=source_path,
                    start_sec=max(0.0, float(raw_candidate.get("start_sec") or 0.0)),
                    duration_sec=max(1.0, float(raw_candidate.get("duration_sec") or settings.live_avatar_idle_generation_duration_sec)),
                    score_bias=float(raw_candidate.get("score_bias") or 0.0),
                )
            )
        return candidates

    def _resolve_source_path(self, raw_value: str) -> Path | None:
        candidate = Path(raw_value)
        if candidate.is_absolute():
            return candidate.resolve()

        project_relative = (self._project_dir / raw_value).resolve()
        if project_relative.exists():
            return project_relative

        asset_relative = (self._asset_dir / raw_value).resolve()
        if asset_relative.exists():
            return asset_relative

        examples_relative = (self._project_dir / "assets" / "examples" / "driving" / raw_value).resolve()
        if examples_relative.exists():
            return examples_relative
        return None

    def _clip_video_segment(
        self,
        *,
        input_video_path: Path,
        output_video_path: Path,
        start_sec: float,
        duration_sec: float,
    ) -> None:
        capture = cv2.VideoCapture(input_video_path.as_posix())
        if not capture.isOpened():
            raise RuntimeError(f"Could not open driver video: {input_video_path}")

        fps = float(capture.get(cv2.CAP_PROP_FPS) or 0.0)
        frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        if fps <= 0 or frame_count <= 0 or width <= 0 or height <= 0:
            capture.release()
            raise RuntimeError(f"Driver video metadata is invalid: {input_video_path}")

        start_frame = min(frame_count - 1, max(0, int(math.floor(start_sec * fps))))
        end_frame = min(frame_count, start_frame + max(1, int(round(duration_sec * fps))))
        if end_frame <= start_frame + 1:
            capture.release()
            raise RuntimeError(
                f"Driver segment is too short after clipping: {input_video_path} start={start_sec} duration={duration_sec}"
            )

        output_video_path.parent.mkdir(parents=True, exist_ok=True)
        writer = cv2.VideoWriter(
            output_video_path.as_posix(),
            cv2.VideoWriter_fourcc(*"mp4v"),
            fps,
            (width, height),
        )
        if not writer.isOpened():
            capture.release()
            raise RuntimeError(f"Could not open driver segment writer: {output_video_path}")

        try:
            capture.set(cv2.CAP_PROP_POS_FRAMES, float(start_frame))
            written_frames = 0
            while capture.isOpened() and (start_frame + written_frames) < end_frame:
                ok, frame = capture.read()
                if not ok:
                    break
                writer.write(frame)
                written_frames += 1
        finally:
            writer.release()
            capture.release()

        if written_frames <= 1:
            raise RuntimeError(
                f"Driver segment did not produce enough frames: {input_video_path} start={start_sec} duration={duration_sec}"
            )

    def _score_candidate(self, candidate: IdleDriverCandidate, metrics: VideoMotionMetrics) -> float:
        target_motion_min = settings.live_avatar_idle_target_motion_min
        target_motion_max = settings.live_avatar_idle_target_motion_max
        spike_ratio_max = settings.live_avatar_idle_target_spike_ratio_max

        low_motion_penalty = max(0.0, target_motion_min - metrics.motion_mean)
        high_motion_penalty = max(0.0, metrics.motion_mean - target_motion_max)
        spike_penalty = max(0.0, metrics.motion_spike_ratio - spike_ratio_max)

        return (
            metrics.seam_diff * 0.58
            + metrics.eye_seam_diff * 0.34
            + metrics.seam_velocity * 0.16
            + spike_penalty * 8.0
            + low_motion_penalty * 32.0
            + high_motion_penalty * 24.0
            + metrics.motion_peak * 0.2
            + candidate.score_bias
        )

    def _is_usable_video(self, video_path: Path) -> bool:
        if not video_path.exists() or video_path.stat().st_size <= 0:
            return False
        capture = cv2.VideoCapture(video_path.as_posix())
        try:
            ok, _ = capture.read()
            return bool(ok)
        finally:
            capture.release()
