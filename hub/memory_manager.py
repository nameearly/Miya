"""
记忆管理器 (Memory Manager)

职责：
1. 用户消息存储
2. AI响应存储
3. 统一跨平台记忆存储
4. 对话历史管理
5. 记忆压缩
"""

import asyncio
import logging
import re
from typing import Dict, List, Optional, Any
from datetime import datetime

from memory import (
    store_dialogue,
    store_important,
    search_memory,
    get_dialogue_history,
    MemoryLevel,
    MemorySource,
)
from memory.historian import get_historian

logger = logging.getLogger(__name__)


class MemoryManager:
    """
    记忆管理器

    单一职责：处理所有与记忆存储和管理相关的逻辑
    """

    def __init__(
        self,
        memory_net: Optional[Any] = None,
        memory_engine: Optional[Any] = None,
    ):
        self.memory_net = memory_net
        self.memory_engine = memory_engine
        self.historian = get_historian()
        logger.info("[记忆管理器] 初始化完成 (使用新版统一记忆API)")

    async def store_user_message(self, perception: Dict) -> None:
        """
        存储用户消息到记忆系统

        Args:
            perception: 感知数据
        """
        try:
            content = perception.get("content", "")
            if isinstance(content, list):
                text_parts = []
                for item in content:
                    if isinstance(item, dict):
                        item_type = item.get("type", "")
                        item_data = item.get("data", {})
                        if item_type == "text":
                            text_parts.append(item_data.get("text", ""))
                        elif item_type == "image":
                            text_parts.append("[图片]")
                    elif isinstance(item, str):
                        text_parts.append(item)
                content = " ".join(text_parts) if text_parts else ""

            user_id = str(perception.get("user_id", "unknown"))
            group_id = str(perception.get("group_id", ""))
            platform = perception.get("platform", "qq")
            sender_name = perception.get("sender_name", "用户")
            message_type = perception.get("message_type", "")
            session_id = f"qq_{user_id}"

            logger.info(f"[记忆管理器] 收到消息: {content[:50]}...")

            # 存储到 MemoryNet 对话历史
            if self.memory_net and self.memory_net.conversation_history:
                metadata = {
                    "user_id": user_id,
                    "group_id": group_id,
                    "message_type": message_type,
                    "sender": sender_name,
                    "chat_label": f"群聊_{group_id}"
                    if message_type == "group" and group_id
                    else "私聊",
                }
                await self.memory_net.conversation_history.add_message(
                    session_id=session_id,
                    role="user",
                    content=content,
                    metadata=metadata,
                )

            # 存储到统一记忆系统 (新版 API)
            await store_dialogue(
                content=content,
                role="user",
                user_id=user_id,
                session_id=session_id,
                platform=platform,
                metadata={
                    "sender_name": sender_name,
                    "message_type": message_type,
                    "group_id": group_id,
                },
            )

            # 自动检测重要信息并存储
            important_patterns = [
                (r"生日", "生日"),
                (r"我喜欢", "喜好"),
                (r"喜欢(.+)", "喜好"),
                (r"我叫", "名字"),
                (r"讨厌", "厌恶"),
                (r"星座", "星座"),
                (r"电话", "电话"),
                (r"邮箱", "邮箱"),
                (r"记住", "明确要求"),
                (r"你记着", "明确要求"),
                (r"帮我记住", "明确要求"),
            ]

            for pattern, info_type in important_patterns:
                if re.search(pattern, content):
                    priority = (
                        0.9
                        if info_type in ["生日", "电话", "邮箱", "明确要求"]
                        else 0.7
                    )
                    await store_important(
                        content=content,
                        user_id=user_id,
                        tags=[info_type],
                        priority=priority,
                        metadata={
                            "source": "auto_extract",
                            "info_type": info_type,
                        },
                    )
                    logger.info(f"[记忆管理器] 已自动存储重要信息: {info_type}")
                    break

        except Exception as e:
            logger.error(f"[记忆管理器] 存储用户消息失败: {e}", exc_info=True)

    async def store_assistant_response(self, perception: Dict, response: str) -> None:
        """
        存储 AI 响应到记忆系统

        Args:
            perception: 感知数据
            response: AI 响应内容
        """
        try:
            user_id = str(perception.get("user_id", "unknown"))
            group_id = str(perception.get("group_id", ""))
            message_type = perception.get("message_type", "")
            platform = perception.get("platform", "qq")
            session_id = f"qq_{user_id}"

            # 存储到 MemoryNet
            if self.memory_net and self.memory_net.conversation_history:
                metadata = {
                    "user_id": user_id,
                    "group_id": group_id,
                    "message_type": message_type,
                    "sender": "弥娅",
                    "chat_label": f"群聊_{group_id}"
                    if message_type == "group" and group_id
                    else "私聊",
                }
                await self.memory_net.conversation_history.add_message(
                    session_id=session_id,
                    role="assistant",
                    content=response,
                    metadata=metadata,
                )

            # 存储到统一记忆系统 (新版 API)
            await store_dialogue(
                content=response,
                role="assistant",
                user_id=user_id,
                session_id=session_id,
                platform=platform,
                metadata={
                    "sender_name": "弥娅",
                    "message_type": message_type,
                    "group_id": group_id,
                },
            )

            # 使用 Historian 自动提取重要记忆
            user_content = perception.get("content", "")
            try:
                await self.historian.process_conversation(
                    user_input=user_content,
                    ai_response=response,
                    user_id=user_id,
                    group_id=group_id,
                    message_type=message_type,
                )
            except Exception as e:
                logger.debug(f"[记忆管理器] Historian 提取失败: {e}")

            # 对话历史压缩
            try:
                if self.memory_net and self.memory_net.conversation_history:
                    messages = await self.memory_net.conversation_history.get_history(
                        session_id, limit=100
                    )
                    if len(messages) > 50:
                        if hasattr(self.memory_net, "compress_conversation_to_tide"):
                            await self.memory_net.compress_conversation_to_tide(
                                session_id=session_id, recent_count=30
                            )
                            logger.info(f"[记忆管理器] 已触发对话压缩: {session_id}")
            except Exception as e:
                logger.debug(f"[记忆管理器] 对话压缩失败: {e}")

        except Exception as e:
            logger.error(f"[记忆管理器] 存储 AI 响应失败: {e}")

    async def store_unified_memory(self, perception: Dict, role: str = "user") -> None:
        """
        存储统一记忆（跨平台）

        Args:
            perception: 感知数据
            role: 角色 ('user' 或 'assistant')
        """
        try:
            platform = perception.get("platform", "terminal")
            user_id = str(perception.get("user_id", "unknown"))

            if role == "user":
                content = perception.get("content", "") or perception.get("input", "")
                sender_name = perception.get("sender_name", "用户")
            else:
                content = perception.get("response", "")
                sender_name = "弥娅"

            session_id = f"{platform}_{user_id}"

            # 存储到统一记忆系统
            await store_dialogue(
                content=content,
                role=role,
                user_id=user_id,
                session_id=session_id,
                platform=platform,
                metadata={
                    "sender_name": sender_name,
                    "group_id": perception.get("group_id", ""),
                    "message_type": perception.get("message_type", ""),
                },
            )

            # 存储到 MemoryNet
            if self.memory_net and self.memory_net.conversation_history:
                await self.memory_net.conversation_history.add_message(
                    session_id=session_id,
                    role=role,
                    content=content,
                    metadata={
                        "platform": platform,
                        "user_id": user_id,
                        "sender_name": sender_name,
                    },
                )

        except Exception as e:
            logger.error(f"[记忆管理器] 存储统一记忆失败: {e}")

    async def get_conversation_history(
        self, session_id: str, current_input: str = "", max_tokens: int = 2000
    ) -> List[Dict]:
        """
        获取对话历史上下文

        Args:
            session_id: 会话ID
            current_input: 当前用户输入
            max_tokens: 最大token数

        Returns:
            对话历史列表
        """
        if not self.memory_net or not self.memory_net.conversation_history:
            return []

        needs_recall = self._check_needs_recall(current_input)
        max_messages = 30 if needs_recall else 8

        try:
            messages = await self.memory_net.conversation_history.get_history(
                session_id, limit=max_messages
            )

            if not messages:
                return []

            recent_messages = (
                messages[-max_messages:] if len(messages) > max_messages else messages
            )

            context = []
            total_tokens = 0

            for msg in recent_messages:
                token_estimate = len(msg.content) // 4
                if total_tokens + token_estimate > max_tokens:
                    break

                context.append(
                    {
                        "role": msg.role,
                        "content": msg.content,
                        "timestamp": msg.timestamp if hasattr(msg, "timestamp") else "",
                    }
                )
                total_tokens += token_estimate

            return context

        except Exception as e:
            logger.error(f"[记忆管理器] 获取对话历史失败: {e}")
            return []

    def _check_needs_recall(self, user_input: str) -> bool:
        """检测用户是否在问关于过去的问题"""
        if not user_input:
            return False

        recall_patterns = [
            r"你记得",
            r"你还记得",
            r"记得.*吗",
            r"上次",
            r"上次我们",
            r"之前.*聊",
            r"昨天",
            r"前天",
            r"以前.*怎么样",
            r"我们.*聊过",
            r"过去.*事",
            r"曾经",
            r"记得.*什么",
            r"回忆.*一下",
            r"想起.*什么",
        ]

        for pattern in recall_patterns:
            if re.search(pattern, user_input):
                logger.info(f"[记忆管理器] 检测到回忆请求: {user_input[:30]}")
                return True

        return False

    async def get_memory_stats(self) -> Dict:
        """获取记忆统计信息"""
        try:
            from memory import get_memory_stats

            return await get_memory_stats()
        except Exception as e:
            logger.error(f"[记忆管理器] 获取统计失败: {e}")
            return {}
