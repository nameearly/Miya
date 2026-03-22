"""
Undefined 风格记忆系统 - 使用新记忆系统作为后端

迁移到 V3.0 统一记忆系统
"""

import json
import logging
import uuid
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import Optional, List
from core.constants import Encoding

logger = logging.getLogger(__name__)


@dataclass
class SimpleMemory:
    """简单记忆数据结构"""

    uuid: str
    fact: str
    created_at: str
    tags: List[str] = field(default_factory=list)


def _default_tags() -> List[str]:
    return []


_global_unified_memory = None


async def get_unified_memory_backend():
    """获取统一记忆系统后端"""
    global _global_unified_memory
    if _global_unified_memory is None:
        from memory.unified_memory import get_unified_memory

        _global_unified_memory = get_unified_memory("data/memory")
        await _global_unified_memory.initialize()
    return _global_unified_memory


class UndefinedMemoryAdapter:
    """Undefined 记忆系统适配器 - 使用新系统作为后端"""

    def __init__(
        self,
        data_dir: Optional[Path] = None,
        max_memories: int = 500,
        filename: str = "undefined_memory.json",
    ):
        self.data_dir = data_dir or Path("data/memory")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.max_memories = max_memories
        self.filename = filename
        self._loaded = False
        self._legacy_memories: List[SimpleMemory] = []
        self._legacy_file = self.data_dir / filename

    async def _load(self):
        """从文件加载旧记忆并迁移"""
        if self._loaded:
            return

        if self._legacy_file.exists():
            try:
                with open(self._legacy_file, "r", encoding=Encoding.UTF8) as f:
                    data = json.load(f)
                    self._legacy_memories = [SimpleMemory(**m) for m in data]
                logger.info(f"已加载 {len(self._legacy_memories)} 条旧记忆")
            except Exception as e:
                logger.error(f"加载旧记忆失败: {e}")
                self._legacy_memories = []
        else:
            self._legacy_memories = []

        self._loaded = True

    async def _save(self):
        """保存到遗留文件（不再使用，保留兼容性）"""
        pass

    async def add(self, fact: str, tags: Optional[List[str]] = None) -> Optional[str]:
        """添加记忆"""
        await self._load()

        existing_uuid = await self._find_existing(fact)
        if existing_uuid:
            return existing_uuid

        new_uuid = str(uuid.uuid4())
        memory = SimpleMemory(
            uuid=new_uuid,
            fact=fact,
            created_at=datetime.now().isoformat(),
            tags=tags or [],
        )
        self._legacy_memories.append(memory)

        unified = await get_unified_memory_backend()
        await unified.add_short_term(
            content=fact, user_id="undefined", priority=0.5, tags=tags or []
        )

        if len(self._legacy_memories) > self.max_memories:
            self._legacy_memories.pop(0)

        return new_uuid

    async def _find_existing(self, fact: str) -> Optional[str]:
        """查找已存在的记忆"""
        for m in self._legacy_memories:
            if m.fact == fact:
                return m.uuid
        return None

    async def update(
        self,
        memory_uuid: str,
        fact: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> bool:
        """更新记忆"""
        await self._load()

        for m in self._legacy_memories:
            if m.uuid == memory_uuid:
                if fact is not None:
                    m.fact = fact
                if tags is not None:
                    m.tags = tags
                return True

        return False

    async def delete(self, memory_uuid: str) -> bool:
        """删除记忆"""
        await self._load()

        for i, m in enumerate(self._legacy_memories):
            if m.uuid == memory_uuid:
                self._legacy_memories.pop(i)
                return True

        return False

    async def search(self, keyword: str, limit: int = 10) -> List[SimpleMemory]:
        """搜索记忆"""
        await self._load()

        if not keyword:
            return self._legacy_memories[-limit:]

        results = []
        keyword_lower = keyword.lower()
        for m in self._legacy_memories:
            if keyword_lower in m.fact.lower():
                results.append(m)

        return results[:limit]

    async def get_all(self) -> List[SimpleMemory]:
        """获取所有记忆"""
        await self._load()
        return self._legacy_memories.copy()

    def count(self) -> int:
        """获取记忆数量"""
        return len(self._legacy_memories)


def get_undefined_memory_adapter() -> UndefinedMemoryAdapter:
    """获取 Undefined 记忆适配器单例"""
    return UndefinedMemoryAdapter()
