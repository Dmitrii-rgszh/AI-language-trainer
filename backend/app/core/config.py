import os

from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = os.getenv("APP_NAME", "AI English Trainer Pro API")
    api_prefix: str = os.getenv("API_PREFIX", "/api")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./trainer.db")
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


settings = Settings()
