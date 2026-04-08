from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if BACKEND_DIR.as_posix() not in sys.path:
    sys.path.insert(0, BACKEND_DIR.as_posix())

from app.live_avatar.avatar.motion_metrics import analyze_video


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect live-avatar idle/speaking video motion metrics.")
    parser.add_argument("video_path", type=Path, help="Path to the video file to inspect.")
    args = parser.parse_args()

    metrics = analyze_video(args.video_path.resolve())
    print(json.dumps(metrics.to_dict(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
