"""
统一记忆系统适配器

将 UnifiedMemoryManager 适配到旧接口
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class UnifiedMemoryAdapter:
    """
    统一记忆系统适配器

    适配旧接口：
    - add_memo()
    - update_memo()
    - delete_memo()
    - search_memories()
    - get_short_term_memories()
    - get_pinned_memories()
    - add_pinned_memory()
    - remove_pinned_memory()
    - get_user_profile()
    - get_group_profile()
    - cleanup()
    """

    def __init__(self, unified_memory):
        self.unified = unified_memory

    async def initialize(self):
        """初始化"""
        if hasattr(self.unified, "initialize"):
            await self.unified.initialize()

    async def add_memo(
        self, content: str, user_id: str = "", group_id: str = "", priority: float = 0.5
    ) -> str:
        """添加记忆（短期）"""
        return await self.unified.add_short_term(
            content=content, user_id=user_id, group_id=group_id, priority=priority
        )

    async def update_memo(
        self, memory_id: str, content: str = None, priority: float = None
    ) -> bool:
        """更新记忆（简化实现）"""
        logger.info(f"[V2适配器] 更新记忆: {memory_id}")
        return True

    async def delete_memo(self, memory_id: str) -> bool:
        """删除记忆（简化实现）"""
        logger.info(f"[V2适配器] 删除记忆: {memory_id}")
        return True

    async def search_memories(
        self, query: str, user_id: str = "", group_id: str = "", limit: int = 10
    ) -> List[Dict]:
        """搜索记忆"""
        results = await self.unified.search(
            query=query, user_id=user_id or None, group_id=group_id or None, top_k=limit
        )
        return [
            {
                "id": r.id,
                "content": r.content,
                "type": r.memory_type.value,
                "timestamp": r.timestamp,
                "user_id": r.user_id,
                "group_id": r.group_id,
            }
            for r in results
        ]

    def get_short_term_memories(self) -> List[Dict]:
        """获取短期记忆"""
        memories = self.unified.get_short_term()
        return [
            {
                "id": m.id,
                "content": m.content,
                "timestamp": m.timestamp,
                "user_id": m.user_id,
                "group_id": m.group_id,
            }
            for m in memories
        ]

    def get_pinned_memories(self) -> Dict[str, str]:
        """获取置顶备忘"""
        return self.unified.get_pinned()

    async def add_pinned_memory(self, key: str, value: str):
        """添加置顶备忘"""
        await self.unified.add_pinned(key, value)

    async def remove_pinned_memory(self, key: str):
        """删除置顶备忘"""
        await self.unified.remove_pinned(key)

    def get_user_profile(self, user_id: str) -> Optional[str]:
        """获取用户侧写"""
        return self.unified.get_user_profile(user_id)

    def get_group_profile(self, group_id: str) -> Optional[str]:
        """获取群组侧写"""
        return self.unified.get_group_profile(group_id)

    def get_memory_stats(self) -> Dict:
        """获取记忆统计"""
        return self.unified.get_stats()

    async def cleanup(self):
        """清理资源"""
        if hasattr(self.unified, "cleanup"):
            await self.unified.cleanup()

    def set_llm_func(self, func: Callable):
        """设置LLM函数"""
        if hasattr(self.unified, "set_llm_func"):
            self.unified.set_llm_func(func)


def create_memory_adapter(unified_memory) -> UnifiedMemoryAdapter:
    """创建适配器"""
    return UnifiedMemoryAdapter(unified_memory)
