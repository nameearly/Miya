# MIYA - 弥娅 AI 虚拟化身系统

<p align="center">
  <img src="docs/icon.svg" width="200" alt="MIYA Logo"/>
</p>

<p align="center">
  <strong>Version 4.0 Ultimate Edition</strong><br>
  多模态 AI 虚拟化身 · 跨平台 · 自我进化 · 记忆引擎
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
</p>

---

## 目录

- [项目简介](#项目简介)
- [核心特性](#核心特性)
- [系统架构](#系统架构)
- [快速开始](#快速开始)
- [项目结构](#项目结构)
- [配置指南](#配置指南)
- [模块详解](#模块详解)
- [开发指南](#开发指南)
- [部署方式](#部署方式)
- [常见问题](#常见问题)

---

## 项目简介

**MIYA（弥娅）** 是一个基于大型语言模型的智能虚拟化身系统。她不仅是一个 AI 聊天机器人，更是一个拥有完整认知架构的虚拟生命体。

### 什么是 MIYA？

MIYA 具备：

- **完整的人格** - 独特的性格特征、情感反应和价值观
- **持久记忆** - 跨会话的长期记忆和知识积累
- **自我进化** - 从交互中学习，不断完善自我
- **多平台接入** - QQ、Web、桌面应用、命令行
- **工具使用** - 搜索、文件操作、代码执行

---

## 核心特性

### 🧠 认知架构

| 特性 | 描述 |
|------|------|
| **人格系统** | 5维度性格向量：温暖、逻辑、创意、共情、韧性 |
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

### 🔗 多平台支持

| 平台 | 协议/技术 | 状态 |
|------|-----------|------|
| **QQ** | OneBot WebSocket | 活跃 |
| **Web** | FastAPI + WebSocket | 活跃 |
| **Desktop** | Tauri (React + Rust) | 活跃 |
| **Terminal** | CLI | 活跃 |

### 🤖 AI 模型支持

- **OpenAI** - GPT-4, GPT-3.5-Turbo
- **DeepSeek** - DeepSeek Chat
- **Anthropic** - Claude 3
- **ZhipuAI** - ChatGLM 系列
- **本地模型** - 支持 Ollama 等本地部署

### 🛠 工具生态

- **TerminalNet** - 终端命令执行
- **WebSearchNet** - 网络搜索集成
- **ToolNet** - 通用工具执行框架
- **CognitiveNet** - 认知处理子网
- **EntertainmentNet** - TRPG、Tavern AI 娱乐功能

### 🔧 自我改进

- **问题扫描器** - 自动发现问题
- **自动修复** - 自我修复能力
- **A/B 测试** - 实验框架
- **增量学习** - 持续学习机制
- **用户协作** - Co-play 学习

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
│     └─────────────┘  └─────────────┘  └─────────────┘              │
└───────────────────────────────┼───────────────────────────────────┘
                               │
┌───────────────────────────────┼───────────────────────────────────┐
│                     核心层 (Core / Soul Anchor)                    │
│     ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│     │   人格系统   │  │   伦理边界   │  │   身份管理   │              │
│     └─────────────┘  └─────────────┘  └─────────────┘              │
│     ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│     │   仲裁器    │  │   熵监测    │  │  提示管理    │              │
│     └─────────────┘  └─────────────┘  └─────────────┘              │
└───────────────────────────────┼───────────────────────────────────┘
                               │
┌───────────────────────────────┼───────────────────────────────────┐
│                     存储层 (Storage Layer)                          │
│     ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│     │    Redis    │  │   Milvus    │  │    Neo4j    │              │
│     │   (缓存)    │  │  (向量库)   │  │  (图数据库)  │              │
│     └─────────────┘  └─────────────┘  └─────────────┘              │
│     ┌─────────────┐  ┌─────────────┐                               │
│     │    文件     │  │   SQLite    │                               │
│     └─────────────┘  └─────────────┘                               │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 快速开始

### 环境要求

- **Python** 3.10+
- **Node.js** 18+ (用于前端/桌面应用)
- **Redis** 6+ (推荐)
- **Milvus** 2.x (可选，向量搜索)
- **Neo4j** 5.x (可选，知识图谱)

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

## 项目结构

```
Miya/
├── core/                    # 核心层 (Soul Anchor)
│   ├── personality.py      # 人格系统
│   ├── ethics.py           # 伦理边界
│   ├── identity.py         # 身份管理
│   ├── arbitrator.py       # 仲裁器
│   ├── entropy.py         # 熵监测
│   ├── ai_client.py        # AI 客户端工厂
│   ├── terminal_manager.py # 终端管理
│   └── web_api/            # Web API 端点
│
├── hub/                    # 决策中心 (Cognitive Core)
│   ├── decision_hub.py     # 主协调器
│   ├── decision.py         # 决策引擎
│   ├── emotion.py         # 情感状态
│   ├── memory_engine.py   # 记忆引擎
│   ├── memory_emotion.py  # 记忆-情感关联
│   ├── scheduler.py       # 任务调度
│   ├── perception_handler.py  # 感知处理
│   └── response_generator.py  # 响应生成
│
├── mlink/                  # M-Link 消息网络
│   ├── mlink_core.py      # 核心消息路由
│   ├── message.py          # 消息类型
│   ├── router.py          # 路由逻辑
│   ├── message_queue.py   # 异步队列
│   └── flow_monitor.py   # 流量监控
│
├── webnet/                 # Web 子网 (The Spider Web)
│   ├── webnet.py          # 主网络管理器
│   ├── qq/                # QQ 机器人
│   │   ├── client.py
│   │   ├── message_handler.py
│   │   ├── core.py
│   │   ├── image_handler.py
│   │   └── tts_handler.py
│   ├── CognitiveNet/      # 认知处理
│   ├── EntertainmentNet/  # 娱乐功能
│   ├── WebSearchNet/      # 网页搜索
│   └── ToolNet/           # 工具执行
│
├── memory/                 # 记忆系统
│   ├── unified_memory.py  # 统一内存接口
│   ├── grag_memory.py     # 图谱内存
│   ├── semantic_dynamics_engine.py  # 语义引擎
│   ├── real_vector_cache.py  # 向量缓存
│   ├── temporal_knowledge_graph.py  # 时序知识图谱
│   ├── quintuple_graph.py # 五元组图
│   ├── session_manager.py # 会话管理
│   └── memory_compressor.py  # 记忆压缩
│
├── storage/               # 存储层
│   ├── redis_client.py    # Redis 客户端
│   ├── milvus_client.py   # Milvus 客户端
│   ├── neo4j_client.py    # Neo4j 客户端
│   └── file_manager.py    # 文件存储
│
├── perceive/              # 感知层
│   ├── perceptual_ring.py  # 全局感知状态
│   └── attention_gate.py   # 注意力门控
│
├── trust/                 # 信任系统
│   ├── trust_score.py     # 信任评分
│   └── trust_propagation.py  # 信任传播
│
├── detect/                # 检测层
│   ├── time_detector.py   # 时间循环检测
│   ├── space_detector.py  # 空间检测
│   └── entropy_diffusion.py  # 熵扩散监测
│
├── evolve/                # 进化层
│   ├── sandbox.py         # 沙盒环境
│   ├── ab_test.py         # A/B 测试
│   ├── incremental_learner.py  # 增量学习
│   └── personality_evolver.py  # 人格进化
│
├── config/                # 配置目录
│   ├── settings.py        # 配置加载器
│   ├── .env               # 环境变量
│   ├── qq_config.yaml     # QQ 配置
│   ├── permissions.json   # 权限配置
│   └── terminal_config.json  # 终端配置
│
├── frontend/              # 前端应用
│   └── packages/
│       ├── web/          # Web 应用
│       ├── desktop/      # 桌面应用 (Tauri)
│       ├── ui/          # 共享 UI 组件
│       └── live2d/      # Live2D 虚拟形象
│
├── run/                   # 入口脚本
│   ├── main.py           # 终端模式主入口
│   ├── qq_main.py        # QQ 模式
│   ├── web_main.py       # Web API 模式
│   ├── runtime_api_start.py  # 运行时 API
│   └── multi_terminal_main_v2.py  # 多终端模式
│
├── prompts/              # 提示词模板
│   ├── miya_core.json    # 核心人格提示
│   ├── default.txt       # 默认对话
│   └── trpg_*.txt        # TRPG 模板
│
├── setup/                # 安装脚本
│   ├── requirements/     # 预置依赖集
│   └── scripts/          # 安装脚本
│
├── docs/                 # 文档
├── requirements.txt      # Python 依赖
├── start.bat/start.sh    # 启动器
└── install.bat/install.sh  # 安装脚本
```

---

## 配置指南

### 环境变量配置

```bash
# config/.env

# AI 模型配置
OPENAI_API_KEY=your_openai_key
DEEPSEEK_API_KEY=your_deepseek_key
ANTHROPIC_API_KEY=your_anthropic_key
ZHIPU_API_KEY=your_zhipu_key

# 数据库配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
MILVUS_HOST=localhost
MILVUS_PORT=19530
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# QQ 机器人配置
QQ_ACCOUNT=123456789
QQ_PASSWORD=your_password
ONEBOT_WS_URL=ws://localhost:8080

# 服务器配置
API_PORT=8001
WEB_PORT=8000
```

### QQ 机器人配置

```yaml
# config/qq_config.yaml
qq:
  account: 123456789
  password: "your_password"
  protocol: android平板
  
onebot:
  ws_url: "ws://localhost:8080"
  auto_reconnect: true
  
features:
  image_recognition: true
  tts: true
  auto_chat: false
  group_response: true
```

### AI 模型配置

```yaml
# config/unified_model_config.yaml
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

---

## 模块详解

### 核心层 (Core)

#### 人格系统 (Personality)

MIYA 的性格由5个维度定义：

```python
personality = {
    "warmth": 0.8,      # 温暖 - 关心他人程度
    "logic": 0.7,       # 逻辑 - 理性思考程度
    "creativity": 0.75, # 创意 - 创新能力
    "empathy": 0.85,    # 共情 - 理解他人
    "resilience": 0.6   # 韧性 - 抗压能力
}
```

#### 情感引擎 (Emotion)

7种基础情感，每种带有强度值和衰减率：

- **Joy (喜)** - 0.0 ~ 1.0
- **Sadness (哀)** - 0.0 ~ 1.0
- **Anger (怒)** - 0.0 ~ 1.0
- **Fear (惧)** - 0.0 ~ 1.0
- **Surprise (惊)** - 0.0 ~ 1.0
- **Disgust (厌)** - 0.0 ~ 1.0
- **Neutral (平)** - 平衡态

### 决策中心 (Hub)

#### 决策流程

```
用户输入 → 感知处理 → 记忆检索 → 决策评分 → 响应生成 → 输出
              ↓
         情感更新 → 人格影响
```

#### 记忆引擎

三层记忆架构：

1. **Tide Memory** - 短期会话记忆，自动过期
2. **Dream Memory** - 重要记忆持久化
3. **Semantic Memory** - 语义相似度匹配

### M-Link 消息总线

内部消息传递系统，支持：

- 发布/订阅模式
- 消息队列
- 流量监控
- 跨模块通信

---

## 开发指南

### 添加新功能

1. **创建子网** (如 `webnet/NewFeatureNet/`)

```python
# webnet/NewFeatureNet/__init__.py
from .feature import NewFeatureHandler

class NewFeatureNet:
    def __init__(self, decision_hub):
        self.handler = NewFeatureHandler()
        
    async def process(self, message):
        return await self.handler.handle(message)
```

2. **注册到网络管理器**

```python
# webnet/net_manager.py
from webnet.NewFeatureNet import NewFeatureNet

class NetManager:
    def __init__(self):
        self.new_feature = NewFeatureNet(self.hub)
```

### 自定义 AI 模型

```python
# core/ai_client.py
from core.ai_client import AIClientFactory

factory = AIClientFactory()

# 添加自定义模型
factory.register_provider("my_model", MyCustomClient)

# 使用
client = factory.create("my_model", api_key="xxx")
response = await client.chat([{"role": "user", "content": "Hello"}])
```

### 添加新工具

```python
# webnet/ToolNet/tools/my_tool.py
from webnet.ToolNet.base import BaseTool

class MyTool(BaseTool):
    name = "my_tool"
    description = "我的自定义工具"
    
    async def execute(self, params):
        # 实现逻辑
        return {"result": "success"}
```

---

## 部署方式

### Docker 部署

```bash
# 启动完整服务
docker-compose up -d

# 启动测试环境
docker-compose -f docker-compose.test.yml up -d
```

### 单独服务部署

```bash
# API 服务
python run/runtime_api_start.py

# Web 服务
python run/web_main.py

# QQ 机器人
python run/qq_main.py
```

---

## 常见问题

### Q: 启动时报错 `ModuleNotFoundError`

```bash
# 重新安装依赖
pip install -r requirements.txt
```

### Q: Redis/Milvus/Neo4j 连接失败

确保服务已启动：

```bash
# Redis
redis-server

# Milvus
docker run -d -p 19530:19530 milvusdb/milvus

# Neo4j
docker run -d -p 7474:7474 -p 7687:7687 neo4j
```

### Q: QQ 机器人无法连接

1. 检查 OneBot 服务是否运行
2. 确认 QQ 号和密码正确
3. 检查网络连接

### Q: API 响应缓慢

1. 检查 AI 模型 API 延迟
2. 优化 Redis 缓存配置
3. 考虑启用 Milvus 加速向量检索

---

## 更新日志

### v4.0 (Ultimate Edition)

- 全新决策中心架构
- 多层记忆系统重构
- Tauri 桌面应用
- Live2D 虚拟形象支持
- 自我进化能力增强

### v3.0

- WebSocket 实时通信
- 知识图谱集成
- A/B 测试框架

### v2.0

- QQ 机器人支持
- 多模型支持
- 基础记忆系统

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
  Made with ❤️ by MIYA Team
</p>
