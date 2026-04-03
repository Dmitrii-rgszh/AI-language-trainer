from __future__ import annotations

import fractions
import io
import threading
import time
import wave
from collections import deque

import numpy as np
from aiortc import AudioStreamTrack, VideoStreamTrack
from av import AudioFrame, VideoFrame
from PIL import Image


class AvatarAudioTrack(AudioStreamTrack):
    def __init__(self, *, chunk_ms: int = 20, sample_rate: int = 48000) -> None:
        super().__init__()
        self._chunk_ms = chunk_ms
        self._sample_rate = sample_rate
        self._samples_per_chunk = int(self._sample_rate * (self._chunk_ms / 1000))
        self._buffer = np.zeros((0,), dtype=np.int16)
        self._lock = threading.Lock()

    def set_response_audio(self, wav_bytes: bytes) -> None:
        samples = self._decode_wav_to_mono_pcm(wav_bytes)
        with self._lock:
            self._buffer = samples

    def clear(self) -> None:
        with self._lock:
            self._buffer = np.zeros((0,), dtype=np.int16)

    async def recv(self) -> AudioFrame:
        if self.readyState != "live":
            raise RuntimeError("Audio track is not live")

        if hasattr(self, "_timestamp"):
            self._timestamp += self._samples_per_chunk
            wait = self._start + (self._timestamp / self._sample_rate) - time.time()
            await self._sleep(wait)
        else:
            self._start = time.time()
            self._timestamp = 0

        with self._lock:
            if self._buffer.size >= self._samples_per_chunk:
                chunk = self._buffer[: self._samples_per_chunk]
                self._buffer = self._buffer[self._samples_per_chunk :]
            elif self._buffer.size > 0:
                chunk = np.pad(
                    self._buffer,
                    (0, self._samples_per_chunk - self._buffer.size),
                    mode="constant",
                )
                self._buffer = np.zeros((0,), dtype=np.int16)
            else:
                chunk = np.zeros((self._samples_per_chunk,), dtype=np.int16)

        frame = AudioFrame(format="s16", layout="mono", samples=self._samples_per_chunk)
        for plane in frame.planes:
            plane.update(chunk.tobytes())
        frame.pts = self._timestamp
        frame.sample_rate = self._sample_rate
        frame.time_base = fractions.Fraction(1, self._sample_rate)
        return frame

    async def _sleep(self, delay: float) -> None:
        if delay > 0:
            import asyncio

            await asyncio.sleep(delay)

    def _decode_wav_to_mono_pcm(self, wav_bytes: bytes) -> np.ndarray:
        with wave.open(io.BytesIO(wav_bytes), "rb") as wav_file:
            sample_rate = wav_file.getframerate()
            channels = wav_file.getnchannels()
            frames = wav_file.readframes(wav_file.getnframes())

        samples = np.frombuffer(frames, dtype=np.int16)
        if channels > 1:
            samples = samples.reshape(-1, channels).mean(axis=1).astype(np.int16)

        if sample_rate == self._sample_rate:
            return samples

        if samples.size == 0:
            return samples

        target_size = max(1, int(round(samples.size * (self._sample_rate / sample_rate))))
        source_index = np.arange(samples.size, dtype=np.float32)
        target_index = np.linspace(0, samples.size - 1, num=target_size, dtype=np.float32)
        resampled = np.interp(target_index, source_index, samples.astype(np.float32))
        return np.clip(resampled, -32768, 32767).astype(np.int16)


class AvatarVideoTrack(VideoStreamTrack):
    def __init__(self, *, avatar_image_path: str, fps: int) -> None:
        super().__init__()
        with Image.open(avatar_image_path) as avatar_image:
            self._idle_frame = np.array(avatar_image.convert("RGB"), dtype=np.uint8)
        self._fps = fps
        self._frame_queue: deque[np.ndarray] = deque()
        self._lock = threading.Lock()

    async def next_timestamp(self) -> tuple[int, fractions.Fraction]:
        if self.readyState != "live":
            raise RuntimeError("Video track is not live")

        if hasattr(self, "_timestamp"):
            self._timestamp += int((1 / self._fps) * 90000)
            wait = self._start + (self._timestamp / 90000) - time.time()
            if wait > 0:
                import asyncio

                await asyncio.sleep(wait)
        else:
            self._start = time.time()
            self._timestamp = 0
        return self._timestamp, fractions.Fraction(1, 90000)

    async def recv(self) -> VideoFrame:
        pts, time_base = await self.next_timestamp()
        with self._lock:
            frame_array = self._frame_queue.popleft() if self._frame_queue else self._idle_frame
        frame = VideoFrame.from_ndarray(frame_array, format="rgb24")
        frame.pts = pts
        frame.time_base = time_base
        return frame

    async def enqueue_frame(self, frame_array: np.ndarray) -> None:
        with self._lock:
            self._frame_queue.append(frame_array)

    def clear(self) -> None:
        with self._lock:
            self._frame_queue.clear()
