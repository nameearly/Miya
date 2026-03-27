# Miya Skills Architecture

## 概述

弥娅技能系统采用分层架构，统一管理所有 AI 能力。

## 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                     ToolNet (92工具)                         │
│                  (webnet/ToolNet/registry.py)               │
├─────────────────────────────────────────────────────────────┤
│  • 基础工具 (terminal_exec, file_read, etc.)                │
│  • Git 工具 (git_status, git_diff, etc.)                   │
│  • Agent 工具 (code_explorer_agent, etc.)                   │
│  • 智能工具 (project_context, task_plan, etc.)              │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │ 使用
┌─────────────────────────────────────────────────────────────┐
│               Skills Registry (15技能)                       │
│                  (core/skills/registry.py)                 │
├─────────────────────────────────────────────────────────────┤
│  Agents (5)        MCP Services (5)    Commands (4)        │
│  • code_explorer    • filesystem        • /git             │
│  • code_reviewer    • memory           • /feature-dev      │
│  • code_architect   • database         • /project          │
│  • security_reviewer web_search        • /code             │
│  • performance_    • code_executor                        │
│    analyzer                                                │
└─────────────────────────────────────────────────────────────┘
```

## 核心组件

### 1. Skills Registry (`core/skills/registry.py`)

统一技能注册中心，提供:

```python
# 获取注册表
registry = await get_skills_registry()

# 获取 Agent handler
handler = await get_agent_handler("code_explorer")

# 获取 MCP 工具 schema
schemas = await get_mcp_tools_schema()

# 调用 MCP 服务
result = await call_mcp_service("filesystem", "read_file", {"file_path": "test.py"})

# 列出所有技能
all_skills = registry.get_help()
```

### 2. Agent 定义 (`core/skills/agents/`)

每个 Agent 目录结构:

```
core/skills/agents/code_explorer/
├── handler.py    # Agent 入口点，必须导出 handler 函数
└── README.md    # 可选文档
```

Agent handler 签名:

```python
async def handler(args: Dict[str, Any], context: Dict[str, Any]) -> str:
    """
    Args:
        args: Agent 参数
        context: 执行上下文
        
    Returns:
        str: 执行结果
    """
    ...
```

### 3. MCP Services (`mcpserver/`)

每个 MCP 服务目录结构:

```
mcpserver/filesystem/
├── service.py          # 服务实现
└── agent-manifest.json # 服务配置
```

### 4. Slash Commands (`core/skills/slash_commands.py`)

命令定义在 `slash_commands.py` 的 `_register_default_commands()` 方法中。

## 工具 vs 技能

| 概念 | 位置 | 说明 |
|------|------|------|
| **Tool** | ToolNet | AI 模型可以直接调用的工具 |
| **Skill** | Skills Registry | 更高层的技能抽象 |

ToolNet 使用 Skills Registry:
- 获取 Agent handler
- 获取 MCP 服务信息
- 列出所有可用技能

## 调用路径

### 方式 1: 直接调用 (Terminal Ultra)

```python
from core.terminal_ultra import call_agent

result = await call_agent("code_explorer", {"action": "explore", "target": "src/"})
```

### 方式 2: 通过 ToolNet

```json
{
  "name": "code_explorer_agent",
  "parameters": {
    "action": "explore",
    "target": "src/"
  }
}
```

### 方式 3: 通过 Skills Registry

```python
from core.skills.registry import get_skills_registry

registry = await get_skills_registry()
print(registry.get_help())
```

## 新增 API

### get_agent_handler(agent_name: str)

获取 Agent handler 函数。

### call_mcp_service(service_name: str, tool_name: str, params: Dict)

调用 MCP 服务。

### get_mcp_tools_schema()

获取所有 MCP 服务的工具定义。

## 注意事项

1. **不要重复定义**: Agent 只在 `core/skills/agents/` 定义一次
2. **ToolNet 桥接**: ToolNet 通过 Skills Registry 获取能力
3. **MCP 服务**: 需要在 `mcpserver/` 目录实现并配置 manifest
