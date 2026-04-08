from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.live_avatar.avatar.avatar_profile import AvatarAssetProfile
from app.live_avatar.avatar.presence_meta import PresenceMeta, load_presence_meta, resolve_current_presence_video_path, save_presence_meta


@dataclass(frozen=True)
class PresenceRepository:
    avatar_profile: AvatarAssetProfile

    @property
    def meta_path(self) -> Path:
        return self.avatar_profile.presence_meta_path

    def load_meta(self) -> PresenceMeta | None:
        return load_presence_meta(self.meta_path)

    def save_meta(self, presence_meta: PresenceMeta) -> None:
        save_presence_meta(self.meta_path, presence_meta)

    def get_current_video_path(self) -> Path | None:
        return resolve_current_presence_video_path(self.meta_path)
