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
from typing import Dict, List, Optional, Any
from datetime import datetime


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
        unified_memory: Optional[Any] = None,
    ):
        """
        初始化记忆管理器

        Args:
            memory_net: MemoryNet实例
            memory_engine: 记忆引擎实例
            unified_memory: 统一记忆系统（用于JSON持久化）
        """
        self.memory_net = memory_net
        self.memory_engine = memory_engine
        self.unified_memory = unified_memory
        logger.info("[记忆管理器] 初始化完成")

    async def store_user_message(self, perception: Dict) -> None:
        """
        存储用户消息到记忆系统

        Args:
            perception: 感知数据
        """
        try:
            # 存储到 MemoryNet 对话历史
            if self.memory_net and self.memory_net.conversation_history:
                session_id = f"qq_{perception.get('user_id', 'unknown')}"

                await self.memory_net.conversation_history.add_message(
                    session_id=session_id,
                    role="user",
                    content=perception.get("content", ""),
                    metadata={
                        "user_id": perception.get("user_id"),
                        "group_id": perception.get("group_id"),
                        "message_type": perception.get("message_type"),
                        "sender": perception.get("sender_name", ""),
                    },
                )

                logger.debug("[记忆管理器] 用户消息已存储到对话历史")

            # 存储到统一记忆系统（JSON持久化）
            if self.unified_memory:
                try:
                    content = perception.get("content", "")
                    user_id = perception.get("user_id", "unknown")
                    platform = perception.get("platform", "qq")

                    if asyncio.iscoroutinefunction(self.unified_memory.add_short_term):
                        await self.unified_memory.add_short_term(
                            content=content,
                            user_id=user_id,
                            group_id=perception.get("group_id", ""),
                            priority=0.5,
                            metadata={
                                "platform": platform,
                                "role": "user",
                                "sender_name": perception.get("sender_name", "用户"),
                                "message_type": perception.get("message_type", ""),
                            },
                        )
                    else:
                        self.unified_memory.add_short_term(
                            content=content,
                            user_id=user_id,
                            group_id=perception.get("group_id", ""),
                            priority=0.5,
                            metadata={
                                "platform": platform,
                                "role": "user",
                                "sender_name": perception.get("sender_name", "用户"),
                                "message_type": perception.get("message_type", ""),
                            },
                        )
                    logger.debug("[记忆管理器] 用户消息已持久化到JSON")
                except Exception as e:
                    logger.warning(f"[记忆管理器] 统一记忆存储失败: {e}")
        except Exception as e:
            logger.error(f"[记忆管理器] 存储用户消息失败: {e}")

    async def store_assistant_response(self, perception: Dict, response: str) -> None:
        """
        存储 AI 响应到记忆系统

        Args:
            perception: 感知数据
            response: AI 响应内容
        """
        try:
            if self.memory_net and self.memory_net.conversation_history:
                session_id = f"qq_{perception.get('user_id', 'unknown')}"

                await self.memory_net.conversation_history.add_message(
                    session_id=session_id,
                    role="assistant",
                    content=response,
                    metadata={
                        "user_id": perception.get("user_id"),
                        "group_id": perception.get("group_id"),
                        "message_type": perception.get("message_type"),
                        "sender": "弥娅",
                    },
                )

                logger.debug("[记忆管理器] AI 响应已存储到对话历史")

                # 自动提取重要信息到 Undefined 记忆
                try:
                    user_content = perception.get("content", "")
                    if self.memory_net:
                        await self.memory_net.extract_and_store_important_info(
                            content=user_content, user_id=perception.get("user_id")
                        )
                except Exception as e:
                    logger.debug(f"[记忆管理器] 自动提取记忆失败: {e}")

                # 对话历史压缩（当对话历史过长时）
                try:
                    if self.memory_net.conversation_history:
                        messages = (
                            await self.memory_net.conversation_history.get_history(
                                session_id, limit=100
                            )
                        )
                        # 只有对话超过50条才触发压缩
                        if len(messages) > 50:
                            await self.memory_net.compress_conversation_to_tide(
                                session_id=session_id, recent_count=30
                            )
                            logger.info(f"[记忆管理器] 已触发对话压缩: {session_id}")
                except Exception as e:
                    logger.debug(f"[记忆管理器] 对话压缩失败: {e}")

            # 存储到统一记忆系统（JSON持久化）
            if self.unified_memory:
                try:
                    user_id = perception.get("user_id", "unknown")
                    platform = perception.get("platform", "qq")

                    if asyncio.iscoroutinefunction(self.unified_memory.add_short_term):
                        await self.unified_memory.add_short_term(
                            content=response,
                            user_id=user_id,
                            group_id=perception.get("group_id", ""),
                            priority=0.5,
                            metadata={
                                "platform": platform,
                                "role": "assistant",
                                "sender_name": "弥娅",
                                "message_type": perception.get("message_type", ""),
                            },
                        )
                    else:
                        self.unified_memory.add_short_term(
                            content=response,
                            user_id=user_id,
                            group_id=perception.get("group_id", ""),
                            priority=0.5,
                            metadata={
                                "platform": platform,
                                "role": "assistant",
                                "sender_name": "弥娅",
                                "message_type": perception.get("message_type", ""),
                            },
                        )
                    logger.debug("[记忆管理器] AI响应已持久化到JSON")
                except Exception as e:
                    logger.warning(f"[记忆管理器] 统一记忆存储失败: {e}")

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
            user_id = perception.get("user_id", "unknown")

            # 如果是用户输入
            if role == "user":
                content = perception.get("content", "") or perception.get("input", "")
                sender_name = perception.get("sender_name", "用户")
            else:
                content = perception.get("response", "")
                sender_name = "弥娅"

            # 存储到潮汐记忆（MemoryEngine - 内存+Redis）
            if self.memory_engine:
                self.memory_engine.store_tide(
                    f"{platform}_{user_id}_{role}_{int(datetime.now().timestamp())}",
                    {
                        "platform": platform,
                        "user_id": user_id,
                        "role": role,
                        "content": content,
                        "sender_name": sender_name,
                        "timestamp": perception.get("timestamp", datetime.now()),
                        "metadata": {
                            "sender_name": perception.get("sender_name"),
                            "group_id": perception.get("group_id"),
                            "message_type": perception.get("message_type"),
                        },
                    },
                )

            # 存储到统一记忆系统（JSON持久化）
            if self.unified_memory:
                try:
                    import asyncio

                    if asyncio.iscoroutinefunction(self.unified_memory.add_short_term):
                        await self.unified_memory.add_short_term(
                            content=content,
                            user_id=user_id,
                            group_id=perception.get("group_id", ""),
                            priority=0.5,
                            metadata={
                                "platform": platform,
                                "role": role,
                                "sender_name": sender_name,
                                "message_type": perception.get("message_type", ""),
                            },
                        )
                    else:
                        self.unified_memory.add_short_term(
                            content=content,
                            user_id=user_id,
                            group_id=perception.get("group_id", ""),
                            priority=0.5,
                            metadata={
                                "platform": platform,
                                "role": role,
                                "sender_name": sender_name,
                                "message_type": perception.get("message_type", ""),
                            },
                        )
                    logger.debug(
                        f"[记忆管理器] 记忆已持久化到JSON: {platform}/{user_id}/{role}"
                    )
                except Exception as e:
                    logger.warning(f"[记忆管理器] 统一记忆存储失败: {e}")

            # 如果有 MemoryNet，也存储到对话历史
            if self.memory_net and self.memory_net.conversation_history:
                session_id = f"{platform}_{user_id}"
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

        # 检测是否需要回忆
        needs_recall = self._check_needs_recall(current_input)

        max_messages = 20 if needs_recall else 3

        try:
            messages = await self.memory_net.conversation_history.get_history(
                session_id, limit=max_messages
            )

            context = []
            total_tokens = 0

            if not messages:
                return context

            recent_messages = (
                messages[-max_messages:] if len(messages) > max_messages else messages
            )

            for msg in recent_messages:
                token_estimate = len(msg.content) // 4
                if total_tokens + token_estimate > max_tokens:
                    break

                context.append(
                    {
                        "role": msg.role,
                        "content": msg.content,
                        "timestamp": msg.timestamp,
                    }
                )
                total_tokens += token_estimate

            return context

        except Exception as e:
            logger.error(f"[记忆管理器] 获取对话历史失败: {e}")
            return []

    def _check_needs_recall(self, user_input: str) -> bool:
        """
        检测用户是否在问关于过去的问题

        Args:
            user_input: 当前用户输入

        Returns:
            是否需要回忆过去
        """
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
            r"记得.*吗",
            r"回忆.*一下",
            r"想起.*什么",
        ]

        import re

        for pattern in recall_patterns:
            if re.search(pattern, user_input):
                logger.info(f"[记忆管理器] 检测到回忆请求: {user_input[:30]}")
                return True

        return False

    async def get_memory_stats(self) -> Dict:
        """
        获取记忆统计信息

        Returns:
            记忆统计字典
        """
        if self.memory_engine:
            return self.memory_engine.get_memory_stats()
        return {}
