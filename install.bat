@echo off
chcp 65001 >nul
echo ========================================
echo Miya 一键安装依赖
echo ========================================

echo.
echo [1/3] 检查 Python 版本...
python --version || (echo 错误: 未找到 Python & pause & exit /b 1)

echo.
echo [2/3] 升级 pip...
python -m pip install --upgrade pip

echo.
echo [3/4] 安装 Python 依赖...
pip install -r requirements.txt

echo.
echo [4/4] 安装前端依赖...
where pnpm >nul 2>nul && (pnpm install) || (
    where npm >nul 2>nul && (npm install) || (
        echo 警告: 未找到 pnpm 或 npm，跳过前端依赖安装
    )
)

echo.
echo ========================================
echo 安装完成！运行: start.bat
echo ========================================
pause