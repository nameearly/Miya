@echo off
chcp 65001 >nul
echo ========================================
echo Miya 一键安装依赖
echo ========================================

echo.
echo [1/4] 检查 Python 版本...
python --version >nul 2>&1 || (echo [错误] 未找到 Python，请先安装 Python 3.8+ & pause & exit /b 1)

echo.
echo [2/4] 升级 pip...
python -m pip install --upgrade pip --quiet

echo.
echo [3/4] 安装 Python 依赖 (终端+QQ版)...
echo [提示] 安装核心依赖 + MCP支持 + QQ基础支持
pip install -r setup/requirements/lightweight.txt
if errorlevel 1 (
    echo [警告] 轻量级依赖安装部分失败，继续安装核心包...
)

echo.
echo [补充] 安装终端灵魂 (MCP) 和 QQ 基础依赖...
pip install mcp websockets pillow aiosqlite

if errorlevel 1 (
    echo.
    echo [错误] 核心依赖安装失败，请检查网络
    pause
    exit /b 1
)

echo.
echo [补充] 安装终端灵魂 (MCP) 和 QQ 基础依赖...
pip install mcp websockets pillow aiosqlite

if errorlevel 1 (
    echo.
    echo [错误] 核心依赖安装失败，请检查网络
    pause
    exit /b 1
)

echo.
echo [4/4] 检查 Node.js...
node --version >nul 2>&1 || (echo [警告] 未找到 Node.js，ClaudeCode 终端功能不可用)

echo.
echo ========================================
echo 安装完成！
echo ========================================
echo 下一步:
echo   1. 复制 config\.env.example 到 config\.env
echo   2. 编辑 config\.env 填入 API 密钥
echo   3. 运行 start.bat 启动
echo ========================================
pause