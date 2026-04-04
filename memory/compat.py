"""
统一记忆系统兼容层 - 保留向后兼容

此类仅用于兼容旧代码，新代码请直接使用 memory 模块。
用法:
    from memory import get_memory_core, store_important, search_memory
"""

import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class UndefinedMemoryAdapter:
    """Undefined记忆适配器 - 兼容旧接口"""

    def __init__(self):
        self._initialized = False

    async def initialize(self):
        """初始化"""
        self._initialized = True

    async def _load(self):
        """加载记忆 - 兼容旧接口"""
        await self.initialize()

    def count(self) -> int:
        """获取记忆数量"""
        return 0

    async def add_memory(self, content: str, user_id: str, **kwargs) -> str:
        """添加记忆"""
        from memory import store_important

        return await store_important(content, user_id, tags=kwargs.get("tags", []))

    async def search_memory(
        self, query: str, user_id: Optional[str] = None, **kwargs
    ) -> List[Dict]:
        """搜索记忆"""
        from memory import search_memory

        results = await search_memory(query, user_id=user_id)
        return [
            {
                "id": r.id,
                "content": r.content,
                "tags": r.tags,
                "created_at": r.created_at,
            }
            for r in results
        ]

    async def get_all(self, limit: int = 10) -> List[Dict]:
        """获取所有记忆（兼容方法）"""
        results = await self.search_memory(query="", user_id=None)
        return results[:limit]

    async def get_by_tag(self, tag: str, limit: int = 10) -> List[Dict]:
        """按标签获取记忆（兼容方法）"""
        results = await self.search_memory(query=tag, user_id=None)
        return results[:limit]


_adapter: Optional[UndefinedMemoryAdapter] = None


def get_undefined_memory_adapter() -> UndefinedMemoryAdapter:
    """获取Undefined记忆适配器"""
    global _adapter
    if _adapter is None:
        _adapter = UndefinedMemoryAdapter()
    return _adapter


def get_undefined_memory_backend():
    """获取后端"""
    return get_undefined_memory_adapter()


def get_unified_memory_backend():
    """获取统一记忆后端 - 兼容接口"""
    return get_undefined_memory_adapter()


class UnifiedMemory:
    """统一记忆系统 - 兼容旧接口"""

    def __init__(self, data_dir: str = "data/memory", config: Optional[Dict] = None):
        self.data_dir = data_dir
        self.config = config or {}
        self._core = None
        self._initialized = False

    async def initialize(self) -> bool:
        """初始化"""
        from memory import get_memory_core

        self._core = await get_memory_core(str(self.data_dir))
        self._initialized = True
        logger.info("统一记忆系统初始化成功")
        return True

    async def add_memory(self, content: str, user_id: str, **kwargs) -> str:
        """添加记忆"""
        from memory import store_important

        tags = kwargs.get("tags", [])
        return await store_important(content, user_id, tags=tags)

    async def search_memory(
        self, query: str, user_id: Optional[str] = None
    ) -> List[Dict]:
        """搜索记忆"""
        from memory import search_memory

        results = await search_memory(query, user_id=user_id)
        return [{"content": r.content, "tags": r.tags} for r in results]

    async def get_all(
        self, user_id: Optional[str] = None, limit: int = 100
    ) -> List[Dict]:
        """获取所有记忆"""
        from memory import get_user_memories

        results = await get_user_memories(user_id, limit=limit)
        return [{"content": r.content, "tags": r.tags} for r in results]

    async def add_short_term(
        self, content: str, user_id: str, ttl: int = 3600, **kwargs
    ) -> str:
        """添加短期记忆"""
        from memory import store_auto

        tags = kwargs.get("tags", [])
        return await store_auto(content, user_id, tags=tags)


_unified_memory_instance: Optional[UnifiedMemory] = None


def get_unified_memory(
    data_dir: str = "data/memory", config: Optional[Dict] = None
) -> UnifiedMemory:
    """获取统一记忆实例"""
    global _unified_memory_instance
    if _unified_memory_instance is None:
        _unified_memory_instance = UnifiedMemory(data_dir, config)
    return _unified_memory_instance


def init_unified_memory(
    data_dir: str = "data/memory", config: Optional[Dict] = None
) -> UnifiedMemory:
    """初始化统一记忆"""
    return get_unified_memory(data_dir, config)


def get_memory_adapter():
    """获取记忆适配器 - 兼容接口

    返回适配器实例
    """
    return get_undefined_memory_adapter()


async def get_memory_adapter_async():
    """获取记忆适配器 - 异步版本

    返回初始化后的适配器
    """
    adapter = get_undefined_memory_adapter()
    await adapter.initialize()
    return adapter


__all__ = [
    "UndefinedMemoryAdapter",
    "get_undefined_memory_adapter",
    "get_undefined_memory_backend",
    "get_unified_memory_backend",
    "UnifiedMemory",
    "get_unified_memory",
    "init_unified_memory",
    "get_memory_adapter",
]
