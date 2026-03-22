#!/bin/bash
# ========================================
# Miya 快速安装脚本
# ========================================
# 用途：一键安装 Miya 的所有依赖
# 使用方法：./setup/scripts/quick_install.sh [选项]
# ========================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# 默认选项
INSTALL_MODE="full"
CHECK_ONLY=false
UPGRADE=false
SKIP_CONFIRM=false

# 显示帮助信息
show_help() {
    cat << EOF
Miya 快速安装脚本

使用方法: $0 [选项]

选项:
  --full         完整安装（生产环境，默认）
  --minimal      最小安装（核心功能）
  --lightweight  轻量级安装（无外部数据库）
  --dev          开发环境安装
  --check        仅检查依赖
  --upgrade      升级已安装的依赖
  --yes          跳过确认提示
  -h, --help     显示帮助信息

示例:
  $0                    # 完整安装
  $0 --minimal          # 最小安装
  $0 --lightweight      # 轻量级安装
  $0 --dev              # 开发环境安装
  $0 --check            # 检查依赖
  $0 --upgrade          # 升级依赖

EOF
}

# 解析命令行参数
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --full)
                INSTALL_MODE="full"
                shift
                ;;
            --minimal)
                INSTALL_MODE="minimal"
                shift
                ;;
            --lightweight)
                INSTALL_MODE="lightweight"
                shift
                ;;
            --dev)
                INSTALL_MODE="dev"
                shift
                ;;
            --check)
                CHECK_ONLY=true
                shift
                ;;
            --upgrade)
                UPGRADE=true
                shift
                ;;
            --yes)
                SKIP_CONFIRM=true
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                echo -e "${RED}未知选项: $1${NC}"
                show_help
                exit 1
                ;;
        esac
    done
}

# 检查 Python 版本
check_python() {
    echo -e "${BLUE}检查 Python 版本...${NC}"

    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}错误: 未找到 Python 3${NC}"
        exit 1
    fi

    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

    echo -e "Python 版本: ${GREEN}$PYTHON_VERSION${NC}"

    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
        echo -e "${RED}错误: 需要 Python 3.8 或更高版本${NC}"
        exit 1
    fi

    echo -e "${GREEN}✓ Python 版本符合要求${NC}"
}

# 检查 pip
check_pip() {
    echo -e "${BLUE}检查 pip...${NC}"

    if ! python3 -m pip --version &> /dev/null; then
        echo -e "${RED}错误: pip 未安装${NC}"
        exit 1
    fi

    echo -e "${GREEN}✓ pip 已安装${NC}"
}

# 检查虚拟环境
check_venv() {
    echo -e "${BLUE}检查虚拟环境...${NC}"

    if [ -d "$PROJECT_ROOT/venv" ]; then
        echo -e "${GREEN}✓ 虚拟环境已存在${NC}"
        return 0
    else
        echo -e "${YELLOW}虚拟环境不存在${NC}"
        return 1
    fi
}

# 创建虚拟环境
create_venv() {
    echo -e "${BLUE}创建虚拟环境...${NC}"

    python3 -m venv "$PROJECT_ROOT/venv"

    echo -e "${GREEN}✓ 虚拟环境创建成功${NC}"
}

# 激活虚拟环境
activate_venv() {
    if [ -f "$PROJECT_ROOT/venv/bin/activate" ]; then
        source "$PROJECT_ROOT/venv/bin/activate"
        echo -e "${GREEN}✓ 虚拟环境已激活${NC}"
    else
        echo -e "${YELLOW}警告: 无法激活虚拟环境，使用系统 Python${NC}"
    fi
}

# 检查依赖
check_dependencies() {
    echo -e "${BLUE}检查依赖...${NC}"

    if [ -f "$PROJECT_ROOT/setup/scripts/check_deps.py" ]; then
        python3 "$PROJECT_ROOT/setup/scripts/check_deps.py"
    else
        echo -e "${YELLOW}check_deps.py 不存在，跳过依赖检查${NC}"
    fi
}

# 安装依赖
install_dependencies() {
    local mode=$1
    local requirements_file=""

    case $mode in
        full)
            requirements_file="$PROJECT_ROOT/setup/requirements/full.txt"
            ;;
        minimal)
            requirements_file="$PROJECT_ROOT/setup/requirements/minimal.txt"
            ;;
        lightweight)
            requirements_file="$PROJECT_ROOT/setup/requirements/lightweight.txt"
            ;;
        dev)
            requirements_file="$PROJECT_ROOT/setup/requirements/dev.txt"
            ;;
        *)
            echo -e "${RED}错误: 未知的安装模式 $mode${NC}"
            exit 1
            ;;
    esac

    if [ ! -f "$requirements_file" ]; then
        echo -e "${RED}错误: 依赖文件不存在 $requirements_file${NC}"
        exit 1
    fi

    echo -e "${BLUE}安装依赖 ($mode 模式)...${NC}"
    echo -e "依赖文件: $requirements_file"

    local pip_args="install -r $requirements_file"
    if [ "$UPGRADE" = true ]; then
        pip_args="$pip_args --upgrade"
    fi

    echo -e "${YELLOW}执行: pip $pip_args${NC}"
    python3 -m pip $pip_args

    echo -e "${GREEN}✓ 依赖安装完成${NC}"
}

# 安装后验证
verify_installation() {
    echo -e "${BLUE}验证安装...${NC}"

    if [ -f "$PROJECT_ROOT/setup/scripts/verify_install.py" ]; then
        python3 "$PROJECT_ROOT/setup/scripts/verify_install.py"
    else
        echo -e "${YELLOW}verify_install.py 不存在，跳过验证${NC}"
    fi
}

# 主函数
main() {
    # 解析参数
    parse_args "$@"

    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}Miya 依赖安装脚本${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""

    # 检查环境
    check_python
    check_pip
    echo ""

    # 检查依赖
    if [ "$CHECK_ONLY" = true ]; then
        check_dependencies
        exit 0
    fi

    # 检查虚拟环境
    if ! check_venv; then
        echo -e "${YELLOW}是否创建虚拟环境?${NC}"
        if [ "$SKIP_CONFIRM" = true ]; then
            CREATE_VENV="y"
        else
            read -p "创建虚拟环境? [y/N] " CREATE_VENV
        fi

        if [[ "$CREATE_VENV" =~ ^[Yy]$ ]]; then
            create_venv
            activate_venv
        fi
    else
        activate_venv
    fi

    echo ""

    # 显示安装信息
    echo -e "${BLUE}安装模式: ${GREEN}$INSTALL_MODE${NC}"
    echo ""

    # 确认安装
    if [ "$SKIP_CONFIRM" = false ]; then
        echo -e "${YELLOW}即将安装 $INSTALL_MODE 模式的依赖${NC}"
        read -p "继续? [Y/n] " CONFIRM
        if [[ ! "$CONFIRM" =~ ^[Yy]$ ]] && [ ! -z "$CONFIRM" ]; then
            echo -e "${YELLOW}安装已取消${NC}"
            exit 0
        fi
    fi

    echo ""

    # 安装依赖
    install_dependencies "$INSTALL_MODE"
    echo ""

    # 验证安装
    verify_installation
    echo ""

    # 完成
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}安装完成！${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "${BLUE}下一步：${NC}"
    echo -e "1. 配置环境变量: cp config/.env.example config/.env"
    echo -e "2. 编辑配置文件: vim config/.env"
    echo -e "3. 启动服务: ./start.sh"
    echo ""
}

# 运行主函数
main "$@"
