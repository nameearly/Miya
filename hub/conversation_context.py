"""对话历史上下文管理器

负责对话历史的智能加载和上下文管理
新增：话题连续性检测、主动回忆机制、上下文压缩
"""

import logging
import re
from typing import Dict, List, Optional, Set
from collections import defaultdict

logger = logging.getLogger(__name__)


class ConversationContextManager:
    """对话历史上下文管理器

    职责：
    - 智能判断是否需要加载历史对话
    - 根据Token限制动态调整上下文大小
    - 检测用户的"回忆"意图
    - 话题连续性检测
    - 主动回忆机制
    """

    # 话题关键词映射
    TOPIC_KEYWORDS = {
        "学习": [
            "上课",
            "学习",
            "考试",
            "作业",
            "学校",
            "老师",
            "同学",
            "补课",
            "自习",
            "复习",
            "预习",
        ],
        "吃饭": [
            "吃饭",
            "饿",
            "饱",
            "零食",
            "外卖",
            "餐厅",
            "食堂",
            "菜",
            "口味",
            "厨师",
        ],
        "休息": [
            "睡觉",
            "困",
            "累",
            "休息",
            "放假",
            "周末",
            "假期",
            "娱乐",
            "游戏",
            "动漫",
        ],
        "情绪": [
            "难过",
            "开心",
            "生气",
            "害怕",
            "担心",
            "焦虑",
            "压力",
            "烦恼",
            "郁闷",
        ],
        "社交": ["朋友", "同学", "家人", "聊天", "聚会", "社交", "联系人"],
    }

    def __init__(
        self,
        memory_net,
        enable_conversation_context: bool = True,
        conversation_context_max_count: int = 20,
        conversation_context_max_tokens: int = 6000,
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

        # 新增：话题跟踪
        self._topic_history: Dict[str, List[str]] = defaultdict(
            list
        )  # session_id -> 话题列表
        self._last_topics: Dict[str, str] = {}  # session_id -> 最近话题
        self._conversation_turns: Dict[str, int] = defaultdict(
            int
        )  # session_id -> 对话轮次

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
                logger.info(f"[对话上下文] 检测到回忆请求: {user_input[:30]}")
                return True

        return False

    async def get_conversation_context(
        self, session_id: str, current_input: str = ""
    ) -> List[Dict]:
        """
        获取对话历史上下文（分层摘要架构）

        分层策略：
        - 精确层（最近10条）：完整对话
        - 摘要层（10-50条）：每5条压缩为一条摘要
        - 回忆模式：加载50条完整历史

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

        # 检测是否是深度讨论（长消息、多个话题词、问题形式）
        is_deep_discussion = self._is_deep_discussion(current_input)

        # 根据情况决定加载数量
        if needs_recall:
            max_messages = 50
            logger.info(f"[对话上下文] 用户正在回忆过去，加载历史对话: {session_id}")
        elif is_deep_discussion:
            max_messages = 30
            logger.debug(f"[对话上下文] 检测到深度讨论，加载30条: {session_id}")
        else:
            max_messages = 20
            logger.debug(f"[对话上下文] 正常对话，加载20条: {session_id}")

        try:
            messages = await self.memory_net.conversation_history.get_history(
                session_id, limit=max_messages
            )

            context = []
            total_tokens = 0

            if not messages:
                return context

            # 根据情况选择加载数量
            if needs_recall:
                recent_messages = (
                    messages[-max_messages:]
                    if len(messages) > max_messages
                    else messages
                )
            elif is_deep_discussion:
                recent_messages = (
                    messages[-max_messages:]
                    if len(messages) > max_messages
                    else messages
                )
            else:
                # 正常对话加载最近15条
                recent_messages = messages[-15:] if len(messages) > 15 else messages

            logger.debug(f"[对话上下文] 加载对话历史: {len(recent_messages)} 条")

            for msg in recent_messages:
                token_estimate = len(msg.content) // 4
                if total_tokens + token_estimate > self.conversation_context_max_tokens:
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
            logger.error(f"[对话上下文] 获取对话历史失败: {e}")
            return []

    def _is_deep_discussion(self, user_input: str) -> bool:
        """
        检测是否是深度讨论

        Args:
            user_input: 用户输入

        Returns:
            是否是深度讨论
        """
        if not user_input or not isinstance(user_input, str):
            return False

        # 长消息通常是深度讨论
        if len(user_input) > 50:
            return True

        # 包含多个话题词
        from memory.cognitive_engine import TOPIC_KEYWORDS

        topic_count = 0
        for topic, keywords in TOPIC_KEYWORDS.items():
            if any(kw in user_input for kw in keywords):
                topic_count += 1

        if topic_count >= 2:
            return True

        # 问题形式（包含多个问号或疑问词）
        if user_input.count("?") + user_input.count("？") >= 2:
            return True

        # 包含讨论相关词汇
        discussion_words = [
            "为什么",
            "怎么",
            "如何",
            "什么",
            "哪",
            "吗",
            "呢",
            "讨论",
            "分析",
            "解释",
        ]
        if (
            any(word in user_input for word in discussion_words)
            and len(user_input) > 20
        ):
            return True

        return False

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
            if (
                hasattr(self.memory_net, "memory_engine")
                and self.memory_net.memory_engine
            ):
                results = self.memory_net.memory_engine.search_tides(
                    query="终端会话", limit=3
                )
            else:
                return ""

            if results:
                summaries = []
                for result in results:
                    data = result.get("data", {})
                    if data.get("type") == "terminal_session":
                        content = data.get("content", "")
                        title = data.get("title", "")
                        summaries.append(f"## {title}\n{content[:500]}")

                if summaries:
                    return "\n\n".join(summaries)

            return ""
        except Exception as e:
            logger.debug(f"[对话上下文] 获取 Lifebook 摘要失败: {e}")
            return ""
