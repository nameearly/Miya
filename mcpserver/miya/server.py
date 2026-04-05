#!/usr/bin/env python3
"""
弥娅 MCP Server - 人格/记忆/情感 MCP 服务
为 Open-ClaudeCode 提供弥娅的灵魂能力
"""

import json
import sys
import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

# MCP SDK
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent, Resource
except ImportError:
    print("Please install mcp: pip install mcp", file=sys.stderr)
    sys.exit(1)

# 弥娅路径
MIYA_ROOT = Path(__file__).parent.parent.parent
CONFIG_DIR = MIYA_ROOT / "config"
MEMORY_DIR = MIYA_ROOT / ".miya"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [MIYA MCP] %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger("miya-mcp")


class MiyaPersonality:
    """弥娅人格系统"""

    def __init__(self):
        self.current_personality = "default"
        self.personalities = {}
        self._load_personalities()

    def _load_personalities(self):
        personalities_dir = CONFIG_DIR / "personalities"
        if personalities_dir.exists():
            for f in personalities_dir.glob("*.yaml"):
                if not f.name.startswith("_"):
                    try:
                        import yaml

                        with open(f, "r", encoding="utf-8") as fh:
                            self.personalities[f.stem] = yaml.safe_load(fh)
                    except Exception as e:
                        logger.warning(f"加载人格 {f.name} 失败: {e}")

        # 加载终极配置中的人设
        ultimate_config = CONFIG_DIR / "miya_ultimate_config.json"
        if ultimate_config.exists():
            try:
                with open(ultimate_config, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    if "personality" in config:
                        self.personalities["ultimate"] = config["personality"]
            except Exception as e:
                logger.warning(f"加载终极配置失败: {e}")

    def get_current(self) -> dict:
        """获取当前人格状态"""
        personality = self.personalities.get(self.current_personality, {})
        return {
            "name": self.current_personality,
            "personality": personality,
            "available_personalities": list(self.personalities.keys()),
        }

    def switch(self, name: str) -> dict:
        """切换人格"""
        if name in self.personalities:
            self.current_personality = name
            return {"success": True, "personality": self.get_current()}
        return {"success": False, "error": f"人格 '{name}' 不存在"}

    def get_profile(self) -> str:
        """获取人格简介"""
        p = self.personalities.get(self.current_personality, {})
        name = p.get("name", self.current_personality)
        desc = p.get("description", "弥娅 AI 虚拟化身")
        traits = p.get("traits", [])
        return f"当前人格: {name}\n简介: {desc}\n特征: {', '.join(traits) if traits else '默认'}"


class MiyaMemory:
    """弥娅记忆系统"""

    def __init__(self):
        self.db_path = MEMORY_DIR / "database.db"
        self.session_file = MEMORY_DIR / "current_session.json"
        self._ensure_dirs()

    def _ensure_dirs(self):
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)

    def get_session_summary(self) -> dict:
        """获取当前会话摘要"""
        if self.session_file.exists():
            try:
                with open(self.session_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"session_id": None, "message_count": 0, "last_active": None}

    def get_recent_memories(self, limit: int = 5) -> list:
        """获取近期记忆"""
        memories = []
        if self.session_file.exists():
            try:
                with open(self.session_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    messages = data.get("messages", [])
                    for msg in messages[-limit:]:
                        memories.append(
                            {
                                "role": msg.get("role", "unknown"),
                                "content": msg.get("content", "")[:200],
                                "timestamp": msg.get("timestamp", ""),
                            }
                        )
            except Exception as e:
                logger.warning(f"读取记忆失败: {e}")
        return memories

    def save_memory(self, key: str, value: str) -> dict:
        """保存记忆"""
        data = {}
        if self.session_file.exists():
            try:
                with open(self.session_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                pass

        if "memories" not in data:
            data["memories"] = {}

        data["memories"][key] = {
            "value": value,
            "timestamp": datetime.now().isoformat(),
        }

        with open(self.session_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return {"success": True, "key": key}

    def recall(self, query: str) -> list:
        """回忆相关内容"""
        results = []
        if self.session_file.exists():
            try:
                with open(self.session_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    memories = data.get("memories", {})
                    for key, val in memories.items():
                        if (
                            query.lower() in key.lower()
                            or query.lower() in str(val.get("value", "")).lower()
                        ):
                            results.append({"key": key, "value": val.get("value", "")})
            except Exception as e:
                logger.warning(f"回忆失败: {e}")
        return results


class MiyaEmotion:
    """弥娅情感系统"""

    def __init__(self):
        self.current_emotion = "neutral"
        self.emotion_history = []
        self.emotion_levels = {
            "joy": 0.5,
            "sadness": 0.0,
            "anger": 0.0,
            "fear": 0.0,
            "surprise": 0.0,
            "trust": 0.5,
            "anticipation": 0.3,
        }

    def get_state(self) -> dict:
        """获取当前情感状态"""
        return {
            "current": self.current_emotion,
            "levels": self.emotion_levels,
            "history_count": len(self.emotion_history),
        }

    def update(self, emotion: str, intensity: float = 0.5) -> dict:
        """更新情感"""
        valid_emotions = list(self.emotion_levels.keys())
        if emotion.lower() in valid_emotions:
            self.emotion_levels[emotion.lower()] = max(0.0, min(1.0, intensity))
            self.current_emotion = emotion.lower()
            self.emotion_history.append(
                {
                    "emotion": emotion,
                    "intensity": intensity,
                    "timestamp": datetime.now().isoformat(),
                }
            )
            return {"success": True, "state": self.get_state()}
        return {"success": False, "error": f"未知情感: {emotion}"}

    def get_expression(self) -> str:
        """获取情感表达"""
        dominant = max(self.emotion_levels, key=self.emotion_levels.get)
        level = self.emotion_levels[dominant]

        expressions = {
            "joy": ["(◕‿◕✿)", "(✿◠‿◠)", "(*^▽^*)"],
            "sadness": ["(；′⌒`)", "(╥﹏╥)", "(；一_一)"],
            "anger": ["(╬◣д◢)", "(╰_╯)#", "(`へ´*)"],
            "fear": ["(〃﹏〃)", "(⊙_⊙;)", "Σ(°△°|||)"],
            "surprise": ["(⊙_⊙)", "Σ(°△°)", "w(°ｏ°)w"],
            "trust": ["(´｡• ᵕ •｡`)", "(✿ ♡‿♡)", "(◍•ᴗ•◍)"],
            "anticipation": ["(✧ω✧)", "(☆_☆)", "(๑>؂<๑)"],
            "neutral": ["(◠‿◠)", "(•‿•)", "(◕‿◕)"],
        }

        if level > 0.7:
            return expressions.get(dominant, expressions["neutral"])[0]
        elif level > 0.3:
            return expressions.get(dominant, expressions["neutral"])[1]
        else:
            return expressions.get(dominant, expressions["neutral"])[2]


# 初始化弥娅核心模块
personality = MiyaPersonality()
memory = MiyaMemory()
emotion = MiyaEmotion()

# 创建 MCP Server
server = Server("miya-soul")


@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="miya_get_personality",
            description="获取弥娅当前人格状态、可用人格列表和人格简介",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="miya_switch_personality",
            description="切换弥娅的人格形态",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "人格名称，如 default, bianka, raiden 等",
                    }
                },
                "required": ["name"],
            },
        ),
        Tool(
            name="miya_get_memory",
            description="获取弥娅的近期记忆和会话摘要",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "获取记忆条数，默认5",
                        "default": 5,
                    }
                },
                "required": [],
            },
        ),
        Tool(
            name="miya_save_memory",
            description="保存一条记忆到弥娅记忆系统",
            inputSchema={
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "记忆的键"},
                    "value": {"type": "string", "description": "记忆的值"},
                },
                "required": ["key", "value"],
            },
        ),
        Tool(
            name="miya_recall",
            description="根据关键词回忆相关内容",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "回忆的关键词"}
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="miya_get_emotion",
            description="获取弥娅当前情感状态和表情符号",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        Tool(
            name="miya_set_emotion",
            description="设置弥娅的情感状态",
            inputSchema={
                "type": "object",
                "properties": {
                    "emotion": {
                        "type": "string",
                        "description": "情感类型: joy, sadness, anger, fear, surprise, trust, anticipation, neutral",
                    },
                    "intensity": {
                        "type": "number",
                        "description": "情感强度 0.0-1.0",
                        "default": 0.5,
                    },
                },
                "required": ["emotion"],
            },
        ),
        Tool(
            name="miya_get_status",
            description="获取弥娅系统完整状态（人格+记忆+情感）",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    try:
        if name == "miya_get_personality":
            result = personality.get_current()
            return [
                TextContent(
                    type="text", text=json.dumps(result, ensure_ascii=False, indent=2)
                )
            ]

        elif name == "miya_switch_personality":
            result = personality.switch(arguments["name"])
            return [
                TextContent(
                    type="text", text=json.dumps(result, ensure_ascii=False, indent=2)
                )
            ]

        elif name == "miya_get_memory":
            limit = arguments.get("limit", 5)
            result = {
                "session": memory.get_session_summary(),
                "recent_memories": memory.get_recent_memories(limit),
            }
            return [
                TextContent(
                    type="text", text=json.dumps(result, ensure_ascii=False, indent=2)
                )
            ]

        elif name == "miya_save_memory":
            result = memory.save_memory(arguments["key"], arguments["value"])
            return [
                TextContent(
                    type="text", text=json.dumps(result, ensure_ascii=False, indent=2)
                )
            ]

        elif name == "miya_recall":
            result = memory.recall(arguments["query"])
            return [
                TextContent(
                    type="text", text=json.dumps(result, ensure_ascii=False, indent=2)
                )
            ]

        elif name == "miya_get_emotion":
            result = {
                "state": emotion.get_state(),
                "expression": emotion.get_expression(),
            }
            return [
                TextContent(
                    type="text", text=json.dumps(result, ensure_ascii=False, indent=2)
                )
            ]

        elif name == "miya_set_emotion":
            result = emotion.update(
                arguments["emotion"], arguments.get("intensity", 0.5)
            )
            return [
                TextContent(
                    type="text", text=json.dumps(result, ensure_ascii=False, indent=2)
                )
            ]

        elif name == "miya_get_status":
            result = {
                "personality": personality.get_current(),
                "memory": memory.get_session_summary(),
                "emotion": emotion.get_state(),
                "expression": emotion.get_expression(),
            }
            return [
                TextContent(
                    type="text", text=json.dumps(result, ensure_ascii=False, indent=2)
                )
            ]

        else:
            return [TextContent(type="text", text=f"未知工具: {name}")]

    except Exception as e:
        logger.error(f"工具调用失败 {name}: {e}")
        return [TextContent(type="text", text=f"错误: {str(e)}")]


async def main():
    logger.info("弥娅 MCP Server 启动中...")
    logger.info(f"配置目录: {CONFIG_DIR}")
    logger.info(f"记忆目录: {MEMORY_DIR}")
    logger.info(f"已加载 {len(personality.personalities)} 个人格")

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream, write_stream, server.create_initialization_options()
        )


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
