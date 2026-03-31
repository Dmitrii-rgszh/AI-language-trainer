@echo off
setlocal
chcp 65001 >nul

set "ROOT_DIR=%~dp0"
cd /d "%ROOT_DIR%"

echo ==========================================
echo AI English Trainer Pro - Local Launch
echo ==========================================
echo.

if not exist "%ROOT_DIR%backend\.venv\Scripts\python.exe" (
    echo [ERROR] Backend virtualenv not found: backend\.venv
    echo Run backend setup first, then try again.
    exit /b 1
)

if not exist "%ROOT_DIR%app\frontend\node_modules" (
    echo [ERROR] Frontend dependencies not found: app\frontend\node_modules
    echo Run npm install in app\frontend, then try again.
    exit /b 1
)

if "%LLM_PROVIDER%"=="" set "LLM_PROVIDER=lmstudio"
if "%LMSTUDIO_BASE_URL%"=="" set "LMSTUDIO_BASE_URL=http://127.0.0.1:1234/v1"
if "%LMSTUDIO_MODEL%"=="" set "LMSTUDIO_MODEL=qwen/qwen3-8b"
if "%BACKEND_HOST%"=="" set "BACKEND_HOST=127.0.0.1"
if "%BACKEND_PORT%"=="" set "BACKEND_PORT=8000"
if "%FRONTEND_HOST%"=="" set "FRONTEND_HOST=127.0.0.1"
if "%FRONTEND_PORT%"=="" set "FRONTEND_PORT=4173"

echo [INFO] Backend URL:  http://%BACKEND_HOST%:%BACKEND_PORT%
echo [INFO] Frontend URL: http://%FRONTEND_HOST%:%FRONTEND_PORT%
echo [INFO] LM Studio:    %LMSTUDIO_BASE_URL%
echo [INFO] Model:        %LMSTUDIO_MODEL%
echo.

start "AI Trainer Backend" cmd /k "cd /d ""%ROOT_DIR%backend"" && set LLM_PROVIDER=%LLM_PROVIDER% && set LMSTUDIO_BASE_URL=%LMSTUDIO_BASE_URL% && set LMSTUDIO_MODEL=%LMSTUDIO_MODEL% && .venv\Scripts\python.exe -m uvicorn app.main:app --host %BACKEND_HOST% --port %BACKEND_PORT%"

start "AI Trainer Frontend" cmd /k "cd /d ""%ROOT_DIR%app\frontend"" && npm run dev -- --host %FRONTEND_HOST% --port %FRONTEND_PORT%"

echo [INFO] Launch commands sent.
echo [INFO] Wait 5-15 seconds for the services to warm up.
echo [INFO] Then open: http://%FRONTEND_HOST%:%FRONTEND_PORT%
echo.
echo [TIP] If LM Studio is not running, backend may fall back to mock/fallback behavior.
echo [TIP] Close the two opened terminal windows to stop the app.
echo.

endlocal
