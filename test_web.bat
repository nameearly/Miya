@echo off
echo ================================================================================
echo                     MIYA Web 应用快速测试
echo ================================================================================
echo.

echo [1/4] 检查构建文件...
if exist "frontend\packages\web\dist\index.html" (
    echo [OK] 前端构建文件存在
) else (
    echo [ERROR] 前端构建文件不存在，请先运行构建命令
    pause
    exit /b 1
)

echo.
echo [2/4] 检查端口占用...
netstat -an | findstr ":8001" >nul
if errorlevel 1 (
    echo [WARNING] 端口 8001 未使用 (Runtime API 未启动)
) else (
    echo [OK] 端口 8001 正在使用
)

netstat -an | findstr ":8002" >nul
if errorlevel 1 (
    echo [WARNING] 端口 8002 未使用 (Web Server 未启动)
) else (
    echo [OK] 端口 8002 正在使用
)

echo.
echo [3/4] 启动服务...
echo 正在启动 Runtime API Server (端口 8001)...
start "MIYA API Server" /B python run\runtime_api_start.py
timeout /t 3 >nul

echo 正在启动 Web Server (端口 8002)...
start "MIYA Web Server" /B python webnet\web_main.py
timeout /t 2 >nul

echo.
echo [4/4] 打开浏览器...
echo 正在打开浏览器访问 http://localhost:8002
timeout /t 2 >nul
start http://localhost:8002

echo.
echo ================================================================================
echo 测试提示:
echo 1. 检查浏览器控制台 (F12) 是否有错误
echo 2. 尝试发送消息测试聊天功能
echo 3. 检查 Service Worker 是否注册成功 (Application > Service Workers)
echo 4. 检查 Network 标签中的 API 请求是否成功
echo.
echo 按 Ctrl+C 停止服务
echo ================================================================================
pause
