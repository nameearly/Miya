"""
谛听 - 群聊消息监听与分层摘要系统

职责：
- 监听所有群消息（不触发大模型）
- 分层摘要：时间线概览 + 关键对话 + 当前话题
- 追踪活跃对话窗口
- 区分公开话题 vs 私密对话
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class MessageSnippet:
    """消息片段"""

    sender_id: str
    sender_name: str
    content: str
    timestamp: float
    is_at_bot: bool = False
    is_reply_to_bot: bool = False
    topic: str = ""  # 自动提取的话题标签


@dataclass
class TopicThread:
    """话题线程：追踪一个话题的完整对话"""

    topic: str
    participants: List[str] = field(default_factory=list)
    messages: List[MessageSnippet] = field(default_factory=list)
    start_time: float = 0.0
    last_active: float = 0.0
    is_active: bool = True

    def add_message(self, snippet: MessageSnippet):
        self.messages.append(snippet)
        self.last_active = snippet.timestamp
        if snippet.sender_name not in self.participants:
            self.participants.append(snippet.sender_name)

    def get_summary(self, max_messages: int = 5) -> str:
        """获取话题摘要"""
        recent = self.messages[-max_messages:]
        lines = []
        for s in recent:
            prefix = "@" if s.is_at_bot or s.is_reply_to_bot else ""
            lines.append(f"{prefix}{s.sender_name}: {s.content}")
        return "\n".join(lines)

    def get_timeline_entry(self) -> str:
        """获取时间线索目"""
        participants = "、".join(self.participants[:3])
        msg_count = len(self.messages)
        first_msg = self.messages[0].content[:30] if self.messages else ""
        return f"[{participants}] 聊了{msg_count}条: {first_msg}..."


class DiTingListener:
    """
    谛听监听器 - 分层摘要版

    功能：
    1. 监听所有群消息
    2. 分层摘要注入（时间线 + 关键对话 + 当前话题）
    3. 追踪活跃对话窗口
    4. 话题线程追踪
    """

    def __init__(
        self,
        max_snippets_per_group: int = 50,
        active_window_seconds: int = 300,
        active_message_threshold: int = 5,
        max_topic_threads: int = 5,
    ):
        self.max_snippets = max_snippets_per_group
        self.active_window = active_window_seconds
        self.active_threshold = active_message_threshold
        self.max_topic_threads = max_topic_threads

        # 群聊消息存储
        self._group_snippets: Dict[str, List[MessageSnippet]] = defaultdict(list)

        # 话题线程：{group_id: [TopicThread, ...]}
        self._topic_threads: Dict[str, List[TopicThread]] = defaultdict(list)

        # 活跃对话追踪：{group_id: {user_id: last_active_time}}
        self._active_conversations: Dict[str, Dict[str, float]] = defaultdict(dict)

        # 用户连续发言计数
        self._user_streaks: Dict[str, Dict[str, int]] = defaultdict(
            lambda: defaultdict(int)
        )

        logger.info("[谛听] 分层摘要监听器初始化完成")

    def on_group_message(
        self,
        group_id: str,
        group_name: str,
        user_id: str,
        user_name: str,
        content: str,
        is_at_bot: bool = False,
        reply_to_bot: bool = False,
    ):
        """处理群消息"""
        snippet = MessageSnippet(
            sender_id=user_id,
            sender_name=user_name,
            content=content[:150],
            timestamp=time.time(),
            is_at_bot=is_at_bot,
            is_reply_to_bot=reply_to_bot,
        )

        # 存储消息
        snippets = self._group_snippets[group_id]
        snippets.append(snippet)
        if len(snippets) > self.max_snippets:
            self._group_snippets[group_id] = snippets[-self.max_snippets :]

        # 更新话题线程
        self._update_topic_thread(group_id, snippet)

        # 更新活跃对话状态
        if is_at_bot or reply_to_bot:
            self._active_conversations[group_id][user_id] = time.time()
            self._user_streaks[group_id][user_id] = 0
        else:
            last_active = self._active_conversations[group_id].get(user_id, 0)
            if time.time() - last_active < self.active_window:
                self._user_streaks[group_id][user_id] += 1
                if self._user_streaks[group_id][user_id] >= self.active_threshold:
                    self._active_conversations[group_id][user_id] = time.time()
            else:
                self._user_streaks[group_id][user_id] = 0

    def _update_topic_thread(self, group_id: str, snippet: MessageSnippet):
        """更新话题线程"""
        threads = self._topic_threads[group_id]

        # 检查是否可以加入现有活跃线程
        for thread in threads:
            if not thread.is_active:
                continue
            # 5分钟内、有相同参与者、内容相关 → 加入同一线程
            if (
                time.time() - thread.last_active < 300
                and snippet.sender_name in thread.participants
            ):
                thread.add_message(snippet)
                return

        # 创建新话题线程
        new_thread = TopicThread(
            topic=f"话题_{len(threads) + 1}",
            start_time=snippet.timestamp,
            last_active=snippet.timestamp,
        )
        new_thread.add_message(snippet)
        threads.append(new_thread)

        # 限制线程数量
        if len(threads) > self.max_topic_threads:
            self._topic_threads[group_id] = threads[-self.max_topic_threads :]

    def get_layered_context(self, group_id: str) -> str:
        """
        获取分层上下文（核心方法）

        返回三层信息：
        1. 时间线概览：谁在什么时间聊了什么
        2. 关键对话：与机器人相关的对话
        3. 当前话题：正在进行的讨论
        """
        snippets = self._group_snippets.get(group_id, [])
        threads = self._topic_threads.get(group_id, [])

        if not snippets:
            return ""

        layers = []

        # Layer 1: 时间线概览
        timeline_entries = []
        for thread in threads:
            entry = thread.get_timeline_entry()
            if entry:
                timeline_entries.append(entry)

        if timeline_entries:
            layers.append("【群聊时间线】")
            layers.extend(timeline_entries)

        # Layer 2: 关键对话（与机器人相关的）
        bot_interactions = [s for s in snippets if s.is_at_bot or s.is_reply_to_bot]
        if bot_interactions:
            layers.append("\n【与弥娅的对话】")
            for s in bot_interactions[-5:]:
                prefix = "@" if s.is_at_bot else "→"
                layers.append(f"{prefix}{s.sender_name}: {s.content}")

        # Layer 3: 当前话题（最近3条）
        recent = snippets[-3:]
        if recent:
            layers.append("\n【当前对话】")
            for s in recent:
                layers.append(f"{s.sender_name}: {s.content}")

        return "\n".join(layers)

    def get_group_context(self, group_id: str, max_snippets: int = 10) -> str:
        """兼容旧接口，返回分层上下文"""
        return self.get_layered_context(group_id)

    def is_user_active_with_bot(self, group_id: str, user_id: str) -> bool:
        """检查用户是否仍在与机器人活跃对话"""
        last_active = self._active_conversations.get(group_id, {}).get(user_id, 0)
        return (time.time() - last_active) < self.active_window

    def get_active_users(self, group_id: str) -> List[str]:
        """获取当前活跃用户列表"""
        cutoff = time.time() - self.active_window
        return [
            uid
            for uid, last_time in self._active_conversations.get(group_id, {}).items()
            if last_time > cutoff
        ]

    def get_related_threads(
        self, group_id: str, query: str, max_threads: int = 3
    ) -> str:
        """获取与查询相关的话题线程"""
        threads = self._topic_threads.get(group_id, [])
        query_lower = query.lower()

        relevant = []
        for thread in threads:
            # 检查线程中是否有与查询相关的内容
            for msg in thread.messages:
                if any(kw in msg.content.lower() for kw in query_lower.split()):
                    relevant.append(thread)
                    break

        if not relevant:
            return ""

        lines = ["【相关话题】"]
        for thread in relevant[:max_threads]:
            lines.append(f"\n{thread.get_summary()}")

        return "\n".join(lines)

    def cleanup_expired(self, max_age_seconds: int = 3600):
        """清理过期数据"""
        cutoff = time.time() - max_age_seconds

        # 清理过期群消息
        expired_groups = [
            gid
            for gid, snippets in self._group_snippets.items()
            if snippets and snippets[-1].timestamp < cutoff
        ]
        for gid in expired_groups:
            del self._group_snippets[gid]
            self._topic_threads.pop(gid, None)

        # 清理过期活跃对话
        for group_id in list(self._active_conversations.keys()):
            expired_users = [
                uid
                for uid, last_time in self._active_conversations[group_id].items()
                if last_time < cutoff
            ]
            for uid in expired_users:
                del self._active_conversations[group_id][uid]
                self._user_streaks[group_id].pop(uid, None)

        if expired_groups:
            logger.debug(f"[谛听] 清理了 {len(expired_groups)} 个过期群数据")


# 全局单例
_diting: Optional[DiTingListener] = None


def get_diting() -> DiTingListener:
    """获取谛听监听器单例"""
    global _diting
    if _diting is None:
        _diting = DiTingListener()
    return _diting
