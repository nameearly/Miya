# Miya 依赖管理系统

## 📁 目录结构

```
setup/
├── INSTALL.md              # 详细安装说明
├── README.md               # 本文件，依赖管理系统说明
├── dependencies/           # 详细依赖配置文件
│   ├── base.txt           # 基础核心依赖（Web 框架、异步通信等）
│   ├── ai.txt             # AI 模型依赖（OpenAI、PyTorch 等）
│   ├── database.txt       # 数据库依赖（Redis、Milvus、Neo4j 等）
│   ├── tts.txt            # 语音合成依赖（Edge-TTS、PyAudio）
│   ├── viz.txt            # 数据可视化依赖（Matplotlib、Seaborn）
│   └── dev.txt            # 开发工具依赖（pytest、black、flake8）
├── requirements/           # 快速安装入口（预设组合）
│   ├── full.txt           # 完整依赖（生产环境）
│   ├── minimal.txt        # 最小依赖（核心功能）
│   ├── lightweight.txt    # 轻量级依赖（无外部数据库）
│   ├── desktop.txt        # 桌面应用依赖
│   └── dev.txt            # 开发环境依赖
└── scripts/               # 安装脚本
    ├── quick_install.sh   # Linux/Mac 快速安装脚本
    ├── install.ps1        # Windows 快速安装脚本
    ├── check_deps.py      # 依赖检查脚本
    └── verify_install.py # 安装验证脚本
```

---

## 🎯 设计理念

### 1. 分层管理

将依赖按功能分层，用户可以根据需要选择安装：

- **dependencies/** - 原子化的依赖配置，每个文件对应一个功能模块
- **requirements/** - 预设的组合依赖，满足常见使用场景

### 2. 兼容性保留

根目录保留 `requirements.txt`，确保向后兼容：

```bash
# 传统方式（仍然支持）
pip install -r requirements.txt

# 推荐方式（更灵活）
./setup/scripts/quick_install.sh
```

### 3. 智能脚本

提供跨平台的智能安装脚本，自动检测环境并选择最佳方案：

- **quick_install.sh** - Linux/Mac 一键安装
- **install.ps1** - Windows 一键安装
- **check_deps.py** - 检查依赖是否完整
- **verify_install.py** - 验证安装是否成功

---

## 🚀 使用场景

### 场景 1：新用户快速开始

```bash
# 一键安装（自动检测环境）
./setup/scripts/quick_install.sh
```

### 场景 2：开发者设置环境

```bash
# 开发环境（包含所有开发工具）
./setup/scripts/quick_install.sh --dev
```

### 场景 3：轻量级开发测试

```bash
# 仅核心功能，使用 Mock 模式
pip install -r setup/requirements/lightweight.txt
```

### 场景 4：生产环境部署

```bash
# 完整依赖，包含所有功能
pip install -r requirements.txt
```

### 场景 5：按需安装

```bash
# 仅安装基础 + AI
pip install -r setup/dependencies/base.txt
pip install -r setup/dependencies/ai.txt
```

---

## 📊 依赖分类说明

### dependencies/base.txt - 基础核心依赖

运行 Miya 的最小依赖集合：

| 包名 | 版本 | 用途 |
|------|------|------|
| fastapi | >=0.95.0,<0.110.0 | Web 框架 |
| uvicorn | >=0.22.0,<0.28.0 | ASGI 服务器 |
| pydantic | >=2.0.0,<3.0.0 | 数据验证 |
| aiohttp | >=3.8.0,<4.0.0 | 异步 HTTP |
| python-dotenv | >=1.0.0 | 环境变量管理 |
| pyyaml | >=6.0 | YAML 配置 |
| psutil | >=5.9.0 | 系统监控 |
| watchdog | >=3.0.0 | 文件监控 |
| requests | >=2.31.0 | HTTP 请求 |
| numpy | >=1.24.0,<2.0.0 | 数值计算 |

### dependencies/ai.txt - AI 模型依赖

AI 功能相关依赖：

| 包名 | 版本 | 用途 |
|------|------|------|
| openai | >=1.3.0,<2.0.0 | OpenAI 兼容 API |
| anthropic | >=0.7.0,<1.0.0 | Claude API |
| zhipuai | >=4.0.0,<5.0.0 | 智谱 AI |
| sentence-transformers | >=2.2.0,<3.0.0 | 本地嵌入模型 |
| torch | >=2.0.0,<2.3.0 | PyTorch 深度学习 |
| transformers | >=4.30.0,<5.0.0 | Hugging Face |

### dependencies/database.txt - 数据库依赖

外部数据库相关依赖（均有 Mock 回退）：

| 包名 | 版本 | 用途 |
|------|------|------|
| chromadb | >=0.4.0,<0.6.0 | 轻量级向量数据库 |
| pymilvus | >=2.3.0,<2.4.0 | 高性能向量数据库 |
| neo4j | >=5.0.0,<6.0.0 | 知识图谱数据库 |
| redis | >=4.5.0,<5.0.0 | 缓存数据库 |
| hiredis | >=2.2.0,<3.0.0 | Redis 性能加速 |

### dependencies/tts.txt - 语音合成依赖

语音合成相关依赖：

| 包名 | 版本 | 用途 |
|------|------|------|
| edge-tts | >=6.1.0,<7.0.0 | Edge 浏览器 TTS |
| pydub | >=0.25.0 | 音频处理 |

### dependencies/viz.txt - 数据可视化依赖

数据可视化和图表生成：

| 包名 | 版本 | 用途 |
|------|------|------|
| matplotlib | >=3.7.0,<4.0.0 | 基础图表 |
| seaborn | >=0.12.0,<0.14.0 | 统计图表 |
| pandas | >=2.0.0,<3.0.0 | 数据处理 |
| scipy | >=1.10.0,<2.0.0 | 科学计算 |
| scikit-learn | >=1.3.0,<2.0.0 | 机器学习 |

### dependencies/dev.txt - 开发工具依赖

代码开发、测试、调试工具：

| 包名 | 版本 | 用途 |
|------|------|------|
| black | >=23.12.0 | 代码格式化 |
| flake8 | >=7.0.0 | 代码检查 |
| mypy | >=1.8.0 | 类型检查 |
| isort | >=5.13.0 | 导入排序 |
| pytest | >=7.4.0 | 测试框架 |
| pytest-asyncio | >=0.21.0 | 异步测试 |
| pytest-cov | >=4.1.0 | 覆盖率测试 |
| ipython | >=8.18.0 | 交互式 Python |
| ipdb | >=0.13.0 | 调试器 |
| py-spy | >=0.3.14 | 性能分析 |
| memory-profiler | >=0.61.0 | 内存分析 |
| sphinx | >=7.2.0 | 文档生成 |

---

## 🔧 requirements/ 预设组合

### full.txt - 完整依赖

包含所有功能模块，适合生产环境：

```
- base.txt (基础核心)
- ai.txt (AI 模型)
- database.txt (数据库)
- tts.txt (语音合成)
- viz.txt (数据可视化)
```

**适用场景**: 生产环境、完整功能部署

**包大小**: ~500MB
**依赖数量**: ~40

### minimal.txt - 最小依赖

仅包含核心功能，适合快速测试：

```
- base.txt (基础核心)
- openai (OpenAI 兼容 API)
- numpy (数据处理)
```

**适用场景**: 快速开发测试、API 测试

**包大小**: ~50MB
**依赖数量**: ~15

### lightweight.txt - 轻量级依赖

无外部数据库，使用 Mock 模式：

```
- base.txt (基础核心)
- ai.txt (AI 模型)
```

所有数据库使用 Mock 模式运行。

**适用场景**: 开发调试、不想部署数据库

**包大小**: ~200MB
**依赖数量**: ~25

**启用方式**: 在 `config/.env` 中设置 `SIMULATION_MODE=true`

### desktop.txt - 桌面应用依赖

适合桌面 UI 应用：

```
- base.txt (基础核心)
- ai.txt (AI 模型)
- chromadb (轻量级向量数据库)
- redis (缓存数据库)
- tts.txt (语音合成)
```

**适用场景**: 桌面应用用户

**包大小**: ~300MB
**依赖数量**: ~30

### dev.txt - 开发环境依赖

完整功能 + 开发工具：

```
- full.txt (完整依赖)
- dev.txt (开发工具)
```

**适用场景**: 开发者

**包大小**: ~600MB
**依赖数量**: ~55

---

## 📝 版本管理策略

### 版本约束

所有依赖都使用明确的版本范围：

- `>=x.y.0,<z.0.0` - 推荐范围，保证兼容性
- 避免使用 `*` 或无版本约束
- 主要版本锁定，允许次要版本更新

### 版本锁定

如果需要精确版本控制，可以创建 `requirements-lock.txt`：

```bash
pip freeze > requirements-lock.txt
```

---

## ✅ 质量保证

### 依赖检查

运行依赖检查脚本：

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

### 安装验证

验证所有依赖是否正确安装：

```bash
python setup/scripts/verify_install.py
```

输出示例：
```
✓ 成功导入的模块:
  ✓ fastapi
  ✓ uvicorn
  ✓ pydantic
  ...

✗ 导入失败的核心模块:
  ✗ openai

⚠ 缺失的可选模块 (不影响基础运行):
  ⚠ chromadb
  ⚠ neo4j
  ...

✓ 核心依赖验证通过！
```

---

## 🔄 更新依赖

### 更新所有依赖

```bash
pip install -r requirements.txt --upgrade
```

### 更新特定模块

```bash
pip install -r setup/dependencies/ai.txt --upgrade
```

### 使用脚本更新

```bash
# Linux/Mac
./setup/scripts/quick_install.sh --upgrade

# Windows
.\setup\scripts\install.ps1 -Upgrade
```

---

## 🐳 Docker 部署

如果使用 Docker 部署，数据库会自动启动，无需额外安装：

```bash
docker-compose up -d
```

---

## 📚 相关文档

- [详细安装说明](INSTALL.md)
- [项目安装指南](../INSTALL.md)
- [架构说明](../docs/ARCHITECTURE.md)
- [开发指南](../docs/DEVELOPMENT.md)

---

## 💡 最佳实践

1. **使用虚拟环境**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # 或
   venv\Scripts\activate  # Windows
   ```

2. **使用一键安装脚本**
   ```bash
   ./setup/scripts/quick_install.sh
   ```

3. **定期检查依赖**
   ```bash
   python setup/scripts/check_deps.py
   ```

4. **开发环境使用 dev 模式**
   ```bash
   ./setup/scripts/quick_install.sh --dev
   ```

5. **生产环境使用 full 模式**
   ```bash
   pip install -r requirements.txt
   ```

---

## 🤝 贡献指南

如果需要添加新的依赖：

1. 确定依赖所属的分类（base/ai/database/tts/viz/dev）
2. 在对应的 `dependencies/*.txt` 中添加依赖
3. 更新 `requirements/full.txt` 如果需要
4. 更新本文档中的依赖说明
5. 运行 `check_deps.py` 验证

---

## ❓ 常见问题

### Q1: 为什么有多个 requirements 文件？

A: 为了灵活性和可维护性。`requirements.txt` 保留兼容性，新的分层系统允许按需安装。

### Q2: 如何选择安装模式？

A:
- 新用户 → `quick_install.sh`
- 开发者 → `quick_install.sh --dev`
- 测试 → `lightweight.txt`
- 生产 → `requirements.txt`

### Q3: 数据库依赖是必需的吗？

A: 不是。所有数据库都有 Mock 回退，可以使用 `lightweight.txt` 并设置 `SIMULATION_MODE=true`。

### Q4: 如何更新依赖？

A: 使用 `--upgrade` 标志或运行 `quick_install.sh --upgrade`。

### Q5: 版本约束太严格怎么办？

A: 可以临时放宽版本约束，但建议先测试兼容性。

---

## 📞 支持

如有问题，请参考：
- 详细安装说明：[setup/INSTALL.md](INSTALL.md)
- 项目安装指南：[../INSTALL.md](../INSTALL.md)
- 提交 Issue：[项目 Issue 页面]
