from __future__ import annotations

import base64
import json
import os
import sys
import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import torch
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from PIL import Image
from pydantic import BaseModel, Field
from transformers import WhisperModel

PROJECT_DIR = Path(
    os.getenv(
        "MUSE_TALK_PROJECT_DIR",
        str((Path(__file__).resolve().parents[1] / ".runtime" / "MuseTalk").as_posix()),
    )
).resolve()
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
os.chdir(PROJECT_DIR)
if PROJECT_DIR.as_posix() not in sys.path:
    sys.path.insert(0, PROJECT_DIR.as_posix())

from musetalk.utils.audio_processor import AudioProcessor
from musetalk.utils.blending import get_image_blending, get_image_prepare_material
from musetalk.utils.face_parsing import FaceParsing
from musetalk.utils.preprocessing import get_landmark_and_bbox
from musetalk.utils.utils import datagen, load_all_model

app = FastAPI(title="MuseTalk Live Sidecar", version="0.1.0")


class PrepareAvatarRequest(BaseModel):
    avatar_id: str = Field(min_length=1, max_length=80)
    image_path: str | None = Field(default=None, min_length=1, max_length=1200)
    base_video_path: str | None = Field(default=None, min_length=1, max_length=1200)


class RenderStreamRequest(BaseModel):
    avatar_id: str = Field(min_length=1, max_length=80)
    audio_path: str = Field(min_length=1, max_length=1200)
    fps: int = Field(default=25, ge=1, le=60)
    start_frame_index: int = Field(default=0, ge=0)


@dataclass
class PreparedAvatar:
    avatar_id: str
    source_signature: str
    frame_list_cycle: list[np.ndarray]
    coord_list_cycle: list[list[int]]
    input_latent_list_cycle: list[torch.Tensor]
    mask_list_cycle: list[np.ndarray]
    mask_coords_list_cycle: list[list[int]]


class MuseTalkLiveRuntime:
    def __init__(self) -> None:
        self._version = os.getenv("MUSE_TALK_VERSION", "v15").strip() or "v15"
        self._gpu_id = int(os.getenv("MUSE_TALK_GPU_ID", "0"))
        self._batch_size = int(os.getenv("MUSE_TALK_BATCH_SIZE", "8"))
        self._fps = int(os.getenv("MUSE_TALK_FPS", "25"))
        self._extra_margin = int(os.getenv("MUSE_TALK_EXTRA_MARGIN", "10"))
        self._audio_padding_left = int(os.getenv("MUSE_TALK_AUDIO_PADDING_LEFT", "2"))
        self._audio_padding_right = int(os.getenv("MUSE_TALK_AUDIO_PADDING_RIGHT", "2"))
        self._unet_model_path = Path(
            os.getenv(
                "MUSE_TALK_UNET_MODEL_PATH",
                str((PROJECT_DIR / "models" / "musetalkV15" / "unet.pth").as_posix()),
            )
        )
        self._unet_config_path = Path(
            os.getenv(
                "MUSE_TALK_UNET_CONFIG",
                str((PROJECT_DIR / "models" / "musetalkV15" / "musetalk.json").as_posix()),
            )
        )
        self._whisper_dir = Path(
            os.getenv(
                "MUSE_TALK_WHISPER_DIR",
                str((PROJECT_DIR / "models" / "whisper").as_posix()),
            )
        )
        self._device = torch.device(f"cuda:{self._gpu_id}" if torch.cuda.is_available() else "cpu")
        self._model_lock = threading.Lock()
        self._avatar_lock = threading.Lock()
        self._avatars: dict[str, PreparedAvatar] = {}
        self._vae: Any | None = None
        self._unet: Any | None = None
        self._pe: Any | None = None
        self._timesteps: torch.Tensor | None = None
        self._audio_processor: AudioProcessor | None = None
        self._whisper: WhisperModel | None = None
        self._fp: FaceParsing | None = None
        self._weight_dtype: Any | None = None

    def health(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "project_dir": PROJECT_DIR.as_posix(),
            "version": self._version,
            "device": str(self._device),
            "model_loaded": self._vae is not None,
            "prepared_avatars": sorted(self._avatars),
        }

    def prepare_avatar(
        self,
        avatar_id: str,
        image_path: str | None,
        base_video_path: str | None = None,
    ) -> None:
        source_signature = self._build_source_signature(
            image_path=image_path,
            base_video_path=base_video_path,
        )
        if avatar_id in self._avatars and self._avatars[avatar_id].source_signature == source_signature:
            return

        self._ensure_runtime()
        with self._avatar_lock:
            if avatar_id in self._avatars and self._avatars[avatar_id].source_signature == source_signature:
                return
            self._avatars[avatar_id] = self._build_avatar(
                avatar_id,
                image_path=image_path,
                base_video_path=base_video_path,
            )

    def render_stream(self, avatar_id: str, audio_path: str, fps: int, start_frame_index: int = 0):
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio path does not exist: {audio_path}")
        self._ensure_runtime()
        if avatar_id not in self._avatars:
            default_image = os.getenv("MUSE_TALK_AVATAR_VERBA_TUTOR_IMAGE", "")
            default_base_video = os.getenv("LIVE_AVATAR_IDLE_LOOP_PATH", "").strip() or None
            if not default_image:
                raise RuntimeError(f"Avatar '{avatar_id}' is not prepared.")
            self.prepare_avatar(avatar_id, default_image, default_base_video)

        avatar = self._avatars[avatar_id]
        runtime_fps = fps or self._fps

        def event_stream():
            yield self._json_line(
                {
                    "type": "meta",
                    "avatarId": avatar_id,
                    "fps": runtime_fps,
                }
            )
            try:
                for frame_index, frame in self._iter_avatar_frames(
                    avatar,
                    audio_path,
                    runtime_fps,
                    start_frame_index=max(0, start_frame_index),
                ):
                    ok, encoded = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 88])
                    if not ok:
                        continue
                    yield self._json_line(
                        {
                            "type": "frame",
                            "index": frame_index,
                            "data": base64.b64encode(encoded.tobytes()).decode("ascii"),
                        }
                    )
                yield self._json_line({"type": "done"})
            except Exception as exc:
                yield self._json_line({"type": "error", "detail": str(exc)})

        return event_stream()

    def _ensure_runtime(self) -> None:
        if self._vae is not None:
            return

        with self._model_lock:
            if self._vae is not None:
                return

            vae, unet, pe = load_all_model(
                unet_model_path=str(self._unet_model_path),
                vae_type="sd-vae",
                unet_config=str(self._unet_config_path),
                device=self._device,
            )
            pe = pe.half().to(self._device)
            vae.vae = vae.vae.half().to(self._device)
            unet.model = unet.model.half().to(self._device)

            audio_processor = AudioProcessor(feature_extractor_path=str(self._whisper_dir))
            whisper = WhisperModel.from_pretrained(str(self._whisper_dir))
            whisper = whisper.to(device=self._device, dtype=unet.model.dtype).eval()
            whisper.requires_grad_(False)
            fp = FaceParsing(left_cheek_width=90, right_cheek_width=90)

            self._vae = vae
            self._unet = unet
            self._pe = pe
            self._timesteps = torch.tensor([0], device=self._device)
            self._audio_processor = audio_processor
            self._whisper = whisper
            self._fp = fp
            self._weight_dtype = unet.model.dtype

    def _build_avatar(
        self,
        avatar_id: str,
        *,
        image_path: str | None,
        base_video_path: str | None = None,
    ) -> PreparedAvatar:
        if base_video_path:
            input_img_list = self._extract_safe_video_frames(avatar_id, base_video_path)
            source_signature = self._build_source_signature(
                image_path=image_path,
                base_video_path=base_video_path,
            )
        elif image_path:
            safe_image_path = self._ensure_safe_image_path(avatar_id, image_path)
            input_img_list = [safe_image_path]
            source_signature = self._build_source_signature(
                image_path=image_path,
                base_video_path=None,
            )
        else:
            raise RuntimeError(f"Avatar '{avatar_id}' requires either an image path or a base video path.")

        coord_list, frame_list = get_landmark_and_bbox(input_img_list, 0)
        input_latent_list: list[torch.Tensor] = []
        sanitized_coords: list[list[int]] = []

        for bbox, frame in zip(coord_list, frame_list):
            x1, y1, x2, y2 = [int(value) for value in bbox]
            if x1 == x2 or y1 == y2:
                raise RuntimeError(f"MuseTalk could not find a valid face crop for avatar '{avatar_id}'.")
            if self._version == "v15":
                y2 = min(y2 + self._extra_margin, frame.shape[0])
            sanitized_coords.append([x1, y1, x2, y2])
            crop_frame = frame[y1:y2, x1:x2]
            resized_crop_frame = cv2.resize(crop_frame, (256, 256), interpolation=cv2.INTER_LANCZOS4)
            input_latent_list.append(self._vae.get_latents_for_unet(resized_crop_frame))

        use_loop_source = bool(base_video_path)
        frame_list_cycle = frame_list if use_loop_source else frame_list + frame_list[::-1]
        coord_list_cycle = sanitized_coords if use_loop_source else sanitized_coords + sanitized_coords[::-1]
        input_latent_list_cycle = input_latent_list if use_loop_source else input_latent_list + input_latent_list[::-1]
        mask_list_cycle: list[np.ndarray] = []
        mask_coords_list_cycle: list[list[int]] = []

        for frame, bbox in zip(frame_list_cycle, coord_list_cycle):
            mask, crop_box = get_image_prepare_material(
                frame,
                bbox,
                fp=self._fp,
                mode="jaw",
            )
            mask_list_cycle.append(mask)
            mask_coords_list_cycle.append(crop_box)

        return PreparedAvatar(
            avatar_id=avatar_id,
            source_signature=source_signature,
            frame_list_cycle=frame_list_cycle,
            coord_list_cycle=coord_list_cycle,
            input_latent_list_cycle=input_latent_list_cycle,
            mask_list_cycle=mask_list_cycle,
            mask_coords_list_cycle=mask_coords_list_cycle,
        )

    def _ensure_safe_image_path(self, avatar_id: str, image_path: str) -> str:
        safe_dir = Path(tempfile.gettempdir()) / "musetalk-live-avatar-inputs"
        safe_dir.mkdir(parents=True, exist_ok=True)
        safe_path = safe_dir / f"{avatar_id}.png"
        with Image.open(image_path) as image:
            image.convert("RGB").save(safe_path)
        return safe_path.as_posix()

    def _extract_safe_video_frames(self, avatar_id: str, video_path: str) -> list[str]:
        capture = cv2.VideoCapture(video_path)
        if not capture.isOpened():
            raise RuntimeError(f"Could not open avatar base video: {video_path}")

        safe_dir = Path(tempfile.gettempdir()) / "musetalk-live-avatar-inputs" / avatar_id / "base-video"
        if safe_dir.exists():
            for existing_path in safe_dir.glob("frame_*.png"):
                existing_path.unlink(missing_ok=True)
        safe_dir.mkdir(parents=True, exist_ok=True)

        frame_paths: list[str] = []
        frame_index = 0
        try:
            while True:
                success, frame = capture.read()
                if not success:
                    break
                frame_path = safe_dir / f"frame_{frame_index:06d}.png"
                if not cv2.imwrite(frame_path.as_posix(), frame):
                    raise RuntimeError(f"Could not persist avatar base frame: {frame_path}")
                frame_paths.append(frame_path.as_posix())
                frame_index += 1
        finally:
            capture.release()

        if not frame_paths:
            raise RuntimeError(f"Avatar base video did not yield any frames: {video_path}")
        return frame_paths

    @staticmethod
    def _build_source_signature(*, image_path: str | None, base_video_path: str | None) -> str:
        normalized_image = (image_path or "").strip()
        normalized_video = (base_video_path or "").strip()
        if normalized_video:
            return f"video:{normalized_video}"
        if normalized_image:
            return f"image:{normalized_image}"
        return "unknown"

    def _iter_avatar_frames(
        self,
        avatar: PreparedAvatar,
        audio_path: str,
        fps: int,
        *,
        start_frame_index: int = 0,
    ):
        whisper_input_features, librosa_length = self._audio_processor.get_audio_feature(
            audio_path,
            weight_dtype=self._weight_dtype,
        )
        whisper_chunks = self._audio_processor.get_whisper_chunk(
            whisper_input_features,
            self._device,
            self._weight_dtype,
            self._whisper,
            librosa_length,
            fps=fps,
            audio_padding_length_left=self._audio_padding_left,
            audio_padding_length_right=self._audio_padding_right,
        )

        generator = datagen(
            whisper_chunks,
            avatar.input_latent_list_cycle,
            self._batch_size,
        )

        frame_index = 0
        for whisper_batch, latent_batch in generator:
            audio_feature_batch = self._pe(whisper_batch.to(self._device))
            latent_batch = latent_batch.to(device=self._device, dtype=self._unet.model.dtype)
            pred_latents = self._unet.model(
                latent_batch,
                self._timesteps,
                encoder_hidden_states=audio_feature_batch,
            ).sample
            pred_latents = pred_latents.to(device=self._device, dtype=self._vae.vae.dtype)
            recon = self._vae.decode_latents(pred_latents)
            for res_frame in recon:
                cycle_index = start_frame_index + frame_index
                yield frame_index, self._blend_frame(avatar, cycle_index, res_frame)
                frame_index += 1

    def _blend_frame(self, avatar: PreparedAvatar, frame_index: int, res_frame: np.ndarray) -> np.ndarray:
        bbox = avatar.coord_list_cycle[frame_index % len(avatar.coord_list_cycle)]
        ori_frame = avatar.frame_list_cycle[frame_index % len(avatar.frame_list_cycle)].copy()
        x1, y1, x2, y2 = bbox
        resized = cv2.resize(res_frame.astype(np.uint8), (x2 - x1, y2 - y1))
        mask = avatar.mask_list_cycle[frame_index % len(avatar.mask_list_cycle)]
        mask_crop_box = avatar.mask_coords_list_cycle[frame_index % len(avatar.mask_coords_list_cycle)]
        return get_image_blending(ori_frame, resized, bbox, mask, mask_crop_box)

    @staticmethod
    def _json_line(payload: dict[str, Any]) -> bytes:
        return (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8")


runtime = MuseTalkLiveRuntime()


@app.get("/health")
def health() -> dict[str, Any]:
    return runtime.health()


@app.post("/prepare-avatar")
def prepare_avatar(payload: PrepareAvatarRequest) -> dict[str, Any]:
    try:
        runtime.prepare_avatar(
            payload.avatar_id,
            payload.image_path,
            payload.base_video_path,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {"status": "ok", "avatar_id": payload.avatar_id}


@app.post("/render-stream")
def render_stream(payload: RenderStreamRequest) -> StreamingResponse:
    try:
        iterator = runtime.render_stream(
            payload.avatar_id,
            payload.audio_path,
            payload.fps,
            payload.start_frame_index,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return StreamingResponse(iterator, media_type="application/x-ndjson")
