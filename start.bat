@echo off
title MIYA AI Launcher
color 0B

:main_menu
cls
echo ================================================================================
echo                         MIYA AI VIRTUAL AVATAR SYSTEM
echo                              Version 4.0 - Ultimate Edition
echo ================================================================================
echo.
echo MAIN MENU:
echo.
echo   === Client Startup ===
echo   [1] QQ Client         - QQ Bot Client
echo   [2] Web Client        - Web Interface Client
echo   [3] Desktop Client    - React + Electron Desktop App
echo   [4] Terminal Client   - Command Line Terminal
echo.
echo   === Combined Startup ===
echo   [5] All Clients       - QQ + Web + Desktop + Terminal (Full)
echo   [6] Web + Desktop     - Web Client + Desktop Client
echo   [7] Custom Launch     - Select services to start
echo.
echo   === System Tools ===
echo   [8] Development       - Code analysis and debugging
echo   [9] Test Suite        - Run tests
echo   [B] Build Web Frontend - Build React web interface
echo   [A] Diagnostics       - Check and troubleshoot (Enter A)
echo.
echo   === Quick Start ===
echo   [Q] Quick Start       - Fast launch full system (Enter Q)
echo.
echo   [0] Exit              - Close launcher
echo.
echo ================================================================================
set /p choice=Enter your choice [0-9, A, B, Q]:

if "%choice%"=="0" goto :exit
if "%choice%"=="1" goto :qq_client
if "%choice%"=="2" goto :web_client
if "%choice%"=="3" goto :desktop_client
if "%choice%"=="4" goto :terminal_client
if "%choice%"=="5" goto :all_clients
if "%choice%"=="6" goto :web_desktop
if "%choice%"=="7" goto :custom_launch
if "%choice%"=="8" goto :development
if "%choice%"=="9" goto :testing
if /i "%choice%"=="B" goto :build_web
if /i "%choice%"=="A" goto :diagnostics
if /i "%choice%"=="Q" goto :quick_start

echo.
echo [ERROR] Invalid choice! Please enter a number between 0 and 9, or A/Q.
pause
goto :main_menu

:exit
cls
echo ================================================================================
echo Thank you for using MIYA AI System!
echo ================================================================================
timeout /t 2 >nul
exit /b 0

:terminal
cls
echo ================================================================================
echo STARTING: TERMINAL MODE WITH API SUPPORT
echo ================================================================================
echo.
echo This mode will start both API server and terminal system
echo for full functionality.
echo.
echo Steps:
echo   1. Starting API Server (port 8001)
echo   2. Starting Terminal System
echo.
echo Features with API:
echo   - Full AI-powered terminal management
echo   - Natural language command processing
echo   - Multi-terminal coordination
echo   - Real-time monitoring and status
echo   - Web API access at http://localhost:8001
echo.
echo Press Ctrl+C to stop BOTH systems.
echo ================================================================================
echo.
echo Step 1: Checking and starting API Server...
call :check_file "run\runtime_api_start.py"
if errorlevel 1 (
    echo [WARNING] API server script not found.
    echo Terminal will run in standalone mode.
    goto :start_terminal_only
)

echo Starting API Server in background...
start "MIYA API Server" /B python run\runtime_api_start.py
timeout /t 3 >nul
echo [OK] API Server started (port: 8001)
echo.

:start_terminal_only
echo Step 2: Starting Terminal System...
call :check_file "run\multi_terminal_main_v2.py"
if errorlevel 1 goto :file_error

echo.
echo ================================================================================
echo TERMINAL SYSTEM STARTING...
echo ================================================================================
echo.
python run\multi_terminal_main_v2.py

echo.
echo ================================================================================
echo CLEANUP: Stopping background services...
echo ================================================================================
echo.
taskkill /F /FI "WINDOWTITLE eq MIYA API Server" >nul 2>nul
echo [OK] API Server stopped.
goto :restart_prompt

:web
cls
echo ================================================================================
echo STARTING: WEB MODE
echo ================================================================================
echo.
echo Launching Web interface and management system...
echo.
echo Access: http://localhost:8000
echo.
echo Features:
echo   - Web-based management interface
echo   - API endpoints
echo   - Real-time monitoring dashboard
echo   - System configuration
echo.
echo Press Ctrl+C to stop the system.
echo ================================================================================
echo.
call :check_file "webnet\web_main.py"
if errorlevel 1 goto :file_error
python webnet\web_main.py
goto :restart_prompt

:api
cls
echo ================================================================================
echo STARTING: API MODE
echo ================================================================================
echo.
echo Launching API server...
echo.
echo Access: http://localhost:8001
echo API Docs: http://localhost:8001/docs
echo.
echo Features:
echo   - RESTful API endpoints
echo   - Swagger documentation
echo   - System status API
echo   - Integration interface
echo.
echo Press Ctrl+C to stop the system.
echo ================================================================================
echo.
call :check_file "run\runtime_api_start.py"
if errorlevel 1 goto :file_error
python run\runtime_api_start.py
goto :restart_prompt

:full_system
cls
echo ================================================================================
echo STARTING: FULL SYSTEM
echo ================================================================================
echo.
echo Launching complete MIYA AI system...
echo This will start: Terminal + Web + API
echo.
echo Services starting:
echo   1. API Server (port 8001)
echo   2. Web Interface (port 8000)
echo   3. Terminal System
echo.
echo Access URLs:
echo   Web:    http://localhost:8000
echo   API:    http://localhost:8001
echo   Docs:   http://localhost:8001/docs
echo.
echo Press Ctrl+C to stop ALL services.
echo ================================================================================
echo.
setlocal enabledelayedexpansion
set services_started=0
set processes=

echo Starting API Server...
call :check_file "run\runtime_api_start.py"
if not errorlevel 1 (
    start "MIYA API" /B python run\runtime_api_start.py
    set /a services_started+=1
    set processes=!processes! api
    timeout /t 3 >nul
    echo [OK] API Server started (port 8001)
)

echo Starting Web Service...
call :check_file "webnet\web_main.py"
if not errorlevel 1 (
    start "MIYA Web" /B python webnet\web_main.py
    set /a services_started+=1
    set processes=!processes! web
    timeout /t 2 >nul
    echo [OK] Web Service started (port 8000)
)

echo Starting Terminal System...
call :check_file "run\multi_terminal_main_v2.py"
if not errorlevel 1 (
    echo [OK] Terminal System ready
)

echo.
echo ================================================================================
echo SYSTEM STATUS:
echo   Services started: !services_started!/3
echo.
if !services_started! gtr 0 (
    echo System is running! Access the services above.
    echo.
    echo To stop all services, press Ctrl+C in THIS window.
) else (
    echo [WARNING] No services started. Check file paths.
)

echo.
echo Starting Terminal System in THIS window...
echo ================================================================================
echo.
if not errorlevel 1 (
    python run\multi_terminal_main_v2.py
)

echo.
echo Stopping all background services...
taskkill /F /FI "WINDOWTITLE eq MIYA API" >nul 2>nul
taskkill /F /FI "WINDOWTITLE eq MIYA Web" >nul 2>nul
echo [OK] All services stopped.
goto :restart_prompt

:development
cls
echo ================================================================================
echo DEVELOPMENT TOOLS
echo ================================================================================
echo.
echo [1] Debug Mode          - Terminal with debug info
echo [2] Code Analysis       - Run code checks
echo [3] Dependency Check    - Verify packages
echo [4] Back to Main Menu
echo.
set /p dev_choice=Select tool [1-4]: 

if "%dev_choice%"=="1" (
    cls
    echo ================================================================================
    echo DEBUG MODE: Terminal with full debugging
    echo ================================================================================
    echo.
    python run\multi_terminal_main_v2.py --debug
    goto :restart_prompt
)

if "%dev_choice%"=="2" (
    cls
    echo ================================================================================
    echo CODE ANALYSIS
    echo ================================================================================
    echo.
    echo Running code checks...
    python -m pylint core\ --exit-zero
    pause
    goto :development
)

if "%dev_choice%"=="3" (
    cls
    echo ================================================================================
    echo DEPENDENCY CHECK
    echo ================================================================================
    echo.
    echo Checking installed packages...
    pip list
    echo.
    echo Required packages from requirements.txt:
    type requirements.txt
    pause
    goto :development
)

if "%dev_choice%"=="4" goto :main_menu
goto :development

:testing
cls
echo ================================================================================
echo TESTING SUITE
echo ================================================================================
echo.
echo [1] Run All Tests       - Complete test suite
echo [2] Unit Tests Only     - Core functionality tests
echo [3] Performance Tests   - Benchmark and performance
echo [4] Quick Test          - Fast basic test
echo [5] Back to Main Menu
echo.
set /p test_choice=Select test type [1-5]: 

if "%test_choice%"=="1" (
    cls
    echo ================================================================================
    echo RUNNING ALL TESTS
    echo ================================================================================
    echo.
    python -m pytest tests\ -v
    pause
    goto :testing
)

if "%test_choice%"=="2" (
    cls
    echo ================================================================================
    echo UNIT TESTS
    echo ================================================================================
    echo.
    python -m pytest tests\unit\ -v
    pause
    goto :testing
)

if "%test_choice%"=="3" (
    cls
    echo ================================================================================
    echo PERFORMANCE TESTS
    echo ================================================================================
    echo.
    python -m pytest tests\ --benchmark-only
    pause
    goto :testing
)

if "%test_choice%"=="4" (
    cls
    echo ================================================================================
    echo QUICK TEST
    echo ================================================================================
    echo.
    python test_simple.py
    pause
    goto :testing
)


if "%test_choice%"=="5" goto :main_menu
goto :testing

:build_web
cls
echo ================================================================================
echo BUILDING: WEB FRONTEND
echo ================================================================================
echo.
echo This will build the React web frontend.
echo.
echo Prerequisites:
echo   - Node.js 18+ installed
echo   - npm 9+ installed
echo.
echo This process may take a few minutes...
echo.
echo Press any key to continue or Ctrl+C to cancel...
pause >nul
cls
echo ================================================================================
echo BUILDING REACT WEB FRONTEND
echo ================================================================================
echo.

echo [1/4] Checking prerequisites...
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found!
    echo Please install Node.js from: https://nodejs.org/
    pause
    goto :main_menu
)
echo [OK] Node.js found

echo.
echo [2/4] Running build script...
call :check_file "scripts\build_web_frontend.ps1"
if not errorlevel 1 (
    powershell -ExecutionPolicy Bypass -File scripts\build_web_frontend.ps1
) else (
    echo [ERROR] Build script not found: scripts\build_web_frontend.ps1
    pause
)

echo.
goto :restart_prompt

:diagnostics
cls
echo ================================================================================
echo SYSTEM DIAGNOSTICS
echo ================================================================================
echo.
echo [1] System Check        - Basic environment check
echo [2] File Verification   - Check critical files
echo [3] Port Check          - Verify service ports
echo [4] Python Check        - Python environment
echo [5] Quick Fix           - Auto-fix common issues
echo [6] Back to Main Menu
echo.
set /p diag_choice=Select diagnostic [1-6]: 

if "%diag_choice%"=="1" (
    call :system_check
    pause
    goto :diagnostics
)

if "%diag_choice%"=="2" (
    call :file_check
    pause
    goto :diagnostics
)

if "%diag_choice%"=="3" (
    call :port_check
    pause
    goto :diagnostics
)

if "%diag_choice%"=="4" (
    call :python_check
    pause
    goto :diagnostics
)

if "%diag_choice%"=="5" (
    call :quick_fix
    pause
    goto :diagnostics
)

if "%diag_choice%"=="6" goto :main_menu
goto :diagnostics

:quick_start
cls
echo ================================================================================
echo QUICK START: TERMINAL + API
echo ================================================================================
echo.
echo Fast startup with API support for full functionality...
echo.
echo Starting API Server in background...
call :check_file "run\runtime_api_start.py"
if not errorlevel 1 (
    start "MIYA API Server" /B python run\runtime_api_start.py
    timeout /t 2 >nul
    echo [OK] API Server started (port: 8001)
)

echo.
echo Starting Terminal System...
echo.
python run\multi_terminal_main_v2.py

echo.
echo Stopping background API Server...
taskkill /F /FI "WINDOWTITLE eq MIYA API Server" >nul 2>nul
echo [OK] Cleanup completed.
goto :restart_prompt

:multi_service
cls
echo ================================================================================
echo MULTI-SERVICE SELECTION
echo ================================================================================
echo.
echo Select services to start (comma-separated numbers):
echo.
echo   1. Terminal System
echo   2. Web Service
echo   3. API Server
echo.
echo Example: 1,3  (for Terminal + API)
echo.
set /p service_choice=Select services: 

setlocal enabledelayedexpansion
set services_started=0

if "!service_choice:1=!" neq "%service_choice%" (
    echo.
    echo Starting Terminal System...
    start "MIYA Terminal" /B python run\multi_terminal_main_v2.py
    set /a services_started+=1
    timeout /t 1 >nul
)

if "!service_choice:2=!" neq "%service_choice%" (
    echo Starting Web Service...
    start "MIYA Web" /B python webnet\web_main.py
    set /a services_started+=1
    timeout /t 1 >nul
)

if "!service_choice:3=!" neq "%service_choice%" (
    echo Starting API Server...
    start "MIYA API" /B python run\runtime_api_start.py
    set /a services_started+=1
    timeout /t 1 >nul
)

echo.
echo ================================================================================
echo SERVICES STARTED: !services_started!
echo.
if !services_started! gtr 0 (
    echo Services are running in background.
    echo.
    echo To stop services:
    echo   1. Close the service windows manually, OR
    echo   2. Run: taskkill /FI "WINDOWTITLE eq MIYA*"
) else (
    echo No services started.
)

echo.
pause
goto :main_menu

:restart_prompt
echo.
echo ================================================================================
echo.
set /p restart=Return to main menu? (Y/N): 
if /i "%restart%"=="Y" goto :main_menu
if /i "%restart%"=="y" goto :main_menu
echo.
echo Goodbye!
timeout /t 2 >nul
exit /b 0

:file_error
echo.
echo [ERROR] Required file not found!
echo Please check that the file exists: %~1
echo.
pause
goto :restart_prompt

:check_file
if exist %~1 exit /b 0
exit /b 1

:system_check
echo.
echo SYSTEM CHECK:
echo ============
python -c "import sys; print('Python:', sys.version); import os; print('Directory:', os.getcwd())"
echo.
echo Critical files:
call :check_file "run\multi_terminal_main_v2.py" && echo [OK] Terminal script || echo [MISSING] Terminal script
call :check_file "core\project_types.py" && echo [OK] Core types || echo [MISSING] Core types
call :check_file "webnet\web_main.py" && echo [OK] Web script || echo [MISSING] Web script
call :check_file "run\runtime_api_start.py" && echo [OK] API script || echo [MISSING] API script
exit /b 0

:file_check
echo.
echo FILE VERIFICATION:
echo =================
for %%f in (
    run\multi_terminal_main_v2.py
    core\project_types.py
    core\terminal_agent.py
    core\error_handler.py
    webnet\web_main.py
    run\runtime_api_start.py
    requirements.txt
    start.bat
) do (
    if exist %%f (
        echo [OK] %%f
    ) else (
        echo [MISSING] %%f
    )
)
exit /b 0

:port_check
echo.
echo PORT CHECK:
echo ===========
echo Checking if ports are available...
for %%p in (8000 8001 8080) do (
    netstat -an | findstr ":%%p " >nul
    if errorlevel 1 (
        echo [FREE] Port %%p
    ) else (
        echo [IN USE] Port %%p
    )
)
exit /b 0

:python_check
echo.
echo PYTHON ENVIRONMENT:
echo ==================
python --version
echo.
echo Python path:
where python
echo.
echo Installed packages:
python -c "import pkgutil; packages = [name for _, name, _ in pkgutil.iter_modules()]; print('Total:', len(packages), 'packages')"
exit /b 0

:qq_client
cls
echo ================================================================================
echo STARTING: QQ CLIENT
echo ================================================================================
echo.
echo Starting QQ Bot Client...
echo.
echo Note: Ports will be automatically selected if default ports are busy
echo.
echo Press Ctrl+C to stop service
echo ================================================================================
echo.

REM Start API Server
call :check_file "run\runtime_api_start.py"
if not errorlevel 1 (
    echo Starting API Server...
    start "MIYA API Server" /B python run\runtime_api_start.py
    timeout /t 3 >nul
    echo [OK] API Server started
)

echo.
echo [NOTE] Starting QQ Bot from run\qq_main.py...
echo.

REM Start QQ Bot
call :check_file "run\qq_main.py"
if not errorlevel 1 (
    python run\qq_main.py
) else (
    echo [ERROR] QQ Bot script not found: run\qq_main.py
    echo [ERROR] Please ensure the file exists
    pause
)

goto :restart_prompt

:web_client
cls
echo ================================================================================
echo STARTING: WEB CLIENT
echo ================================================================================
echo.
echo Starting Web Interface Client with full AI functionality...
echo.
echo Access: http://localhost:8001
echo.
echo Features:
echo   - Web-based chat interface
echo   - Full AI integration (memory, personality, emotion)
echo   - Real-time responses
echo.
echo Press Ctrl+C to stop service
echo ================================================================================
echo.
echo Step 1: Starting API Server...
call :check_file "run\runtime_api_start.py"
if not errorlevel 1 (
    start "MIYA API Server" /B python run\runtime_api_start.py
    timeout /t 3 >nul
    echo [OK] API Server started (port: 8001)
)
echo.
echo Step 2: Starting Web Client...
call :check_file "webnet\web_main.py"
if not errorlevel 1 (
    python webnet\web_main.py
) else (
    echo [ERROR] Web Client script not found
)
echo.
echo Stopping background API Server...
taskkill /F /FI "WINDOWTITLE eq MIYA API Server" >nul 2>nul
echo [OK] API Server stopped
goto :restart_prompt

:desktop_client
cls
echo ================================================================================
echo STARTING: DESKTOP CLIENT (Tauri)
echo ================================================================================
echo.
echo Starting Tauri Desktop Application...
echo.
echo Prerequisites:
echo   - Node.js 18+ installed
echo   - Rust toolchain installed
echo   - Tauri CLI installed
echo.
echo Steps:
echo   1. Start API Server
echo   2. Build Tauri App (first run will take longer)
echo   3. Start Vite Dev Server
echo   4. Launch Tauri Desktop Window
echo.
echo Press Ctrl+C to stop service
echo ================================================================================
echo.
call start_tauri_desktop.bat
goto :restart_prompt

:terminal_client
cls
echo ================================================================================
echo STARTING: TERMINAL CLIENT
echo ================================================================================
echo.
echo Starting Command Line Terminal...
echo.
echo Features:
echo   - AI-driven terminal management
echo   - Natural language command processing
echo   - Multi-terminal coordination
echo   - Real-time monitoring and status
echo   - Web API Access: http://localhost:8001
echo.
echo Press Ctrl+C to stop service
echo ================================================================================
echo.
echo Step 1: Starting API Server...
call :check_file "run\runtime_api_start.py"
if not errorlevel 1 (
    start "MIYA API Server" /B python run\runtime_api_start.py
    timeout /t 3 >nul
    echo [OK] API Server started (port: 8001)
)
echo.
echo Step 2: Starting Terminal System...
call :check_file "run\multi_terminal_main_v2.py"
if not errorlevel 1 (
    echo.
    echo ================================================================================
    echo Terminal System starting...
    echo ================================================================================
    echo.
    python run\multi_terminal_main_v2.py
) else (
    goto :file_error
)
echo.
echo Stopping background services...
taskkill /F /FI "WINDOWTITLE eq MIYA API Server" >nul 2>nul
echo [OK] API Server stopped
goto :restart_prompt

:all_clients
cls
echo ================================================================================
echo STARTING: ALL CLIENTS (QQ + Web + Desktop + Terminal)
echo ================================================================================
echo.
echo Starting all clients simultaneously...
echo.
echo Service list:
echo   1. API Server (port 8001)
echo   2. Web Service (port 8000)
echo   3. QQ Client
echo   4. Desktop Client
echo   5. Terminal System
echo.
echo Access URLs:
echo   Web:     http://localhost:8000
echo   API:     http://localhost:8001
echo   Docs:    http://localhost:8001/docs
echo.
echo Press Ctrl+C in terminal window to stop all services
echo ================================================================================
echo.
setlocal enabledelayedexpansion
set services_started=0

echo [1/5] Starting API Server...
call :check_file "run\runtime_api_start.py"
if not errorlevel 1 (
    start "MIYA API Server" /B python run\runtime_api_start.py
    set /a services_started+=1
    timeout /t 2 >nul
    echo [OK] API Server started
)

echo [2/5] Starting Web Service...
call :check_file "webnet\web_main.py"
if not errorlevel 1 (
    start "MIYA Web" /B python webnet\web_main.py
    set /a services_started+=1
    timeout /t 1 >nul
    echo [OK] Web Service started
)

echo [3/5] Preparing QQ Client...
echo [NOTE] QQ Client requires separate configuration
call :check_file "core\qq_bot.py"
if not errorlevel 1 (
    echo [OK] QQ Client script found
    echo [NOTE] To start QQ Client, run: python core\qq_bot.py
)

echo [4/5] Preparing Desktop Client...
echo [NOTE] Desktop Client will start below
call :check_file "frontend\packages\desktop\package.json"
if not errorlevel 1 (
    start "MIYA Desktop" /B cmd /c "cd frontend\packages\desktop && npm run dev"
    set /a services_started+=1
    timeout /t 1 >nul
    echo [OK] Desktop Client started
)

echo [5/5] Starting Terminal System (in current window)...
call :check_file "run\multi_terminal_main_v2.py"
if not errorlevel 1 (
    echo.
    echo ================================================================================
    echo Terminal System starting...
    echo ================================================================================
    echo.
    echo System status:
    echo   Services started: !services_started!/5
    echo.
    echo Tips:
    echo   - Web and API services running in background
    echo   - Desktop Client running in new window
    echo   - Current window is Terminal System
    echo   - Press Ctrl+C to stop all background services
    echo.
    python run\multi_terminal_main_v2.py
)

echo.
echo Stopping all background services...
taskkill /F /FI "WINDOWTITLE eq MIYA API*" >nul 2>nul
taskkill /F /FI "WINDOWTITLE eq MIYA Web" >nul 2>nul
taskkill /F /FI "WINDOWTITLE eq MIYA Desktop" >nul 2>nul
echo [OK] All services stopped
goto :restart_prompt

:web_desktop
cls
echo ================================================================================
echo STARTING: WEB + DESKTOP CLIENT
echo ================================================================================
echo.
echo Starting Web Client and Desktop Client simultaneously...
echo.
echo Service list:
echo   1. API Server (port 8001)
echo   2. Web Service (port 8000)
echo   3. Desktop Client
echo.
echo Access URLs:
echo   Web:     http://localhost:8000
echo   API:     http://localhost:8001
echo.
echo Press Ctrl+C in terminal window to stop all services
echo ================================================================================
echo.
setlocal enabledelayedexpansion

echo [1/3] Starting API Server...
call :check_file "run\runtime_api_start.py"
if not errorlevel 1 (
    start "MIYA API Server" /B python run\runtime_api_start.py
    timeout /t 2 >nul
    echo [OK] API Server started
)

echo [2/3] Starting Web Service...
call :check_file "webnet\web_main.py"
if not errorlevel 1 (
    start "MIYA Web" /B python webnet\web_main.py
    timeout /t 1 >nul
    echo [OK] Web Service started
)

echo [3/3] Starting Desktop Client...
call :check_file "frontend\packages\desktop\package.json"
if not errorlevel 1 (
    start "MIYA Desktop" /B cmd /c "cd frontend\packages\desktop && npm run dev"
    timeout /t 1 >nul
    echo [OK] Desktop Client started
)

echo.
echo [NOTE] All services started in background
echo [NOTE] Press Ctrl+C to stop all services
echo.
pause

echo.
echo Stopping all services...
taskkill /F /FI "WINDOWTITLE eq MIYA API*" >nul 2>nul
taskkill /F /FI "WINDOWTITLE eq MIYA Web" >nul 2>nul
taskkill /F /FI "WINDOWTITLE eq MIYA Desktop" >nul 2>nul
echo [OK] All services stopped
goto :restart_prompt

:custom_launch
cls
echo ================================================================================
echo CUSTOM LAUNCH - Select Services to Start
echo ================================================================================
echo.
echo Select services to start (separate multiple with spaces):
echo.
echo   [1] API Server      - API Service (must start first)
echo   [2] Web Service     - Web Interface
echo   [3] QQ Client       - QQ Bot
echo   [4] Desktop Client  - React Desktop App
echo   [5] Terminal System - Command Line Terminal
echo.
echo Example: 1 2 4 (Start API + Web + Desktop)
echo.
set /p service_choice=Enter service numbers (space-separated):

echo.
echo You selected: !service_choice!
echo.
setlocal enabledelayedexpansion
set count=0

if "!service_choice:1=!" neq "%service_choice%" (
    echo [1/!] Starting API Server...
    call :check_file "run\runtime_api_start.py"
    if not errorlevel 1 (
        start "MIYA API Server" /B python run\runtime_api_start.py
        set /a count+=1
        timeout /t 2 >nul
        echo [OK] API Server started
    )
)

if "!service_choice:2=!" neq "%service_choice%" (
    echo [2/!] Starting Web Service...
    call :check_file "webnet\web_main.py"
    if not errorlevel 1 (
        start "MIYA Web" /B python webnet\web_main.py
        set /a count+=1
        timeout /t 1 >nul
        echo [OK] Web Service started
    )
)

if "!service_choice:3=!" neq "%service_choice%" (
    echo [3/!] Preparing QQ Client...
    call :check_file "core\qq_bot.py"
    if not errorlevel 1 (
        echo [NOTE] QQ Client script found
        echo [NOTE] Run: python core\qq_bot.py
        set /a count+=1
    )
)

if "!service_choice:4=!" neq "%service_choice%" (
    echo [4/!] Starting Desktop Client...
    call :check_file "frontend\packages\desktop\package.json"
    if not errorlevel 1 (
        start "MIYA Desktop" /B cmd /c "cd frontend\packages\desktop && npm run dev"
        set /a count+=1
        timeout /t 1 >nul
        echo [OK] Desktop Client started
    )
)

if "!service_choice:5=!" neq "%service_choice%" (
    echo [5/!] Starting Terminal System...
    call :check_file "run\multi_terminal_main_v2.py"
    if not errorlevel 1 (
        echo [OK] Terminal System started
        set /a count+=1
    )
)

echo.
echo [SUMMARY] Successfully started !count! services
echo [NOTE] Press Ctrl+C to stop all services
echo.
pause

echo.
echo Stopping all services...
taskkill /F /FI "WINDOWTITLE eq MIYA*" >nul 2>nul
echo [OK] All services stopped
goto :restart_prompt

:quick_fix
echo.
echo QUICK FIX:
echo =========
echo 1. Setting console encoding...
chcp 65001 >nul
echo 2. Checking Python...
where python >nul && echo   [OK] Python found || echo   [ERROR] Python not in PATH
echo 3. Creating backup of start.bat...
if exist start.bat.bak del start.bat.bak
if exist start.bat copy start.bat start.bat.bak >nul && echo   [OK] Backup created
echo 4. Quick fix completed.
echo.
echo If problems persist, try:
echo   - Run: python run\multi_terminal_main_v2.py (direct)
echo   - Check: python --version
echo   - Verify file paths
exit /b 0
