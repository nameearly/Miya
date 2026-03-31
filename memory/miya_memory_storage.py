"""
弥娅智能记忆存储模块 (MiyaMemoryStorage)

类似 Undefined 项目的 MemoryStorage，实现：
- JSON 文件持久化存储
- 自动去重
- 自动清理过期记忆
- 智能检索
"""

import json
import logging
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

MEMORY_FILE_PATH = Path("data/miya_memories.json")


@dataclass
class MiyaMemory:
    """单条记忆数据"""

    uuid: str
    fact: str
    created_at: str
    importance: float = 0.5
    tags: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class MiyaMemoryStorage:
    """弥娅智能记忆存储管理器

    特点：
    - 只存储重要事实，不存储所有对话
    - 自动去重，避免重复记忆
    - 基于重要性的自动清理
    - 支持语义检索（通过 CognitiveEngine）
    """

    def __init__(self, max_memories: int = 200):
        """初始化记忆存储

        Args:
            max_memories: 最大记忆数量
        """
        self.max_memories = max_memories
        self._memories: List[MiyaMemory] = []
        self._load()

    def _load(self) -> None:
        """从文件加载记忆"""
        if not MEMORY_FILE_PATH.exists():
            self._memories = []
            logger.info("[Miya记忆] 记忆文件不存在，创建新的记忆库")
            return

        try:
            with open(MEMORY_FILE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)

            loaded_memories = []
            for item in data:
                if "uuid" not in item:
                    item["uuid"] = str(uuid.uuid4())
                loaded_memories.append(MiyaMemory(**item))

            self._memories = loaded_memories
            logger.info(
                "[Miya记忆] 加载完成: count=%s",
                len(self._memories),
            )
        except Exception as exc:
            logger.warning("[Miya记忆] 加载失败: %s", exc)
            self._memories = []

    async def _save(self) -> None:
        """保存记忆到文件"""
        try:
            MEMORY_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
            data = [asdict(m) for m in self._memories]
            with open(MEMORY_FILE_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.debug("[Miya记忆] 保存完成: count=%s", len(self._memories))
        except Exception as exc:
            logger.error("[Miya记忆] 保存失败: %s", exc)

    async def add(
        self, fact: str, importance: float = 0.5, tags: List[str] = None
    ) -> Optional[str]:
        """添加一条记忆

        Args:
            fact: 记忆内容
            importance: 重要程度 0-1
            tags: 标签列表

        Returns:
            新生成的 UUID，如果失败则返回 None
        """
        if not fact or not fact.strip():
            logger.warning("[Miya记忆] 尝试添加空记忆，已忽略")
            return None

        fact = fact.strip()

        # 检查是否已存在相同内容
        for existing in self._memories:
            if existing.fact == fact:
                logger.debug("[Miya记忆] 记忆内容已存在，忽略: %s...", fact[:30])
                return existing.uuid

        memory = MiyaMemory(
            uuid=str(uuid.uuid4()),
            fact=fact,
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            importance=importance,
            tags=tags or [],
        )

        # 按重要性插入，重要记忆靠前
        inserted = False
        for i, m in enumerate(self._memories):
            if importance > m.importance:
                self._memories.insert(i, memory)
                inserted = True
                break
        if not inserted:
            self._memories.append(memory)

        # 如果超过上限，移除最不重要的
        while len(self._memories) > self.max_memories:
            removed = self._memories.pop()
            logger.info(
                "[Miya记忆] 超过上限，移除低重要性记忆: %s...", removed.fact[:30]
            )

        await self._save()
        logger.info(
            "[Miya记忆] 已添加: uuid=%s importance=%s content=%s...",
            memory.uuid,
            importance,
            fact[:30],
        )
        return memory.uuid

    async def update(self, memory_uuid: str, fact: str) -> bool:
        """更新一条记忆

        Args:
            memory_uuid: 记忆的 UUID
            fact: 新的内容

        Returns:
            是否更新成功
        """
        for i, m in enumerate(self._memories):
            if m.uuid == memory_uuid:
                self._memories[i].fact = fact.strip()
                await self._save()
                logger.info("[Miya记忆] 已更新: uuid=%s", memory_uuid)
                return True
        logger.warning("[Miya记忆] 未找到 UUID=%s 的记忆", memory_uuid)
        return False

    async def delete(self, memory_uuid: str) -> bool:
        """删除一条记忆

        Args:
            memory_uuid: 记忆的 UUID

        Returns:
            是否删除成功
        """
        for i, m in enumerate(self._memories):
            if m.uuid == memory_uuid:
                removed = self._memories.pop(i)
                await self._save()
                logger.info("[Miya记忆] 已删除: uuid=%s", memory_uuid)
                return True
        logger.warning("[Miya记忆] 未找到 UUID=%s 的记忆", memory_uuid)
        return False

    def get_all(self) -> List[MiyaMemory]:
        """获取所有记忆

        Returns:
            记忆列表（按重要性排序）
        """
        return self._memories.copy()

    def get_recent(self, limit: int = 10) -> List[MiyaMemory]:
        """获取最近的记忆

        Returns:
            按时间排序的记忆列表
        """
        sorted_memories = sorted(
            self._memories, key=lambda m: m.created_at, reverse=True
        )
        return sorted_memories[:limit]

    def search_by_keyword(
        self, keywords: List[str], limit: int = 5
    ) -> List[MiyaMemory]:
        """通过关键词搜索记忆

        Args:
            keywords: 关键词列表
            limit: 返回数量限制

        Returns:
            匹配的记忆列表
        """
        results = []
        for memory in self._memories:
            for keyword in keywords:
                if keyword.lower() in memory.fact.lower():
                    results.append(memory)
                    break

        # 按重要性排序
        results.sort(key=lambda m: m.importance, reverse=True)
        return results[:limit]

    def get_by_tag(self, tag: str, limit: int = 10) -> List[MiyaMemory]:
        """通过标签获取记忆

        Args:
            tag: 标签
            limit: 返回数量限制

        Returns:
            匹配的记忆列表
        """
        results = [m for m in self._memories if tag in m.tags]
        return results[:limit]

    async def clear(self) -> None:
        """清空所有记忆"""
        self._memories = []
        await self._save()
        logger.info("[Miya记忆] 已清空所有记忆")

    def count(self) -> int:
        """获取记忆数量

        Returns:
            当前记忆数量
        """
        return len(self._memories)


# 单例实例
_memory_storage: Optional[MiyaMemoryStorage] = None


def get_memory_storage() -> MiyaMemoryStorage:
    """获取记忆存储单例实例"""
    global _memory_storage
    if _memory_storage is None:
        _memory_storage = MiyaMemoryStorage()
    return _memory_storage
