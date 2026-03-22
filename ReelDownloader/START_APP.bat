@echo off
title Reel & Shorts Downloader
echo.
echo  ========================================
echo   Instagram Reels & YouTube Shorts
echo   Downloader  -  Starting...
echo  ========================================
echo.

REM Check if Python is available
where python >nul 2>&1
if %errorlevel% neq 0 (
    where python3 >nul 2>&1
    if %errorlevel% neq 0 (
        echo  [ERROR] Python not found. Please install Python from https://python.org
        pause
        exit /b 1
    )
    set PYTHON=python3
) else (
    set PYTHON=python
)

REM Install dependencies if needed
echo  Installing dependencies (first run may take a moment)...
%PYTHON% -m pip install flask yt-dlp --quiet

echo.
echo  ✅  Open your browser at: http://localhost:5055
echo  Press Ctrl+C to stop the app.
echo.

REM Launch the app and open browser
start "" "http://localhost:5055"
%PYTHON% app.py

pause
