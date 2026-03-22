"""对话历史上下文管理器

负责对话历史的智能加载和上下文管理
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class ConversationContextManager:
    """对话历史上下文管理器
    
    职责：
    - 智能判断是否需要加载历史对话
    - 根据Token限制动态调整上下文大小
    - 检测用户的"回忆"意图
    """

    def __init__(
        self,
        memory_net,
        enable_conversation_context: bool = True,
        conversation_context_max_count: int = 10,
        conversation_context_max_tokens: int = 2000
    ):
        """
        初始化对话上下文管理器

        Args:
            memory_net: MemoryNet记忆系统
            enable_conversation_context: 是否启用对话上下文
            conversation_context_max_count: 最大消息数量
            conversation_context_max_tokens: 最大Token数量
        """
        self.memory_net = memory_net
        self.enable_conversation_context = enable_conversation_context
        self.conversation_context_max_count = conversation_context_max_count
        self.conversation_context_max_tokens = conversation_context_max_tokens

    def check_needs_recall(self, user_input: str) -> bool:
        """
        检测用户是否在问关于过去的问题

        Args:
            user_input: 当前用户输入（可能是字符串或列表）

        Returns:
            是否需要回忆过去
        """
        # 安全处理用户输入 - 处理图片消息等非字符串情况
        if not user_input:
            return False
            
        if not isinstance(user_input, str):
            if isinstance(user_input, list):
                # 尝试从列表中提取文本（QQ图片消息格式）
                content_str = ""
                for item in user_input:
                    if isinstance(item, dict):
                        item_type = item.get("type", "")
                        if item_type == "text":
                            content_str += item.get("data", {}).get("text", "")
                        elif item_type == "image":
                            # 图片消息，不需要回忆检测
                            continue
                    elif isinstance(item, str):
                        content_str += item
                user_input = content_str if content_str else ""
            else:
                # 其他类型转换为字符串
                user_input = str(user_input)
        
        if not user_input:
            return False

        recall_patterns = [
            r'你记得', r'你还记得', r'记得.*吗',
            r'上次', r'上次我们', r'之前.*聊',
            r'昨天', r'前天', r'以前.*怎么样',
            r'我们.*聊过', r'过去.*事', r'曾经',
            r'记得.*什么', r'记得.*吗',
            r'回忆.*一下', r'想起.*什么',
        ]

        import re
        for pattern in recall_patterns:
            if re.search(pattern, user_input):
                logger.info(f"[对话上下文] 检测到回忆请求: {user_input[:30]}")
                return True

        return False

    async def get_conversation_context(
        self,
        session_id: str,
        current_input: str = ""
    ) -> List[Dict]:
        """
        获取对话历史上下文（限制token消耗）

        智能记忆策略：
        - 短期对话：只加载最近3条，确保连贯性
        - 长期记忆：只有用户明确问"你还记得..."时才加载历史，否则不干扰

        Args:
            session_id: 会话ID
            current_input: 当前用户输入（用于判断是否需要回忆）

        Returns:
            对话历史列表
        """
        if not self.enable_conversation_context:
            return []

        if not self.memory_net or not self.memory_net.conversation_history:
            return []

        # 检测用户是否在问关于过去的问题
        needs_recall = self.check_needs_recall(current_input)

        # 根据是否需要回忆决定加载数量
        if needs_recall:
            max_messages = 20
            logger.info(f"[对话上下文] 用户正在回忆过去，加载历史对话: {session_id}")
        else:
            max_messages = 3
            logger.debug(f"[对话上下文] 正常对话，只加载最近3条: {session_id}")

        try:
            messages = await self.memory_net.conversation_history.get_history(
                session_id,
                limit=max_messages
            )

            context = []
            total_tokens = 0

            if not messages:
                return context

            # 根据是否需要回忆选择加载数量
            if needs_recall:
                recent_messages = messages[-max_messages:] if len(messages) > max_messages else messages
            else:
                recent_messages = messages[-3:] if len(messages) > 3 else messages

            logger.debug(f"[对话上下文] 加载对话历史: {len(recent_messages)} 条")

            for msg in recent_messages:
                token_estimate = len(msg.content) // 4
                if total_tokens + token_estimate > self.conversation_context_max_tokens:
                    break

                context.append({
                    'role': msg.role,
                    'content': msg.content,
                    'timestamp': msg.timestamp
                })
                total_tokens += token_estimate

            return context

        except Exception as e:
            logger.error(f"[对话上下文] 获取对话历史失败: {e}")
            return []

    async def get_lifebook_summary(self) -> str:
        """
        从记忆系统中获取 Lifebook 终端会话摘要

        Returns:
            摘要文本，如果没有则返回空字符串
        """
        try:
            from core.memory_engine import MemoryEngine

            if not self.memory_net:
                return ""

            # 搜索最近保存的终端会话记录
            if hasattr(self.memory_net, 'memory_engine') and self.memory_net.memory_engine:
                results = self.memory_net.memory_engine.search_tides(
                    query="终端会话",
                    limit=3
                )
            else:
                return ""

            if results:
                summaries = []
                for result in results:
                    data = result.get('data', {})
                    if data.get('type') == 'terminal_session':
                        content = data.get('content', '')
                        title = data.get('title', '')
                        summaries.append(f"## {title}\n{content[:500]}")

                if summaries:
                    return "\n\n".join(summaries)

            return ""
        except Exception as e:
            logger.debug(f"[对话上下文] 获取 Lifebook 摘要失败: {e}")
            return ""
