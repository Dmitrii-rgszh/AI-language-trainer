# MuseTalk 1.5 Runtime

Verba now has a dedicated integration layer for MuseTalk 1.5 on the welcome mini-proof-lesson AI tutor step.

## What is already wired into the app

- Backend route: `POST /api/welcome/ai-tutor/video`
- Backend status: `GET /api/welcome/ai-tutor/status`
- Frontend step 2 AI tutor tries `MuseTalk` first and falls back to normal TTS only when the runtime is unavailable
- Default avatar asset: `backend/assets/musetalk/verba_tutor.png`

## Windows setup

Run:

```powershell
pwsh -File backend/scripts/setup_musetalk_runtime.ps1
```

The script:

1. clones the official `TMElyralab/MuseTalk` repository into `backend/.runtime/MuseTalk`
2. creates a dedicated `backend/.venv-musetalk`
3. installs the official PyTorch/CUDA baseline used by MuseTalk 1.5
4. installs the OpenMMLab dependencies
5. downloads official model weights

## Required environment variables

Before starting the backend, set:

```text
MUSE_TALK_ENABLED=1
MUSE_TALK_PYTHON_PATH=<repo>/backend/.venv-musetalk/Scripts/python.exe
MUSE_TALK_PROJECT_DIR=<repo>/backend/.runtime/MuseTalk
MUSE_TALK_RESULT_DIR=<repo>/backend/generated/musetalk
MUSE_TALK_AVATAR_VERBA_TUTOR_IMAGE=<repo>/backend/assets/musetalk/verba_tutor.png
```

If you start the app through `run_local_app.bat`, these values are now auto-injected when the local MuseTalk runtime is detected.

## Runtime expectations

- MuseTalk 1.5 should run in a separate CUDA-enabled Python environment
- the main backend `.venv` can stay independent
- `/api/welcome/ai-tutor/status` reports `fallback` until CUDA + weights are ready

## Source

- Official repository: https://github.com/TMElyralab/MuseTalk
