"""
MemoryNet 适配器 - 集成到弥娅记忆系统

此类将 MemoryNet 完全集成到新的统一记忆系统。
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from memory import (
    MiyaMemoryCore,
    get_memory_core,
    MemoryItem,
    MemoryLevel,
    MemorySource,
    store_dialogue,
    store_important,
    search_memory,
    get_user_profile,
)

logger = logging.getLogger(__name__)


class MiyaMemoryNet:
    """
    弥娅记忆子网 (MemoryNet)

    统一管理所有对话历史和记忆数据，提供 M-Link 接口。
    """

    def __init__(self, mlink=None):
        self.mlink = mlink
        self._core: Optional[MiyaMemoryCore] = None

        # 统计
        self.stats = {
            "total_messages_stored": 0,
            "total_memories_added": 0,
            "total_retrievals": 0,
            "last_access": None,
        }

        logger.info("[MiyaMemoryNet] 初始化完成")

    async def initialize(self):
        """初始化"""
        logger.info("[MiyaMemoryNet] 初始化中...")
        self._core = await get_memory_core()
        logger.info("[MiyaMemoryNet] 初始化成功")
        return True

    @property
    def core(self) -> MiyaMemoryCore:
        if self._core is None:
            raise RuntimeError("MemoryNet 未初始化")
        return self._core

    # ==================== 对话历史 ====================

    async def add_conversation(
        self,
        session_id: str,
        role: str,
        content: str,
        agent_id: Optional[str] = None,
        images: Optional[List[str]] = None,
        metadata: Optional[Dict] = None,
    ) -> str:
        """
        添加对话历史

        Args:
            session_id: 会话ID
            role: 角色 (user/assistant)
            content: 内容
            agent_id: Agent ID
            images: 图片列表
            metadata: 元数据

        Returns:
            记忆ID
        """
        # 提取用户信息
        user_id, platform = self._parse_session_id(session_id)

        full_metadata = metadata or {}
        if agent_id:
            full_metadata["agent_id"] = agent_id
        if images:
            full_metadata["images"] = images

        memory_id = await store_dialogue(
            content=content,
            role=role,
            user_id=user_id,
            session_id=session_id,
            platform=platform,
            metadata=full_metadata,
        )

        self.stats["total_messages_stored"] += 1
        self.stats["last_access"] = datetime.now().isoformat()

        logger.debug(f"[MiyaMemoryNet] 添加对话: {session_id}, role={role}")
        return memory_id

    async def get_conversation(
        self,
        session_id: str,
        limit: int = 20,
    ) -> List[Dict]:
        """
        获取对话历史

        Args:
            session_id: 会话ID
            limit: 限制数量

        Returns:
            消息列表
        """
        user_id, platform = self._parse_session_id(session_id)

        memories = await self.core.get_dialogue(
            session_id=session_id,
            platform=platform,
            limit=limit,
        )

        self.stats["total_retrievals"] += 1

        return [
            {
                "role": m.role,
                "content": m.content,
                "timestamp": m.created_at,
                "session_id": m.session_id,
                "images": m.metadata.get("images", []),
                "agent_id": m.metadata.get("agent_id"),
                "metadata": m.metadata,
            }
            for m in memories
        ]

    # ==================== 记忆管理 ====================

    async def add_memory(
        self,
        fact: str,
        tags: Optional[List[str]] = None,
        user_id: str = "global",
        priority: float = 0.7,
    ) -> str:
        """
        添加记忆

        Args:
            fact: 记忆内容
            tags: 标签
            user_id: 用户ID
            priority: 优先级

        Returns:
            记忆ID
        """
        memory_id = await store_important(
            content=fact,
            user_id=user_id,
            tags=tags or [],
            priority=priority,
        )

        self.stats["total_memories_added"] += 1
        self.stats["last_access"] = datetime.now().isoformat()

        logger.debug(f"[MiyaMemoryNet] 添加记忆: {memory_id}")
        return memory_id

    async def search_memory(
        self,
        keyword: str,
        user_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 20,
    ) -> List[Dict]:
        """
        搜索记忆

        Args:
            keyword: 关键词
            user_id: 用户ID
            tags: 标签
            limit: 限制

        Returns:
            记忆列表
        """
        memories = await search_memory(
            query=keyword,
            user_id=user_id,
            tags=tags,
            limit=limit,
        )

        self.stats["total_retrievals"] += 1

        return [
            {
                "id": m.id,
                "content": m.content,
                "tags": m.tags,
                "priority": m.priority,
                "created_at": m.created_at,
                "level": m.level.value,
                "source": m.source.value,
            }
            for m in memories
        ]

    async def get_all_memories(
        self,
        user_id: Optional[str] = None,
        level: Optional[MemoryLevel] = None,
        limit: int = 100,
    ) -> List[Dict]:
        """
        获取所有记忆

        Args:
            user_id: 用户ID
            level: 记忆层级
            limit: 限制

        Returns:
            记忆列表
        """
        from memory import get_user_memories

        memories = await get_user_memories(user_id, level=level, limit=limit)

        return [
            {
                "id": m.id,
                "content": m.content,
                "tags": m.tags,
                "priority": m.priority,
                "created_at": m.created_at,
                "level": m.level.value,
            }
            for m in memories
        ]

    # ==================== 用户画像 ====================

    async def get_user_profile(self, user_id: str) -> Dict:
        """
        获取用户画像

        Args:
            user_id: 用户ID

        Returns:
            用户画像
        """
        return await get_user_profile(user_id)

    # ==================== 统计 ====================

    async def get_statistics(self) -> Dict:
        """
        获取统计信息

        Returns:
            统计字典
        """
        core_stats = await self.core.get_statistics()

        return {
            **core_stats,
            "memory_net": self.stats,
        }

    # ==================== 清理 ====================

    async def clear_expired(self) -> int:
        """清理过期记忆"""
        return await self.core.delete_expired()

    async def clear_session(self, session_id: str) -> bool:
        """清空会话"""
        memories = await self.get_conversation(session_id, limit=1000)

        for msg in memories:
            await self.core.delete(msg.get("id", ""))

        return True

    # ==================== 自动提取 ====================

    async def extract_and_store_important_info(
        self,
        content: str,
        user_id: Optional[str] = None,
    ) -> int:
        """
        自动提取并存储重要信息

        Args:
            content: 对话内容
            user_id: 用户ID

        Returns:
            提取数量
        """
        from memory.core import MemorySource

        if not content or not isinstance(content, str):
            return 0

        # 提取规则
        patterns = [
            (r"我叫(.+)", ["身份", "名字"], 0.8),
            (r"我的名字是(.+)", ["身份", "名字"], 0.8),
            (r"我喜欢(.+)", ["偏好", "喜欢"], 0.7),
            (r"我讨厌(.+)", ["偏好", "讨厌"], 0.7),
            (r"记住(.+)", ["重要", "手动添加"], 0.9),
            (r"别忘了(.+)", ["重要", "约定"], 0.8),
            (r"生日是?(.+)", ["生日", "重要日期"], 0.9),
            (r"电话是?(.+)", ["联系方式", "电话"], 0.9),
            (r"邮箱是?(.+)", ["联系方式", "邮箱"], 0.9),
        ]

        import re

        count = 0
        for pattern, tags, priority in patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0] if match else ""

                if not match or len(match.strip()) < 2:
                    continue

                await store_important(
                    content=match.strip(),
                    user_id=user_id or "unknown",
                    tags=tags,
                    priority=priority,
                )
                count += 1

        if count > 0:
            logger.info(f"[MiyaMemoryNet] 自动提取了 {count} 条重要信息")

        return count

    # ==================== 辅助方法 ====================

    def _parse_session_id(self, session_id: str) -> tuple:
        """
        解析会话ID

        Args:
            session_id: 会话ID (如 qq_123456)

        Returns:
            (user_id, platform)
        """
        user_id = "unknown"
        platform = "unknown"

        if not session_id:
            return user_id, platform

        parts = session_id.split("_", 1)

        if len(parts) >= 2:
            platform = parts[0]
            user_id = parts[1]
        else:
            user_id = session_id

        return user_id, platform

    # ==================== 兼容接口 ====================

    @property
    def conversation_history(self):
        """兼容旧接口"""
        return self

    @property
    def undefined_memory(self):
        """兼容旧接口"""
        return self


# ==================== 全局实例 ====================

_global_memory_net: Optional[MiyaMemoryNet] = None


async def get_memory_net() -> MiyaMemoryNet:
    """获取全局 MemoryNet 实例"""
    global _global_memory_net

    if _global_memory_net is None:
        _global_memory_net = MiyaMemoryNet()
        await _global_memory_net.initialize()

    return _global_memory_net


def reset_memory_net():
    """重置全局 MemoryNet"""
    global _global_memory_net
    _global_memory_net = None
