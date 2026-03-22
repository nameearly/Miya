# ========================================
# Miya 快速安装脚本 (Windows PowerShell)
# ========================================
# 用途：一键安装 Miya 的所有依赖
# 使用方法：.\setup\scripts\install.ps1 [选项]
# ========================================

param(
    [switch]$Full = $true,
    [switch]$Minimal,
    [switch]$Lightweight,
    [switch]$Dev,
    [switch]$Check,
    [switch]$Upgrade,
    [switch]$Yes,
    [switch]$Help
)

# 颜色定义
$colors = @{
    Red = [ConsoleColor]::Red
    Green = [ConsoleColor]::Green
    Yellow = [ConsoleColor]::Yellow
    Blue = [ConsoleColor]::Blue
}

# 项目根目录
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $ScriptDir)

# 显示帮助信息
function Show-Help {
    Write-Host "Miya 快速安装脚本" -ForegroundColor Blue
    Write-Host ""
    Write-Host "使用方法: .\setup\scripts\install.ps1 [选项]"
    Write-Host ""
    Write-Host "选项:"
    Write-Host "  -Full          完整安装（生产环境，默认）"
    Write-Host "  -Minimal       最小安装（核心功能）"
    Write-Host "  -Lightweight   轻量级安装（无外部数据库）"
    Write-Host "  -Dev           开发环境安装"
    Write-Host "  -Check         仅检查依赖"
    Write-Host "  -Upgrade       升级已安装的依赖"
    Write-Host "  -Yes           跳过确认提示"
    Write-Host "  -Help          显示帮助信息"
    Write-Host ""
    Write-Host "示例:"
    Write-Host "  .\setup\scripts\install.ps1              # 完整安装"
    Write-Host "  .\setup\scripts\install.ps1 -Minimal     # 最小安装"
    Write-Host "  .\setup\scripts\install.ps1 -Lightweight # 轻量级安装"
    Write-Host "  .\setup\scripts\install.ps1 -Dev         # 开发环境安装"
    Write-Host "  .\setup\scripts\install.ps1 -Check       # 检查依赖"
    Write-Host "  .\setup\scripts\install.ps1 -Upgrade     # 升级依赖"
    Write-Host ""
}

# 解析参数
$InstallMode = "full"

if ($Help) {
    Show-Help
    exit 0
}

if ($Minimal) {
    $InstallMode = "minimal"
    $Full = $false
}
elseif ($Lightweight) {
    $InstallMode = "lightweight"
    $Full = $false
}
elseif ($Dev) {
    $InstallMode = "dev"
    $Full = $false
}

# 检查 Python 版本
function Check-Python {
    Write-Host "检查 Python 版本..." -ForegroundColor Blue

    try {
        $pythonVersion = python --version 2>&1
        Write-Host "Python 版本: $pythonVersion" -ForegroundColor Green

        # 解析版本号
        if ($pythonVersion -match "Python (\d+)\.(\d+)") {
            $major = [int]$matches[1]
            $minor = [int]$matches[2]

            if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 8)) {
                Write-Host "错误: 需要 Python 3.8 或更高版本" -ForegroundColor Red
                exit 1
            }

            Write-Host "✓ Python 版本符合要求" -ForegroundColor Green
        }
    }
    catch {
        Write-Host "错误: 未找到 Python" -ForegroundColor Red
        exit 1
    }
}

# 检查 pip
function Check-Pip {
    Write-Host "检查 pip..." -ForegroundColor Blue

    try {
        python -m pip --version | Out-Null
        Write-Host "✓ pip 已安装" -ForegroundColor Green
    }
    catch {
        Write-Host "错误: pip 未安装" -ForegroundColor Red
        exit 1
    }
}

# 检查虚拟环境
function Check-Venv {
    Write-Host "检查虚拟环境..." -ForegroundColor Blue

    if (Test-Path "$ProjectRoot\venv") {
        Write-Host "✓ 虚拟环境已存在" -ForegroundColor Green
        return $true
    }
    else {
        Write-Host "虚拟环境不存在" -ForegroundColor Yellow
        return $false
    }
}

# 创建虚拟环境
function Create-Venv {
    Write-Host "创建虚拟环境..." -ForegroundColor Blue

    try {
        python -m venv "$ProjectRoot\venv"
        Write-Host "✓ 虚拟环境创建成功" -ForegroundColor Green
    }
    catch {
        Write-Host "错误: 创建虚拟环境失败" -ForegroundColor Red
        exit 1
    }
}

# 激活虚拟环境
function Activate-Venv {
    if (Test-Path "$ProjectRoot\venv\Scripts\activate.ps1") {
        & "$ProjectRoot\venv\Scripts\activate.ps1"
        Write-Host "✓ 虚拟环境已激活" -ForegroundColor Green
    }
    else {
        Write-Host "警告: 无法激活虚拟环境，使用系统 Python" -ForegroundColor Yellow
    }
}

# 检查依赖
function Check-Dependencies {
    Write-Host "检查依赖..." -ForegroundColor Blue

    if (Test-Path "$ProjectRoot\setup\scripts\check_deps.py") {
        python "$ProjectRoot\setup\scripts\check_deps.py"
    }
    else {
        Write-Host "check_deps.py 不存在，跳过依赖检查" -ForegroundColor Yellow
    }
}

# 安装依赖
function Install-Dependencies {
    param(
        [string]$Mode
    )

    $requirementsFile = switch ($Mode) {
        "full" { "$ProjectRoot\setup\requirements\full.txt" }
        "minimal" { "$ProjectRoot\setup\requirements\minimal.txt" }
        "lightweight" { "$ProjectRoot\setup\requirements\lightweight.txt" }
        "dev" { "$ProjectRoot\setup\requirements\dev.txt" }
        default {
            Write-Host "错误: 未知的安装模式 $Mode" -ForegroundColor Red
            exit 1
        }
    }

    if (-not (Test-Path $requirementsFile)) {
        Write-Host "错误: 依赖文件不存在 $requirementsFile" -ForegroundColor Red
        exit 1
    }

    Write-Host "安装依赖 ($Mode 模式)..." -ForegroundColor Blue
    Write-Host "依赖文件: $requirementsFile"

    $pipArgs = "install -r `"$requirementsFile`""
    if ($Upgrade) {
        $pipArgs = "$pipArgs --upgrade"
    }

    Write-Host "执行: pip $pipArgs" -ForegroundColor Yellow

    try {
        python -m pip $pipArgs.Split(" ")
        Write-Host "✓ 依赖安装完成" -ForegroundColor Green
    }
    catch {
        Write-Host "错误: 依赖安装失败" -ForegroundColor Red
        exit 1
    }
}

# 安装后验证
function Verify-Installation {
    Write-Host "验证安装..." -ForegroundColor Blue

    if (Test-Path "$ProjectRoot\setup\scripts\verify_install.py") {
        python "$ProjectRoot\setup\scripts\verify_install.py"
    }
    else {
        Write-Host "verify_install.py 不存在，跳过验证" -ForegroundColor Yellow
    }
}

# 主函数
function Main {
    Write-Host "========================================" -ForegroundColor Blue
    Write-Host "Miya 依赖安装脚本" -ForegroundColor Blue
    Write-Host "========================================" -ForegroundColor Blue
    Write-Host ""

    # 检查环境
    Check-Python
    Check-Pip
    Write-Host ""

    # 检查依赖
    if ($Check) {
        Check-Dependencies
        exit 0
    }

    # 检查虚拟环境
    if (-not (Check-Venv)) {
        Write-Host "是否创建虚拟环境?" -ForegroundColor Yellow
        if ($Yes) {
            $CreateVenv = "y"
        }
        else {
            $CreateVenv = Read-Host "创建虚拟环境? [y/N]"
        }

        if ($CreateVenv -match "^[Yy]$") {
            Create-Venv
            Activate-Venv
        }
    }
    else {
        Activate-Venv
    }

    Write-Host ""

    # 显示安装信息
    Write-Host "安装模式: $InstallMode" -ForegroundColor Green
    Write-Host ""

    # 确认安装
    if (-not $Yes) {
        Write-Host "即将安装 $InstallMode 模式的依赖" -ForegroundColor Yellow
        $Confirm = Read-Host "继续? [Y/n]"
        if ($Confirm -and $Confirm -notmatch "^[Yy]$") {
            Write-Host "安装已取消" -ForegroundColor Yellow
            exit 0
        }
    }

    Write-Host ""

    # 安装依赖
    Install-Dependencies -Mode $InstallMode
    Write-Host ""

    # 验证安装
    Verify-Installation
    Write-Host ""

    # 完成
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "安装完成！" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "下一步：" -ForegroundColor Blue
    Write-Host "1. 配置环境变量: copy config\.env.example config\.env"
    Write-Host "2. 编辑配置文件: notepad config\.env"
    Write-Host "3. 启动服务: start.bat"
    Write-Host ""
}

# 运行主函数
Main
