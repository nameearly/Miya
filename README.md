# MIYA - 弥娅 AI 虚拟化身系统

<p align="center">
  <img src="docs/miya.jpg" width="300" alt="弥娅"/>
</p>

<p align="center">
  <strong>Version 4.3.1 Dynamic Edition</strong><br>
  多模态 AI 虚拟化身 · 跨平台 · 自我进化 · 隐私感知记忆 · MCP支持 · 队列管理
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
- [新功能教程](#新功能教程-v41-upgrade)
  - [Skills 热重载](#1-skills-热重载-skills-hot-reload)
  - [三层认知记忆](#2-三层认知记忆-three-layer-cognitive-memory)
  - [WebUI 管理界面](#3-webui-管理界面-miya-management-webui)
  - [MCP 支持](#4-mcp-支持-model-context-protocol)
  - [安全防护](#5-安全防护-security-service)
  - [并发工具执行](#6-并发工具执行)
  - [Terminal Ultra](#7-超级终端控制系统-terminal-ultra)
  - [MiyaAgentV3](#8-miya_agent_v3---ai驱动的推理引擎)
  - [Runtime API 缓存优化](#9-runtime-api-全局缓存优化)
  - [终端模式启动](#10-终端模式启动)
  - [动态话题生成系统](#11-动态话题生成系统-dynamic-topic-generation)
  - [隐私感知记忆系统](#隐私感知记忆系统-v431-新增)
  - [MCP支持增强](#mcp-支持增强-v431-新增)
  - [队列管理系统](#队列管理系统---车站-列车模型-v431-新增)
  - [Skills配置系统](#skills-配置系统-v431-新增)
  - [隐私感知记忆系统](#12-隐私感知记忆系统-privacy-aware-memory)
  - [MCP 支持增强](#13-mcp-支持增强)
  - [队列管理系统](#14-队列管理系统-车站-列车模型)

---

## v4.3.1 更新日志 (2026-03-31)

### 本次更新概述

v4.3.1 版本在 v4.3.0 基础上进行了多项重要改进，主要包括：

1. **工具系统优化与清理** - 删除冗余目录，统一配置
2. **QQ消息解析器升级** - 支持引用消息、文件消息
3. **隐私感知记忆系统** - 识别群聊/私聊，自动判断私密话题
4. **MCP 支持增强** - 新增 MCP 工具注册中心
5. **队列管理系统** - 实现车站-列车模型

---

### 1. 工具系统优化与清理

#### 1.1 问题背景

弥娅的工具系统存在以下问题：
- 存在重复/空目录（如 `web_search/`、`info/`）
- 工具分类标准不统一
- 部分工具注册逻辑冗余

#### 1.2 已完成的优化

##### 1.2.1 删除冗余目录

```bash
# 已删除的目录
- config/proactive_chat/          # 旧插件系统
- config/proactive_chat.yaml       # 冗余配置
- webnet/ToolNet/tools/web_search/  # 空目录
- webnet/ToolNet/tools/info/       # 合并到network
- webnet/ToolNet/tools/qq/qq_active_chat.py  # 废弃工具
```

##### 1.2.2 工具目录结构（当前）

```
webnet/ToolNet/tools/
├── auth/          # 认证授权
├── basic/         # 基础功能（时间/用户）
├── bilibili/      # B站
├── cognitive/     # 认知档案
├── core/          # 核心服务
├── cross_terminal/ # 跨终端
├── entertainment/ # 娱乐
├── game/          # 游戏存档
├── group/         # 群管理
├── knowledge/     # 知识库
├── life/          # 生活记忆
├── memory/        # 记忆管理
├── message/       # 消息工具
├── network/       # 网络工具（搜索/爬虫/天气等）
├── office/        # 办公文档
├── qq/            # QQ多媒体
├── reporting/     # 报表
├── scheduler/     # 定时任务
├── social/        # 社交平台（微信/Discord）
├── terminal/       # 终端工具（主）
├── terminal_net/   # 终端网络（辅助）
└── visualization/ # 可视化
```

##### 1.2.3 工具注册测试

```python
from webnet.ToolNet.registry import ToolRegistry

registry = ToolRegistry()
registry.load_all_tools()
print(f"已注册工具数量: {len(registry.tools)}")
# 输出: 已注册工具数量: 102
```

#### 1.3 原理解释

工具系统优化遵循以下原则：

1. **按功能域分类**：而非按平台分类
2. **删除空目录**：减少代码库复杂度
3. **统一配置**：主动聊天配置统一在 `config/personalities/_base.yaml`

---

### 2. QQ消息解析器升级

#### 2.1 问题背景

弥娅在处理QQ消息时存在以下问题：
- 无法识别引用消息（reply）
- 无法识别文件/语音消息
- 图片分析API调用失败

#### 2.2 解决方案

##### 2.2.1 新增模块：QQMessageParser

```python
# webnet/qq/message_parser.py
from webnet.qq.message_parser import QQMessageParser

parser = QQMessageParser()
parser.set_client(onebot_client)  # 设置QQ客户端

# 解析消息段
segments = parser.normalize_message(raw_message)

# 获取引用ID
reply_id = parser.get_reply_id(segments)
```

##### 2.2.2 新增消息段类型

```python
# webnet/qq/models.py
class ReplySegment:
    """引用消息段"""
    def __init__(self, message_id: int):
        self.type = "reply"
        self.message_id = message_id

class FileSegment:
    """文件消息段"""
    def __init__(self, file_id: str, file_name: str, file_size: int):
        self.type = "file"
        self.file_id = file_id
        self.file_name = file_name
        self.file_size = file_size
```

##### 2.2.3 视觉模型路由修复

```python
# core/model_pool.py
def select_model_for_task(self, task: str, platform: str = "terminal") -> ChatModelConfig:
    # 新增 image_description 路由
    if task == "image_description":
        return self.select_model("vision", platform=platform)
    # ... 其他路由
```

---

## 隐私感知记忆系统 (v4.3.1 新增)

### 1. 系统概述

弥娅的记忆系统现在具备**隐私感知**能力，可以：
- 自动识别消息来自群聊还是私聊
- 判断话题是否私密
- 根据隐私级别决定存储策略

### 2. 隐私级别定义

| 级别 | 说明 | 存储范围 | 示例 |
|------|------|----------|------|
| `secret` | 极密 | 仅开发者（佳）可见 | 密码、身份证号 |
| `personal` | 个人私密 | 用户专属 | 私人对话、健康信息 |
| `group_private` | 群内私密 | 群聊专属 | 群内秘密 |
| `context` | 上下文 | 当前会话 | 群聊日常对话 |
| `public` | 公开 | 全局 | 可共享的内容 |

### 3. 敏感话题检测

系统自动检测以下敏感话题：

```python
# memory/privacy_classifier.py

SENSITIVE_PATTERNS = {
    # 个人信息
    "personal_info": [
        r"(手机|电话|身份证|银行卡|密码|账号).{0,10}(号|码|码|号)",
        r"\d{11,}",  # 手机号
    ],
    # 健康相关
    "health": [
        r"(生病|生病|医院|看病|体检|确诊|病情)",
        r"(抑郁|焦虑|心理|精神|情绪崩溃)",
    ],
    # 情感相关
    "emotion": [
        r"(暗恋|表白|追求|分手|离婚)",
        r"(秘密|不能告诉别人|只告诉你)",
    ],
    # 财务相关
    "finance": [
        r"(工资|收入|存款|负债|欠款)",
        r"(借钱|借我|还钱|转账)",
    ],
}
```

### 4. 使用方法

#### 4.1 存储时自动分类

```python
from memory.privacy_memory import store_dialogue_with_privacy

# 存储对话时自动进行隐私分类
memory_id = await store_dialogue_with_privacy(
    content="我最近身体不舒服，去医院检查",
    role="user",
    user_id=123456,
    session_id="session_001",
    message_type="private",  # 私聊
)
# 系统自动判断为 personal + sensitive
```

#### 4.2 隐私感知搜索

```python
from memory.privacy_memory import search_memory_with_context

# 搜索时自动过滤不适合当前上下文的结果
results = await search_memory_with_context(
    query="关于健康的话题",
    user_id=123456,      # 当前用户
    group_id=789012,     # 当前群聊
)
# 只返回用户有权查看的记忆
```

### 5. 隐私分类结果

```python
@dataclass
class PrivacyClassification:
    chat_type: ChatType              # 聊天类型 (private/group)
    privacy_level: PrivacyLevel      # 隐私级别
    is_sensitive: bool               # 是否敏感
    sensitivity_reasons: List[str]   # 敏感原因
    should_remember: bool            # 是否应该记住
    storage_scope: str               # 存储范围
```

### 6. 测试示例

```python
from memory.privacy_classifier import PrivacyClassifier, ChatType

classifier = PrivacyClassifier()

# 测试私聊健康话题
result = classifier.classify(
    message="我最近身体不舒服，去医院检查发现有心脏病",
    chat_type=ChatType.PRIVATE,
    user_id="123456"
)
# 结果:
# - chat_type: private
# - privacy_level: personal
# - is_sensitive: True (health)
# - should_remember: True

# 测试群聊日常
result = classifier.classify(
    message="大家今天吃什么？",
    chat_type=ChatType.GROUP,
    group_id="789012"
)
# 结果:
# - chat_type: group
# - privacy_level: context
# - is_sensitive: False
# - should_remember: False
```

---

## MCP 支持增强 (v4.3.1 新增)

### 1. 概述

MCP (Model Context Protocol) 是用于连接外部工具和数据源的协议。弥娅现在原生支持 MCP，可以连接各种外部服务。

### 2. 配置文件

创建 `config/mcp.yaml`：

```yaml
# MCP (Model Context Protocol) 配置
enabled: false
config_path: "config/mcp.json"

# 工具命名策略: "mcp" (前缀mcp.) 或 "raw" (原始名称)
tool_name_strategy: "mcp"
```

### 3. MCP 服务器配置示例

创建 `config/mcp.json`：

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["-y", "@playwright/mcp@latest"]
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/directory"]
    }
  }
}
```

### 4. 使用 MCP 注册中心

```python
# webnet/mcp/registry.py
from webnet.mcp.registry import MCPToolRegistry

# 初始化 MCP
mcp_registry = MCPToolRegistry(config_path="config/mcp.json")
await mcp_registry.initialize()

# 获取工具 schema
tools_schema = mcp_registry.get_tools_schema()

# 执行 MCP 工具
result = await mcp_registry.execute_tool(
    tool_name="mcp.playwright.screenshot",
    args={"url": "https://example.com"},
    context={}
)
```

### 5. Agent 私有 MCP

可以为特定 Agent 配置独立的 MCP：

```yaml
# config/mcp.yaml
agent_mcp:
  web_agent:
    enabled: true
    servers:
      playwright: ...
```

---

## 队列管理系统 - 车站-列车模型 (v4.3.1 新增)

### 1. 概述

弥娅实现了类似 Undefined 的"车站-列车"队列模型，用于高并发消息处理。

### 2. 核心特性

- **多模型隔离**：每个 AI 模型拥有独立的请求队列组
- **非阻塞发车**：按配置节奏发车，即使前一个请求未完成
- **优先级管理**：四级优先级确保重要消息优先响应
- **自动修剪**：普通群聊队列超过阈值时自动丢弃旧请求

### 3. 队列通道

| 通道 | 优先级 | 说明 |
|------|--------|------|
| `superadmin` | 最高 | 超级管理员私聊 |
| `group_superadmin` | 高 | 群聊超级管理员 |
| `private` | 中高 | 普通私聊 |
| `group_mention` | 中 | 群聊被@ |
| `group_normal` | 低 | 群聊普通 |
| `background` | 最低 | 后台请求 |

### 4. 使用方法

```python
# core/queue_manager.py
from core.queue_manager import QueueManager, QueueLane, get_queue_manager

# 获取全局队列管理器
queue_manager = get_queue_manager()

# 入队请求
receipt = await queue_manager.enqueue(
    model_name="gpt-4",
    request_data={"message": "你好"},
    lane=QueueLane.PRIVATE
)

# 获取队列统计
stats = queue_manager.get_queue_stats()
print(f"总待处理: {queue_manager.get_total_pending()}")
```

### 5. 队列分发

```python
# 设置分发回调
async def dispatch_callback(model_name: str, request: dict):
    # 处理请求
    result = await process_request(request)
    await send_response(result)

queue_manager = QueueManager(
    dispatch_callback=dispatch_callback,
    default_interval=1.0  # 每秒发车一次
)

# 启动队列调度
await queue_manager.start()
```

---

## Skills 配置系统 (v4.3.1 新增)

### 1. 概述

弥娅现在使用统一的 YAML 配置文件来管理技能系统，包括工具注册、热重载、Agent 配置等。

### 2. 配置文件

创建 `config/skills.yaml`：

```yaml
skills:
  # 热重载配置
  hot_reload:
    enabled: true
    watch_paths:
      - "webnet/ToolNet/tools"
      - "webnet/ToolNet/agents"
    watch_files:
      - "config.json"
      - "handler.py"
    interval_seconds: 2.0
    debounce_seconds: 0.5

  # 工具注册配置
  tool_registry:
    enabled: true
    base_dir: "webnet/ToolNet/tools"
    timeout_seconds: 480.0

  # Agent 配置
  agents:
    info_agent:
      enabled: true
      description: "信息查询助手 - 天气/热搜/B站/arxiv等"
    web_agent:
      enabled: true
      description: "网络搜索助手"
    entertainment_agent:
      enabled: true
      description: "娱乐助手"
```

### 3. Agent 功能对照

| Agent | 功能 | 工具 |
|-------|------|------|
| `info_agent` | 信息查询 | weather_query, weibohot, bilibili_search, arxiv_search, whois, tcping |
| `web_agent` | 网络搜索 | web_search, crawl_webpage, grok_search |
| `entertainment_agent` | 娱乐 | ai_draw_one, horoscope, minecraft_skin |
| `file_analysis_agent` | 文件分析 | extract_pdf, extract_docx, extract_xlsx (需额外依赖) |
| `naga_code_agent` | 代码分析 | read_file, glob, search_file_content (需NagaAgent) |
| `code_delivery_agent` | 代码交付 | write_code, run_bash_command (需Docker) |

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

