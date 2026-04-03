@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul

if "%BACKEND_PORT%"=="" set "BACKEND_PORT=8000"
if "%FRONTEND_PORT%"=="" set "FRONTEND_PORT=5173"
if "%QWEN_TTS_PORT%"=="" set "QWEN_TTS_PORT=8010"
if "%MUSE_TALK_LIVE_PORT%"=="" set "MUSE_TALK_LIVE_PORT=8011"
set "LEGACY_FRONTEND_PORT=4173"

echo ==========================================
echo AI English Trainer Pro - Local Stop
echo ==========================================
echo.

call :kill_port "%BACKEND_PORT%" "backend"
call :kill_port "%QWEN_TTS_PORT%" "qwen-tts"
call :kill_port "%MUSE_TALK_LIVE_PORT%" "musetalk-live"
call :kill_port "%FRONTEND_PORT%" "frontend"

if /I not "%FRONTEND_PORT%"=="%LEGACY_FRONTEND_PORT%" (
    call :kill_port "%LEGACY_FRONTEND_PORT%" "frontend legacy"
)

echo.
echo [INFO] Stop routine finished.
echo [INFO] LM Studio was not touched.
echo.
endlocal
exit /b 0

:kill_port
set "TARGET_PORT=%~1"
set "TARGET_LABEL=%~2"
set "FOUND_ANY=0"

for /f "tokens=5" %%P in ('netstat -ano ^| findstr /r /c:":%TARGET_PORT% .*LISTENING"') do (
    set "FOUND_ANY=1"
    echo [INFO] Stopping %TARGET_LABEL% on port %TARGET_PORT% ^(PID %%P^)^...
    taskkill /PID %%P /T /F >nul 2>&1
    if errorlevel 1 (
        echo [WARN] Could not stop PID %%P on port %TARGET_PORT%.
    ) else (
        echo [OK] %TARGET_LABEL% process on port %TARGET_PORT% stopped.
    )
)

if "!FOUND_ANY!"=="0" (
    echo [INFO] No %TARGET_LABEL% process found on port %TARGET_PORT%.
)

goto :eof
