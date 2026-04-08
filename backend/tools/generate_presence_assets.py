from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _bootstrap_backend_path() -> Path:
    backend_dir = Path(__file__).resolve().parents[1]
    if backend_dir.as_posix() not in sys.path:
        sys.path.insert(0, backend_dir.as_posix())
    return backend_dir


def main() -> int:
    _bootstrap_backend_path()

    from app.live_avatar.avatar.avatar_profile import load_avatar_asset_profile_from_settings
    from app.live_avatar.avatar.liveportrait_adapter import LivePortraitAdapter
    from app.live_avatar.avatar.presence_generator import PresenceAssetGenerator

    parser = argparse.ArgumentParser(
        description="Generate or regenerate long presence video assets for the live avatar.",
    )
    parser.add_argument(
        "--avatar-key",
        default=None,
        help="Optional avatar key override. Defaults to LIVE_AVATAR_DEFAULT_AVATAR_KEY.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate presence assets even if presence_meta/current master already exist.",
    )
    args = parser.parse_args()

    profile = load_avatar_asset_profile_from_settings(avatar_key=args.avatar_key)
    adapter = LivePortraitAdapter()
    available, reason = adapter.is_available()
    result = PresenceAssetGenerator(liveportrait_adapter=adapter).ensure_presence_assets(profile, force=args.force)

    print(f"avatar_key={profile.avatar_key}")
    print(f"presence_current={result.current_video_path}")
    print(f"presence_id={result.current_presence_id}")
    print(f"presence_meta={result.meta_path}")
    print("presence_masters=")
    for master_path in result.master_video_paths:
        print(f"  {master_path}")
    print(f"liveportrait_available={available}")
    print(f"liveportrait_detail={reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
