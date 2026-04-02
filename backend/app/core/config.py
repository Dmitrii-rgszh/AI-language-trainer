import os
from pathlib import Path

from pydantic import BaseModel


BACKEND_DIR = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_URL = f"sqlite:///{(BACKEND_DIR / 'trainer.db').as_posix()}"


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


settings = Settings()
