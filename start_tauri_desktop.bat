@echo off
title MIYA Tauri Desktop Launcher
color 0B

echo ================================================================================
echo Starting MIYA Tauri Desktop Application
echo ================================================================================
echo.

REM 设置 Rust 路径
set PATH=%USERPROFILE%\.cargo\bin;%PATH%

echo [1/4] Starting API Server...
start "MIYA API Server" /B python run\runtime_api_start.py
timeout /t 3 >nul
echo [OK] API Server started (port: 8001)

echo.
echo [2/4] Building Tauri App (first run will take longer)...
cd frontend\packages\web\src-tauri
C:\Users\luobo\.cargo\bin\cargo.exe build
if errorlevel 1 (
    echo [ERROR] Build failed
    pause
    exit /b 1
)
echo [OK] Build completed

echo.
echo [3/4] Starting Vite Dev Server...
cd ..
start "MIYA Vite Server" /B pnpm run dev
timeout /t 5 >nul
echo [OK] Vite Server started (port: 5173)

echo.
echo [4/4] Starting Tauri App...
cd src-tauri
C:\Users\luobo\.cargo\bin\cargo.exe run
cd ..\..\..

echo.
echo ================================================================================
echo Tauri Desktop App stopped
echo ================================================================================
pause
