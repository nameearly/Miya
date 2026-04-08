@echo off
chcp 65001 >nul
echo ========================================
echo Miya Dependency Installer
echo ========================================

echo.
echo [1/4] Checking Python version...
python --version >nul 2>&1 || (echo [ERROR] Python not found. Please install Python 3.8+ & pause & exit /b 1)

echo.
echo [2/4] Upgrading pip...
python -m pip install --upgrade pip --quiet

echo.
echo [3/4] Installing Python dependencies...
echo [INFO] Installing core packages + MCP support + QQ basic support
pip install -r setup/requirements/lightweight.txt
if errorlevel 1 (
    echo [WARNING] Some lightweight dependencies failed, continuing...
)

echo.
echo [INFO] Installing MCP and QQ core dependencies...
pip install mcp websockets pillow aiosqlite

if errorlevel 1 (
    echo.
    echo [ERROR] Core dependencies installation failed. Check network connection.
    pause
    exit /b 1
)

echo.
echo [4/4] Checking Node.js...
node --version >nul 2>&1 || (echo [WARNING] Node.js not found. ClaudeCode terminal features unavailable)

echo.
echo ========================================
echo Installation completed!
echo ========================================
echo Next steps:
echo   1. Copy config\.env.example to config\.env
echo   2. Edit config\.env with your API keys
echo   3. Run start.bat to launch
echo ========================================
pause