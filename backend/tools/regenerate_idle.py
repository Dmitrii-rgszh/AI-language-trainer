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
    from app.live_avatar.avatar.idle_generator import IdleLoopGenerator
    from app.live_avatar.avatar.liveportrait_adapter import LivePortraitAdapter

    parser = argparse.ArgumentParser(
        description="Generate or regenerate the canonical idle loop for the live avatar.",
    )
    parser.add_argument(
        "--avatar-key",
        default=None,
        help="Optional avatar key override. Defaults to LIVE_AVATAR_DEFAULT_AVATAR_KEY.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate the idle loop even if the canonical file already exists.",
    )
    args = parser.parse_args()

    profile = load_avatar_asset_profile_from_settings(avatar_key=args.avatar_key)
    adapter = LivePortraitAdapter()
    available, reason = adapter.is_available()
    result = IdleLoopGenerator(liveportrait_adapter=adapter).ensure_idle_loop(profile, force=args.force)

    print(f"avatar_key={profile.avatar_key}")
    print(f"source_image={profile.source_image_path}")
    print(f"idle_loop={result.output_video_path}")
    print(f"raw_video={result.raw_video_path}")
    print(f"metadata={result.metadata_path}")
    print(f"renderer={'liveportrait' if result.used_liveportrait else 'synthetic'}")
    print(f"selected_driver_id={result.selected_driver_id}")
    print(f"selected_driver_report={result.selected_driver_report_path}")
    print(f"liveportrait_available={available}")
    print(f"liveportrait_detail={reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
