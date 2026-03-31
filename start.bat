@echo off
title Watson Backend
setlocal enabledelayedexpansion
cd /d "%~dp0"
if exist .env (
    for /f "usebackq tokens=*" %%i in (".env") do (
        set "line=%%i"
        if not "!line:~0,1!"=="#" if not "!line!"=="" set %%i
    )
)
echo [Watson] Starting backend on http://127.0.0.1:8000
.venv\Scripts\uvicorn backend.main:app --host 127.0.0.1 --port 8000
pause
