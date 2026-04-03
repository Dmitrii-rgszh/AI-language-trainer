@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul

set "ROOT_DIR=%~dp0"
cd /d "%ROOT_DIR%"

set "BACKEND_DIR=%ROOT_DIR%backend"
set "FRONTEND_DIR=%ROOT_DIR%app\frontend"
set "BACKEND_PYTHON=%BACKEND_DIR%\.venv\Scripts\python.exe"
set "BACKEND_LOG=%BACKEND_DIR%\backend-dev.log"
set "BACKEND_ERR_LOG=%BACKEND_DIR%\backend-dev.err.log"
set "FRONTEND_LOG=%FRONTEND_DIR%\frontend-dev.log"
set "FRONTEND_ERR_LOG=%FRONTEND_DIR%\frontend-dev.err.log"
set "MUSE_TALK_PYTHON=%BACKEND_DIR%\.venv-musetalk\Scripts\python.exe"
set "MUSE_TALK_PROJECT=%BACKEND_DIR%\.runtime\MuseTalk"
set "MUSE_TALK_RESULTS=%BACKEND_DIR%\generated\musetalk"
set "MUSE_TALK_AVATAR=%BACKEND_DIR%\assets\musetalk\verba_tutor.png"
set "XTTS_REFERENCE_DEFAULT=%BACKEND_DIR%\assets\voices\tutor_reference_02.WAV"
set "QWEN_TTS_PYTHON=%BACKEND_DIR%\.venv-qwen\Scripts\python.exe"
set "QWEN_TTS_LOG=%BACKEND_DIR%\qwen-tts-dev.log"
set "QWEN_TTS_ERR_LOG=%BACKEND_DIR%\qwen-tts-dev.err.log"
set "MUSE_TALK_LIVE_LOG=%BACKEND_DIR%\musetalk-live-dev.log"
set "MUSE_TALK_LIVE_ERR_LOG=%BACKEND_DIR%\musetalk-live-dev.err.log"
set "RESET_DB=0"
set "SKIP_DEMO_SEED=0"

if exist "%BACKEND_DIR%\trainer.db" set "SKIP_DEMO_SEED=1"

if /I "%~1"=="--reset-db" set "RESET_DB=1"
if /I "%~1"=="/reset-db" set "RESET_DB=1"
if "%RESET_DB%"=="1" set "SKIP_DEMO_SEED=0"

echo ==========================================
echo AI English Trainer Pro - Full Stack Restart
echo ==========================================
echo.

if not exist "%BACKEND_PYTHON%" (
    echo [ERROR] Backend virtualenv not found: backend\.venv
    echo Run backend setup first, then try again.
    exit /b 1
)

if not exist "%FRONTEND_DIR%\node_modules" (
    echo [ERROR] Frontend dependencies not found: app\frontend\node_modules
    echo Run npm install in app\frontend, then try again.
    exit /b 1
)

if "%LLM_PROVIDER%"=="" set "LLM_PROVIDER=lmstudio"
if "%TTS_PROVIDER%"=="" set "TTS_PROVIDER=qwen3_tts"
if "%LMSTUDIO_BASE_URL%"=="" set "LMSTUDIO_BASE_URL=http://127.0.0.1:1234/v1"
if "%LMSTUDIO_MODEL%"=="" set "LMSTUDIO_MODEL=qwen/qwen3-8b"
if "%BACKEND_HOST%"=="" set "BACKEND_HOST=127.0.0.1"
if "%BACKEND_PORT%"=="" set "BACKEND_PORT=8000"
if "%FRONTEND_HOST%"=="" set "FRONTEND_HOST=127.0.0.1"
if "%FRONTEND_PORT%"=="" set "FRONTEND_PORT=5173"
if "%QWEN_TTS_HOST%"=="" set "QWEN_TTS_HOST=127.0.0.1"
if "%QWEN_TTS_PORT%"=="" set "QWEN_TTS_PORT=8010"
if "%QWEN_TTS_BASE_URL%"=="" set "QWEN_TTS_BASE_URL=http://%QWEN_TTS_HOST%:%QWEN_TTS_PORT%"
if "%QWEN_TTS_MODEL_ID%"=="" set "QWEN_TTS_MODEL_ID=Qwen/Qwen3-TTS-12Hz-1.7B-Base"
if "%QWEN_TTS_MODEL%"=="" set "QWEN_TTS_MODEL=%QWEN_TTS_MODEL_ID%"
if "%QWEN_TTS_MODE%"=="" set "QWEN_TTS_MODE=clone"
if "%QWEN_TTS_STREAMING_ENABLED%"=="" set "QWEN_TTS_STREAMING_ENABLED=1"
if "%QWEN_TTS_DEVICE%"=="" set "QWEN_TTS_DEVICE=cuda:0"
if "%QWEN_TTS_DTYPE%"=="" set "QWEN_TTS_DTYPE=float16"
if "%QWEN_TTS_TEMPERATURE%"=="" set "QWEN_TTS_TEMPERATURE=0.35"
if "%QWEN_TTS_TOP_P%"=="" set "QWEN_TTS_TOP_P=0.82"
if "%QWEN_TTS_TOP_K%"=="" set "QWEN_TTS_TOP_K=20"
if "%QWEN_TTS_REPETITION_PENALTY%"=="" set "QWEN_TTS_REPETITION_PENALTY=1.05"
if "%QWEN_TTS_MAX_NEW_TOKENS%"=="" set "QWEN_TTS_MAX_NEW_TOKENS=1200"
if "%MUSE_TALK_ENABLED%"=="" (
    if exist "%MUSE_TALK_PYTHON%" if exist "%MUSE_TALK_PROJECT%\models\musetalkV15\unet.pth" if exist "%MUSE_TALK_AVATAR%" (
        set "MUSE_TALK_ENABLED=1"
    ) else (
        set "MUSE_TALK_ENABLED=0"
    )
)
if "%MUSE_TALK_PYTHON_PATH%"=="" set "MUSE_TALK_PYTHON_PATH=%MUSE_TALK_PYTHON%"
if "%MUSE_TALK_PROJECT_DIR%"=="" set "MUSE_TALK_PROJECT_DIR=%MUSE_TALK_PROJECT%"
if "%MUSE_TALK_RESULT_DIR%"=="" set "MUSE_TALK_RESULT_DIR=%MUSE_TALK_RESULTS%"
if "%MUSE_TALK_AVATAR_VERBA_TUTOR_IMAGE%"=="" set "MUSE_TALK_AVATAR_VERBA_TUTOR_IMAGE=%MUSE_TALK_AVATAR%"
if "%MUSE_TALK_DEFAULT_SPEAKER%"=="" set "MUSE_TALK_DEFAULT_SPEAKER=Daisy Studious"
if "%MUSE_TALK_LIVE_ENABLED%"=="" set "MUSE_TALK_LIVE_ENABLED=%MUSE_TALK_ENABLED%"
if "%MUSE_TALK_LIVE_HOST%"=="" set "MUSE_TALK_LIVE_HOST=127.0.0.1"
if "%MUSE_TALK_LIVE_PORT%"=="" set "MUSE_TALK_LIVE_PORT=8011"
if "%MUSE_TALK_LIVE_BASE_URL%"=="" set "MUSE_TALK_LIVE_BASE_URL=http://%MUSE_TALK_LIVE_HOST%:%MUSE_TALK_LIVE_PORT%"
if "%LIVE_AVATAR_ENABLED%"=="" set "LIVE_AVATAR_ENABLED=1"
if "%WEBRTC_STUN_URLS%"=="" set "WEBRTC_STUN_URLS=stun:stun.l.google.com:19302"
if "%XTTS_REFERENCE_WAV%"=="" if exist "%XTTS_REFERENCE_DEFAULT%" set "XTTS_REFERENCE_WAV=%XTTS_REFERENCE_DEFAULT%"
if "%QWEN_TTS_REFERENCE_WAV%"=="" if exist "%XTTS_REFERENCE_DEFAULT%" set "QWEN_TTS_REFERENCE_WAV=%XTTS_REFERENCE_DEFAULT%"
if "%QWEN_TTS_REF_AUDIO_PATH%"=="" set "QWEN_TTS_REF_AUDIO_PATH=%QWEN_TTS_REFERENCE_WAV%"
if "%QWEN_TTS_REFERENCE_TEXT_FILE%"=="" set "QWEN_TTS_REFERENCE_TEXT_FILE=%BACKEND_DIR%\generated\qwen_tts\reference\tutor_reference_02.transcript.txt"
if "%QWEN_TTS_REF_TEXT%"=="" if exist "%QWEN_TTS_REFERENCE_TEXT_FILE%" set /p QWEN_TTS_REF_TEXT=<"%QWEN_TTS_REFERENCE_TEXT_FILE%"

if /I "%TTS_PROVIDER%"=="qwen3_tts" if not exist "%QWEN_TTS_PYTHON%" (
    echo [ERROR] Qwen3-TTS runtime not found: %QWEN_TTS_PYTHON%
    echo Run backend\scripts\setup_qwen_tts_runtime.ps1, then try again.
    exit /b 1
)
if "%MUSE_TALK_LIVE_ENABLED%"=="1" if not exist "%MUSE_TALK_PYTHON%" (
    echo [ERROR] MuseTalk live runtime not found: %MUSE_TALK_PYTHON%
    echo Run backend\scripts\setup_musetalk_runtime.ps1, then try again.
    exit /b 1
)

echo [INFO] Backend URL:  http://%BACKEND_HOST%:%BACKEND_PORT%
echo [INFO] Frontend URL: http://%FRONTEND_HOST%:%FRONTEND_PORT%
echo [INFO] SQLite DB:    %BACKEND_DIR%\trainer.db
echo [INFO] LM Studio:    %LMSTUDIO_BASE_URL%
echo [INFO] Model:        %LMSTUDIO_MODEL%
echo [INFO] TTS Provider: %TTS_PROVIDER%
echo [INFO] MuseTalk:     %MUSE_TALK_ENABLED%
echo [INFO] Live Avatar:  %LIVE_AVATAR_ENABLED%
if /I "%TTS_PROVIDER%"=="qwen3_tts" (
    echo [INFO] Qwen TTS URL: %QWEN_TTS_BASE_URL%
    echo [INFO] Qwen Model:   %QWEN_TTS_MODEL_ID%
    echo [INFO] Qwen Ref:     %QWEN_TTS_REFERENCE_WAV%
    echo [INFO] Qwen Preset:  friendly_stable ^(temp=%QWEN_TTS_TEMPERATURE%, top_p=%QWEN_TTS_TOP_P%, top_k=%QWEN_TTS_TOP_K%, rep=%QWEN_TTS_REPETITION_PENALTY%^)
) else (
    if "%XTTS_REFERENCE_WAV%"=="" (
        echo [INFO] XTTS ref:     built-in speaker
    ) else (
        echo [INFO] XTTS ref:     %XTTS_REFERENCE_WAV%
    )
)
if "%RESET_DB%"=="1" (
    echo [INFO] Database reset: enabled
) else (
    echo [INFO] Database reset: disabled
)
echo.

echo [STEP] Stopping previous frontend/backend processes...
call "%ROOT_DIR%stop_local_app.bat"
echo.

if "%RESET_DB%"=="1" (
    if exist "%BACKEND_DIR%\trainer.db" (
        echo [STEP] Removing existing SQLite database...
        del /f /q "%BACKEND_DIR%\trainer.db"
        if errorlevel 1 (
            echo [ERROR] Failed to delete backend\trainer.db
            exit /b 1
        )
        echo [OK] SQLite database removed.
    ) else (
        echo [INFO] SQLite database not found, skipping deletion.
    )
    echo.
)

pushd "%BACKEND_DIR%"

echo [STEP] Applying database migrations...
"%BACKEND_PYTHON%" -m alembic upgrade head
if errorlevel 1 (
    popd
    echo [ERROR] Alembic migration failed.
    exit /b 1
)
echo [OK] Database schema is up to date.
echo.

echo [STEP] Bootstrapping static content...
"%BACKEND_PYTHON%" scripts\bootstrap_content.py
if errorlevel 1 (
    popd
    echo [ERROR] Content bootstrap failed.
    exit /b 1
)
echo [OK] Static content is ready.
echo.

if "%SKIP_DEMO_SEED%"=="1" (
    echo [STEP] Skipping demo seed because local DB already exists...
    echo [OK] Existing local runtime data preserved.
    echo.
) else (
    echo [STEP] Seeding demo user and runtime data...
    "%BACKEND_PYTHON%" scripts\seed_demo_data.py
    if errorlevel 1 (
        popd
        echo [ERROR] Demo data seeding failed.
        exit /b 1
    )
    echo [OK] Demo data is ready.
    echo.
)

popd

echo [STEP] Resetting launch logs...
break > "%BACKEND_LOG%"
break > "%BACKEND_ERR_LOG%"
break > "%FRONTEND_LOG%"
break > "%FRONTEND_ERR_LOG%"
break > "%QWEN_TTS_LOG%"
break > "%QWEN_TTS_ERR_LOG%"
break > "%MUSE_TALK_LIVE_LOG%"
break > "%MUSE_TALK_LIVE_ERR_LOG%"

if /I "%TTS_PROVIDER%"=="qwen3_tts" (
    echo [STEP] Starting Qwen3-TTS sidecar in background...
    powershell -NoProfile -Command "$env:QWEN_TTS_MODEL_ID='%QWEN_TTS_MODEL_ID%'; $env:QWEN_TTS_DEVICE='%QWEN_TTS_DEVICE%'; $env:QWEN_TTS_DTYPE='%QWEN_TTS_DTYPE%'; $env:QWEN_TTS_ATTN_IMPLEMENTATION='%QWEN_TTS_ATTN_IMPLEMENTATION%'; $env:QWEN_TTS_TEMPERATURE='%QWEN_TTS_TEMPERATURE%'; $env:QWEN_TTS_TOP_P='%QWEN_TTS_TOP_P%'; $env:QWEN_TTS_TOP_K='%QWEN_TTS_TOP_K%'; $env:QWEN_TTS_REPETITION_PENALTY='%QWEN_TTS_REPETITION_PENALTY%'; $env:QWEN_TTS_MAX_NEW_TOKENS='%QWEN_TTS_MAX_NEW_TOKENS%'; $env:QWEN_TTS_REF_AUDIO_PATH='%QWEN_TTS_REF_AUDIO_PATH%'; $env:QWEN_TTS_REFERENCE_WAV='%QWEN_TTS_REFERENCE_WAV%'; $env:QWEN_TTS_REF_TEXT='%QWEN_TTS_REF_TEXT%'; $env:QWEN_TTS_REFERENCE_TEXT_FILE='%QWEN_TTS_REFERENCE_TEXT_FILE%'; Start-Process -FilePath '%QWEN_TTS_PYTHON%' -ArgumentList '-m','uvicorn','scripts.qwen_tts_sidecar:app','--host','%QWEN_TTS_HOST%','--port','%QWEN_TTS_PORT%' -WorkingDirectory '%BACKEND_DIR%' -RedirectStandardOutput '%QWEN_TTS_LOG%' -RedirectStandardError '%QWEN_TTS_ERR_LOG%'" >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Failed to start Qwen3-TTS sidecar process.
        exit /b 1
    )

    echo [STEP] Waiting for Qwen3-TTS sidecar on port %QWEN_TTS_PORT%...
    call :wait_for_http "%QWEN_TTS_BASE_URL%/health" 60 "qwen-tts"
    if errorlevel 1 (
        echo [ERROR] Qwen3-TTS sidecar did not become ready in time.
        echo [ERROR] Qwen stdout log: %QWEN_TTS_LOG%
        echo [ERROR] Qwen stderr log: %QWEN_TTS_ERR_LOG%
        exit /b 1
    )
    echo [OK] Qwen3-TTS sidecar is ready.
)

if "%MUSE_TALK_LIVE_ENABLED%"=="1" (
    echo [STEP] Starting MuseTalk live sidecar in background...
    powershell -NoProfile -Command "$env:MUSE_TALK_PROJECT_DIR='%MUSE_TALK_PROJECT_DIR%'; $env:MUSE_TALK_VERSION='%MUSE_TALK_VERSION%'; $env:MUSE_TALK_GPU_ID='%MUSE_TALK_GPU_ID%'; $env:MUSE_TALK_BATCH_SIZE='%MUSE_TALK_BATCH_SIZE%'; $env:MUSE_TALK_FPS='%MUSE_TALK_FPS%'; $env:MUSE_TALK_EXTRA_MARGIN='%MUSE_TALK_EXTRA_MARGIN%'; $env:MUSE_TALK_AUDIO_PADDING_LEFT='%MUSE_TALK_AUDIO_PADDING_LEFT%'; $env:MUSE_TALK_AUDIO_PADDING_RIGHT='%MUSE_TALK_AUDIO_PADDING_RIGHT%'; $env:MUSE_TALK_AVATAR_VERBA_TUTOR_IMAGE='%MUSE_TALK_AVATAR_VERBA_TUTOR_IMAGE%'; Start-Process -FilePath '%MUSE_TALK_PYTHON%' -ArgumentList '-m','uvicorn','scripts.musetalk_live_sidecar:app','--host','%MUSE_TALK_LIVE_HOST%','--port','%MUSE_TALK_LIVE_PORT%' -WorkingDirectory '%BACKEND_DIR%' -RedirectStandardOutput '%MUSE_TALK_LIVE_LOG%' -RedirectStandardError '%MUSE_TALK_LIVE_ERR_LOG%'" >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Failed to start MuseTalk live sidecar process.
        exit /b 1
    )

    echo [STEP] Waiting for MuseTalk live sidecar on port %MUSE_TALK_LIVE_PORT%...
    call :wait_for_http "%MUSE_TALK_LIVE_BASE_URL%/health" 60 "musetalk-live"
    if errorlevel 1 (
        echo [ERROR] MuseTalk live sidecar did not become ready in time.
        echo [ERROR] MuseTalk live stdout log: %MUSE_TALK_LIVE_LOG%
        echo [ERROR] MuseTalk live stderr log: %MUSE_TALK_LIVE_ERR_LOG%
        exit /b 1
    )
    echo [OK] MuseTalk live sidecar is ready.
)

echo [STEP] Starting backend in background...
powershell -NoProfile -Command "$env:LLM_PROVIDER='%LLM_PROVIDER%'; $env:TTS_PROVIDER='%TTS_PROVIDER%'; $env:LMSTUDIO_BASE_URL='%LMSTUDIO_BASE_URL%'; $env:LMSTUDIO_MODEL='%LMSTUDIO_MODEL%'; $env:XTTS_REFERENCE_WAV='%XTTS_REFERENCE_WAV%'; $env:LIVE_AVATAR_ENABLED='%LIVE_AVATAR_ENABLED%'; $env:WEBRTC_STUN_URLS='%WEBRTC_STUN_URLS%'; $env:MUSE_TALK_LIVE_ENABLED='%MUSE_TALK_LIVE_ENABLED%'; $env:MUSE_TALK_LIVE_BASE_URL='%MUSE_TALK_LIVE_BASE_URL%'; $env:QWEN_TTS_BASE_URL='%QWEN_TTS_BASE_URL%'; $env:QWEN_TTS_MODEL='%QWEN_TTS_MODEL%'; $env:QWEN_TTS_MODEL_ID='%QWEN_TTS_MODEL_ID%'; $env:QWEN_TTS_MODE='%QWEN_TTS_MODE%'; $env:QWEN_TTS_STREAMING_ENABLED='%QWEN_TTS_STREAMING_ENABLED%'; $env:QWEN_TTS_DEVICE='%QWEN_TTS_DEVICE%'; $env:QWEN_TTS_DTYPE='%QWEN_TTS_DTYPE%'; $env:QWEN_TTS_REF_AUDIO_PATH='%QWEN_TTS_REF_AUDIO_PATH%'; $env:QWEN_TTS_REF_TEXT='%QWEN_TTS_REF_TEXT%'; $env:QWEN_TTS_REFERENCE_WAV='%QWEN_TTS_REFERENCE_WAV%'; $env:QWEN_TTS_REFERENCE_TEXT_FILE='%QWEN_TTS_REFERENCE_TEXT_FILE%'; $env:QWEN_TTS_TEMPERATURE='%QWEN_TTS_TEMPERATURE%'; $env:QWEN_TTS_TOP_P='%QWEN_TTS_TOP_P%'; $env:QWEN_TTS_TOP_K='%QWEN_TTS_TOP_K%'; $env:QWEN_TTS_REPETITION_PENALTY='%QWEN_TTS_REPETITION_PENALTY%'; $env:QWEN_TTS_MAX_NEW_TOKENS='%QWEN_TTS_MAX_NEW_TOKENS%'; $env:MUSE_TALK_ENABLED='%MUSE_TALK_ENABLED%'; $env:MUSE_TALK_PYTHON_PATH='%MUSE_TALK_PYTHON_PATH%'; $env:MUSE_TALK_PROJECT_DIR='%MUSE_TALK_PROJECT_DIR%'; $env:MUSE_TALK_RESULT_DIR='%MUSE_TALK_RESULT_DIR%'; $env:MUSE_TALK_AVATAR_VERBA_TUTOR_IMAGE='%MUSE_TALK_AVATAR_VERBA_TUTOR_IMAGE%'; $env:MUSE_TALK_DEFAULT_SPEAKER='%MUSE_TALK_DEFAULT_SPEAKER%'; Start-Process -FilePath '%BACKEND_PYTHON%' -ArgumentList '-m','uvicorn','app.main:app','--host','%BACKEND_HOST%','--port','%BACKEND_PORT%' -WorkingDirectory '%BACKEND_DIR%'" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Failed to start backend process.
    exit /b 1
)

echo [STEP] Starting frontend in background...
powershell -NoProfile -Command "Start-Process -FilePath 'npm.cmd' -ArgumentList 'run','dev','--','--host','%FRONTEND_HOST%','--port','%FRONTEND_PORT%' -WorkingDirectory '%FRONTEND_DIR%' -RedirectStandardOutput '%FRONTEND_LOG%' -RedirectStandardError '%FRONTEND_ERR_LOG%'" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Failed to start frontend process.
    exit /b 1
)

echo [STEP] Waiting for frontend on port %FRONTEND_PORT%...
call :wait_for_http "http://%FRONTEND_HOST%:%FRONTEND_PORT%" 30 "frontend"
if errorlevel 1 (
    set "FRONTEND_READY=0"
    echo [WARN] Frontend did not become ready in time.
    echo [WARN] Frontend stdout log: %FRONTEND_LOG%
    echo [WARN] Frontend stderr log: %FRONTEND_ERR_LOG%
) else (
    set "FRONTEND_READY=1"
    echo [OK] Frontend is ready.
)

echo [STEP] Waiting for backend on port %BACKEND_PORT%...
call :wait_for_http "http://%BACKEND_HOST%:%BACKEND_PORT%/api/health" 90 "backend"
if errorlevel 1 (
    set "BACKEND_READY=0"
    echo [WARN] Backend is still warming up or failed to start.
    echo [WARN] Backend stdout log: %BACKEND_LOG%
    echo [WARN] Backend stderr log: %BACKEND_ERR_LOG%
) else (
    set "BACKEND_READY=1"
    echo [OK] Backend is ready.
)

if "%FRONTEND_READY%"=="1" if "%BACKEND_READY%"=="1" (
    echo [STEP] Opening browser...
    start "" "http://%FRONTEND_HOST%:%FRONTEND_PORT%"
)

echo.
echo [INFO] Full stack restart requested successfully.
echo [INFO] Open: http://%FRONTEND_HOST%:%FRONTEND_PORT%
echo.
echo [TIP] Separate database server is not used right now.
echo [TIP] Backend stores data in backend\trainer.db ^(SQLite^).
echo [TIP] Backend startup may be slower because local STT/TTS providers are initialized during boot.
echo [TIP] Qwen/frontend logs are written to files. Backend now starts without stdout/stderr redirection because PowerShell redirection was blocking startup in this workspace.
echo [TIP] Logs: backend\qwen-tts-dev.log, backend\qwen-tts-dev.err.log, backend\musetalk-live-dev.log, backend\musetalk-live-dev.err.log, app\frontend\frontend-dev.log, app\frontend\frontend-dev.err.log
echo [TIP] Use run_local_app.bat --reset-db for a clean local DB rebuild.
echo.

endlocal
exit /b 0

:wait_for_http
set "TARGET_URL=%~1"
set "MAX_ATTEMPTS=%~2"
set "TARGET_LABEL=%~3"
set /a ATTEMPT=0

:wait_for_http_loop
set /a ATTEMPT+=1
powershell -NoProfile -Command "try { $response = Invoke-WebRequest -UseBasicParsing '%TARGET_URL%'; if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) { exit 0 } else { exit 1 } } catch { exit 1 }" >nul 2>&1
if not errorlevel 1 (
    goto :eof
)

if !ATTEMPT! geq %MAX_ATTEMPTS% (
    exit /b 1
)

timeout /t 1 /nobreak >nul
goto :wait_for_http_loop
