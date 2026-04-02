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
set "RESET_DB=0"

if /I "%~1"=="--reset-db" set "RESET_DB=1"
if /I "%~1"=="/reset-db" set "RESET_DB=1"

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
if "%LMSTUDIO_BASE_URL%"=="" set "LMSTUDIO_BASE_URL=http://127.0.0.1:1234/v1"
if "%LMSTUDIO_MODEL%"=="" set "LMSTUDIO_MODEL=qwen/qwen3-8b"
if "%BACKEND_HOST%"=="" set "BACKEND_HOST=127.0.0.1"
if "%BACKEND_PORT%"=="" set "BACKEND_PORT=8000"
if "%FRONTEND_HOST%"=="" set "FRONTEND_HOST=127.0.0.1"
if "%FRONTEND_PORT%"=="" set "FRONTEND_PORT=5173"

echo [INFO] Backend URL:  http://%BACKEND_HOST%:%BACKEND_PORT%
echo [INFO] Frontend URL: http://%FRONTEND_HOST%:%FRONTEND_PORT%
echo [INFO] SQLite DB:    %BACKEND_DIR%\trainer.db
echo [INFO] LM Studio:    %LMSTUDIO_BASE_URL%
echo [INFO] Model:        %LMSTUDIO_MODEL%
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

echo [STEP] Seeding demo user and runtime data...
"%BACKEND_PYTHON%" scripts\seed_demo_data.py
if errorlevel 1 (
    popd
    echo [ERROR] Demo data seeding failed.
    exit /b 1
)
echo [OK] Demo data is ready.
echo.

popd

echo [STEP] Resetting launch logs...
break > "%BACKEND_LOG%"
break > "%BACKEND_ERR_LOG%"
break > "%FRONTEND_LOG%"
break > "%FRONTEND_ERR_LOG%"

echo [STEP] Starting backend in background...
powershell -NoProfile -Command "$env:LLM_PROVIDER='%LLM_PROVIDER%'; $env:LMSTUDIO_BASE_URL='%LMSTUDIO_BASE_URL%'; $env:LMSTUDIO_MODEL='%LMSTUDIO_MODEL%'; Start-Process -FilePath '%BACKEND_PYTHON%' -ArgumentList '-m','uvicorn','app.main:app','--host','%BACKEND_HOST%','--port','%BACKEND_PORT%' -WorkingDirectory '%BACKEND_DIR%' -RedirectStandardOutput '%BACKEND_LOG%' -RedirectStandardError '%BACKEND_ERR_LOG%'" >nul 2>&1
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
echo [TIP] Logs: backend\backend-dev.log, backend\backend-dev.err.log, app\frontend\frontend-dev.log, app\frontend\frontend-dev.err.log
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
