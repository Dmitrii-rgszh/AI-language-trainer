from __future__ import annotations

import io
import wave
from collections.abc import Iterator
from dataclasses import dataclass


@dataclass(frozen=True)
class WavAudioChunk:
    pcm_bytes: bytes
    sample_rate: int
    channels: int
    sample_width: int


def iter_wav_audio_chunks(wav_bytes: bytes, *, chunk_ms: int = 120) -> Iterator[WavAudioChunk]:
    with wave.open(io.BytesIO(wav_bytes), "rb") as wav_file:
        sample_rate = wav_file.getframerate()
        channels = wav_file.getnchannels()
        sample_width = wav_file.getsampwidth()
        chunk_frames = max(1, int(sample_rate * (chunk_ms / 1000)))

        while True:
            frames = wav_file.readframes(chunk_frames)
            if not frames:
                break
            yield WavAudioChunk(
                pcm_bytes=frames,
                sample_rate=sample_rate,
                channels=channels,
                sample_width=sample_width,
            )
