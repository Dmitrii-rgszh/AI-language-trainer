from __future__ import annotations

import ctypes
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from app.core.config import settings


_REQUIRED_WEIGHT_RELATIVE_PATHS = (
    Path("pretrained_weights/liveportrait/base_models/appearance_feature_extractor.pth"),
    Path("pretrained_weights/liveportrait/base_models/motion_extractor.pth"),
    Path("pretrained_weights/liveportrait/base_models/spade_generator.pth"),
    Path("pretrained_weights/liveportrait/base_models/warping_module.pth"),
    Path("pretrained_weights/liveportrait/landmark.onnx"),
    Path("pretrained_weights/liveportrait/retargeting_models/stitching_retargeting_module.pth"),
    Path("pretrained_weights/insightface/models/buffalo_l/2d106det.onnx"),
    Path("pretrained_weights/insightface/models/buffalo_l/det_10g.onnx"),
)
_DEFAULT_DRIVING_CANDIDATES = (
    Path("assets/examples/driving/d9.mp4"),
    Path("assets/examples/driving/d0.mp4"),
)


@dataclass(frozen=True)
class LivePortraitRenderRequest:
    source_image_path: Path
    driving_video_path: Path
    output_video_path: Path


class LivePortraitAdapter:
    def __init__(self) -> None:
        self._enabled = settings.live_avatar_liveportrait_enabled
        self._python_path = Path(settings.live_avatar_liveportrait_python_path)
        self._project_dir = Path(settings.live_avatar_liveportrait_project_dir)
        self._command_template = settings.live_avatar_liveportrait_command.strip()
        self._inference_entrypoint = self._project_dir / "inference.py"

    def is_available(self) -> tuple[bool, str]:
        if not self._enabled:
            return False, "LivePortrait is disabled in configuration."
        if not self._python_path.exists():
            return False, f"LivePortrait python was not found: {self._python_path}"
        if not self._project_dir.exists():
            return False, f"LivePortrait project dir was not found: {self._project_dir}"
        if not self._inference_entrypoint.exists():
            return False, f"LivePortrait inference entrypoint was not found: {self._inference_entrypoint}"
        missing_weights = self._get_missing_required_weights()
        if missing_weights:
            preview = ", ".join(path.as_posix() for path in missing_weights[:2])
            if len(missing_weights) > 2:
                preview += ", ..."
            return False, f"LivePortrait weights are missing: {preview}"
        return True, "LivePortrait adapter is configured."

    def resolve_default_driving_video(self) -> Path | None:
        configured_path = Path(settings.live_avatar_idle_driving_video).resolve()
        if configured_path.exists():
            return configured_path

        for relative_path in _DEFAULT_DRIVING_CANDIDATES:
            candidate = (self._project_dir / relative_path).resolve()
            if candidate.exists():
                return candidate
        return None

    def render_idle_raw(self, request: LivePortraitRenderRequest) -> Path:
        available, reason = self.is_available()
        if not available:
            raise RuntimeError(reason)

        request.output_video_path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="liveportrait-idle-") as workspace_raw:
            workspace_dir = Path(workspace_raw)
            source_copy = workspace_dir / f"source{request.source_image_path.suffix or '.png'}"
            driving_copy = workspace_dir / f"driving{request.driving_video_path.suffix or '.mp4'}"
            output_dir = workspace_dir / "animations"
            output_dir.mkdir(parents=True, exist_ok=True)

            shutil.copy2(request.source_image_path, source_copy)
            shutil.copy2(request.driving_video_path, driving_copy)

            completed = self._run_liveportrait(
                source_path=source_copy,
                driving_path=driving_copy,
                output_dir=output_dir,
                expected_output_path=request.output_video_path,
            )
            if completed.returncode != 0:
                raise RuntimeError(
                    "LivePortrait idle render failed. "
                    f"stdout: {completed.stdout.strip()} stderr: {completed.stderr.strip()}"
                )

            rendered_output = self._resolve_rendered_output(
                output_dir=output_dir,
                source_path=source_copy,
                driving_path=driving_copy,
            )
            if rendered_output is None:
                raise RuntimeError(
                    "LivePortrait command finished without creating the expected output video. "
                    f"Output dir: {output_dir}"
                )
            shutil.copy2(rendered_output, request.output_video_path)

        if not request.output_video_path.exists() or request.output_video_path.stat().st_size <= 0:
            raise RuntimeError(
                "LivePortrait command finished without creating a usable output video: "
                f"{request.output_video_path}"
            )
        return request.output_video_path

    def _run_liveportrait(
        self,
        *,
        source_path: Path,
        driving_path: Path,
        output_dir: Path,
        expected_output_path: Path,
    ) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment.setdefault("PYTHONUTF8", "1")
        environment.setdefault("PYTHONIOENCODING", "utf-8")
        if self._command_template:
            command = self._command_template.format(
                python=self._to_process_path(self._python_path),
                project_dir=self._to_process_path(self._project_dir),
                source=self._to_process_path(source_path),
                driving=self._to_process_path(driving_path),
                output=self._to_process_path(expected_output_path),
                output_dir=self._to_process_path(output_dir),
            )
            return subprocess.run(
                command,
                cwd=self._to_process_path(self._project_dir),
                shell=True,
                capture_output=True,
                text=True,
                env=environment,
                check=False,
            )

        command = [
            self._to_process_path(self._python_path),
            "inference.py",
            "-s",
            self._to_process_path(source_path),
            "-d",
            self._to_process_path(driving_path),
            "-o",
            self._to_process_path(output_dir),
            "--flag_crop_driving_video",
            "--driving_option",
            "expression-friendly",
            "--driving_multiplier",
            "1.0",
        ]
        return subprocess.run(
            command,
            cwd=self._to_process_path(self._project_dir),
            capture_output=True,
            text=True,
            env=environment,
            check=False,
        )

    def _resolve_rendered_output(
        self,
        *,
        output_dir: Path,
        source_path: Path,
        driving_path: Path,
    ) -> Path | None:
        direct_candidate = output_dir / f"{source_path.stem}--{driving_path.stem}.mp4"
        if direct_candidate.exists():
            return direct_candidate

        preferred_candidates = sorted(
            candidate
            for candidate in output_dir.glob("*.mp4")
            if "_concat" not in candidate.stem
        )
        if preferred_candidates:
            return preferred_candidates[0]

        any_candidates = sorted(output_dir.glob("*.mp4"))
        if any_candidates:
            return any_candidates[0]
        return None

    def _get_missing_required_weights(self) -> list[Path]:
        missing: list[Path] = []
        for relative_path in _REQUIRED_WEIGHT_RELATIVE_PATHS:
            candidate = self._project_dir / relative_path
            if not candidate.exists():
                missing.append(relative_path)
        return missing

    def _to_process_path(self, path: Path) -> str:
        resolved = path.resolve()
        short_path = _get_windows_short_path(resolved)
        if short_path:
            return short_path
        return resolved.as_posix()


def _get_windows_short_path(path: Path) -> str | None:
    if os.name != "nt":
        return None
    if not path.exists():
        return None

    buffer = ctypes.create_unicode_buffer(32768)
    result = ctypes.windll.kernel32.GetShortPathNameW(str(path), buffer, len(buffer))
    if result <= 0:
        return None
    return buffer.value
