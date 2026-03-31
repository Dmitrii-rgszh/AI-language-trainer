@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul

set "BACKEND_PORT=8000"
set "FRONTEND_PORT=4173"

echo ==========================================
echo AI English Trainer Pro - Local Stop
echo ==========================================
echo.

call :kill_port %BACKEND_PORT% "backend"
call :kill_port %FRONTEND_PORT% "frontend"

echo.
echo [INFO] Stop routine finished.
echo [INFO] LM Studio was not touched.
echo.
endlocal
exit /b 0

:kill_port
set "TARGET_PORT=%~1"
set "TARGET_LABEL=%~2"
set "FOUND_PID="

for /f "tokens=5" %%P in ('netstat -ano ^| findstr /r /c:":%TARGET_PORT% .*LISTENING"') do (
    set "FOUND_PID=%%P"
    goto :kill_found
)

echo [INFO] No %TARGET_LABEL% process found on port %TARGET_PORT%.
goto :eof

:kill_found
echo [INFO] Stopping %TARGET_LABEL% on port %TARGET_PORT% ^(PID !FOUND_PID!^)^...
taskkill /PID !FOUND_PID! /T /F >nul 2>&1

if errorlevel 1 (
    echo [WARN] Could not stop PID !FOUND_PID! on port %TARGET_PORT%.
) else (
    echo [OK] %TARGET_LABEL% stopped.
)

goto :eof
