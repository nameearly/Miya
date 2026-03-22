@echo off
setlocal

REM 设置工作目录
set WORK_DIR=d:\AI_MIYA_Facyory\MIYA\Miya\frontend\packages\web

echo 正在构建弥娅 Web 前端...
echo 工作目录: %WORK_DIR%
echo.

REM 切换到 Web 包目录
pushd "%WORK_DIR%"

REM 运行 Vite 构建
echo 运行 Vite 构建...
node node_modules\vite\bin\vite.js build --mode production

REM 检查构建结果
if exist "dist\index.html" (
    echo.
    echo ======================================================
    echo 构建成功！
    echo 输出目录: %WORK_DIR%\dist
    echo ======================================================
) else (
    echo.
    echo ======================================================
    echo 构建失败！
    echo ======================================================
)

REM 恢复目录
popd

pause
