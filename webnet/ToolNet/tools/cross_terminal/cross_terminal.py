"""
跨终端操作工具 v2.0

实现真正的多端联动功能：
1. 消息同步 - QQ/终端/Web/桌面消息互通
2. 状态共享 - 各端状态实时同步
3. 通知推送 - 一端通知多端推送
4. 命令转发 - 一端发命令另一端执行
"""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from webnet.ToolNet.base import BaseTool
from webnet.ToolNet.base import ToolContext

logger = logging.getLogger(__name__)


class CrossTerminalHub:
    """
    跨端消息Hub

    使用内存存储实现本地跨端通信
    """

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if CrossTerminalHub._initialized:
            return

        # 消息存储
        self.messages: Dict[str, list] = {
            "qq": [],
            "terminal": [],
            "web": [],
            "desktop": [],
        }

        # 在线终端
        self.online_terminals: Dict[str, datetime] = {}

        # 状态存储
        self.state: Dict[str, Any] = {}

        # 消息限制
        self.max_messages_per_terminal = 100

        CrossTerminalHub._initialized = True

    def register_terminal(self, terminal_type: str) -> bool:
        """注册终端"""
        self.online_terminals[terminal_type] = datetime.now()
        logger.info(f"[CrossTerminal] 终端 {terminal_type} 已注册")
        return True

    def unregister_terminal(self, terminal_type: str):
        """注销终端"""
        if terminal_type in self.online_terminals:
            del self.online_terminals[terminal_type]
            logger.info(f"[CrossTerminal] 终端 {terminal_type} 已注销")

    def send_message(
        self,
        source: str,
        target: str,
        content: str,
        message_type: str = "text",
        metadata: Optional[Dict] = None,
    ) -> str:
        """
        发送跨端消息

        Args:
            source: 源终端
            target: 目标终端（None表示广播）
            content: 消息内容
            message_type: 消息类型
            metadata: 额外数据

        Returns:
            消息ID
        """
        import uuid

        msg_id = str(uuid.uuid4())

        message = {
            "id": msg_id,
            "source": source,
            "target": target,
            "content": content,
            "type": message_type,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat(),
        }

        # 存储消息
        if target:
            # 单发
            if target not in self.messages:
                self.messages[target] = []
            self.messages[target].append(message)
        else:
            # 广播
            for terminal in self.messages:
                self.messages[terminal].append(message.copy())

        # 限制消息数量
        for terminal in self.messages:
            if len(self.messages[terminal]) > self.max_messages_per_terminal:
                self.messages[terminal] = self.messages[terminal][
                    -self.max_messages_per_terminal :
                ]

        logger.info(f"[CrossTerminal] 消息发送: {source} -> {target or 'broadcast'}")
        return msg_id

    def get_messages(self, terminal: str, since: Optional[str] = None) -> list:
        """获取指定终端的消息"""
        messages = self.messages.get(terminal, [])

        if since:
            since_time = datetime.fromisoformat(since)
            messages = [
                m
                for m in messages
                if datetime.fromisoformat(m["timestamp"]) > since_time
            ]

        return messages

    def clear_messages(self, terminal: str):
        """清除终端消息"""
        if terminal in self.messages:
            self.messages[terminal] = []

    def set_state(self, key: str, value: Any):
        """设置跨端状态"""
        self.state[key] = {
            "value": value,
            "updated_at": datetime.now().isoformat(),
            "updated_by": None,
        }
        logger.info(f"[CrossTerminal] 状态更新: {key}")

    def get_state(self, key: str, default: Any = None) -> Any:
        """获取跨端状态"""
        return self.state.get(key, {}).get("value", default)

    def get_online_terminals(self) -> list:
        """获取在线终端列表"""
        return list(self.online_terminals.keys())

    def is_terminal_online(self, terminal: str) -> bool:
        """检查终端是否在线"""
        return terminal in self.online_terminals


# 全局Hub实例
_cross_terminal_hub = None


def get_cross_terminal_hub() -> CrossTerminalHub:
    """获取跨端Hub实例"""
    global _cross_terminal_hub
    if _cross_terminal_hub is None:
        _cross_terminal_hub = CrossTerminalHub()
    return _cross_terminal_hub


class CrossTerminalTool(BaseTool):
    """跨终端操作工具"""

    @property
    def config(self) -> Dict[str, Any]:
        return {
            "name": "cross_terminal",
            "description": """在不同终端之间执行操作，支持：
- 发送消息到其他终端
- 查询其他终端的消息
- 同步状态到所有终端
- 检查终端在线状态

例如：
- 从QQ发送消息到终端
- 从终端发送消息到QQ
- 在所有终端显示通知""",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "description": "操作类型: send（发送消息）, query（查询消息）, sync（同步状态）, status（状态检查）",
                        "enum": ["send", "query", "sync", "status"],
                    },
                    "target": {
                        "type": "string",
                        "description": "目标终端: qq, terminal, web, desktop 或 all（全部）",
                    },
                    "source": {
                        "type": "string",
                        "description": "源终端（可选，自动检测）",
                    },
                    "content": {
                        "type": "string",
                        "description": "消息内容（send/sync操作需要）",
                    },
                    "message_type": {
                        "type": "string",
                        "description": "消息类型: text（文本）, notification（通知）, command（命令）",
                        "default": "text",
                    },
                    "since": {
                        "type": "string",
                        "description": "查询起始时间ISO格式（query操作需要）",
                    },
                },
                "required": ["action"],
            },
        }

    async def execute(self, args: Dict, context: ToolContext) -> str:
        """执行跨终端操作"""
        action = args.get("action")
        target = args.get("target", "all")
        source = args.get("source")
        content = args.get("content", "")
        message_type = args.get("message_type", "text")
        since = args.get("since")

        # 获取Hub实例
        hub = get_cross_terminal_hub()

        # 自动检测源终端
        if not source:
            source = self._detect_source(context)

        if action == "send":
            # 发送消息
            if not content:
                return "❌ 发送消息需要提供 content 参数"

            msg_id = hub.send_message(
                source=source,
                target=target if target != "all" else None,
                content=content,
                message_type=message_type,
                metadata={"context": str(context.session_id) if context else None},
            )

            target_display = target if target != "all" else "所有终端"
            return f"✅ 消息已发送到 {target_display}\n📝 消息ID: {msg_id}"

        elif action == "query":
            # 查询消息
            if target == "all":
                return f"❌ query 操作需要指定 target 终端"

            messages = hub.get_messages(target, since)

            if not messages:
                return f"📭 {target} 终端暂无新消息"

            # 构建消息列表
            msg_list = [f"📬 {target} 终端消息 ({len(messages)}条):"]
            for msg in messages[-10:]:  # 只显示最近10条
                timestamp = msg["timestamp"][11:19]  # 只显示时间部分
                msg_list.append(
                    f"  [{timestamp}] {msg['source']}: {msg['content'][:50]}"
                )

            return "\n".join(msg_list)

        elif action == "sync":
            # 同步状态
            if not content:
                return "❌ 同步状态需要提供 content 参数"

            try:
                data = json.loads(content)
                for key, value in data.items():
                    hub.set_state(key, value)
                return f"✅ 状态已同步到所有终端\n📋 同步内容: {list(data.keys())}"
            except json.JSONDecodeError:
                hub.set_state(target or "shared", content)
                return f"✅ 状态已同步: {content[:50]}"

        elif action == "status":
            # 状态检查
            online = hub.get_online_terminals()
            status_info = ["📡 终端在线状态:"]

            for terminal in ["qq", "terminal", "web", "desktop"]:
                if terminal in online:
                    status_info.append(f"  ✅ {terminal}: 在线")
                else:
                    status_info.append(f"  ❌ {terminal}: 离线")

            return "\n".join(status_info)

        else:
            return f"❌ 未知操作: {action}"

    def _detect_source(self, context: ToolContext) -> str:
        """检测源终端"""
        if not context:
            return "unknown"

        # 根据session_id或其他信息推断
        session_id = str(context.session_id or "")

        if "qq" in session_id.lower():
            return "qq"
        elif "web" in session_id.lower():
            return "web"
        elif "desktop" in session_id.lower():
            return "desktop"
        elif "terminal" in session_id.lower():
            return "terminal"

        return "terminal"  # 默认终端
