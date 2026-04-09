from __future__ import annotations

import base64
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import tempfile
import threading
import time
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
import numpy as np

from app.core.config import BACKEND_DIR, settings
from app.core.errors import BadGatewayError, BadRequestError, ServiceUnavailableError
from app.live_avatar.avatar.avatar_profile import load_avatar_asset_profile_from_settings
from app.live_avatar.avatar.idle_generator import IdleLoopGenerator
from app.live_avatar.avatar.presence_generator import PresenceAssetGenerator
from app.services.voice_service.service import VoiceService
from app.services.welcome_tutor_service.presets import (
    build_welcome_tutor_preset_path,
    iter_welcome_tutor_presets,
    resolve_welcome_tutor_preset,
)


@dataclass(frozen=True)
class MuseTalkRuntimeStatus:
    available: bool
    details: str
    mode: str = "musetalk"


@dataclass(frozen=True)
class MuseTalkRuntimeConfig:
    enabled: bool
    python_path: Path
    project_dir: Path
    result_dir: Path
    ffmpeg_path: str
    avatar_image_paths: dict[str, Path]
    version: str
    gpu_id: int
    fps: int
    batch_size: int
    extra_margin: int
    audio_padding_left: int
    audio_padding_right: int
    use_float16: bool
    default_speaker: str

    @property
    def unet_model_path(self) -> Path:
        return self.project_dir / "models" / "musetalkV15" / "unet.pth"

    @property
    def unet_config_path(self) -> Path:
        return self.project_dir / "models" / "musetalkV15" / "musetalk.json"

    @property
    def whisper_dir(self) -> Path:
        return self.project_dir / "models" / "whisper"

    @property
    def inference_script_path(self) -> Path:
        return self.project_dir / "scripts" / "inference.py"

    @property
    def sd_vae_config_path(self) -> Path:
        return self.project_dir / "models" / "sd-vae" / "config.json"

    @property
    def sd_vae_weights_path(self) -> Path:
        return self.project_dir / "models" / "sd-vae" / "diffusion_pytorch_model.bin"

    @property
    def whisper_config_path(self) -> Path:
        return self.whisper_dir / "config.json"

    @property
    def whisper_weights_path(self) -> Path:
        return self.whisper_dir / "pytorch_model.bin"

    @property
    def whisper_preprocessor_config_path(self) -> Path:
        return self.whisper_dir / "preprocessor_config.json"

    @property
    def dwpose_model_path(self) -> Path:
        return self.project_dir / "models" / "dwpose" / "dw-ll_ucoco_384.pth"

    @property
    def syncnet_model_path(self) -> Path:
        return self.project_dir / "models" / "syncnet" / "latentsync_syncnet.pt"

    @property
    def face_parse_model_path(self) -> Path:
        return self.project_dir / "models" / "face-parse-bisent" / "79999_iter.pth"

    @property
    def face_parse_resnet_path(self) -> Path:
        return self.project_dir / "models" / "face-parse-bisent" / "resnet18-5c106cde.pth"


@dataclass(frozen=True)
class CachedMuseTalkStatus:
    checked_at: float
    status: MuseTalkRuntimeStatus


MUSE_TALK_STATUS_CACHE_TTL_SECONDS = 90.0
MUSE_TALK_RENDER_PIPELINE_REVISION = "muxed_audio_v9_presence_01_forced"
WELCOME_TUTOR_AUDIO_SAMPLE_RATE = 24000
WELCOME_TUTOR_AUDIO_CHANNELS = 1
WELCOME_TUTOR_AUDIO_SAMPLE_WIDTH = 2
WELCOME_TUTOR_SILENCE_THRESHOLD = 0.008
WELCOME_TUTOR_SILENCE_PADDING_MS = 80
WELCOME_TUTOR_MIN_CLIP_DURATION_SECONDS = 1.0
WELCOME_TUTOR_CLIP_TO_AUDIO_DURATION_RATIO_FLOOR = 0.7
class WelcomeTutorService:
    def __init__(self, voice_service: VoiceService) -> None:
        self._voice_service = voice_service
        self._cached_status: CachedMuseTalkStatus | None = None
        self._prewarm_started = False
        self._prewarm_lock = threading.Lock()
        self._render_lock_guard = threading.Lock()
        self._render_locks: dict[str, threading.Lock] = {}
        self._runtime_config = MuseTalkRuntimeConfig(
            enabled=settings.musetalk_enabled,
            python_path=Path(settings.musetalk_python_path),
            project_dir=Path(settings.musetalk_project_dir),
            result_dir=Path(settings.musetalk_result_dir),
            ffmpeg_path=settings.musetalk_ffmpeg_path,
            avatar_image_paths={
                "verba_tutor": Path(settings.musetalk_avatar_verba_tutor_image),
            },
            version=settings.musetalk_version,
            gpu_id=settings.musetalk_gpu_id,
            fps=settings.musetalk_fps,
            batch_size=settings.musetalk_batch_size,
            extra_margin=settings.musetalk_extra_margin,
            audio_padding_left=settings.musetalk_audio_padding_left,
            audio_padding_right=settings.musetalk_audio_padding_right,
            use_float16=settings.musetalk_use_float16,
            default_speaker=settings.musetalk_default_speaker,
        )

    def schedule_default_prewarm(self) -> None:
        if not self._runtime_config.enabled:
            return

        with self._prewarm_lock:
            if self._prewarm_started:
                return
            self._prewarm_started = True

        threading.Thread(
            target=self._prewarm_default_clips_safe,
            name="welcome-tutor-prewarm",
            daemon=True,
        ).start()

    def get_status(self) -> MuseTalkRuntimeStatus:
        now = time.monotonic()
        if (
            self._cached_status is not None
            and now - self._cached_status.checked_at < MUSE_TALK_STATUS_CACHE_TTL_SECONDS
        ):
            return self._cached_status.status

        status = self._compute_status()
        self._cached_status = CachedMuseTalkStatus(checked_at=now, status=status)
        return status

    def _compute_status(self) -> MuseTalkRuntimeStatus:
        if not self._runtime_config.enabled:
            return MuseTalkRuntimeStatus(
                available=False,
                details="MuseTalk runtime is disabled in configuration.",
                mode="fallback",
            )

        missing_paths = [
            path
            for path in (
                self._runtime_config.python_path,
                self._runtime_config.project_dir,
                self._runtime_config.inference_script_path,
                self._runtime_config.unet_model_path,
                self._runtime_config.unet_config_path,
                self._runtime_config.whisper_dir,
                self._runtime_config.whisper_config_path,
                self._runtime_config.whisper_weights_path,
                self._runtime_config.whisper_preprocessor_config_path,
                self._runtime_config.sd_vae_config_path,
                self._runtime_config.sd_vae_weights_path,
                self._runtime_config.dwpose_model_path,
                self._runtime_config.syncnet_model_path,
                self._runtime_config.face_parse_model_path,
                self._runtime_config.face_parse_resnet_path,
            )
            if not path.exists()
        ]
        if missing_paths:
            return MuseTalkRuntimeStatus(
                available=False,
                details=(
                    "MuseTalk runtime is configured but incomplete. Missing: "
                    + ", ".join(path.as_posix() for path in missing_paths)
                ),
                mode="fallback",
            )

        ffmpeg_available = (
            shutil.which(self._runtime_config.ffmpeg_path) is not None
            if not Path(self._runtime_config.ffmpeg_path).is_absolute()
            else Path(self._runtime_config.ffmpeg_path).exists()
        )
        if not ffmpeg_available:
            return MuseTalkRuntimeStatus(
                available=False,
                details=f"FFmpeg is not available for MuseTalk: {self._runtime_config.ffmpeg_path}",
                mode="fallback",
            )

        missing_avatars = [
            f"{avatar_key}: {avatar_path.as_posix()}"
            for avatar_key, avatar_path in self._runtime_config.avatar_image_paths.items()
            if not avatar_path.exists()
        ]
        if missing_avatars:
            return MuseTalkRuntimeStatus(
                available=False,
                details="MuseTalk avatar assets are missing. " + ", ".join(missing_avatars),
                mode="fallback",
            )

        runtime_available, runtime_details = self._check_python_runtime()
        if not runtime_available:
            return MuseTalkRuntimeStatus(
                available=False,
                details=runtime_details,
                mode="fallback",
            )

        return MuseTalkRuntimeStatus(
            available=True,
            details=(
                f"MuseTalk {self._runtime_config.version} runtime is configured at "
                f"{self._runtime_config.project_dir.as_posix()} using avatar lip sync. "
                f"{runtime_details}"
            ),
        )

    def render_clip(self, *, text: str, language: str, avatar_key: str = "verba_tutor") -> Path:
        normalized_text = text.strip()
        if not normalized_text:
            raise BadRequestError("Tutor prompt cannot be empty.")

        status = self.get_status()
        if not status.available:
            raise ServiceUnavailableError(status.details)

        avatar_path = self._runtime_config.avatar_image_paths.get(avatar_key)
        if avatar_path is None:
            raise BadRequestError(f"Unknown avatar key: {avatar_key}")
        base_video_path = self._resolve_base_video_path(avatar_key=avatar_key)

        clip_hash = self._build_clip_hash(
            avatar_key=avatar_key,
            text=normalized_text,
            language=language,
        )
        output_dir = self._runtime_config.result_dir / self._runtime_config.version
        output_path = output_dir / f"{clip_hash}.mp4"
        render_lock = self._get_render_lock(clip_hash)
        with render_lock:
            if output_path.exists():
                if self._is_valid_cached_clip(output_path):
                    return output_path
                output_path.unlink(missing_ok=True)

            workspace_root = Path(tempfile.gettempdir()) / "verba-musetalk" / clip_hash
            input_dir = workspace_root / "inputs"
            render_result_dir = workspace_root / "results"
            temp_dir = input_dir
            temp_dir.mkdir(parents=True, exist_ok=True)
            output_dir.mkdir(parents=True, exist_ok=True)

            audio_path = temp_dir / "voice.wav"
            inference_config_path = temp_dir / "inference.yaml"
            avatar_workspace_path = temp_dir / f"{avatar_key}{avatar_path.suffix or '.png'}"
            normalized_output_path = temp_dir / f"normalized_{output_path.name}"

            try:
                audio_bytes = self._voice_service.synthesize(
                    text=normalized_text,
                    language=language,
                    speaker=self._runtime_config.default_speaker,
                    style="warm",
                )
                normalized_audio_bytes = self._trim_wav_silence(audio_bytes)
                shutil.copy2(avatar_path, avatar_workspace_path)
                audio_path.write_bytes(normalized_audio_bytes)
                inference_config_path.write_text(
                    self._build_inference_config(
                        avatar_path=avatar_workspace_path,
                        audio_path=audio_path,
                    ),
                    encoding="utf-8",
                )

                if settings.musetalk_live_enabled:
                    self._render_clip_with_live_sidecar(
                        source_audio_path=audio_path,
                        avatar_key=avatar_key,
                        base_video_path=base_video_path,
                        target_output_path=normalized_output_path,
                    )
                else:
                    command = self._build_command(
                        inference_config_path=inference_config_path,
                        result_dir=render_result_dir,
                        output_name=output_path.name,
                    )
                    process = subprocess.run(
                        command,
                        cwd=self._runtime_config.project_dir,
                        env={
                            **os.environ,
                            "PYTHONIOENCODING": "utf-8",
                            "PYTHONUTF8": "1",
                        },
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                        check=False,
                    )
                    rendered_output_path = render_result_dir / self._runtime_config.version / output_path.name

                    if process.returncode != 0 or not rendered_output_path.exists():
                        diagnostics = "\n".join(
                            part
                            for part in (
                                process.stdout.strip(),
                                process.stderr.strip(),
                            )
                            if part
                        )
                        raise BadGatewayError(
                            "MuseTalk render failed."
                            + (f" Diagnostics:\n{diagnostics[-1200:]}" if diagnostics else "")
                        )

                    self._normalize_muxed_clip(
                        rendered_video_path=rendered_output_path,
                        source_audio_path=audio_path,
                        target_output_path=normalized_output_path,
                    )
                self._ensure_clip_matches_audio(
                    clip_path=normalized_output_path,
                    source_audio_path=audio_path,
                )
                shutil.move(str(normalized_output_path), str(output_path))
                return output_path
            except Exception:
                if settings.musetalk_live_enabled and not normalized_output_path.exists():
                    command = self._build_command(
                        inference_config_path=inference_config_path,
                        result_dir=render_result_dir,
                        output_name=output_path.name,
                    )
                    process = subprocess.run(
                        command,
                        cwd=self._runtime_config.project_dir,
                        env={
                            **os.environ,
                            "PYTHONIOENCODING": "utf-8",
                            "PYTHONUTF8": "1",
                        },
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                        check=False,
                    )
                    rendered_output_path = render_result_dir / self._runtime_config.version / output_path.name
                    if process.returncode != 0 or not rendered_output_path.exists():
                        diagnostics = "\n".join(
                            part
                            for part in (
                                process.stdout.strip(),
                                process.stderr.strip(),
                            )
                            if part
                        )
                        raise BadGatewayError(
                            "MuseTalk render failed."
                            + (f" Diagnostics:\n{diagnostics[-1200:]}" if diagnostics else "")
                        )
                    self._normalize_muxed_clip(
                        rendered_video_path=rendered_output_path,
                        source_audio_path=audio_path,
                        target_output_path=normalized_output_path,
                    )
                    self._ensure_clip_matches_audio(
                        clip_path=normalized_output_path,
                        source_audio_path=audio_path,
                    )
                    shutil.move(str(normalized_output_path), str(output_path))
                    return output_path
                raise
            finally:
                shutil.rmtree(workspace_root, ignore_errors=True)

    def ensure_preset_clip(
        self,
        *,
        locale: str,
        kind: str,
        variant: int = 0,
        avatar_key: str = "verba_tutor",
    ) -> Path:
        preset = resolve_welcome_tutor_preset(locale=locale, kind=kind, variant=variant)
        preset_dir = Path(settings.welcome_preset_video_dir).resolve()
        target_path = build_welcome_tutor_preset_path(preset_dir, preset)
        if self._is_valid_cached_clip(target_path):
            return target_path

        source_clip_path = self.render_clip(
            text=preset.text,
            language=preset.locale,
            avatar_key=avatar_key,
        )
        source_clip_signature = self._fingerprint_file(source_clip_path.as_posix())
        metadata_path = self._build_preset_metadata_path(target_path)
        existing_metadata = self._read_preset_metadata(metadata_path)
        if (
            target_path.exists()
            and self._is_valid_cached_clip(target_path)
            and existing_metadata.get("source_clip_signature") == source_clip_signature
        ):
            return target_path

        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_clip_path, target_path)
        metadata_path.write_text(
            json.dumps(
                {
                    "locale": preset.locale,
                    "kind": preset.kind,
                    "variant": preset.variant,
                    "source_clip_path": source_clip_path.as_posix(),
                    "source_clip_signature": source_clip_signature,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        return target_path

    def _prewarm_default_clips_safe(self) -> None:
        try:
            status = self.get_status()
            if not status.available:
                return

            for preset in iter_welcome_tutor_presets():
                self.ensure_preset_clip(
                    locale=preset.locale,
                    kind=preset.kind,
                    variant=preset.variant,
                    avatar_key="verba_tutor",
                )
        except Exception:
            return

    def _get_render_lock(self, clip_hash: str) -> threading.Lock:
        with self._render_lock_guard:
            existing_lock = self._render_locks.get(clip_hash)
            if existing_lock is not None:
                return existing_lock
            next_lock = threading.Lock()
            self._render_locks[clip_hash] = next_lock
            return next_lock

    @staticmethod
    def _build_preset_metadata_path(preset_path: Path) -> Path:
        return preset_path.with_suffix(f"{preset_path.suffix}.meta.json")

    @staticmethod
    def _read_preset_metadata(metadata_path: Path) -> dict[str, Any]:
        if not metadata_path.exists():
            return {}

        try:
            return json.loads(metadata_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}

    def _build_command(
        self,
        *,
        inference_config_path: Path,
        result_dir: Path,
        output_name: str,
    ) -> list[str]:
        command = [
            str(self._runtime_config.python_path),
            "-m",
            "scripts.inference",
            "--inference_config",
            str(inference_config_path),
            "--result_dir",
            str(result_dir),
            "--ffmpeg_path",
            self._runtime_config.ffmpeg_path,
            "--unet_model_path",
            str(self._runtime_config.unet_model_path),
            "--unet_config",
            str(self._runtime_config.unet_config_path),
            "--whisper_dir",
            str(self._runtime_config.whisper_dir),
            "--version",
            self._runtime_config.version,
            "--fps",
            str(self._runtime_config.fps),
            "--batch_size",
            str(self._runtime_config.batch_size),
            "--gpu_id",
            str(self._runtime_config.gpu_id),
            "--extra_margin",
            str(self._runtime_config.extra_margin),
            "--audio_padding_length_left",
            str(self._runtime_config.audio_padding_left),
            "--audio_padding_length_right",
            str(self._runtime_config.audio_padding_right),
            "--saved_coord",
            "--use_saved_coord",
            "--output_vid_name",
            output_name,
        ]
        if self._runtime_config.use_float16:
            command.append("--use_float16")
        return command

    def _render_clip_with_live_sidecar(
        self,
        *,
        source_audio_path: Path,
        avatar_key: str,
        base_video_path: Path,
        target_output_path: Path,
    ) -> None:
        avatar_path = self._runtime_config.avatar_image_paths[avatar_key]
        base_url = settings.musetalk_live_base_url.rstrip("/")
        avatar_runtime_id = self._build_live_sidecar_avatar_id(
            avatar_key=avatar_key,
            base_video_path=base_video_path,
        )
        frames_dir = target_output_path.parent / "live_frames"
        frames_dir.mkdir(parents=True, exist_ok=True)
        frame_index = 0
        timeout = httpx.Timeout(connect=30.0, read=600.0, write=60.0, pool=30.0)

        with httpx.Client(timeout=timeout) as client:
            prepare_response = client.post(
                f"{base_url}/prepare-avatar",
                json={
                    "avatar_id": avatar_runtime_id,
                    "image_path": avatar_path.as_posix(),
                    "base_video_path": base_video_path.as_posix(),
                },
            )
            prepare_response.raise_for_status()

            with client.stream(
                "POST",
                f"{base_url}/render-stream",
                json={
                    "avatar_id": avatar_runtime_id,
                    "audio_path": source_audio_path.as_posix(),
                    "fps": self._runtime_config.fps,
                },
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if not line:
                        continue
                    payload = json.loads(line)
                    event_type = payload.get("type")
                    if event_type in {"meta", "done"}:
                        continue
                    if event_type == "error":
                        raise RuntimeError(payload.get("detail", "MuseTalk live render failed."))
                    if event_type != "frame":
                        continue

                    image_bytes = base64.b64decode(payload["data"])
                    frame_path = frames_dir / f"frame_{frame_index:06d}.jpg"
                    frame_path.write_bytes(image_bytes)
                    frame_index += 1

        if frame_index == 0:
            raise RuntimeError("MuseTalk live render did not return any frames.")

        self._encode_frames_to_clip(
            frames_dir=frames_dir,
            source_audio_path=source_audio_path,
            target_output_path=target_output_path,
        )

    def _encode_frames_to_clip(
        self,
        *,
        frames_dir: Path,
        source_audio_path: Path,
        target_output_path: Path,
    ) -> None:
        process = subprocess.run(
            [
                self._runtime_config.ffmpeg_path,
                "-y",
                "-v",
                "warning",
                "-framerate",
                str(self._runtime_config.fps),
                "-i",
                str(frames_dir / "frame_%06d.jpg"),
                "-i",
                str(source_audio_path),
                "-map",
                "0:v:0",
                "-map",
                "1:a:0",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-preset",
                "veryfast",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-shortest",
                "-movflags",
                "+faststart",
                str(target_output_path),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if process.returncode != 0 or not target_output_path.exists():
            diagnostics = "\n".join(
                part
                for part in (
                    process.stdout.strip(),
                    process.stderr.strip(),
                )
                if part
            )
            raise BadGatewayError(
                "MuseTalk live post-processing failed."
                + (f" Diagnostics:\n{diagnostics[-1200:]}" if diagnostics else "")
            )

    @staticmethod
    def _build_inference_config(*, avatar_path: Path, audio_path: Path) -> str:
        return (
            "task_0:\n"
            f"  video_path: {json.dumps(avatar_path.as_posix())}\n"
            f"  audio_path: {json.dumps(audio_path.as_posix())}\n"
        )

    def _normalize_muxed_clip(
        self,
        *,
        rendered_video_path: Path,
        source_audio_path: Path,
        target_output_path: Path,
    ) -> None:
        process = subprocess.run(
            [
                self._runtime_config.ffmpeg_path,
                "-y",
                "-v",
                "warning",
                "-i",
                str(rendered_video_path),
                "-i",
                str(source_audio_path),
                "-map",
                "0:v:0",
                "-map",
                "1:a:0",
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-af",
                "apad",
                "-shortest",
                "-movflags",
                "+faststart",
                str(target_output_path),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if process.returncode != 0 or not target_output_path.exists():
            diagnostics = "\n".join(
                part
                for part in (
                    process.stdout.strip(),
                    process.stderr.strip(),
                )
                if part
            )
            raise BadGatewayError(
                "MuseTalk post-processing failed."
                + (f" Diagnostics:\n{diagnostics[-1200:]}" if diagnostics else "")
            )

    def _is_valid_cached_clip(self, clip_path: Path) -> bool:
        duration_seconds = self._probe_media_duration_seconds(clip_path)
        return duration_seconds >= WELCOME_TUTOR_MIN_CLIP_DURATION_SECONDS

    def _ensure_clip_matches_audio(self, *, clip_path: Path, source_audio_path: Path) -> None:
        clip_duration_seconds = self._probe_media_duration_seconds(clip_path)
        audio_duration_seconds = self._probe_wav_duration_seconds(source_audio_path)
        minimum_expected_duration = max(
            WELCOME_TUTOR_MIN_CLIP_DURATION_SECONDS,
            audio_duration_seconds * WELCOME_TUTOR_CLIP_TO_AUDIO_DURATION_RATIO_FLOOR,
        )
        if clip_duration_seconds < minimum_expected_duration:
            raise BadGatewayError(
                "MuseTalk produced an unexpectedly short welcome clip. "
                f"Expected at least {minimum_expected_duration:.2f}s from {audio_duration_seconds:.2f}s audio, "
                f"but got {clip_duration_seconds:.2f}s."
            )

    def _probe_media_duration_seconds(self, media_path: Path) -> float:
        ffprobe_path = self._resolve_ffprobe_path()
        process = subprocess.run(
            [
                ffprobe_path,
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(media_path),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if process.returncode != 0:
            return 0.0

        try:
            return float(process.stdout.strip())
        except ValueError:
            return 0.0

    def _resolve_ffprobe_path(self) -> str:
        ffmpeg_path = Path(self._runtime_config.ffmpeg_path)
        if not ffmpeg_path.is_absolute():
            return "ffprobe"

        ffprobe_name = ffmpeg_path.name.replace("ffmpeg", "ffprobe")
        return str(ffmpeg_path.with_name(ffprobe_name))

    @staticmethod
    def _probe_wav_duration_seconds(audio_path: Path) -> float:
        with wave.open(str(audio_path), "rb") as wav_file:
            frame_rate = wav_file.getframerate()
            frame_count = wav_file.getnframes()
        if frame_rate <= 0:
            return 0.0
        return frame_count / frame_rate

    def _build_clip_hash(self, *, avatar_key: str, text: str, language: str) -> str:
        base_video_path = self._resolve_base_video_path(avatar_key=avatar_key)
        payload = "|".join(
                [
                    avatar_key,
                    language,
                    text,
                    self._runtime_config.version,
                    self._runtime_config.default_speaker,
                    self._build_tts_cache_signature(),
                    self._fingerprint_file(base_video_path.as_posix()),
                    MUSE_TALK_RENDER_PIPELINE_REVISION,
                ]
            )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:20]

    def _resolve_base_video_path(self, *, avatar_key: str) -> Path:
        canonical_welcome_presence_path = (BACKEND_DIR / "generated" / "live_avatar" / "presence_01.mp4").resolve()
        if avatar_key == "verba_tutor" and canonical_welcome_presence_path.exists():
            return canonical_welcome_presence_path

        configured_presence_path = Path(settings.welcome_presence_video_path).resolve()
        if avatar_key == "verba_tutor" and configured_presence_path.exists():
            return configured_presence_path

        avatar_profile = load_avatar_asset_profile_from_settings(avatar_key=avatar_key)
        if settings.live_avatar_presence_enabled:
            presence_result = PresenceAssetGenerator().ensure_presence_assets(avatar_profile)
            return presence_result.current_video_path

        IdleLoopGenerator().ensure_idle_loop(avatar_profile)
        return avatar_profile.idle_loop_path

    def _build_tts_cache_signature(self) -> str:
        provider_key = settings.tts_provider.strip().lower() or "unknown"
        parts = [f"provider={provider_key}"]

        if provider_key == "qwen3_tts":
            parts.extend(
                [
                    f"model={settings.qwen_tts_model_id}",
                    self._fingerprint_file(settings.qwen_tts_reference_wav or settings.xtts_reference_wav),
                    self._fingerprint_text_source(),
                ]
            )
        elif provider_key == "xtts":
            parts.extend(
                [
                    f"model={settings.xtts_model_name}",
                    f"default_speaker={settings.xtts_default_speaker}",
                    self._fingerprint_file(settings.xtts_reference_wav),
                ]
            )

        return "|".join(part for part in parts if part)

    def _build_live_sidecar_avatar_id(self, *, avatar_key: str, base_video_path: Path) -> str:
        fingerprint = self._fingerprint_file(base_video_path.as_posix())
        digest = hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()[:12]
        return f"{avatar_key}-welcome-{digest}"

    @staticmethod
    def _fingerprint_file(file_path: str) -> str:
        normalized_path = (file_path or "").strip()
        if not normalized_path:
            return "file=none"

        path = Path(normalized_path)
        if not path.exists():
            return f"file={path.as_posix()}|missing"

        stat = path.stat()
        return f"file={path.as_posix()}|size={stat.st_size}|mtime={stat.st_mtime_ns}"

    def _fingerprint_text_source(self) -> str:
        inline_text = settings.qwen_tts_reference_text.strip()
        if inline_text:
            return self._fingerprint_text(inline_text, prefix="inline")

        text_file = settings.qwen_tts_reference_text_file.strip()
        if text_file:
            path = Path(text_file)
            if path.exists():
                return self._fingerprint_text(path.read_text(encoding="utf-8", errors="ignore"), prefix=path.as_posix())
            return f"text_file={path.as_posix()}|missing"

        return "text=auto"

    @staticmethod
    def _fingerprint_text(text: str, *, prefix: str) -> str:
        normalized = re.sub(r"\s+", " ", text).strip()
        digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]
        return f"text_source={prefix}|sha={digest}"

    def _trim_wav_silence(self, audio_bytes: bytes) -> bytes:
        with wave.open(io.BytesIO(audio_bytes), "rb") as wav_file:
            sample_rate = wav_file.getframerate()
            sample_width = wav_file.getsampwidth()
            channels = wav_file.getnchannels()
            frames = wav_file.readframes(wav_file.getnframes())

        if sample_width != WELCOME_TUTOR_AUDIO_SAMPLE_WIDTH or channels != WELCOME_TUTOR_AUDIO_CHANNELS:
            return audio_bytes

        pcm = np.frombuffer(frames, dtype=np.int16)
        if pcm.size == 0:
            return audio_bytes

        normalized = np.abs(pcm.astype(np.float32) / 32768.0)
        non_silent_indices = np.where(normalized > WELCOME_TUTOR_SILENCE_THRESHOLD)[0]
        if non_silent_indices.size == 0:
            return audio_bytes

        padding_samples = int(sample_rate * (WELCOME_TUTOR_SILENCE_PADDING_MS / 1000))
        start_index = max(0, int(non_silent_indices[0]) - padding_samples)
        end_index = min(pcm.size, int(non_silent_indices[-1]) + padding_samples)
        trimmed_pcm = pcm[start_index:end_index]

        output_buffer = io.BytesIO()
        with wave.open(output_buffer, "wb") as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(sample_width)
            wav_file.setframerate(sample_rate or WELCOME_TUTOR_AUDIO_SAMPLE_RATE)
            wav_file.writeframes(trimmed_pcm.tobytes())

        return output_buffer.getvalue()

    def _check_python_runtime(self) -> tuple[bool, str]:
        process = subprocess.run(
            [
                str(self._runtime_config.python_path),
                "-c",
                (
                    "import json, torch, diffusers, transformers, mmengine, mmcv, mmdet, mmpose; "
                    "print(json.dumps({"
                    "'torch': getattr(torch, '__version__', 'unknown'), "
                    "'cuda': bool(torch.cuda.is_available()), "
                    "'device_count': int(torch.cuda.device_count())"
                    "}))"
                ),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if process.returncode != 0:
            diagnostics = process.stderr.strip() or process.stdout.strip() or "unknown error"
            return False, f"MuseTalk Python runtime is not ready: {diagnostics[-600:]}"

        try:
            payload = json.loads(process.stdout.strip().splitlines()[-1])
        except (json.JSONDecodeError, IndexError):
            return False, "MuseTalk Python runtime returned an unreadable preflight response."

        if not payload.get("cuda"):
            return (
                False,
                "MuseTalk Python runtime is installed, but CUDA is unavailable. "
                "Real-time lip sync requires a CUDA-enabled torch build.",
            )

        device_count = payload.get("device_count", 0)
        torch_version = payload.get("torch", "unknown")
        return True, f"CUDA runtime ready via torch {torch_version} with {device_count} GPU(s)."
