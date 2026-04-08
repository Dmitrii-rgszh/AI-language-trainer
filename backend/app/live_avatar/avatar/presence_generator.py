from __future__ import annotations

import json
import math
import shutil
import subprocess
import tempfile
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np

from app.core.config import settings
from app.live_avatar.avatar.avatar_profile import AvatarAssetProfile
from app.live_avatar.avatar.liveportrait_adapter import LivePortraitAdapter, LivePortraitRenderRequest
from app.live_avatar.avatar.presence_meta import PresenceMasterMeta, PresenceMeta, PresenceSegmentMeta
from app.live_avatar.avatar.presence_repository import PresenceRepository


@dataclass(frozen=True)
class PresenceSegmentRecipe:
    source_path: Path
    start_sec: float
    duration_sec: float


@dataclass(frozen=True)
class PresenceMasterRecipe:
    presence_id: str
    segments: tuple[PresenceSegmentRecipe, ...]
    renderer: str = "liveportrait"
    duration_sec: float = 0.0
    is_default: bool = False


@dataclass(frozen=True)
class PresenceGenerationResult:
    current_presence_id: str
    current_video_path: Path
    meta_path: Path
    master_video_paths: tuple[Path, ...]


class PresenceAssetGenerator:
    def __init__(
        self,
        *,
        liveportrait_adapter: LivePortraitAdapter | None = None,
    ) -> None:
        self._liveportrait_adapter = liveportrait_adapter or LivePortraitAdapter()
        self._manifest_path = Path(settings.live_avatar_presence_manifest_path).resolve()
        self._project_dir = Path(settings.live_avatar_liveportrait_project_dir).resolve()
        self._asset_dir = Path(settings.live_avatar_asset_dir).resolve()

    def ensure_presence_assets(
        self,
        avatar_profile: AvatarAssetProfile,
        *,
        force: bool = False,
    ) -> PresenceGenerationResult:
        repository = PresenceRepository(avatar_profile)
        current_video_path = repository.get_current_video_path()
        if current_video_path is not None and current_video_path.exists() and not force:
            presence_meta = repository.load_meta()
            if presence_meta is not None:
                return PresenceGenerationResult(
                    current_presence_id=presence_meta.current_presence_id,
                    current_video_path=current_video_path,
                    meta_path=repository.meta_path,
                    master_video_paths=tuple(
                        self._resolve_meta_video_path(repository.meta_path, master.video_path)
                        for master in presence_meta.masters
                    ),
                )

        recipes = self._load_recipes()
        if not recipes:
            raise RuntimeError("Presence asset generator did not find any master recipes.")

        requires_liveportrait = any(recipe.renderer != "synthetic_calm" for recipe in recipes)
        if requires_liveportrait:
            available, reason = self._liveportrait_adapter.is_available()
            if not available:
                raise RuntimeError(reason)

        generated_dir = Path(settings.live_avatar_generated_dir).resolve() / avatar_profile.avatar_key / "presence"
        generated_dir.mkdir(parents=True, exist_ok=True)
        masters_meta: list[PresenceMasterMeta] = []
        master_video_paths: list[Path] = []
        current_presence_id: str | None = None

        for recipe in recipes:
            target_output_path = avatar_profile.presence_meta_path.parent / f"{recipe.presence_id}.mp4"
            self._render_presence_master(
                avatar_profile=avatar_profile,
                recipe=recipe,
                target_output_path=target_output_path,
                generated_dir=generated_dir / recipe.presence_id,
            )
            master_video_paths.append(target_output_path)
            duration_sec = self._probe_duration_seconds(target_output_path)
            masters_meta.append(
                PresenceMasterMeta(
                    presence_id=recipe.presence_id,
                    video_path=target_output_path.as_posix(),
                    duration_sec=duration_sec,
                    fps=avatar_profile.idle_fps,
                    size=avatar_profile.idle_size,
                    renderer=recipe.renderer,
                    segments=tuple(
                        PresenceSegmentMeta(
                            source_path=segment.source_path.as_posix(),
                            start_sec=segment.start_sec,
                            duration_sec=segment.duration_sec,
                        )
                        for segment in recipe.segments
                    ),
                )
            )
            if recipe.is_default and current_presence_id is None:
                current_presence_id = recipe.presence_id

        current_presence_id = current_presence_id or masters_meta[0].presence_id
        presence_meta = PresenceMeta(
            avatar_key=avatar_profile.avatar_key,
            current_presence_id=current_presence_id,
            masters=tuple(masters_meta),
            generated_at_utc=datetime.now(timezone.utc).isoformat(),
        )
        repository.save_meta(presence_meta)
        current_video_path = repository.get_current_video_path()
        if current_video_path is None:
            raise RuntimeError("Presence meta was generated, but current presence video could not be resolved.")
        return PresenceGenerationResult(
            current_presence_id=current_presence_id,
            current_video_path=current_video_path,
            meta_path=repository.meta_path,
            master_video_paths=tuple(master_video_paths),
        )

    def _load_recipes(self) -> list[PresenceMasterRecipe]:
        if self._manifest_path.exists():
            payload = json.loads(self._manifest_path.read_text(encoding="utf-8"))
            raw_masters = payload.get("masters") if isinstance(payload, dict) else payload
        else:
            raw_masters = []

        recipes: list[PresenceMasterRecipe] = []
        for index, raw_master in enumerate(raw_masters or []):
            if not isinstance(raw_master, dict):
                continue
            presence_id = str(raw_master.get("presence_id") or f"presence_master_{index + 1:02d}").strip()
            if not presence_id:
                continue
            renderer = str(raw_master.get("renderer") or "liveportrait").strip() or "liveportrait"
            segments: list[PresenceSegmentRecipe] = []
            for raw_segment in raw_master.get("segments") or []:
                if not isinstance(raw_segment, dict):
                    continue
                source_path = self._resolve_source_path(str(raw_segment.get("source_path") or "").strip())
                if source_path is None or not source_path.exists():
                    continue
                segments.append(
                    PresenceSegmentRecipe(
                        source_path=source_path,
                        start_sec=max(0.0, float(raw_segment.get("start_sec") or 0.0)),
                        duration_sec=max(1.0, float(raw_segment.get("duration_sec") or settings.live_avatar_presence_target_duration_sec)),
                    )
                )
            if renderer != "synthetic_calm" and not segments:
                continue
            recipes.append(
                PresenceMasterRecipe(
                    presence_id=presence_id,
                    segments=tuple(segments),
                    renderer=renderer,
                    duration_sec=max(0.0, float(raw_master.get("duration_sec") or 0.0)),
                    is_default=bool(raw_master.get("is_default")),
                )
            )
        return recipes

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

    def _render_presence_master(
        self,
        *,
        avatar_profile: AvatarAssetProfile,
        recipe: PresenceMasterRecipe,
        target_output_path: Path,
        generated_dir: Path,
    ) -> None:
        generated_dir.mkdir(parents=True, exist_ok=True)
        if recipe.renderer == "synthetic_calm":
            self._render_synthetic_calm_presence(
                avatar_profile=avatar_profile,
                target_output_path=target_output_path,
                duration_sec=recipe.duration_sec or settings.live_avatar_presence_target_duration_sec,
            )
            return

        normalized_segments: list[Path] = []

        try:
            for segment_index, segment in enumerate(recipe.segments):
                segment_dir = generated_dir / f"segment_{segment_index:02d}"
                segment_dir.mkdir(parents=True, exist_ok=True)
                clipped_driving_path = segment_dir / "driving_segment.mp4"
                raw_render_path = segment_dir / "presence_raw.mp4"
                normalized_path = segment_dir / "presence_normalized.mp4"

                self._clip_video_segment(
                    input_video_path=segment.source_path,
                    output_video_path=clipped_driving_path,
                    start_sec=segment.start_sec,
                    duration_sec=segment.duration_sec,
                )
                self._liveportrait_adapter.render_idle_raw(
                    LivePortraitRenderRequest(
                        source_image_path=avatar_profile.source_image_path,
                        driving_video_path=clipped_driving_path,
                        output_video_path=raw_render_path,
                    )
                )
                self._normalize_video_segment(
                    input_video_path=raw_render_path,
                    output_video_path=normalized_path,
                    fps=avatar_profile.idle_fps,
                    size=avatar_profile.idle_size,
                )
                normalized_segments.append(normalized_path)

            self._compose_presence_video(
                segment_video_paths=normalized_segments,
                output_video_path=target_output_path,
                fps=avatar_profile.idle_fps,
                size=avatar_profile.idle_size,
                blend_frames=settings.live_avatar_presence_segment_blend_frames,
            )
        finally:
            pass

    def _render_synthetic_calm_presence(
        self,
        *,
        avatar_profile: AvatarAssetProfile,
        target_output_path: Path,
        duration_sec: float,
    ) -> None:
        frame = self._load_source_frame(avatar_profile)
        fps = avatar_profile.idle_fps
        frame_count = max(1, int(round(duration_sec * fps)))
        rendered_frames: list[np.ndarray] = []

        blink_schedule_sec = (3.8, 8.2, 12.1, 16.4, 20.2, 24.6, 28.1)
        blink_span_frames = max(4, int(round(fps * 0.24)))
        blink_half_span = blink_span_frames // 2

        for frame_index in range(frame_count):
            calm_frame = frame.copy()
            blink_amount = 0.0
            for blink_time in blink_schedule_sec:
                blink_center = int(round(blink_time * fps))
                distance = abs(frame_index - blink_center)
                if distance > blink_half_span:
                    continue
                progress = 1.0 - (distance / max(1, blink_half_span))
                blink_amount = max(blink_amount, progress)
            if blink_amount > 0.0:
                calm_frame = self._apply_synthetic_blink(calm_frame, blink_amount)
            rendered_frames.append(calm_frame)

        self._write_browser_video(
            frames=rendered_frames,
            output_video_path=target_output_path,
            fps=fps,
            size=avatar_profile.idle_size,
        )

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
            raise RuntimeError(f"Could not open presence driving video: {input_video_path}")

        fps = float(capture.get(cv2.CAP_PROP_FPS) or 0.0)
        frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        if fps <= 0 or frame_count <= 0 or width <= 0 or height <= 0:
            capture.release()
            raise RuntimeError(f"Presence driving video metadata is invalid: {input_video_path}")

        start_frame = min(frame_count - 1, max(0, int(math.floor(start_sec * fps))))
        requested_frames = max(1, int(round(duration_sec * fps)))
        end_frame = min(frame_count, start_frame + requested_frames)
        if end_frame <= start_frame + 1:
            capture.release()
            raise RuntimeError(
                f"Presence segment is too short after clipping: {input_video_path} start={start_sec} duration={duration_sec}"
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
            raise RuntimeError(f"Could not open presence driving segment writer: {output_video_path}")

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
                f"Presence driving segment did not produce enough frames: {input_video_path} start={start_sec} duration={duration_sec}"
            )

    def _normalize_video_segment(
        self,
        *,
        input_video_path: Path,
        output_video_path: Path,
        fps: int,
        size: int,
    ) -> None:
        capture = cv2.VideoCapture(input_video_path.as_posix())
        if not capture.isOpened():
            raise RuntimeError(f"Could not open rendered presence segment: {input_video_path}")

        source_fps = float(capture.get(cv2.CAP_PROP_FPS) or 0.0) or float(fps)
        source_frames: list[np.ndarray] = []
        try:
            while True:
                ok, frame = capture.read()
                if not ok:
                    break
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                if frame.shape[0] != size or frame.shape[1] != size:
                    frame = cv2.resize(frame, (size, size), interpolation=cv2.INTER_LANCZOS4)
                source_frames.append(frame.astype(np.uint8))
        finally:
            capture.release()

        if not source_frames:
            raise RuntimeError(f"Presence segment render did not yield any frames: {input_video_path}")

        duration_sec = len(source_frames) / source_fps if source_fps > 0 else len(source_frames) / max(1, fps)
        target_frame_count = max(1, int(round(duration_sec * fps)))
        indices = np.linspace(0, len(source_frames) - 1, num=target_frame_count, dtype=np.float32)
        normalized_frames = [source_frames[int(round(index))] for index in indices]
        self._write_browser_video(
            frames=normalized_frames,
            output_video_path=output_video_path,
            fps=fps,
            size=size,
        )

    def _compose_presence_video(
        self,
        *,
        segment_video_paths: list[Path],
        output_video_path: Path,
        fps: int,
        size: int,
        blend_frames: int,
    ) -> None:
        if not segment_video_paths:
            raise RuntimeError("Presence composer received no normalized segment videos.")

        with tempfile.NamedTemporaryFile(prefix="presence-master-raw-", suffix=".mp4", delete=False) as temp_file:
            raw_output_path = Path(temp_file.name)

        writer = cv2.VideoWriter(
            raw_output_path.as_posix(),
            cv2.VideoWriter_fourcc(*"mp4v"),
            fps,
            (size, size),
        )
        if not writer.isOpened():
            raw_output_path.unlink(missing_ok=True)
            raise RuntimeError(f"Could not open presence master writer: {raw_output_path}")

        try:
            tail_buffer: deque[np.ndarray] = deque()
            neutral_frame: np.ndarray | None = None
            for segment_index, segment_video_path in enumerate(segment_video_paths):
                head_frames, remaining_capture = self._open_segment_with_head_frames(
                    segment_video_path=segment_video_path,
                    blend_frames=blend_frames,
                )
                current_tail: deque[np.ndarray] = deque(maxlen=max(1, blend_frames))

                if segment_index == 0:
                    neutral_frame = head_frames[0].copy() if head_frames else None
                    self._append_frames_to_tail(current_tail, head_frames, writer, neutral_frame=neutral_frame)
                else:
                    crossfade_count = min(len(tail_buffer), len(head_frames), max(1, blend_frames))
                    if crossfade_count > 0:
                        tail_frames = list(tail_buffer)[-crossfade_count:]
                        for frame_offset in range(crossfade_count):
                            alpha = (frame_offset + 1) / (crossfade_count + 1)
                            blended_frame = cv2.addWeighted(
                                tail_frames[frame_offset],
                                1.0 - alpha,
                                head_frames[frame_offset],
                                alpha,
                                0.0,
                            ).astype(np.uint8)
                            writer.write(
                                cv2.cvtColor(
                                    self._calmify_frame(blended_frame, neutral_frame),
                                    cv2.COLOR_RGB2BGR,
                                )
                            )
                    for remaining_head_frame in head_frames[crossfade_count:]:
                        self._append_frame_to_tail(current_tail, remaining_head_frame, writer, neutral_frame=neutral_frame)

                try:
                    while True:
                        ok, frame = remaining_capture.read()
                        if not ok:
                            break
                        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB).astype(np.uint8)
                        self._append_frame_to_tail(current_tail, frame, writer, neutral_frame=neutral_frame)
                finally:
                    remaining_capture.release()

                tail_buffer = current_tail

            while tail_buffer:
                frame = tail_buffer.popleft()
                writer.write(
                    cv2.cvtColor(
                        self._calmify_frame(frame, neutral_frame),
                        cv2.COLOR_RGB2BGR,
                    )
                )
        finally:
            writer.release()

        try:
            self._transcode_to_browser_mp4(
                input_video_path=raw_output_path,
                output_video_path=output_video_path,
            )
        finally:
            raw_output_path.unlink(missing_ok=True)

    def _open_segment_with_head_frames(
        self,
        *,
        segment_video_path: Path,
        blend_frames: int,
    ) -> tuple[list[np.ndarray], cv2.VideoCapture]:
        capture = cv2.VideoCapture(segment_video_path.as_posix())
        if not capture.isOpened():
            raise RuntimeError(f"Could not open normalized presence segment: {segment_video_path}")

        head_frames: list[np.ndarray] = []
        while len(head_frames) < blend_frames:
            ok, frame = capture.read()
            if not ok:
                break
            head_frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB).astype(np.uint8))
        return head_frames, capture

    def _append_frames_to_tail(
        self,
        tail_buffer: deque[np.ndarray],
        frames: list[np.ndarray],
        writer: cv2.VideoWriter,
        *,
        neutral_frame: np.ndarray | None,
    ) -> None:
        for frame in frames:
            self._append_frame_to_tail(tail_buffer, frame, writer, neutral_frame=neutral_frame)

    def _append_frame_to_tail(
        self,
        tail_buffer: deque[np.ndarray],
        frame: np.ndarray,
        writer: cv2.VideoWriter,
        *,
        neutral_frame: np.ndarray | None,
    ) -> None:
        if tail_buffer.maxlen is not None and len(tail_buffer) >= tail_buffer.maxlen:
            oldest = tail_buffer.popleft()
            writer.write(
                cv2.cvtColor(
                    self._calmify_frame(oldest, neutral_frame),
                    cv2.COLOR_RGB2BGR,
                )
            )
        tail_buffer.append(frame)

    def _calmify_frame(self, frame: np.ndarray, neutral_frame: np.ndarray | None) -> np.ndarray:
        if neutral_frame is None:
            return frame.astype(np.uint8)

        height, width = frame.shape[:2]
        damping_mask = np.zeros((height, width), dtype=np.float32)
        damping_mask = np.maximum(
            damping_mask,
            self._soft_box_mask(
                height=height,
                width=width,
                x0=0.30,
                y0=0.54,
                x1=0.70,
                y1=0.80,
                strength=settings.live_avatar_presence_lower_face_damping,
                blur_sigma=height * 0.028,
            ),
        )
        damping_mask = np.maximum(
            damping_mask,
            self._soft_box_mask(
                height=height,
                width=width,
                x0=0.36,
                y0=0.60,
                x1=0.64,
                y1=0.74,
                strength=settings.live_avatar_presence_mouth_damping,
                blur_sigma=height * 0.022,
            ),
        )

        frame_float = frame.astype(np.float32)
        neutral_float = neutral_frame.astype(np.float32)
        blended = frame_float * (1.0 - damping_mask[..., None]) + neutral_float * damping_mask[..., None]
        return np.clip(blended, 0, 255).astype(np.uint8)

    def _apply_synthetic_blink(self, frame: np.ndarray, blink_amount: float) -> np.ndarray:
        output = frame.copy()
        eye_regions = (
            (0.24, 0.29, 0.43, 0.41),
            (0.57, 0.29, 0.76, 0.41),
        )
        for x0, y0, x1, y1 in eye_regions:
            output = self._apply_blink_to_eye_region(output, x0, y0, x1, y1, blink_amount)
        return output

    def _apply_blink_to_eye_region(
        self,
        frame: np.ndarray,
        x0: float,
        y0: float,
        x1: float,
        y1: float,
        blink_amount: float,
    ) -> np.ndarray:
        height, width = frame.shape[:2]
        left = int(round(width * x0))
        top = int(round(height * y0))
        right = int(round(width * x1))
        bottom = int(round(height * y1))
        region = frame[top:bottom, left:right].copy()
        region_h = region.shape[0]
        region_w = region.shape[1]
        if region_h <= 4 or region_w <= 4:
            return frame

        top_band = region[: max(1, int(region_h * 0.36)), :, :]
        bottom_band = region[region_h - max(1, int(region_h * 0.34)) :, :, :]
        expanded_top_h = min(region_h, max(top_band.shape[0], int(round(region_h * (0.36 + blink_amount * 0.28)))))
        expanded_bottom_h = min(region_h, max(bottom_band.shape[0], int(round(region_h * (0.34 + blink_amount * 0.28)))))

        top_cover = cv2.resize(top_band, (region_w, expanded_top_h), interpolation=cv2.INTER_LINEAR)
        bottom_cover = cv2.resize(bottom_band, (region_w, expanded_bottom_h), interpolation=cv2.INTER_LINEAR)

        closed_region = region.copy()
        closed_region[:expanded_top_h, :, :] = top_cover
        closed_region[region_h - expanded_bottom_h :, :, :] = bottom_cover
        if expanded_top_h + expanded_bottom_h < region_h:
            bridge_top = expanded_top_h
            bridge_bottom = region_h - expanded_bottom_h
            eyelid_color = (
                0.55 * np.mean(top_band.astype(np.float32), axis=(0, 1))
                + 0.45 * np.mean(bottom_band.astype(np.float32), axis=(0, 1))
            )
            closed_region[bridge_top:bridge_bottom, :, :] = eyelid_color.astype(np.uint8)

        mask = self._soft_box_mask(
            height=height,
            width=width,
            x0=x0 - 0.02,
            y0=y0 - 0.02,
            x1=x1 + 0.02,
            y1=y1 + 0.03,
            strength=min(1.0, blink_amount * 0.92),
            blur_sigma=height * 0.012,
        )
        blended = frame.astype(np.float32)
        blended[top:bottom, left:right, :] = (
            region.astype(np.float32) * (1.0 - np.clip(blink_amount, 0.0, 1.0))
            + closed_region.astype(np.float32) * np.clip(blink_amount, 0.0, 1.0)
        )
        alpha = mask[..., None]
        final = frame.astype(np.float32) * (1.0 - alpha) + blended * alpha
        return np.clip(final, 0, 255).astype(np.uint8)

    def _load_source_frame(self, avatar_profile: AvatarAssetProfile) -> np.ndarray:
        from PIL import Image

        with Image.open(avatar_profile.source_image_path) as source_image:
            image = source_image.convert("RGB")
            crop = avatar_profile.face_crop
            cropped = image.crop(
                (
                    crop.x,
                    crop.y,
                    crop.x + crop.width,
                    crop.y + crop.height,
                )
            )
            if cropped.size != avatar_profile.frame_size:
                cropped = cropped.resize(avatar_profile.frame_size, Image.Resampling.LANCZOS)
            return np.array(cropped, dtype=np.uint8)

    def _soft_box_mask(
        self,
        *,
        height: int,
        width: int,
        x0: float,
        y0: float,
        x1: float,
        y1: float,
        strength: float,
        blur_sigma: float,
    ) -> np.ndarray:
        mask = np.zeros((height, width), dtype=np.float32)
        left = int(round(width * x0))
        top = int(round(height * y0))
        right = int(round(width * x1))
        bottom = int(round(height * y1))
        mask[top:bottom, left:right] = np.clip(strength, 0.0, 1.0)
        kernel_size = max(3, int(round(blur_sigma)) * 2 + 1)
        return cv2.GaussianBlur(mask, (kernel_size, kernel_size), blur_sigma)

    def _write_browser_video(
        self,
        *,
        frames: list[np.ndarray],
        output_video_path: Path,
        fps: int,
        size: int,
    ) -> None:
        with tempfile.NamedTemporaryFile(prefix="presence-segment-raw-", suffix=".mp4", delete=False) as temp_file:
            raw_output_path = Path(temp_file.name)
        writer = cv2.VideoWriter(
            raw_output_path.as_posix(),
            cv2.VideoWriter_fourcc(*"mp4v"),
            fps,
            (size, size),
        )
        if not writer.isOpened():
            raw_output_path.unlink(missing_ok=True)
            raise RuntimeError(f"Could not open presence segment writer: {raw_output_path}")
        try:
            for frame in frames:
                writer.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
        finally:
            writer.release()
        try:
            self._transcode_to_browser_mp4(
                input_video_path=raw_output_path,
                output_video_path=output_video_path,
            )
        finally:
            raw_output_path.unlink(missing_ok=True)

    def _transcode_to_browser_mp4(
        self,
        *,
        input_video_path: Path,
        output_video_path: Path,
    ) -> None:
        ffmpeg_path = self._resolve_ffmpeg_path()
        output_video_path.parent.mkdir(parents=True, exist_ok=True)
        if ffmpeg_path is None:
            shutil.copy2(input_video_path, output_video_path)
            return

        with tempfile.NamedTemporaryFile(prefix="presence-browser-", suffix=".mp4", delete=False) as temp_file:
            browser_output_path = Path(temp_file.name)
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
                browser_output_path.as_posix(),
            ]
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
            )
            if completed.returncode != 0 or not browser_output_path.exists() or browser_output_path.stat().st_size <= 0:
                raise RuntimeError(
                    "Presence ffmpeg transcode failed. "
                    f"stdout: {completed.stdout.strip()} stderr: {completed.stderr.strip()}"
                )
            shutil.copy2(browser_output_path, output_video_path)
        finally:
            browser_output_path.unlink(missing_ok=True)

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

    def _resolve_meta_video_path(self, meta_path: Path, video_path: str) -> Path:
        candidate = Path(video_path)
        if not candidate.is_absolute():
            candidate = (meta_path.parent / candidate).resolve()
        return candidate

    def _probe_duration_seconds(self, video_path: Path) -> float:
        capture = cv2.VideoCapture(video_path.as_posix())
        if not capture.isOpened():
            return 0.0
        try:
            fps = float(capture.get(cv2.CAP_PROP_FPS) or 0.0)
            frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        finally:
            capture.release()
        if fps <= 0:
            return 0.0
        return frame_count / fps
