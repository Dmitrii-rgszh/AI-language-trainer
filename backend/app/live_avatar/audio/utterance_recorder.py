from __future__ import annotations

import io
import wave
from collections import deque
from dataclasses import dataclass

import numpy as np
from av import AudioFrame


@dataclass(frozen=True)
class CapturedUtterance:
    wav_bytes: bytes
    sample_rate: int
    duration_ms: int


class UtteranceRecorder:
    def __init__(
        self,
        *,
        start_threshold: float,
        continue_threshold: float,
        min_speech_ms: int,
        trailing_silence_ms: int,
        max_utterance_ms: int,
        preroll_ms: int,
    ) -> None:
        self._start_threshold = start_threshold
        self._continue_threshold = continue_threshold
        self._min_speech_ms = min_speech_ms
        self._trailing_silence_ms = trailing_silence_ms
        self._max_utterance_ms = max_utterance_ms
        self._preroll_limit_ms = preroll_ms
        self._reset()

    def process_frame(self, frame: AudioFrame) -> CapturedUtterance | None:
        mono_samples, sample_rate = self._frame_to_mono(frame)
        if mono_samples.size == 0 or sample_rate <= 0:
            return None

        frame_duration_ms = int((mono_samples.size / sample_rate) * 1000)
        rms = self._compute_rms(mono_samples)
        self._push_preroll(mono_samples, sample_rate)

        if not self._capturing:
            if rms < self._start_threshold:
                return None

            self._capturing = True
            self._sample_rate = sample_rate
            self._segments.extend(self._preroll)
            self._segments.append(mono_samples)
            self._utterance_ms = self._segments_duration_ms(self._segments, sample_rate)
            self._silence_ms = 0
            return self._maybe_finalize()

        self._sample_rate = sample_rate
        self._segments.append(mono_samples)
        self._utterance_ms += frame_duration_ms
        if rms >= self._continue_threshold:
            self._silence_ms = 0
        else:
            self._silence_ms += frame_duration_ms

        return self._maybe_finalize()

    def force_finalize(self) -> CapturedUtterance | None:
        if not self._capturing or self._sample_rate <= 0:
            return None
        if self._utterance_ms < self._min_speech_ms:
            self._reset()
            return None
        return self._finalize()

    def reset(self) -> None:
        self._reset()

    def _maybe_finalize(self) -> CapturedUtterance | None:
        if not self._capturing:
            return None

        if self._utterance_ms >= self._max_utterance_ms:
            return self._finalize()

        if self._utterance_ms >= self._min_speech_ms and self._silence_ms >= self._trailing_silence_ms:
            return self._finalize()

        return None

    def _finalize(self) -> CapturedUtterance:
        sample_rate = self._sample_rate
        pcm = np.concatenate(list(self._segments)).astype(np.int16, copy=False)
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(pcm.tobytes())

        utterance = CapturedUtterance(
            wav_bytes=buffer.getvalue(),
            sample_rate=sample_rate,
            duration_ms=self._utterance_ms,
        )
        self._reset()
        return utterance

    def _push_preroll(self, mono_samples: np.ndarray, sample_rate: int) -> None:
        self._preroll.append(mono_samples)
        self._preroll_buffer_ms += int((mono_samples.size / sample_rate) * 1000)
        while self._preroll and self._preroll_buffer_ms > self._preroll_limit_ms:
            removed = self._preroll.popleft()
            self._preroll_buffer_ms -= int((removed.size / sample_rate) * 1000)

    def _reset(self) -> None:
        self._capturing = False
        self._sample_rate = 0
        self._segments: deque[np.ndarray] = deque()
        self._utterance_ms = 0
        self._silence_ms = 0
        self._preroll: deque[np.ndarray] = deque()
        self._preroll_buffer_ms = 0

    @staticmethod
    def _segments_duration_ms(segments: deque[np.ndarray], sample_rate: int) -> int:
        total_samples = sum(segment.size for segment in segments)
        return int((total_samples / sample_rate) * 1000)

    @staticmethod
    def _compute_rms(samples: np.ndarray) -> float:
        if samples.size == 0:
            return 0.0
        normalized = samples.astype(np.float32) / 32768.0
        return float(np.sqrt(np.mean(np.square(normalized))))

    @staticmethod
    def _frame_to_mono(frame: AudioFrame) -> tuple[np.ndarray, int]:
        array = frame.to_ndarray()
        if array.ndim == 2:
            if array.shape[0] <= array.shape[1]:
                mono = array.mean(axis=0)
            else:
                mono = array.mean(axis=1)
        else:
            mono = array

        mono = np.clip(mono, -32768, 32767).astype(np.int16, copy=False)
        return mono, int(frame.sample_rate or 0)
