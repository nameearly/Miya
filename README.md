# MIYA - 弥娅 AI 虚拟化身系统

<p align="center">
  <img src="docs/miya.jpg" width="300" alt="弥娅"/>
</p>

<p align="center">
  <strong>Version 4.2 Terminal Ultra Edition</strong><br>
  多模态 AI 虚拟化身 · 跨平台 · 自我进化 · 记忆引擎 · 超级终端控制
</p>

<p align="center">
  <a href="./LICENSE">
    <img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License">
  </a>
  <a href="https://github.com/Jia-520-only/Miya">
    <img src="https://img.shields.io/badge/GitHub-Jia--520--only/Miya-green.svg" alt="GitHub">
  </a>
  <img src="https://img.shields.io/badge/Python-3.10+-yellow.svg" alt="Python">
  <img src="https://img.shields.io/badge/React-18-blue.svg" alt="React">
  <img src="https://img.shields.io/badge/Status-Stable-green.svg" alt="Status">
</p>

---

## 目录

- [项目简介](#项目简介)
  - [什么是 MIYA？](#什么是-miya)
  - [为什么选择 MIYA？](#为什么选择-miya)
- [核心特性](#核心特性)
- [系统架构](#系统架构)
- [快速开始](#快速开始)
- [终端模式教程](#终端模式教程)
- [配置指南](#配置指南)
- [模块详解](#模块详解)
- [API 参考](#api-参考)
- [常见问题](#常见问题)
- [更新日志](#更新日志)
- [贡献指南](#贡献指南)

---

## 项目简介

### 什么是 MIYA？

**MIYA（弥娅）** 是一个基于大型语言模型的智能虚拟化身系统。她不仅是一个 AI 聊天机器人，更是一个拥有完整认知架构的虚拟生命体。

弥娅具备独特的三层人格结构——**冷硬脆**：
- **冷**：不知道怎么热，语言是工具不是玩具
- **硬**：有判断力，你看得出她在想什么但不拆穿
- **脆**：怕被忘、怕不够、怕自己是假的

### 为什么选择 MIYA？

| 特性 | 说明 |
|------|------|
| 🎭 独特人格 | "冷硬脆"三层结构，创造与众不同的 AI 角色 |
| 🧠 认知架构 | 完整的人格、情感、记忆系统，模拟真实生命体 |
| 🔧 超级终端 | 8大终端工具，完整的文件系统操作和代码执行能力 |
| 🤖 AI 推理 | MiyaAgentV3 驱动的多步骤自主任务执行 |
| 🌐 多平台 | QQ、Web、桌面、命令行，统一的用户体验 |
| 🔒 安全防护 | 注入检测、敏感词过滤、速率限制 |
| 📚 知识管理 | 三层认知记忆、语义搜索、知识图谱 |
| 🔌 扩展性 | MCP 协议支持、Skills 热重载、工具生态 |

---

## 核心特性

### 🧠 认知架构

| 特性 | 描述 |
|------|------|
| **人格系统** | 冷硬脆三层结构：冷（不知道怎么热）、硬（有判断不拆穿）、脆（怕被忘） |
| **情感引擎** | 7种基础情感（喜、怒、哀、惧、惊、厌、平），带强度衰减 |
| **伦理边界** | 基于用户权限的伦理约束执行 |
| **仲裁机制** | 人格欲望与伦理约束的冲突解决 |

### 💾 多层记忆系统

| 记忆层 | 类型 | 说明 |
|--------|------|------|
| **Tide Memory** | 短期 | 会话内短期记忆，带 TTL |
| **Dream Memory** | 长期 | 持久化存储 |
| **Semantic Memory** | 向量 | 基于 Milvus 的语义相似度搜索 |
| **Knowledge Graph** | 图谱 | Neo4j 知识图谱，五元组表示 |
| **Session Memory** | 会话 | 多会话管理 |
| **Cognitive Memory** | 认知 | 三层认知记忆，ChromaDB 向量存储 |

### 🔗 多平台支持

| 平台 | 协议/技术 | 状态 |
|------|-----------|------|
| **QQ** | OneBot WebSocket | ✅ 活跃 |
| **Web** | FastAPI + WebSocket | ✅ 活跃 |
| **Desktop** | Tauri (React + Rust) | ✅ 活跃 |
| **Terminal** | CLI | ✅ 活跃 |

### 🤖 AI 模型支持

- **OpenAI** - GPT-4, GPT-3.5-Turbo, GPT-4o
- **DeepSeek** - DeepSeek Chat, DeepSeek Coder
- **Anthropic** - Claude 3, Claude 3.5
- **ZhipuAI** - ChatGLM 系列
- **本地模型** - 支持 Ollama、LM Studio 等本地部署

### 🛠 工具生态 (68+ 工具)

| 工具类别 | 工具数 | 功能 |
|----------|--------|------|
| **TerminalUltra** | 8 | 终端命令、文件操作、代码执行、项目分析 |
| **Basic** | 3 | 时间查询、用户信息、Python解释器 |
| **Terminal** | 4 | 终端控制、系统信息 |
| **Memory** | 6 | 记忆管理、提取、搜索 |
| **Knowledge** | 5 | 知识库操作 |
| **Bilibili** | 4 | B站相关功能 |
| **Scheduler** | 3 | 定时任务 |
| **Entertainment** | 8 | TRPG、 Tavern AI 等 |

### 💻 超级终端 (Terminal Ultra)

弥娅终端模式全新升级，拥有完全终端掌控能力：

| 工具 | 功能 | 示例 |
|------|------|------|
| **terminal_exec** | 执行任意终端命令 | `python script.py`, `npm install` |
| **file_read** | 读取文件内容 | 查看代码、配置 |
| **file_write** | 创建/写入文件 | 创建新文件 |
| **file_edit** | 编辑/修改文件 | 修改代码 |
| **file_delete** | 删除文件 | 清理文件 |
| **directory_tree** | 目录树结构 | 查看项目结构 |
| **code_execute** | 代码执行 | 运行 Python/JS 代码 |
| **project_analyze** | 项目分析 | 统计语言分布 |

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                         展现层 (Presentation)                        │
│     ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│     │   QQ     │  │   Web    │  │ Desktop  │  │ Terminal │        │
│     └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘        │
└──────────┼─────────────┼─────────────┼─────────────┼───────────────┘
           │             │             │             │
           └─────────────┴─────────────┴─────────────┘
                              │
                   ┌──────────┴──────────┐
                   │   M-Link 消息总线    │
                   └──────────┬──────────┘
                              │
┌───────────────────────────────┼───────────────────────────────────┐
│                     决策中心 (Decision Hub)                        │
│     ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│     │   感知处理   │  │   响应生成   │  │   情感控制   │              │
│     └─────────────┘  └─────────────┘  └─────────────┘              │
│     ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│     │   记忆引擎   │  │   调度器    │  │  信任评分    │              │
│     │ (含V3代理)   │  │            │  │             │              │
│     └─────────────┘  └─────────────┘  └─────────────┘              │
└───────────────────────────────┼───────────────────────────────────┘
                              │
┌───────────────────────────────┼───────────────────────────────────┐
│                     核心层 (Core / Soul Anchor)                    │
│     ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│     │   人格系统   │  │   伦理边界   │  │  身份管理   │              │
│     │  (冷硬脆)   │  │             │  │             │              │
│     └─────────────┘  └─────────────┘  └─────────────┘              │
│     ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│     │   仲裁器    │  │   熵监测    │  │  提示管理    │              │
│     └─────────────┘  └─────────────┘  └─────────────┘              │
│     ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│     │ TerminalUltra│ │ MiyaAgentV3 │  │ 安全防护    │              │
│     │ (8大工具)   │  │ (AI推理)    │  │             │              │
│     └─────────────┘  └─────────────┘  └─────────────┘              │
└───────────────────────────────┼───────────────────────────────────┘
                              │
┌───────────────────────────────┼───────────────────────────────────┐
│                     存储层 (Storage Layer)                          │
│     ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│     │    Redis    │  │   Milvus    │  │    Neo4j    │              │
│     │   (缓存)    │  │  (向量库)   │  │  (图数据库)  │              │
│     └─────────────┘  └─────────────┘  └─────────────┘              │
│     ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│     │  ChromaDB   │  │   SQLite    │  │    文件     │              │
│     │ (认知记忆)  │  │             │  │             │              │
│     └─────────────┘  └─────────────┘  └─────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 快速开始

### 环境要求

| 要求 | 版本 | 说明 |
|------|------|------|
| **Python** | 3.10+ | 核心运行环境 |
| **Node.js** | 18+ | 前端/桌面应用 |
| **Redis** | 6+ | 推荐，增强缓存 |
| **Milvus** | 2.x | 可选，向量搜索 |
| **Neo4j** | 5.x | 可选，知识图谱 |
| **ChromaDB** | - | 可选，认知记忆 |

### 安装方式

#### 方式一：Windows 一键安装

```bash
.\install.bat
```

#### 方式二：Linux/Mac 安装

```bash
chmod +x install.sh
./install.sh
```

#### 方式三：手动安装

```bash
# 克隆项目
git clone https://github.com/Jia-520-only/Miya.git
cd Miya

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp config/.env.example config/.env
# 编辑 config/.env 填入你的 API Key
```

### 启动系统

#### Windows

```bash
start.bat
```

#### Linux/Mac

```bash
./start.sh
```

#### 启动选项

| 选项 | 功能 |
|------|------|
| 1 | QQ 客户端 |
| 2 | Web 客户端 |
| 3 | 桌面客户端 |
| 4 | 终端客户端 |
| 5 | 全部客户端 |
| 6 | Web + 桌面 |
| 7 | 自定义启动 |
| Q | 快速启动（终端 + API） |

---

## 终端模式教程

### 启动终端模式

```bash
# 方式一：交互式启动（推荐）
python run/main.py

# 方式二：快速启动（终端 + API）
# 在 start.bat/start.sh 中选择 Q
```

### 基本交互

启动后，您可以：

| 命令 | 功能 |
|------|------|
| `直接输入` | 与弥娅对话 |
| `/terminal` | 进入终端控制模式 |
| `/quit` 或 `exit` | 退出程序 |
| `list terminals` | 查看所有终端状态 |
| `switch <名称>` | 切换到指定终端 |

### 使用终端工具

在终端模式下，您可以无缝使用以下工具：

```bash
# 查看当前目录结构
dir

# 读取文件
cat README.md

# 执行终端命令
python script.py

# 直接让弥娅执行任务
帮我创建一个 Python 文件并运行
```

### V3 代理模式

当弥娅检测到复杂任务时，会自动启用 V3 代理进行多步骤执行：

```
用户: 帮我创建一个计算器应用
弥娅: [V3代理] 开始执行任务...
  步骤1: 创建计算器项目目录
  步骤2: 编写 main.py
  步骤3: 编写 ui.py
  步骤4: 测试运行
  完成: 计算器应用已创建
```

---

## 配置指南

### AI 模型配置

编辑 `config/unified_model_config.yaml`：

```yaml
models:
  default: gpt-4o-mini
  
  gpt-4o:
    provider: openai
    api_key: ${OPENAI_API_KEY}
    base_url: https://api.openai.com/v1
    
  deepseek-chat:
    provider: deepseek
    api_key: ${DEEPSEEK_API_KEY}
    base_url: https://api.deepseek.com
    
  claude-3-haiku:
    provider: anthropic
    api_key: ${ANTHROPIC_API_KEY}
```

### 多模型路由配置

编辑 `config/multi_model_config.json`：

```json
{
  "models": {
    "gpt-4o-mini": {
      "provider": "openai",
      "api_key": "your-key",
      "name": "gpt-4o-mini"
    }
  },
  "routing_strategy": {
    "simple_chat": {
      "primary": "gpt-4o-mini",
      "fallback": "deepseek-chat"
    },
    "complex_reasoning": {
      "primary": "gpt-4o",
      "fallback": "claude-3-haiku"
    }
  }
}
```

### 环境变量配置

编辑 `config/.env`：

```bash
# AI 模型配置
OPENAI_API_KEY=your_openai_key
DEEPSEEK_API_KEY=your_deepseek_key
ANTHROPIC_API_KEY=your_anthropic_key
ZHIPU_API_KEY=your_zhipu_key

# 数据库配置
REDIS_HOST=localhost
REDIS_PORT=6379

# 服务器配置
API_PORT=8001
WEB_PORT=8000
```

---

## 模块详解

### 核心层 (Core)

| 模块 | 功能 |
|------|------|
| `personality.py` | 冷硬脆人格系统、形态切换 |
| `ethics.py` | 伦理边界、权限控制 |
| `emotion.py` | 7种情感、情绪染色 |
| `prompt_manager.py` | 系统提示词管理 |
| `ai_client.py` | 多模型工厂、支持68+工具 |
| `terminal_ultra.py` | 8大终端工具、文件系统操作 |
| `miya_agent_v3.py` | AI推理引擎、多步骤执行 |
| `security_service.py` | 注入检测、敏感词过滤 |
| `mcp_client.py` | MCP协议支持 |
| `skills_hot_reload.py` | 技能热重载 |

### 决策中心 (Hub)

| 模块 | 功能 |
|------|------|
| `decision_hub.py` | 主协调器、感知→决策→响应 |
| `memory_engine.py` | 记忆存储、检索 |
| `emotion.py` | 情感状态管理 |
| `scheduler.py` | 任务调度、定时触发 |
| `perception_handler.py` | 感知处理、意图识别 |
| `response_generator.py` | 响应生成、格式化 |

### M-Link 消息总线

内部消息传递系统，支持：
- 发布/订阅模式
- 消息队列
- 流量监控
- 跨模块通信

---

## API 参考

### Runtime API

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/terminal/chat` | POST | 终端聊天（含V3代理） |
| `/api/runtime/probe` | GET | 运行态探针 |
| `/api/runtime/memory/query` | GET | 查询记忆（只读） |

### Management API

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/management/status` | GET | 获取Bot状态 |
| `/api/management/bot/start` | POST | 启动Bot |
| `/api/management/bot/stop` | POST | 停止Bot |
| `/api/management/stats` | GET | 获取系统统计 |
| `/api/management/logs` | GET | 获取日志 |
| `/api/management/health` | GET | 健康报告 |

---

## 常见问题

### 安装问题

**Q: 启动时报错 `ModuleNotFoundError`**

```bash
# 重新安装依赖
pip install -r requirements.txt
```

**Q: Redis 连接失败**

确保 Redis 服务已启动：
```bash
redis-server
```

### 运行问题

**Q: 终端模式中文输入乱码**

Windows 下确保控制台编码为 UTF-8：
```bash
chcp 65001
```

**Q: API 响应缓慢**

检查 AI 模型 API 延迟，或启用 Runtime API 全局缓存（v4.2+）。

### 功能问题

**Q: Terminal Ultra 工具无法使用**

确保工具参数正确：
- `file_read`: 参数 `file_path`
- `file_write`: 参数 `file_path`, `content`
- `file_delete`: 参数 `file_path`

**Q: V3 代理不生效**

V3 代理自动处理复杂任务，手动调用：
```python
from core.miya_agent_v3 import create_agent_v3
agent = create_agent_v3(max_steps=10)
result = await agent.run("任务描述", model_client)
```

---

## 更新日志

### v4.2 (Terminal Ultra Edition)

- ✅ 超级终端控制系统 (Terminal Ultra)
- ✅ 8大终端工具: terminal_exec, file_read, file_write, file_edit, file_delete, directory_tree, code_execute, project_analyze
- ✅ MiyaAgentV3 - AI驱动的推理引擎
  - AI意图理解、多步骤自主执行、任务完成检测
  - 跨平台命令推理 (Windows/Linux/Mac)
- ✅ Runtime API 全局缓存优化 - 后续请求<1秒响应
- ✅ 终端模式跨平台支持增强
- ✅ 68+ 工具完整支持

### v4.1 (Upgrade Edition)

- ✅ Skills 热重载功能
- ✅ 三层认知记忆系统
- ✅ WebUI 管理界面
- ✅ MCP 协议支持
- ✅ 安全防护模块
- ✅ 并发工具执行优化

### v4.0 (Ultimate Edition)

- ✅ 完整人格系统
- ✅ 多层记忆架构
- ✅ 多平台支持

---

## 贡献指南

欢迎提交 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

---

## 许可证

本项目采用 [MIT 许可证](LICENSE)。

---

## 联系方式

- **GitHub**: [Jia-520-only/Miya](https://github.com/Jia-520-only/Miya)
- **问题反馈**: [Issues](https://github.com/Jia-520-only/Miya/issues)

---

<p align="center">
  Made with ❤️ by Jia
</p>