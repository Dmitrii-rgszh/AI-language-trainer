from __future__ import annotations

import json
import math
import shutil
from datetime import datetime, timezone
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from app.core.config import settings
from app.live_avatar.avatar.avatar_profile import AvatarAssetProfile
from app.live_avatar.avatar.idle_driver_selector import IdleDriverSelector
from app.live_avatar.avatar.liveportrait_adapter import LivePortraitAdapter, LivePortraitRenderRequest
from app.live_avatar.avatar.loop_postprocess import IdleLoopPostprocessor, create_temp_video_path


@dataclass(frozen=True)
class IdleLoopGenerationResult:
    used_liveportrait: bool
    output_video_path: Path
    raw_video_path: Path
    metadata_path: Path
    selected_driver_id: str | None = None
    selected_driver_report_path: Path | None = None


class IdleLoopGenerator:
    def __init__(
        self,
        *,
        liveportrait_adapter: LivePortraitAdapter | None = None,
        postprocessor: IdleLoopPostprocessor | None = None,
        driver_selector: IdleDriverSelector | None = None,
    ) -> None:
        self._liveportrait_adapter = liveportrait_adapter or LivePortraitAdapter()
        self._postprocessor = postprocessor or IdleLoopPostprocessor()
        self._driver_selector = driver_selector or IdleDriverSelector(
            liveportrait_adapter=self._liveportrait_adapter,
            postprocessor=self._postprocessor,
        )

    def ensure_idle_loop(
        self,
        avatar_profile: AvatarAssetProfile,
        *,
        force: bool = False,
    ) -> IdleLoopGenerationResult:
        generated_dir = Path(settings.live_avatar_generated_dir).resolve() / avatar_profile.avatar_key
        generated_dir.mkdir(parents=True, exist_ok=True)
        raw_video_path = generated_dir / "idle_loop_raw.mp4"
        metadata_path = avatar_profile.idle_loop_path.with_suffix(".meta.json")

        liveportrait_available, _ = self._liveportrait_adapter.is_available()
        resolved_driving_video = self._resolve_liveportrait_driving_video()
        prefer_liveportrait = liveportrait_available and resolved_driving_video is not None
        existing_renderer = self._read_existing_renderer(metadata_path)
        if self._is_usable_video(avatar_profile.idle_loop_path) and not force:
            if not prefer_liveportrait or existing_renderer == "liveportrait":
                selected_driver_id, selected_driver_report_path = self._read_existing_driver_selection(metadata_path)
                return IdleLoopGenerationResult(
                    used_liveportrait=existing_renderer == "liveportrait",
                    output_video_path=avatar_profile.idle_loop_path,
                    raw_video_path=raw_video_path if raw_video_path.exists() else avatar_profile.idle_loop_path,
                    metadata_path=metadata_path,
                    selected_driver_id=selected_driver_id,
                    selected_driver_report_path=selected_driver_report_path,
                )

        used_liveportrait = False
        selected_driver_id: str | None = None
        selected_driver_report_path: Path | None = None
        if prefer_liveportrait and resolved_driving_video is not None:
            if settings.live_avatar_idle_driver_autoselect:
                selection = self._driver_selector.select_driver(
                    avatar_profile,
                    generated_dir=generated_dir,
                )
                resolved_driving_video = selection.canonical_driving_video_path
                selected_driver_id = selection.candidate.candidate_id
                selected_driver_report_path = selection.report_path

            request = LivePortraitRenderRequest(
                source_image_path=avatar_profile.source_image_path,
                driving_video_path=resolved_driving_video,
                output_video_path=raw_video_path,
            )
            self._liveportrait_adapter.render_idle_raw(request)
            used_liveportrait = True
        else:
            self._generate_synthetic_idle_raw(
                avatar_profile=avatar_profile,
                output_video_path=raw_video_path,
                duration_sec=settings.live_avatar_idle_generation_duration_sec,
            )

        normalized_path = avatar_profile.idle_loop_path
        self._postprocessor.normalize_loop(
            input_video_path=raw_video_path,
            output_video_path=normalized_path,
            fps=avatar_profile.idle_fps,
            size=avatar_profile.idle_size,
            loop_duration_sec=settings.live_avatar_idle_loop_duration_sec,
            blend_frames=settings.live_avatar_idle_loop_blend_frames,
        )
        self._write_metadata(
            metadata_path=metadata_path,
            avatar_profile=avatar_profile,
            raw_video_path=raw_video_path,
            output_video_path=normalized_path,
            renderer="liveportrait" if used_liveportrait else "synthetic",
            driving_video_path=resolved_driving_video if used_liveportrait else None,
            selected_driver_id=selected_driver_id,
            selected_driver_report_path=selected_driver_report_path,
        )
        return IdleLoopGenerationResult(
            used_liveportrait=used_liveportrait,
            output_video_path=normalized_path,
            raw_video_path=raw_video_path,
            metadata_path=metadata_path,
            selected_driver_id=selected_driver_id,
            selected_driver_report_path=selected_driver_report_path,
        )

    def _is_usable_video(self, video_path: Path) -> bool:
        if not video_path.exists() or video_path.stat().st_size <= 0:
            return False

        capture = cv2.VideoCapture(video_path.as_posix())
        try:
            success, _ = capture.read()
            return bool(success)
        finally:
            capture.release()

    def _generate_synthetic_idle_raw(
        self,
        *,
        avatar_profile: AvatarAssetProfile,
        output_video_path: Path,
        duration_sec: float,
    ) -> None:
        output_video_path.parent.mkdir(parents=True, exist_ok=True)
        frame_count = max(1, int(round(duration_sec * avatar_profile.idle_fps)))
        source_frame = self._load_source_frame(avatar_profile)

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(
            output_video_path.as_posix(),
            fourcc,
            avatar_profile.idle_fps,
            avatar_profile.frame_size,
        )
        if not writer.isOpened():
            raise RuntimeError(f"Could not open synthetic idle writer for: {output_video_path}")

        try:
            for frame_index in range(frame_count):
                frame = self._render_synthetic_idle_frame(
                    source_frame=source_frame,
                    frame_index=frame_index,
                    frame_count=frame_count,
                    output_size=avatar_profile.idle_size,
                )
                writer.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
        finally:
            writer.release()

    def _load_source_frame(self, avatar_profile: AvatarAssetProfile) -> np.ndarray:
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

    def _render_synthetic_idle_frame(
        self,
        *,
        source_frame: np.ndarray,
        frame_index: int,
        frame_count: int,
        output_size: int,
    ) -> np.ndarray:
        progress = frame_index / max(1, frame_count)
        breath = math.sin(progress * math.tau)
        sway = math.sin(progress * math.tau * 0.6 + 0.9)
        drift = math.cos(progress * math.tau * 0.35 + 0.2)
        settle = math.sin(progress * math.tau * 1.35 + 1.4)

        # Keep the fallback loop visibly alive even without LivePortrait:
        # a soft zoom-breathe, a gentle side sway, and a mild vertical settle.
        scale = 1.055 + (settings.live_avatar_idle_breathing_amplitude * breath)
        rotation = 0.34 * drift
        translation_x = output_size * settings.live_avatar_idle_sway_amplitude * sway
        translation_y = (
            output_size * settings.live_avatar_idle_breathing_amplitude * 0.95 * breath
            + output_size * settings.live_avatar_idle_sway_amplitude * 0.28 * settle
        )

        scaled_size = max(output_size, int(round(output_size * scale)))
        scaled = cv2.resize(source_frame, (scaled_size, scaled_size), interpolation=cv2.INTER_LANCZOS4)

        center = (scaled_size / 2.0, scaled_size / 2.0)
        transform = cv2.getRotationMatrix2D(center, rotation, 1.0)
        transform[0, 2] += translation_x
        transform[1, 2] += translation_y

        transformed = cv2.warpAffine(
            scaled,
            transform,
            (scaled_size, scaled_size),
            flags=cv2.INTER_LANCZOS4,
            borderMode=cv2.BORDER_REFLECT_101,
        )

        start_x = max(0, (scaled_size - output_size) // 2)
        start_y = max(0, (scaled_size - output_size) // 2)
        cropped = transformed[start_y : start_y + output_size, start_x : start_x + output_size]
        if cropped.shape[0] != output_size or cropped.shape[1] != output_size:
            cropped = cv2.resize(cropped, (output_size, output_size), interpolation=cv2.INTER_LANCZOS4)
        return cropped.astype(np.uint8)

    def _resolve_liveportrait_driving_video(self) -> Path | None:
        configured_path = Path(settings.live_avatar_idle_driving_video).resolve()
        if configured_path.exists():
            return configured_path

        fallback_path = self._liveportrait_adapter.resolve_default_driving_video()
        if fallback_path is None or not fallback_path.exists():
            return None

        configured_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(fallback_path, configured_path)
        return configured_path

    def _read_existing_renderer(self, metadata_path: Path) -> str | None:
        if not metadata_path.exists():
            return None
        try:
            payload = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            return None
        renderer = str(payload.get("renderer") or "").strip().lower()
        return renderer or None

    def _read_existing_driver_selection(self, metadata_path: Path) -> tuple[str | None, Path | None]:
        if not metadata_path.exists():
            return None, None
        try:
            payload = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            return None, None
        selected_driver_id = str(payload.get("selected_driver_id") or "").strip() or None
        raw_report_path = str(payload.get("selected_driver_report_path") or "").strip()
        if not raw_report_path:
            return selected_driver_id, None
        report_path = Path(raw_report_path)
        if not report_path.is_absolute():
            report_path = (metadata_path.parent / report_path).resolve()
        return selected_driver_id, report_path

    def _write_metadata(
        self,
        *,
        metadata_path: Path,
        avatar_profile: AvatarAssetProfile,
        raw_video_path: Path,
        output_video_path: Path,
        renderer: str,
        driving_video_path: Path | None,
        selected_driver_id: str | None,
        selected_driver_report_path: Path | None,
    ) -> None:
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "avatar_key": avatar_profile.avatar_key,
            "renderer": renderer,
            "source_image_path": avatar_profile.source_image_path.as_posix(),
            "driving_video_path": driving_video_path.as_posix() if driving_video_path is not None else None,
            "raw_video_path": raw_video_path.as_posix(),
            "output_video_path": output_video_path.as_posix(),
            "idle_fps": avatar_profile.idle_fps,
            "idle_size": avatar_profile.idle_size,
            "selected_driver_id": selected_driver_id,
            "selected_driver_report_path": selected_driver_report_path.as_posix() if selected_driver_report_path is not None else None,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
        }
        metadata_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
