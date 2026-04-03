import os
from pathlib import Path

from pydantic import BaseModel


BACKEND_DIR = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_URL = f"sqlite:///{(BACKEND_DIR / 'trainer.db').as_posix()}"


def _split_env_list(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


class Settings(BaseModel):
    app_name: str = os.getenv("APP_NAME", "AI English Trainer Pro API")
    api_prefix: str = os.getenv("API_PREFIX", "/api")
    database_url: str = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
    default_ui_language: str = os.getenv("DEFAULT_UI_LANGUAGE", "ru")
    llm_provider: str = os.getenv("LLM_PROVIDER", "mock")
    lmstudio_base_url: str = os.getenv("LMSTUDIO_BASE_URL", "http://127.0.0.1:1234/v1")
    lmstudio_model: str = os.getenv("LMSTUDIO_MODEL", "local-model")
    lmstudio_api_key: str = os.getenv("LMSTUDIO_API_KEY", "lm-studio")
    lmstudio_timeout_seconds: float = float(os.getenv("LMSTUDIO_TIMEOUT_SECONDS", "30"))
    tts_provider: str = os.getenv("TTS_PROVIDER", "xtts")
    stt_provider: str = os.getenv("STT_PROVIDER", "faster_whisper")
    faster_whisper_model: str = os.getenv("FASTER_WHISPER_MODEL", "large-v3-turbo")
    faster_whisper_device: str = os.getenv("FASTER_WHISPER_DEVICE", "auto")
    faster_whisper_compute_type: str = os.getenv("FASTER_WHISPER_COMPUTE_TYPE", "auto")
    xtts_model_name: str = os.getenv("XTTS_MODEL_NAME", "tts_models/multilingual/multi-dataset/xtts_v2")
    xtts_hf_repo_id: str = os.getenv("XTTS_HF_REPO_ID", "coqui/XTTS-v2")
    xtts_device: str = os.getenv("XTTS_DEVICE", "auto")
    xtts_default_language: str = os.getenv("XTTS_DEFAULT_LANGUAGE", "en")
    xtts_default_speaker: str = os.getenv("XTTS_DEFAULT_SPEAKER", "Ana Florence")
    xtts_reference_wav: str = os.getenv("XTTS_REFERENCE_WAV", "")
    qwen_tts_base_url: str = os.getenv("QWEN_TTS_BASE_URL", "http://127.0.0.1:8010")
    qwen_tts_model_id: str = os.getenv("QWEN_TTS_MODEL_ID", "Qwen/Qwen3-TTS-12Hz-1.7B-Base")
    qwen_tts_model: str = os.getenv("QWEN_TTS_MODEL", os.getenv("QWEN_TTS_MODEL_ID", "Qwen/Qwen3-TTS-12Hz-1.7B-Base"))
    qwen_tts_device: str = os.getenv("QWEN_TTS_DEVICE", "cuda:0")
    qwen_tts_dtype: str = os.getenv("QWEN_TTS_DTYPE", "float16")
    qwen_tts_mode: str = os.getenv("QWEN_TTS_MODE", "clone")
    qwen_tts_streaming_enabled: bool = os.getenv("QWEN_TTS_STREAMING_ENABLED", "1") == "1"
    qwen_tts_attn_implementation: str = os.getenv("QWEN_TTS_ATTN_IMPLEMENTATION", "")
    qwen_tts_timeout_seconds: float = float(os.getenv("QWEN_TTS_TIMEOUT_SECONDS", "300"))
    qwen_tts_ref_audio_path: str = os.getenv(
        "QWEN_TTS_REF_AUDIO_PATH",
        os.getenv("QWEN_TTS_REFERENCE_WAV", os.getenv("XTTS_REFERENCE_WAV", "")),
    )
    qwen_tts_reference_wav: str = os.getenv("QWEN_TTS_REFERENCE_WAV", os.getenv("QWEN_TTS_REF_AUDIO_PATH", os.getenv("XTTS_REFERENCE_WAV", "")))
    qwen_tts_ref_text: str = os.getenv("QWEN_TTS_REF_TEXT", os.getenv("QWEN_TTS_REFERENCE_TEXT", ""))
    qwen_tts_reference_text: str = os.getenv("QWEN_TTS_REFERENCE_TEXT", os.getenv("QWEN_TTS_REF_TEXT", ""))
    qwen_tts_reference_text_file: str = os.getenv("QWEN_TTS_REFERENCE_TEXT_FILE", "")
    qwen_tts_warmup: bool = os.getenv("QWEN_TTS_WARMUP", "1") == "1"
    qwen_tts_sample_rate: int = int(os.getenv("QWEN_TTS_SAMPLE_RATE", "24000"))
    qwen_tts_temperature: float = float(os.getenv("QWEN_TTS_TEMPERATURE", "0.35"))
    qwen_tts_top_p: float = float(os.getenv("QWEN_TTS_TOP_P", "0.82"))
    qwen_tts_top_k: int = int(os.getenv("QWEN_TTS_TOP_K", "20"))
    qwen_tts_repetition_penalty: float = float(os.getenv("QWEN_TTS_REPETITION_PENALTY", "1.05"))
    qwen_tts_max_new_tokens: int = int(os.getenv("QWEN_TTS_MAX_NEW_TOKENS", "1200"))
    coqui_tos_agreed: bool = os.getenv("COQUI_TOS_AGREED", "1") == "1"
    musetalk_enabled: bool = os.getenv("MUSE_TALK_ENABLED", "0") == "1"
    musetalk_python_path: str = os.getenv(
        "MUSE_TALK_PYTHON_PATH",
        str((BACKEND_DIR / ".venv-musetalk" / "Scripts" / "python.exe").as_posix()),
    )
    musetalk_project_dir: str = os.getenv(
        "MUSE_TALK_PROJECT_DIR",
        str((BACKEND_DIR / ".runtime" / "MuseTalk").as_posix()),
    )
    musetalk_result_dir: str = os.getenv(
        "MUSE_TALK_RESULT_DIR",
        str((BACKEND_DIR / "generated" / "musetalk").as_posix()),
    )
    musetalk_ffmpeg_path: str = os.getenv("MUSE_TALK_FFMPEG_PATH", "ffmpeg")
    musetalk_avatar_verba_tutor_image: str = os.getenv(
        "MUSE_TALK_AVATAR_VERBA_TUTOR_IMAGE",
        str((BACKEND_DIR / "assets" / "musetalk" / "verba_tutor.png").as_posix()),
    )
    musetalk_version: str = os.getenv("MUSE_TALK_VERSION", "v15")
    musetalk_gpu_id: int = int(os.getenv("MUSE_TALK_GPU_ID", "0"))
    musetalk_fps: int = int(os.getenv("MUSE_TALK_FPS", "25"))
    musetalk_batch_size: int = int(os.getenv("MUSE_TALK_BATCH_SIZE", "8"))
    musetalk_extra_margin: int = int(os.getenv("MUSE_TALK_EXTRA_MARGIN", "10"))
    musetalk_audio_padding_left: int = int(os.getenv("MUSE_TALK_AUDIO_PADDING_LEFT", "2"))
    musetalk_audio_padding_right: int = int(os.getenv("MUSE_TALK_AUDIO_PADDING_RIGHT", "2"))
    musetalk_use_float16: bool = os.getenv("MUSE_TALK_USE_FLOAT16", "1") == "1"
    musetalk_default_speaker: str = os.getenv("MUSE_TALK_DEFAULT_SPEAKER", "Daisy Studious")
    musetalk_frame_buffer: int = int(os.getenv("MUSE_TALK_FRAME_BUFFER", "48"))
    musetalk_warmup: bool = os.getenv("MUSE_TALK_WARMUP", "1") == "1"
    musetalk_quality_mode: str = os.getenv("MUSE_TALK_QUALITY_MODE", "balanced")
    musetalk_live_enabled: bool = os.getenv("MUSE_TALK_LIVE_ENABLED", "1") == "1"
    musetalk_live_base_url: str = os.getenv("MUSE_TALK_LIVE_BASE_URL", "http://127.0.0.1:8011")
    live_avatar_enabled: bool = os.getenv("LIVE_AVATAR_ENABLED", "1") == "1"
    live_avatar_default_avatar_key: str = os.getenv("LIVE_AVATAR_DEFAULT_AVATAR_KEY", "verba_tutor")
    live_avatar_default_voice_profile_id: str = os.getenv("LIVE_AVATAR_DEFAULT_VOICE_PROFILE_ID", "liza-qwen-clone")
    live_avatar_default_voice_name: str = os.getenv("LIVE_AVATAR_DEFAULT_VOICE_NAME", "Liza Friendly Clone")
    live_avatar_vad_start_threshold: float = float(os.getenv("LIVE_AVATAR_VAD_START_THRESHOLD", "0.015"))
    live_avatar_vad_continue_threshold: float = float(os.getenv("LIVE_AVATAR_VAD_CONTINUE_THRESHOLD", "0.01"))
    live_avatar_min_speech_ms: int = int(os.getenv("LIVE_AVATAR_MIN_SPEECH_MS", "450"))
    live_avatar_trailing_silence_ms: int = int(os.getenv("LIVE_AVATAR_TRAILING_SILENCE_MS", "900"))
    live_avatar_max_utterance_ms: int = int(os.getenv("LIVE_AVATAR_MAX_UTTERANCE_MS", "15000"))
    live_avatar_preroll_ms: int = int(os.getenv("LIVE_AVATAR_PREROLL_MS", "250"))
    live_avatar_audio_chunk_ms: int = int(os.getenv("LIVE_AVATAR_AUDIO_CHUNK_MS", "20"))
    live_avatar_idle_video_fps: int = int(os.getenv("LIVE_AVATAR_IDLE_VIDEO_FPS", os.getenv("MUSE_TALK_FPS", "25")))
    webrtc_stun_urls: list[str] = _split_env_list(
        os.getenv("WEBRTC_STUN_URLS", "stun:stun.l.google.com:19302")
    )
    webrtc_turn_urls: list[str] = _split_env_list(os.getenv("WEBRTC_TURN_URLS", ""))
    webrtc_turn_username: str = os.getenv("WEBRTC_TURN_USERNAME", "")
    webrtc_turn_password: str = os.getenv("WEBRTC_TURN_PASSWORD", "")


settings = Settings()
