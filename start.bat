@echo off
chcp 65001 >nul
title MIYA AI Virtual Avatar System - Powered by Claude Code
color 0B

set DEFAULT_MODEL=miya-deepseek_v3_official
if not defined TERMINAL_TYPE (
    if exist .miya_terminal_type (
        set /p TERMINAL_TYPE=<.miya_terminal_type
    ) else (
        set TERMINAL_TYPE=cmd
    )
)

:main_menu
cls
echo ================================================================================
echo                          MIYA AI VIRTUAL AVATAR SYSTEM
echo                            Version 4.3.1 Dynamic Edition
echo                          Powered by Open-ClaudeCode
echo ================================================================================
echo.
echo MAIN MENU:
echo.
echo   === Core Modes ===
echo   [1] MIYA Terminal     - Claude Code with Miya Soul (Personality+Memory+Emotion)
echo   [2] QQ Client         - QQ Bot Client
echo   [3] Web Client        - Web Interface Client
echo.
echo   === Combined Startup ===
echo   [4] Full System       - QQ + Web + MIYA Terminal
echo   [5] Custom Launch     - Select services to start
echo.
echo   === System Tools ===
echo   [6] Model Bridge      - Start Miya Model Bridge (Anthropic to OpenAI)
echo   [7] MCP Setup         - Install Miya MCP dependencies
echo   [8] Diagnostics       - Check system status
echo   [9] Test Suite        - Run tests
echo.
echo   === Quick Start ===
echo   [Q] Quick Start       - Fast launch MIYA Terminal
echo   [M] Select Model      - Choose AI model
echo   [T] Select Terminal    - Choose terminal type (cmd/powershell/wt)
echo.
echo   [0] Exit              - Close launcher
echo.
echo Current model: %DEFAULT_MODEL%  -  Terminal: %TERMINAL_TYPE%
echo ================================================================================
set /p choice=Enter your choice [0-9, M, T, Q]:

if "%choice%"=="0" goto :exit
if "%choice%"=="1" goto :miya_terminal
if "%choice%"=="2" goto :qq_client
if "%choice%"=="3" goto :web_client
if "%choice%"=="4" goto :full_system
if "%choice%"=="5" goto :custom_launch
if "%choice%"=="6" goto :model_bridge
if "%choice%"=="7" goto :mcp_setup
if "%choice%"=="8" goto :diagnostics
if "%choice%"=="9" goto :testing
if /i "%choice%"=="Q" goto :quick_start
if /i "%choice%"=="M" goto :model_select
if /i "%choice%"=="T" goto :terminal_select

echo.
echo [ERROR] Invalid choice! Please enter a valid option.
pause
goto :main_menu

:exit
cls
echo ================================================================================
echo Thank you for using MIYA AI System v4.3.1 Dynamic Edition!
echo ================================================================================
timeout /t 2 >nul
exit /b 0

:model_select
cls
echo ================================================================================
echo                          SELECT MODEL
echo ================================================================================
echo.
echo Available models:
echo.
echo   [1] DeepSeek V3     - Fast, good for general tasks
echo   [2] DeepSeek R1      - Reasoning model, complex tasks  
echo   [3] Qwen 72B         - High performance, good quality
echo   [4] Qwen 7B          - Fast, lightweight
echo   [5] Claude (Real)    - Requires API key (option A from main menu)
echo.
echo   [R] Return to main menu
echo.
echo Current: %DEFAULT_MODEL%
echo ================================================================================
set /p model_choice=Select model [1-5, R]:

if "%model_choice%"=="1" set DEFAULT_MODEL=miya-deepseek_v3_official && goto :main_menu
if "%model_choice%"=="2" set DEFAULT_MODEL=miya-deepseek_r1_official && goto :main_menu
if "%model_choice%"=="3" set DEFAULT_MODEL=miya-qwen_72b && goto :main_menu
if "%model_choice%"=="4" set DEFAULT_MODEL=miya-qwen_7b && goto :main_menu
if "%model_choice%"=="5" goto :claude_api_mode
if /i "%model_choice%"=="R" goto :main_menu
goto :model_select

:terminal_select
cls
echo ================================================================================
echo                        SELECT TERMINAL TYPE
echo ================================================================================
echo.
echo Available terminal types:
echo.
echo   [1] Windows Terminal (wt)  - Recommended, better rendering
echo   [2] PowerShell             - Native Windows shell
echo   [3] cmd                    - Classic Windows command prompt
echo.
echo   [R] Return to main menu
echo.
echo Current: %TERMINAL_TYPE%
echo ================================================================================
set /p term_choice=Select terminal [1-3, R]:

if "%term_choice%"=="1" set TERMINAL_TYPE=wt && echo wt > .miya_terminal_type && goto :main_menu
if "%term_choice%"=="2" set TERMINAL_TYPE=powershell && echo powershell > .miya_terminal_type && goto :main_menu
if "%term_choice%"=="3" set TERMINAL_TYPE=cmd && echo cmd > .miya_terminal_type && goto :main_menu
if /i "%term_choice%"=="R" goto :main_menu
goto :terminal_select

:model_bridge
cls
echo ================================================================================
echo STARTING: MIYA MODEL BRIDGE
echo ================================================================================
echo.
echo This starts the Anthropic to OpenAI protocol bridge.
echo ClaudeCode will use Miya's model pool through this bridge.
echo.
echo Bridge endpoint: http://localhost:8888
echo.
echo Press Ctrl+C to stop.
echo ================================================================================
echo.
python mcpserver\model-bridge\server.py
goto :restart_prompt

:miya_terminal
cls
echo ================================================================================
echo STARTING: MIYA TERMINAL (Claude Code + Miya Soul)
echo ================================================================================
echo.
echo This mode launches Claude Code with Miya's personality, memory, and emotion.
echo ClaudeCode uses Miya's model pool via the Model Bridge.
echo.
echo Features:
echo   - Full Claude Code terminal capabilities
echo   - Miya personality system integration
echo   - Persistent memory across sessions
echo   - Dynamic emotion responses
echo   - Custom Miya-themed UI
echo   - Miya model pool (DeepSeek, Qwen, GLM, etc.)
echo.
echo MCP Tools available:
echo   - miya_get_personality   - Get current personality state
echo   - miya_switch_personality - Switch personality
echo   - miya_get_memory        - Get recent memories
echo   - miya_save_memory       - Save a memory
echo   - miya_recall            - Recall by keyword
echo   - miya_get_emotion       - Get emotion state
echo   - miya_set_emotion       - Set emotion
echo   - miya_get_status        - Get full system status
echo.
echo Press Ctrl+C to stop.
echo ================================================================================
echo.

REM Check if Claude Code CLI exists
if exist "Open-ClaudeCode\package\cli.js" (
    echo [OK] Claude Code found
) else (
    echo [ERROR] Claude Code not found at Open-ClaudeCode\package\cli.js
    echo Please ensure Open-ClaudeCode is properly set up.
    pause
    goto :main_menu
)

REM Check MCP Server
if exist "mcpserver\miya\server.py" (
    echo [OK] Miya MCP Server found
) else (
    echo [WARNING] Miya MCP Server not found at mcpserver\miya\server.py
    echo Miya soul features will not be available.
)

REM Check Model Bridge
echo [INFO] Cleaning up any existing Model Bridge processes...
if exist .miya_bridge.pid (
    for /f %%a in (.miya_bridge.pid) do (
        taskkill /F /PID %%a >nul 2>nul
    )
    del .miya_bridge.pid >nul 2>nul
)
timeout /t 1 >nul

if exist "mcpserver\model-bridge\server.py" (
    echo [OK] Miya Model Bridge found
    echo Starting Model Bridge in background...
    start "MIYA Model Bridge" /MIN /B pythonw mcpserver\model-bridge\server.py >nul 2>&1
    timeout /t 3 >nul
    echo [OK] Model Bridge started at http://localhost:8888
) else (
    echo [WARNING] Miya Model Bridge not found
)

echo.
echo Starting MIYA Terminal...
echo ================================================================================
echo Selected model: %DEFAULT_MODEL%
echo.

REM Extract model display name (remove miya- prefix)
set MODEL_DISPLAY=%DEFAULT_MODEL:miya-%

REM Launch Claude Code with Miya configuration
set ANTHROPIC_BASE_URL=http://localhost:8888
set ANTHROPIC_AUTH_TOKEN=%DEFAULT_MODEL%
set CLAUDE_CODE_SKIP_AUTH=1
set ANTHROPIC_MODEL=%DEFAULT_MODEL%
set ANTHROPIC_STREAMING=false

echo Starting MIYA Terminal in %TERMINAL_TYPE%...
echo Selected model: %MODEL_DISPLAY%
echo.

if "%TERMINAL_TYPE%"=="wt" (
    start wt -c "node Open-ClaudeCode\package\cli.js"
) else if "%TERMINAL_TYPE%"=="powershell" (
    start powershell -NoExit -Command "cd '%CD%'; node Open-ClaudeCode\package\cli.js"
) else (
    node Open-ClaudeCode\package\cli.js
)

echo.
echo Stopping background Model Bridge...
taskkill /F /FI "WINDOWTITLE eq MIYA Model Bridge" >nul 2>nul
echo [OK] Cleanup completed.
pause
goto :restart_prompt

:web_client
cls
echo ================================================================================
echo STARTING: WEB CLIENT
echo ================================================================================
echo.
echo Starting Web Interface Client...
echo.
echo Access: http://localhost:8000
echo.
echo Press Ctrl+C to stop service.
echo ================================================================================
echo.
call :check_file "webnet\web_main.py"
if errorlevel 1 goto :file_error
python webnet\web_main.py
goto :restart_prompt

:qq_client
cls
echo ================================================================================
echo STARTING: QQ CLIENT
echo ================================================================================
echo.
echo Starting QQ Bot Client...
echo.
echo Press Ctrl+C to stop service.
echo ================================================================================
echo.
call :check_file "run\qq_main.py"
if errorlevel 1 goto :file_error
python run\qq_main.py
goto :restart_prompt

:full_system
cls
echo ================================================================================
echo STARTING: FULL SYSTEM
echo ================================================================================
echo.
echo This will start: Web + QQ + MIYA Terminal
echo.
echo Services:
echo   1. Web Service (port 8000)
echo   2. QQ Client
echo   3. MIYA Terminal (Claude Code + Miya Soul + Model Bridge)
echo.
echo Access URLs:
echo   Web: http://localhost:8000
echo   Bridge: http://localhost:8888
echo.
echo Press Ctrl+C in terminal window to stop all services.
echo ================================================================================
echo.

echo [1/4] Starting Model Bridge...
call :check_file "mcpserver\model-bridge\server.py"
if not errorlevel 1 (
    start "MIYA Model Bridge" /B python mcpserver\model-bridge\server.py
    timeout /t 3 >nul
    echo [OK] Model Bridge started
)

echo [2/4] Starting Web Service...
call :check_file "webnet\web_main.py"
if not errorlevel 1 (
    start "MIYA Web" /B python webnet\web_main.py
    timeout /t 2 >nul
    echo [OK] Web Service started
)

echo [3/4] Starting QQ Client...
call :check_file "run\qq_main.py"
if not errorlevel 1 (
    start "MIYA QQ" /B python run\qq_main.py
    timeout /t 2 >nul
    echo [OK] QQ Client started
)

echo [4/4] Starting MIYA Terminal (in current window)...
echo.
echo ================================================================================
echo MIYA Terminal starting...
echo Selected model: %DEFAULT_MODEL%
echo.
set ANTHROPIC_BASE_URL=http://localhost:8888
set ANTHROPIC_AUTH_TOKEN=%DEFAULT_MODEL%
set CLAUDE_CODE_SKIP_AUTH=1
set ANTHROPIC_MODEL=%DEFAULT_MODEL%
set ANTHROPIC_STREAMING=false

set MODEL_DISPLAY=%DEFAULT_MODEL:miya-%
echo Starting MIYA Terminal in %TERMINAL_TYPE%...

if "%TERMINAL_TYPE%"=="wt" (
    start wt -c "node Open-ClaudeCode\package\cli.js"
) else if "%TERMINAL_TYPE%"=="powershell" (
    start powershell -NoExit -Command "cd '%CD%'; node Open-ClaudeCode\package\cli.js"
) else (
    node Open-ClaudeCode\package\cli.js
)

echo.
echo Stopping background services...
taskkill /F /FI "WINDOWTITLE eq MIYA Model Bridge" >nul 2>nul
taskkill /F /FI "WINDOWTITLE eq MIYA Web" >nul 2>nul
taskkill /F /FI "WINDOWTITLE eq MIYA QQ" >nul 2>nul
echo [OK] All services stopped
goto :restart_prompt

:mcp_setup
cls
echo ================================================================================
echo MIYA MCP SETUP
echo ================================================================================
echo.
echo Installing Miya MCP Server and Model Bridge dependencies...
echo.

echo [1/4] Checking Python...
python --version
if errorlevel 1 (
    echo [ERROR] Python not found!
    pause
    goto :main_menu
)

echo.
echo [2/4] Installing MCP SDK...
pip install mcp
if errorlevel 1 (
    echo [WARNING] Failed to install MCP SDK
    echo You can try: pip install mcp --user
)

echo.
echo [3/4] Installing FastAPI and Uvicorn (for Model Bridge)...
pip install fastapi uvicorn httpx
if errorlevel 1 (
    echo [WARNING] Failed to install FastAPI/Uvicorn
)

echo.
echo [4/4] Installing PyYAML...
pip install pyyaml
if errorlevel 1 (
    echo [WARNING] Failed to install PyYAML
)

echo.
echo [OK] MCP Setup completed!
echo.
echo MCP Server location: mcpserver\miya\server.py
echo Model Bridge location: mcpserver\model-bridge\server.py
echo MCP Config: .mcp.json
echo.
pause
goto :main_menu

:diagnostics
cls
echo ================================================================================
echo SYSTEM DIAGNOSTICS
echo ================================================================================
echo.

echo [1/7] Python Environment:
python --version 2>nul && echo   [OK] Python found || echo   [ERROR] Python not found
echo.

echo [2/7] Node.js Environment:
node --version 2>nul && echo   [OK] Node.js found || echo   [WARNING] Node.js not found
echo.

echo [3/7] Claude Code:
if exist "Open-ClaudeCode\package\cli.js" (
    echo   [OK] Claude Code found
) else (
    echo   [ERROR] Claude Code not found
)
echo.

echo [4/7] Miya MCP Server:
if exist "mcpserver\miya\server.py" (
    echo   [OK] Miya MCP Server found
) else (
    echo   [ERROR] Miya MCP Server not found
)
echo.

echo [5/7] Miya Model Bridge:
if exist "mcpserver\model-bridge\server.py" (
    echo   [OK] Miya Model Bridge found
) else (
    echo   [ERROR] Miya Model Bridge not found
)
echo.

echo [6/7] MCP Config:
if exist ".mcp.json" (
    echo   [OK] .mcp.json found
) else (
    echo   [ERROR] .mcp.json not found
)
echo.

echo [7/7] Claude Code Config:
if exist ".claude\settings.json" (
    echo   [OK] .claude\settings.json found
) else (
    echo   [WARNING] .claude\settings.json not found
)
echo.

echo Critical Miya Files:
call :check_file "config\miya_ultimate_config.json" && echo   [OK] Ultimate Config || echo   [MISSING] Ultimate Config
call :check_file "config\multi_model_config.json" && echo   [OK] Multi Model Config || echo   [MISSING] Multi Model Config
call :check_file "config\personalities\_default.yaml" && echo   [OK] Default Personality || echo   [MISSING] Default Personality
call :check_file ".miya\database.db" && echo   [OK] Database || echo   [MISSING] Database
echo.

pause
goto :main_menu

:testing
cls
echo ================================================================================
echo TESTING SUITE
echo ================================================================================
echo.
echo [1] Run All Tests
echo [2] Unit Tests Only
echo [3] Back to Main Menu
echo.
set /p test_choice=Select test type [1-3]:

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

if "%test_choice%"=="3" goto :main_menu
goto :testing

:quick_start
cls
echo ================================================================================
echo QUICK START: MIYA TERMINAL
echo ================================================================================
echo.
echo Fast startup of Claude Code with Miya Soul and Model Bridge...
echo.

REM Start Model Bridge
if exist "mcpserver\model-bridge\server.py" (
    echo Starting Model Bridge...
    start "MIYA Model Bridge" /B python mcpserver\model-bridge\server.py
    timeout /t 3 >nul
    echo [OK] Model Bridge started
)

set ANTHROPIC_BASE_URL=http://localhost:8888
set ANTHROPIC_AUTH_TOKEN=%DEFAULT_MODEL%
set CLAUDE_CODE_SKIP_AUTH=1
set CLAUDE_CODE_ENTRYPOINT=local
set ANTHROPIC_MODEL=%DEFAULT_MODEL%
set ANTHROPIC_STREAMING=false

set MODEL_DISPLAY=%DEFAULT_MODEL:miya-%
echo Starting MIYA Terminal in %TERMINAL_TYPE%...

if "%TERMINAL_TYPE%"=="wt" (
    start wt -c "node Open-ClaudeCode\package\cli.js --settings .claude\settings.json"
) else if "%TERMINAL_TYPE%"=="powershell" (
    start powershell -NoExit -Command "cd '%CD%'; node Open-ClaudeCode\package\cli.js --settings .claude\settings.json"
) else (
    node Open-ClaudeCode\package\cli.js --settings .claude\settings.json
)

echo.
echo Stopping background Model Bridge...
taskkill /F /FI "WINDOWTITLE eq MIYA Model Bridge" >nul 2>nul
echo [OK] Cleanup completed.
goto :restart_prompt

:custom_launch
cls
echo ================================================================================
echo CUSTOM LAUNCH - Select Services to Start
echo ================================================================================
echo.
echo Select services to start (space-separated numbers):
echo.
echo   [1] MIYA Terminal     - Claude Code + Miya Soul
echo   [2] Web Service       - Web Interface
echo   [3] QQ Client         - QQ Bot
echo   [4] Model Bridge      - Anthropic to OpenAI Bridge
echo.
echo Example: 1 4 (Start Terminal + Model Bridge)
echo.
set /p service_choice=Enter service numbers (space-separated):

echo.
echo You selected: %service_choice%
echo.

if "%service_choice:4=%" neq "%service_choice%" (
    echo [1/4] Starting Model Bridge...
    start "MIYA Model Bridge" /B python mcpserver\model-bridge\server.py
    timeout /t 3 >nul
    echo [OK] Model Bridge started
    set ANTHROPIC_BASE_URL=http://localhost:8888
    set ANTHROPIC_AUTH_TOKEN=%DEFAULT_MODEL%
    set CLAUDE_CODE_SKIP_AUTH=1
    set ANTHROPIC_MODEL=%DEFAULT_MODEL%
    set ANTHROPIC_STREAMING=false
)

if "%service_choice:1=%" neq "%service_choice%" (
    echo [2/4] Starting MIYA Terminal...
    set MODEL_DISPLAY=%DEFAULT_MODEL:miya-%
    start "MIYA - %MODEL_DISPLAY%" /B cmd /c "set ANTHROPIC_BASE_URL=http://localhost:8888 && set ANTHROPIC_AUTH_TOKEN=%DEFAULT_MODEL% && set CLAUDE_CODE_SKIP_AUTH=1 && set ANTHROPIC_MODEL=%DEFAULT_MODEL% && title MIYA - %MODEL_DISPLAY% && node Open-ClaudeCode\package\cli.js"
    timeout /t 2 >nul
    echo [OK] MIYA Terminal started in new window
)

if "%service_choice:2=%" neq "%service_choice%" (
    echo [3/4] Starting Web Service...
    call :check_file "webnet\web_main.py"
    if not errorlevel 1 (
        start "MIYA Web" /B python webnet\web_main.py
        timeout /t 1 >nul
        echo [OK] Web Service started
    )
)

if "%service_choice:3=%" neq "%service_choice%" (
    echo [4/4] Starting QQ Client...
    call :check_file "run\qq_main.py"
    if not errorlevel 1 (
        start "MIYA QQ" /B python run\qq_main.py
        timeout /t 1 >nul
        echo [OK] QQ Client started
    )
)

echo.
echo [SUMMARY] Services started
pause
goto :main_menu

:claude_api_mode
cls
echo ================================================================================
echo CLAUDE API MODE
echo ================================================================================
echo.
echo This mode uses the real Claude API for full Claude Code capabilities.
echo You need to have ANTHROPIC_API_KEY set in your environment.
echo.
echo IMPORTANT: This requires an Anthropic API key.
echo Set it with: set ANTHROPIC_API_KEY=sk-ant-api03-xxx...
echo.
echo Features:
echo   - Full Claude Code terminal capabilities
echo   - Best code analysis and reasoning
echo.
echo ================================================================================
echo.

if defined ANTHROPIC_API_KEY (
    echo [OK] Claude API key detected
    set DEFAULT_MODEL=miya-claude_sonnet
    goto :miya_terminal
) else (
    echo [ERROR] No Claude API key found!
    echo Please set ANTHROPIC_API_KEY environment variable
    echo Example: set ANTHROPIC_API_KEY=sk-ant-api03-xxx...
    echo.
    pause
    goto :model_select
)

goto :model_select

:end_of_file

REM Check if Claude Code CLI exists
if exist "Open-ClaudeCode\package\cli.js" (
    echo [OK] Claude Code found
) else (
    echo [ERROR] Claude Code not found at Open-ClaudeCode\package\cli.js
    pause
    goto :main_menu
)

REM Check Model Bridge
echo [INFO] Cleaning up any existing Model Bridge processes...
if exist .miya_bridge.pid (
    for /f %%a in (.miya_bridge.pid) do (
        taskkill /F /PID %%a >nul 2>nul
    )
    del .miya_bridge.pid >nul 2>nul
)
timeout /t 1 >nul

if exist "mcpserver\model-bridge\server.py" (
    echo [OK] Miya Model Bridge found
    echo Starting Model Bridge in background...
    start "MIYA Model Bridge" /MIN /B pythonw mcpserver\model-bridge\server.py >nul 2>&1
    timeout /t 3 >nul
    echo [OK] Model Bridge started at http://localhost:8888
) else (
    echo [WARNING] Miya Model Bridge not found
)

echo.
echo Starting MIYA Terminal (Chinese Models)...
echo Selected model: %DEFAULT_MODEL%
echo.

set ANTHROPIC_BASE_URL=http://localhost:8888
set ANTHROPIC_AUTH_TOKEN=%DEFAULT_MODEL%
set CLAUDE_CODE_SKIP_AUTH=1
set ANTHROPIC_MODEL=%DEFAULT_MODEL%
set ANTHROPIC_STREAMING=false

set MODEL_DISPLAY=%DEFAULT_MODEL:miya-%
title MIYA - %MODEL_DISPLAY%

echo Starting Claude Code with Miya Model Bridge (Chinese Models)...
echo.
node Open-ClaudeCode\package\cli.js

echo.
echo Stopping background Model Bridge...
taskkill /F /FI "WINDOWTITLE eq MIYA Model Bridge" >nul 2>nul
echo [OK] Cleanup completed.
goto :restart_prompt

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
echo [ERROR] Required file not found: %~1
echo.
pause
goto :restart_prompt

:check_file
if exist %~1 exit /b 0
exit /b 1
