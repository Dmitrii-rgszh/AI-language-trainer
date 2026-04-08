from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.live_avatar.avatar.presence_meta import resolve_current_presence_video_path


@dataclass(frozen=True)
class AvatarFaceCrop:
    x: int
    y: int
    width: int
    height: int


@dataclass(frozen=True)
class AvatarAssetProfile:
    avatar_key: str
    source_image_path: Path
    idle_loop_path: Path
    presence_meta_path: Path
    presence_default_master_path: Path
    idle_fps: int
    idle_size: int
    face_crop: AvatarFaceCrop
    profile_path: Path | None = None

    @property
    def frame_size(self) -> tuple[int, int]:
        return (self.idle_size, self.idle_size)

    @property
    def presence_video_path(self) -> Path | None:
        resolved = resolve_current_presence_video_path(self.presence_meta_path)
        if resolved is not None:
            return resolved
        if self.presence_default_master_path.exists():
            return self.presence_default_master_path
        return None

    @property
    def motion_video_path(self) -> Path:
        return self.presence_video_path or self.idle_loop_path

    @property
    def cache_key(self) -> str:
        return "|".join(
            [
                self.avatar_key,
                self.source_image_path.as_posix(),
                self.idle_loop_path.as_posix(),
                self.presence_meta_path.as_posix(),
                self.motion_video_path.as_posix(),
                str(self.idle_fps),
                str(self.idle_size),
                str(self.face_crop.x),
                str(self.face_crop.y),
                str(self.face_crop.width),
                str(self.face_crop.height),
            ]
        )


def load_avatar_asset_profile_from_settings(
    *,
    avatar_key: str | None = None,
) -> AvatarAssetProfile:
    profile_path = Path(settings.live_avatar_profile_path).resolve()
    if profile_path.exists():
        return _load_avatar_asset_profile_from_file(
            profile_path,
            avatar_key=avatar_key or settings.live_avatar_default_avatar_key,
        )

    source_image_path = Path(settings.live_avatar_source_image).resolve()
    idle_loop_path = Path(settings.live_avatar_idle_loop_path).resolve()
    presence_meta_path = Path(settings.live_avatar_presence_meta_path).resolve()
    presence_default_master_path = Path(settings.live_avatar_presence_default_master_path).resolve()
    idle_size = settings.live_avatar_idle_size
    return AvatarAssetProfile(
        avatar_key=avatar_key or settings.live_avatar_default_avatar_key,
        source_image_path=source_image_path,
        idle_loop_path=idle_loop_path,
        presence_meta_path=presence_meta_path,
        presence_default_master_path=presence_default_master_path,
        idle_fps=settings.live_avatar_idle_fps,
        idle_size=idle_size,
        face_crop=AvatarFaceCrop(x=0, y=0, width=idle_size, height=idle_size),
        profile_path=profile_path,
    )


def _load_avatar_asset_profile_from_file(
    profile_path: Path,
    *,
    avatar_key: str,
) -> AvatarAssetProfile:
    payload = json.loads(profile_path.read_text(encoding="utf-8"))
    source_image_path = _resolve_profile_path(
        profile_path.parent,
        payload.get("source_image_path"),
        fallback=settings.live_avatar_source_image,
    )
    idle_loop_path = _resolve_profile_path(
        profile_path.parent,
        payload.get("idle_loop_path"),
        fallback=settings.live_avatar_idle_loop_path,
    )
    presence_meta_path = _resolve_profile_path(
        profile_path.parent,
        payload.get("presence_meta_path"),
        fallback=settings.live_avatar_presence_meta_path,
    )
    presence_default_master_path = _resolve_profile_path(
        profile_path.parent,
        payload.get("presence_default_master_path"),
        fallback=settings.live_avatar_presence_default_master_path,
    )
    idle_fps = int(payload.get("idle_fps") or settings.live_avatar_idle_fps)
    idle_size = int(payload.get("idle_size") or settings.live_avatar_idle_size)
    crop_payload = payload.get("face_crop") or {}
    face_crop = AvatarFaceCrop(
        x=int(crop_payload.get("x", 0)),
        y=int(crop_payload.get("y", 0)),
        width=int(crop_payload.get("width", idle_size)),
        height=int(crop_payload.get("height", idle_size)),
    )
    return AvatarAssetProfile(
        avatar_key=str(payload.get("avatar_key") or avatar_key).strip() or avatar_key,
        source_image_path=source_image_path,
        idle_loop_path=idle_loop_path,
        presence_meta_path=presence_meta_path,
        presence_default_master_path=presence_default_master_path,
        idle_fps=max(1, idle_fps),
        idle_size=max(1, idle_size),
        face_crop=face_crop,
        profile_path=profile_path,
    )


def _resolve_profile_path(base_dir: Path, value: Any, *, fallback: str) -> Path:
    raw_value = str(value or fallback).strip()
    path = Path(raw_value)
    if not path.is_absolute():
        path = (base_dir / path).resolve()
    return path
