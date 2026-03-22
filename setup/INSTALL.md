# Miya 依赖管理目录说明

本目录包含所有依赖管理和安装相关的文件。

## 📁 目录结构

```
setup/
├── INSTALL.md              # 本文件，安装说明
├── dependencies/           # 依赖配置文件
│   ├── base.txt           # 基础核心依赖
│   ├── ai.txt             # AI 模型依赖
│   ├── database.txt       # 数据库依赖
│   ├── tts.txt            # 语音合成依赖
│   ├── visualization.txt  # 数据可视化依赖
│   ├── dev.txt            # 开发工具依赖
│   └── optional.txt       # 可选依赖
├── requirements/           # 快速安装入口
│   ├── full.txt           # 完整依赖（生产环境）
│   ├── minimal.txt        # 最小依赖（开发测试）
│   ├── lightweight.txt    # 轻量级依赖（无外部数据库）
│   └── desktop.txt        # 桌面应用依赖
└── scripts/               # 安装脚本
    ├── install.sh         # Linux/Mac 安装脚本
    ├── install.ps1        # Windows 安装脚本
    ├── check_deps.py      # 依赖检查脚本
    ├── verify_install.py # 安装验证脚本
    └── quick_install.sh   # 快速安装脚本
```

## 🚀 快速开始

### 一键安装（推荐）

```bash
# Linux/Mac
./setup/scripts/quick_install.sh

# Windows
.\setup\scripts\install.ps1
```

### 手动安装

```bash
# 完整安装（生产环境）
pip install -r setup/requirements/full.txt

# 轻量级安装（无外部数据库）
pip install -r setup/requirements/lightweight.txt

# 最小安装（仅核心功能）
pip install -r setup/requirements/minimal.txt
```

### 分层安装

```bash
# 1. 安装基础核心
pip install -r setup/dependencies/base.txt

# 2. 根据需要安装其他模块
pip install -r setup/dependencies/ai.txt
pip install -r setup/dependencies/database.txt
pip install -r setup/dependencies/tts.txt
```

## 📝 依赖说明

### dependencies/ 目录

详细分类的依赖配置文件，适合按需选择：

| 文件 | 说明 | 包含内容 |
|------|------|----------|
| `base.txt` | 基础核心依赖 | FastAPI、aiohttp、pydantic、配置管理等 |
| `ai.txt` | AI 模型依赖 | OpenAI、Anthropic、PyTorch、Sentence Transformers |
| `database.txt` | 数据库依赖 | Redis、Milvus、Neo4j、ChromaDB |
| `tts.txt` | 语音合成依赖 | Edge-TTS、PyAudio、音频处理 |
| `visualization.txt` | 数据可视化依赖 | Matplotlib、Seaborn、Plotly |
| `dev.txt` | 开发工具依赖 | pytest、black、flake8、mypy |
| `optional.txt` | 可选依赖 | 各种可选功能模块 |

### requirements/ 目录

预设的组合依赖配置，适合快速安装：

| 文件 | 说明 | 适用场景 |
|------|------|----------|
| `full.txt` | 完整依赖 | 生产环境，包含所有功能 |
| `minimal.txt` | 最小依赖 | 快速开发测试，仅核心功能 |
| `lightweight.txt` | 轻量级依赖 | 无外部数据库，使用 Mock 模式 |
| `desktop.txt` | 桌面应用依赖 | 桌面 UI 应用 |

## 🔧 安装脚本说明

### quick_install.sh

智能安装脚本，自动检测环境并选择最佳安装方案：

```bash
./setup/scripts/quick_install.sh [选项]

选项：
  --full         完整安装（默认）
  --minimal      最小安装
  --lightweight  轻量级安装
  --dev          开发环境安装
  --check        仅检查依赖
  --upgrade      升级已安装的依赖
```

### install.ps1

Windows PowerShell 安装脚本：

```powershell
.\setup\scripts\install.ps1 [选项]

选项：
  -Full          完整安装（默认）
  -Minimal       最小安装
  -Lightweight   轻量级安装
  -Dev           开发环境安装
  -Check         仅检查依赖
  -Upgrade       升级已安装的依赖
```

### check_deps.py

依赖检查脚本，检测是否缺少依赖：

```bash
python setup/scripts/check_deps.py
```

输出示例：
```
✓ fastapi 0.104.1
✓ uvicorn 0.24.0
✗ openai 未安装
✓ pydantic 2.5.0
...
缺少 2 个依赖，建议运行：pip install -r setup/requirements/full.txt
```

### verify_install.py

验证所有依赖是否正确安装：

```bash
python setup/scripts/verify_install.py
```

## ⚙️ 特殊说明

### 模拟模式

使用轻量级安装时，在 `config/.env` 中设置：

```bash
SIMULATION_MODE=true
```

这样即使没有安装数据库依赖，系统也会使用 Mock 模式运行。

### GPU 支持

如果需要 GPU 加速，请根据 CUDA 版本选择：

```bash
# CUDA 11.8
pip install torch --index-url https://download.pytorch.org/whl/cu118

# CUDA 12.1
pip install torch --index-url https://download.pytorch.org/whl/cu121
```

### PyAudio 安装

平台特定的安装方式：

```bash
# Windows
pip install pipwin
pipwin install pyaudio

# Linux
sudo apt-get install python3-dev portaudio19-dev
pip install pyaudio

# macOS
brew install portaudio
pip install pyaudio
```

## 📊 安装对比

| 安装方式 | 包大小 | 依赖数量 | 数据库 | AI | 可视化 | 适用场景 |
|----------|--------|----------|--------|-----|--------|----------|
| minimal.txt | ~50MB | 15 | Mock | ❌ | ❌ | 快速测试 |
| lightweight.txt | ~200MB | 25 | Mock | ✅ | ❌ | 开发调试 |
| full.txt | ~500MB | 40 | ✅ | ✅ | ✅ | 生产环境 |

## 🐳 Docker 部署

如果使用 Docker，数据库会自动启动，无需额外安装：

```bash
docker-compose up -d
```

## ✅ 验证安装

```bash
# 检查依赖
python setup/scripts/check_deps.py

# 验证安装
python setup/scripts/verify_install.py

# 运行健康检查
python run/health.py
```

## 🔗 相关文档

- [安装指南](../INSTALL.md)
- [架构说明](../docs/ARCHITECTURE.md)
- [开发指南](../docs/DEVELOPMENT.md)
