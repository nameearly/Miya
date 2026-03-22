@echo off
echo 正在构建 Web 前端...
cd /d "%~dp0"
node node_modules\vite\bin\vite.js build --mode production
echo 构建完成！
pause
