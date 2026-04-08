from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PresenceSegmentMeta:
    source_path: str
    start_sec: float
    duration_sec: float


@dataclass(frozen=True)
class PresenceMasterMeta:
    presence_id: str
    video_path: str
    duration_sec: float
    fps: int
    size: int
    renderer: str
    segments: tuple[PresenceSegmentMeta, ...]


@dataclass(frozen=True)
class PresenceMeta:
    avatar_key: str
    current_presence_id: str
    masters: tuple[PresenceMasterMeta, ...]
    generated_at_utc: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_presence_meta(meta_path: Path) -> PresenceMeta | None:
    if not meta_path.exists():
        return None
    payload = json.loads(meta_path.read_text(encoding="utf-8"))
    masters_payload = payload.get("masters") or []
    masters = tuple(
        PresenceMasterMeta(
            presence_id=str(master_payload.get("presence_id") or "").strip(),
            video_path=str(master_payload.get("video_path") or "").strip(),
            duration_sec=float(master_payload.get("duration_sec") or 0.0),
            fps=int(master_payload.get("fps") or 0),
            size=int(master_payload.get("size") or 0),
            renderer=str(master_payload.get("renderer") or "").strip() or "unknown",
            segments=tuple(
                PresenceSegmentMeta(
                    source_path=str(segment_payload.get("source_path") or "").strip(),
                    start_sec=float(segment_payload.get("start_sec") or 0.0),
                    duration_sec=float(segment_payload.get("duration_sec") or 0.0),
                )
                for segment_payload in (master_payload.get("segments") or [])
                if isinstance(segment_payload, dict)
            ),
        )
        for master_payload in masters_payload
        if isinstance(master_payload, dict)
    )
    current_presence_id = str(payload.get("current_presence_id") or "").strip()
    avatar_key = str(payload.get("avatar_key") or "").strip()
    generated_at_utc = str(payload.get("generated_at_utc") or "").strip()
    if not avatar_key or not current_presence_id or not masters:
        return None
    return PresenceMeta(
        avatar_key=avatar_key,
        current_presence_id=current_presence_id,
        masters=masters,
        generated_at_utc=generated_at_utc,
    )


def save_presence_meta(meta_path: Path, presence_meta: PresenceMeta) -> None:
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    meta_path.write_text(
        json.dumps(presence_meta.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def resolve_current_presence_video_path(meta_path: Path) -> Path | None:
    presence_meta = load_presence_meta(meta_path)
    if presence_meta is None:
        return None
    for master in presence_meta.masters:
        if master.presence_id != presence_meta.current_presence_id:
            continue
        video_path = Path(master.video_path)
        if not video_path.is_absolute():
            video_path = (meta_path.parent / video_path).resolve()
        if video_path.exists():
            return video_path
    return None
