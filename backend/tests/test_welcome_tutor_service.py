from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from app.services.welcome_tutor_service.presets import resolve_welcome_tutor_preset
from app.services.welcome_tutor_service.service import MuseTalkRuntimeConfig, WelcomeTutorService


class FakeVoiceService:
    def synthesize(
        self,
        text: str,
        language: str,
        speaker: str | None = None,
        style: str | None = None,
    ) -> bytes:
        return b"fake-wave"


def build_runtime_config(root: Path) -> MuseTalkRuntimeConfig:
    return MuseTalkRuntimeConfig(
        enabled=True,
        python_path=root / "python.exe",
        project_dir=root / "MuseTalk",
        result_dir=root / "results",
        ffmpeg_path="ffmpeg",
        avatar_image_paths={"verba_tutor": root / "avatar.png"},
        version="v15",
        gpu_id=0,
        fps=25,
        batch_size=8,
        extra_margin=10,
        audio_padding_left=2,
        audio_padding_right=2,
        use_float16=True,
        default_speaker="Ana Florence",
    )


def build_service(config: MuseTalkRuntimeConfig) -> WelcomeTutorService:
    service = WelcomeTutorService(FakeVoiceService())
    service._runtime_config = config
    return service


def test_welcome_tutor_status_reports_disabled_runtime(tmp_path) -> None:
    config = replace(build_runtime_config(tmp_path), enabled=False)
    service = build_service(config)

    status = service.get_status()

    assert status.available is False
    assert status.mode == "fallback"
    assert "disabled" in status.details


def test_welcome_tutor_status_reports_missing_runtime_files(tmp_path) -> None:
    service = build_service(build_runtime_config(tmp_path))

    status = service.get_status()

    assert status.available is False
    assert status.mode == "fallback"
    assert "Missing:" in status.details


def test_welcome_tutor_status_reports_ready_runtime_when_assets_exist(tmp_path, monkeypatch) -> None:
    config = build_runtime_config(tmp_path)
    config.python_path.write_text("", encoding="utf-8")
    config.avatar_image_paths["verba_tutor"].write_text("avatar", encoding="utf-8")
    config.project_dir.mkdir(parents=True, exist_ok=True)
    config.inference_script_path.parent.mkdir(parents=True, exist_ok=True)
    config.inference_script_path.write_text("# fake", encoding="utf-8")
    config.unet_model_path.parent.mkdir(parents=True, exist_ok=True)
    config.unet_model_path.write_text("weights", encoding="utf-8")
    config.unet_config_path.write_text("{}", encoding="utf-8")
    config.whisper_dir.mkdir(parents=True, exist_ok=True)
    config.whisper_config_path.write_text("{}", encoding="utf-8")
    config.whisper_weights_path.write_text("weights", encoding="utf-8")
    config.whisper_preprocessor_config_path.write_text("{}", encoding="utf-8")
    config.sd_vae_config_path.parent.mkdir(parents=True, exist_ok=True)
    config.sd_vae_config_path.write_text("{}", encoding="utf-8")
    config.sd_vae_weights_path.write_text("weights", encoding="utf-8")
    config.dwpose_model_path.parent.mkdir(parents=True, exist_ok=True)
    config.dwpose_model_path.write_text("weights", encoding="utf-8")
    config.syncnet_model_path.parent.mkdir(parents=True, exist_ok=True)
    config.syncnet_model_path.write_text("weights", encoding="utf-8")
    config.face_parse_model_path.parent.mkdir(parents=True, exist_ok=True)
    config.face_parse_model_path.write_text("weights", encoding="utf-8")
    config.face_parse_resnet_path.write_text("weights", encoding="utf-8")

    service = build_service(config)
    monkeypatch.setattr(service, "_check_python_runtime", lambda: (True, "CUDA runtime ready for tests."))
    monkeypatch.setattr("app.services.welcome_tutor_service.service.shutil.which", lambda _: "ffmpeg")

    status = service.get_status()

    assert status.available is True
    assert status.mode == "musetalk"
    assert "CUDA runtime ready for tests." in status.details


def test_welcome_tutor_command_targets_official_inference_script(tmp_path) -> None:
    config = build_runtime_config(tmp_path)
    service = build_service(config)

    command = service._build_command(
        inference_config_path=tmp_path / "inference.yaml",
        result_dir=tmp_path / "results",
        output_name="clip.mp4",
    )

    assert command[0] == str(config.python_path)
    assert command[1:3] == ["-m", "scripts.inference"]
    assert "--output_vid_name" in command
    assert "clip.mp4" in command


def test_welcome_tutor_prefers_presence_01_for_verba_tutor(tmp_path, monkeypatch) -> None:
    config = build_runtime_config(tmp_path)
    service = build_service(config)
    forced_presence_path = tmp_path / "generated" / "live_avatar" / "presence_01.mp4"
    forced_presence_path.parent.mkdir(parents=True, exist_ok=True)
    forced_presence_path.write_text("presence", encoding="utf-8")

    monkeypatch.setattr(
        "app.services.welcome_tutor_service.service.BACKEND_DIR",
        tmp_path,
    )

    resolved_path = service._resolve_base_video_path(avatar_key="verba_tutor")

    assert resolved_path == forced_presence_path.resolve()


def test_welcome_clarity_presets_keep_english_model_voice() -> None:
    ru_intro = resolve_welcome_tutor_preset(locale="ru", kind="clarity_intro", variant=0)
    ru_model = resolve_welcome_tutor_preset(locale="ru", kind="clarity_model", variant=0)
    intro_prompt = resolve_welcome_tutor_preset(locale="ru", kind="intro", variant=2)

    assert ru_intro.render_language == "ru"
    assert ru_model.render_language == "en"
    assert intro_prompt.revision == "welcome-presets-v6-presence-01-forced"
    assert ru_intro.revision == "welcome-presets-v7-stable-coach"
    assert "I'd like a coffee without sugar." in ru_model.text
