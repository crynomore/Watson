@echo off
:: ──────────────────────────────────────────────────────────────────
::  Watson — one-click installer for Windows
:: ──────────────────────────────────────────────────────────────────
title Watson Installer
setlocal enabledelayedexpansion

echo.
echo  ╔══════════════════════════════════════╗
echo  ║   Watson — AI Bug Bounty Assistant   ║
echo  ╚══════════════════════════════════════╝
echo.

:: Check Python
where python >nul 2>&1 || (
    echo [ERROR] Python not found. Install from https://python.org
    pause & exit /b 1
)
echo [OK] Python found

:: Create venv
echo [Watson] Creating virtual environment...
python -m venv .venv
echo [OK] Virtual environment ready

:: Install dependencies
echo [Watson] Installing dependencies...
.venv\Scripts\pip install --quiet --upgrade pip
.venv\Scripts\pip install --quiet -r requirements.txt
echo [OK] Dependencies installed

:: Copy .env
if not exist .env (
    copy .env.example .env >nul
    echo [!] .env created — edit it and add your API key(s)
) else (
    echo [OK] .env already exists
)

:: Check for JAR
set JAR_FOUND=
for /r extension %%f in (*.jar) do (
    set JAR_FOUND=%%f
    goto :jar_done
)
:jar_done

echo.
if defined JAR_FOUND (
    echo [OK] Extension JAR found: !JAR_FOUND!
    set JAR_PATH=!JAR_FOUND!
) else (
    echo [!] No JAR found in extension\
    echo [!] Download watson-burp.jar from GitHub Releases and place it in extension\
    set JAR_PATH=extension\watson-burp.jar  (download from Releases)
)

echo.
echo  ══════════════════════════════════════════
echo    Watson installation complete!
echo  ══════════════════════════════════════════
echo.
echo  Next steps:
echo.
echo    1. Edit .env — add your API key
echo       Gemini is FREE: https://aistudio.google.com/apikey
echo.
echo    2. Start the Watson backend:
echo       start.bat
echo.
echo    3. Load the Burp extension:
echo       Burp Suite ^> Extensions ^> Add ^> Java extension
echo       File: !JAR_PATH!
echo.
pause
