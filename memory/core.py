"""
================================================================
        弥娅统一记忆系统 (Miya Unified Memory System) V3.1
================================================================

这是弥娅的**唯一**记忆系统核心，所有记忆操作都必须通过此类。

设计原则：
1. 单一入口 - 100%统一
2. 分层存储 - 对话/短期/长期/向量/图谱
3. 数据一致 - 单一数据结构
4. 自动生命周期管理
5. 企业级可靠性

架构：
┌─────────────────────────────────────────────────────────────┐
│                      MiyaMemoryCore                          │
│                   (唯一记忆系统核心)                           │
├─────────────────────────────────────────────────────────────┤
│  MemoryLevel.DIALOGUE     - 对话历史 (会话级)                │
│  MemoryLevel.SHORT_TERM   - 短期记忆 (TTL自动过期)           │
│  MemoryLevel.LONG_TERM    - 长期记忆 (持久化)                │
│  MemoryLevel.SEMANTIC     - 语义记忆 (向量搜索)              │
│  MemoryLevel.KNOWLEDGE    - 知识图谱 (实体关系)              │
├─────────────────────────────────────────────────────────────┤
│  存储后端：JSON文件 + Redis + Milvus + Neo4j                │
└─────────────────────────────────────────────────────────────┘

作者: 编程大师
日期: 2026
================================================================
"""

import asyncio
import json
import logging
import re
import uuid
import hashlib
import aiofiles
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union, Type
from collections import defaultdict
import copy
import os


# 直接定义编码常量，避免循环导入
class Encoding:
    UTF8 = "utf-8"


logger = logging.getLogger(__name__)


# ==================== 枚举定义 ====================


class MemoryLevel(Enum):
    """记忆层级"""

    DIALOGUE = "dialogue"  # 对话历史
    SHORT_TERM = "short_term"  # 短期记忆 (TTL过期)
    LONG_TERM = "long_term"  # 长期记忆 (持久化)
    SEMANTIC = "semantic"  # 语义记忆 (向量搜索)
    KNOWLEDGE = "knowledge"  # 知识图谱


class MemoryPriority(Enum):
    """记忆优先级"""

    LOW = 0.3
    NORMAL = 0.5
    HIGH = 0.7
    CRITICAL = 0.9


class MemorySource(Enum):
    """记忆来源"""

    DIALOGUE = "dialogue"  # 对话中自动存储
    AUTO_EXTRACT = "auto_extract"  # 自动提取
    MANUAL = "manual"  # 手动添加
    SYSTEM = "system"  # 系统生成
    IMPORTED = "imported"  # 导入


# ==================== 核心数据结构 ====================


@dataclass
class MemoryItem:
    """
    统一记忆数据项 - 整个系统的唯一数据结构

    所有记忆都是这个格式，没有任何例外！
    """

    # 唯一标识
    id: str = ""

    # 内容
    content: str = ""

    # 层级
    level: MemoryLevel = MemoryLevel.SHORT_TERM

    # 优先级
    priority: float = 0.5

    # 标签
    tags: List[str] = field(default_factory=list)

    # 用户关联
    user_id: str = "global"
    session_id: str = ""
    group_id: str = ""
    platform: str = "unknown"

    # 来源
    source: MemorySource = MemorySource.SYSTEM
    role: str = ""  # user/assistant

    # 对话详情
    event_type: str = ""  # 对话事件类型 (如"工作会议", "日常聊天", "学习讨论")
    location: str = ""  # 对话地点 (如"办公室", "咖啡馆", "线上")
    conversation_partner: str = ""  # 明确的对话对象
    emotional_tone: str = ""  # 情感基调 (如"愉快", "焦虑", "中性", "兴奋")
    significance: float = 0.5  # 主观重要性评分 (0-1)

    # 时间戳
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    expires_at: Optional[str] = None

    # 向量 (语义层)
    vector: Optional[List[float]] = None

    # 知识图谱 (图谱层)
    subject: str = ""
    predicate: str = ""
    obj: str = ""

    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)

    # 访问统计
    access_count: int = 0
    last_accessed: Optional[str] = None

    # 状态
    is_pinned: bool = False  # 置顶
    is_archived: bool = False  # 归档

    def __post_init__(self):
        """初始化后处理"""
        # 自动生成ID
        if not self.id:
            self.id = self._generate_id()

        # 初始化时间
        now = datetime.now().isoformat()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now

    def _generate_id(self) -> str:
        """生成唯一ID"""
        unique_str = f"{self.content}{self.user_id}{datetime.now().isoformat()}{uuid.uuid4().hex[:8]}"
        return hashlib.md5(unique_str.encode("utf-8")).hexdigest()[:16]

    def to_dict(self) -> Dict:
        """转换为字典"""
        data = asdict(self)
        # 处理枚举
        data["level"] = (
            self.level.value if isinstance(self.level, MemoryLevel) else self.level
        )
        data["source"] = (
            self.source.value if isinstance(self.source, MemorySource) else self.source
        )
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> Optional["MemoryItem"]:
        """从字典创建"""
        if not data:
            return None

        data = data.copy()

        # 处理枚举
        if isinstance(data.get("level"), str):
            data["level"] = MemoryLevel(data["level"])
        if isinstance(data.get("source"), str):
            data["source"] = MemorySource(data["source"])

        # 移除None值
        data = {k: v for k, v in data.items() if v is not None}

        return cls(**data)

    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.level != MemoryLevel.SHORT_TERM:
            return False
        if not self.expires_at:
            return False
        try:
            return datetime.now() > datetime.fromisoformat(self.expires_at)
        except:
            return False

    def is_valid(self) -> bool:
        """检查是否有效"""
        # 过期检查
        if self.is_expired():
            return False
        # 归档检查
        if self.is_archived:
            return False
        # 内容检查
        if not self.content or len(self.content.strip()) < 1:
            return False
        return True

    def update_access(self):
        """更新访问统计"""
        self.access_count += 1
        self.last_accessed = datetime.now().isoformat()

    def clone(self) -> "MemoryItem":
        """克隆记忆"""
        cloned = MemoryItem.from_dict(self.to_dict())
        if cloned is None:
            # This should never happen with a valid MemoryItem, but handle just in case
            raise RuntimeError("Failed to clone memory item")
        return cloned


@dataclass
class MemoryQuery:
    """记忆查询条件"""

    # 文本搜索
    query: str = ""

    # 用户过滤
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    group_id: Optional[str] = None
    platform: Optional[str] = None

    # 层级过滤
    level: Optional[MemoryLevel] = None
    levels: Optional[List[MemoryLevel]] = None

    # 标签过滤
    tags: Optional[List[str]] = None
    any_tag: bool = False  # True: 任一匹配, False: 全部匹配

    # 优先级过滤
    priority: Optional[float] = None
    min_priority: float = 0.0
    max_priority: float = 1.0

    # 来源过滤
    source: Optional[MemorySource] = None

    # 时间过滤
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    # 状态过滤
    include_archived: bool = False
    include_expired: bool = False
    is_pinned: Optional[bool] = None

    # 对话详情过滤
    event_type: Optional[str] = None
    location: Optional[str] = None
    conversation_partner: Optional[str] = None
    emotional_tone: Optional[str] = None
    min_significance: float = 0.0
    max_significance: float = 1.0

    # 分页
    limit: int = 20
    offset: int = 0

    # 排序
    sort_by: str = "priority"  # priority, created_at, updated_at, access_count
    sort_order: str = "desc"  # asc, desc


# ==================== 存储后端接口 ====================


class MemoryBackend:
    """记忆存储后端基类"""

    async def save(self, memory: MemoryItem) -> bool:
        raise NotImplementedError

    async def load(self, memory_id: str) -> Optional[MemoryItem]:
        raise NotImplementedError

    async def delete(self, memory_id: str) -> bool:
        raise NotImplementedError

    async def query(self, query: MemoryQuery) -> List[MemoryItem]:
        raise NotImplementedError

    async def close(self):
        pass


class JsonBackend(MemoryBackend):
    """JSON文件后端"""

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

        # 子目录
        self.dialogue_dir = base_dir / "dialogue"
        self.short_term_dir = base_dir / "short_term"
        self.long_term_dir = base_dir / "long_term"
        self.semantic_dir = base_dir / "semantic"
        self.knowledge_dir = base_dir / "knowledge"

        for d in [
            self.dialogue_dir,
            self.short_term_dir,
            self.long_term_dir,
            self.semantic_dir,
            self.knowledge_dir,
        ]:
            d.mkdir(parents=True, exist_ok=True)

        # 索引文件
        self.index_file = base_dir / "index.json"
        self._index: Dict[str, Dict] = {}

        # 加载索引
        self._load_index()

    def _load_index(self):
        """加载索引"""
        if self.index_file.exists():
            try:
                with open(self.index_file, "r", encoding="utf-8") as f:
                    self._index = json.load(f)
            except Exception as e:
                logger.warning(f"加载索引失败: {e}")
                self._index = {}

    def _save_index(self):
        """保存索引"""
        try:
            with open(self.index_file, "w", encoding="utf-8") as f:
                json.dump(self._index, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存索引失败: {e}")

    def _get_dir(self, level: Union[MemoryLevel, List[MemoryLevel]]) -> Path:
        """获取层级目录"""
        # 如果是列表，取第一个元素
        if isinstance(level, list):
            if level:
                level = level[0]
            else:
                level = MemoryLevel.LONG_TERM  # 默认值

        dirs = {
            MemoryLevel.DIALOGUE: self.dialogue_dir,
            MemoryLevel.SHORT_TERM: self.short_term_dir,
            MemoryLevel.LONG_TERM: self.long_term_dir,
            MemoryLevel.SEMANTIC: self.semantic_dir,
            MemoryLevel.KNOWLEDGE: self.knowledge_dir,
        }
        return dirs.get(level, self.long_term_dir)

    def _get_file_path(self, memory: MemoryItem) -> Path:
        """获取文件路径"""
        level_dir = self._get_dir(memory.level)

        # 按用户分组
        if memory.user_id and memory.user_id != "global":
            user_dir = level_dir / memory.user_id
            user_dir.mkdir(parents=True, exist_ok=True)
            return user_dir / f"{memory.id}.json"

        return level_dir / f"{memory.id}.json"

    async def save(self, memory: MemoryItem) -> bool:
        """保存记忆"""
        try:
            file_path = self._get_file_path(memory)

            # 异步写入
            async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
                await f.write(
                    json.dumps(memory.to_dict(), ensure_ascii=False, indent=2)
                )

            # 更新索引
            self._index[memory.id] = {
                "level": memory.level.value,
                "user_id": memory.user_id,
                "session_id": memory.session_id,
                "tags": memory.tags,
                "created_at": memory.created_at,
                "file_path": str(file_path),
            }
            self._save_index()

            return True
        except Exception as e:
            logger.error(f"保存记忆失败: {e}")
            return False

    async def load(self, memory_id: str) -> Optional[MemoryItem]:
        """加载记忆"""
        if memory_id not in self._index:
            return None

        try:
            file_path = Path(self._index[memory_id]["file_path"])
            if not file_path.exists():
                return None

            async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                content = await f.read()
                data = json.loads(content)
                return MemoryItem.from_dict(data)
        except Exception as e:
            logger.error(f"加载记忆失败: {e}")
            return None

    async def delete(self, memory_id: str) -> bool:
        """删除记忆"""
        if memory_id not in self._index:
            return False

        try:
            file_path = Path(self._index[memory_id].get("file_path", ""))
            if file_path.exists():
                file_path.unlink()

            del self._index[memory_id]
            self._save_index()
            return True
        except Exception as e:
            logger.error(f"删除记忆失败: {e}")
            return False

    async def query(self, query: MemoryQuery) -> List[MemoryItem]:
        """查询记忆"""
        results = []

        # 决定搜索范围
        search_levels = (
            [query.levels]
            if query.levels
            else [query.level]
            if query.level
            else list(MemoryLevel)
        )

        for level in search_levels:
            level_dir = self._get_dir(level)
            if not level_dir.exists():
                continue

            # 遍历所有文件
            for file_path in level_dir.rglob("*.json"):
                try:
                    async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                        content = await f.read()
                        data = json.loads(content)
                        memory = MemoryItem.from_dict(data)

                        if self._match_query(memory, query):
                            results.append(memory)
                except:
                    continue

        # 排序
        results = self._sort_results(results, query.sort_by, query.sort_order)

        # 分页
        return results[query.offset : query.offset + query.limit]

    def _match_query(self, memory: Optional[MemoryItem], query: MemoryQuery) -> bool:
        """检查是否匹配查询"""
        if memory is None:
            return False

        # 用户过滤
        if query.user_id and memory.user_id != query.user_id:
            return False

        # 会话过滤
        if query.session_id and memory.session_id != query.session_id:
            return False

        # 标签过滤
        if query.tags:
            if query.any_tag:
                if not any(tag in memory.tags for tag in query.tags):
                    return False
            else:
                if not all(tag in memory.tags for tag in query.tags):
                    return False

        # 优先级过滤
        if memory.priority < query.min_priority or memory.priority > query.max_priority:
            return False

        # 时间过滤
        if query.start_time or query.end_time:
            try:
                mem_time = datetime.fromisoformat(memory.created_at)
                if query.start_time and mem_time < query.start_time:
                    return False
                if query.end_time and mem_time > query.end_time:
                    return False
            except:
                pass

        # 归档过滤
        if not query.include_archived and memory.is_archived:
            return False

        # 过期过滤
        if not query.include_expired and memory.is_expired():
            return False

        # 置顶过滤
        if query.is_pinned is not None and memory.is_pinned != query.is_pinned:
            return False

        # 文本搜索
        if query.query:
            if query.query.lower() not in memory.content.lower():
                # 检查标签
                if not any(query.query.lower() in tag.lower() for tag in memory.tags):
                    return False

        # 对话详情过滤
        if query.event_type and memory.event_type != query.event_type:
            return False
        if query.location and memory.location != query.location:
            return False
        if (
            query.conversation_partner
            and memory.conversation_partner != query.conversation_partner
        ):
            return False
        if query.emotional_tone and memory.emotional_tone != query.emotional_tone:
            return False
        if (
            memory.significance < query.min_significance
            or memory.significance > query.max_significance
        ):
            return False

        return True

    def _sort_results(
        self, results: List[MemoryItem], sort_by: str, order: str
    ) -> List[MemoryItem]:
        """排序结果"""
        reverse = order == "desc"

        if sort_by == "priority":
            results.sort(key=lambda x: x.priority, reverse=reverse)
        elif sort_by == "created_at":
            results.sort(key=lambda x: x.created_at, reverse=reverse)
        elif sort_by == "updated_at":
            results.sort(key=lambda x: x.updated_at, reverse=reverse)
        elif sort_by == "access_count":
            results.sort(key=lambda x: x.access_count, reverse=reverse)

        return results

    async def get_all_ids(self, level: Optional[MemoryLevel] = None) -> List[str]:
        """获取所有记忆ID"""
        if level:
            return [
                mid
                for mid, info in self._index.items()
                if info.get("level") == level.value
            ]
        return list(self._index.keys())

    async def count(self, level: Optional[MemoryLevel] = None) -> int:
        """统计数量"""
        if level:
            return sum(
                1 for info in self._index.values() if info.get("level") == level.value
            )
        return len(self._index)


# ==================== 核心系统 ====================


class MiyaMemoryCore:
    """
    弥娅统一记忆系统核心

    这是唯一入口，所有代码都必须使用此类！
    """

    def __init__(
        self,
        data_dir: Union[str, Path] = "data/memory",
        redis_client=None,
        milvus_client=None,
        neo4j_client=None,
        short_term_ttl: int = 3600,
        enable_backup: bool = True,
    ):
        self.data_dir = Path(data_dir)
        self.redis_client = redis_client
        self.milvus_client = milvus_client
        self.neo4j_client = neo4j_client
        self.short_term_ttl = short_term_ttl
        self.enable_backup = enable_backup

        # 后端
        self.backend: JsonBackend = JsonBackend(self.data_dir)

        # 内存缓存
        self._cache: Dict[str, MemoryItem] = {}
        self._user_index: Dict[str, Set[str]] = defaultdict(set)
        self._tag_index: Dict[str, Set[str]] = defaultdict(set)

        # 统计
        self._stats = {
            "total_stored": 0,
            "total_retrieved": 0,
            "total_deleted": 0,
            "total_updated": 0,
        }

        # 加载索引
        self._loaded = False

        logger.info(f"[MiyaMemoryCore] 初始化完成, 数据目录: {self.data_dir}")

    async def initialize(self):
        """初始化"""
        if self._loaded:
            return

        logger.info("[MiyaMemoryCore] 加载索引...")

        # 加载所有ID
        all_ids = await self.backend.get_all_ids()

        # 构建索引
        for memory_id in all_ids:
            memory = await self.backend.load(memory_id)
            if memory:
                self._cache[memory_id] = memory
                self._user_index[memory.user_id].add(memory_id)
                for tag in memory.tags:
                    self._tag_index[tag].add(memory_id)

        self._loaded = True
        logger.info(f"[MiyaMemoryCore] 加载完成, 缓存: {len(self._cache)} 条")

    # ==================== 核心存储方法 ====================

    async def store(
        self,
        content: str,
        level: Optional[MemoryLevel] = None,
        priority: float = 0.5,
        tags: Optional[List[str]] = None,
        user_id: str = "global",
        session_id: str = "",
        group_id: str = "",
        platform: str = "unknown",
        source: MemorySource = MemorySource.SYSTEM,
        role: str = "",
        # 对话详情
        event_type: str = "",
        location: str = "",
        conversation_partner: str = "",
        emotional_tone: str = "",
        significance: float = 0.5,
        ttl: Optional[int] = None,
        metadata: Optional[Dict] = None,
        # 知识图谱字段
        subject: str = "",
        predicate: str = "",
        obj: str = "",
    ) -> str:
        """
        存储记忆 - 统一入口

        Args:
            content: 记忆内容
            level: 存储层级 (自动判断)
            priority: 优先级 0-1
            tags: 标签列表
            user_id: 用户ID
            session_id: 会话ID
            group_id: 群组ID
            platform: 平台
            source: 来源
            role: 角色
            event_type: 对话事件类型
            location: 对话地点
            conversation_partner: 明确的对话对象
            emotional_tone: 情感基调
            significance: 主观重要性评分 (0-1)
            ttl: 短期记忆TTL(秒)
            metadata: 元数据
            subject: 知识图谱-主体
            predicate: 知识图谱-关系
            obj: 知识图谱-客体

        Returns:
            记忆ID
        """
        # 转换层级
        if isinstance(level, str):
            try:
                level = MemoryLevel(level)
            except:
                level = MemoryLevel.SHORT_TERM
        elif level is None:
            level = MemoryLevel.SHORT_TERM

        # 转换来源
        if isinstance(source, str):
            try:
                source = MemorySource(source)
            except:
                source = MemorySource.SYSTEM

        # 自动分类
        if level is None:
            level = self._auto_classify(
                content, tags, source, significance, emotional_tone, event_type
            )

        # 计算过期时间
        expires_at = None
        if level is not None and level == MemoryLevel.SHORT_TERM:
            ttl = ttl or self.short_term_ttl
            expires_at = (datetime.now() + timedelta(seconds=ttl)).isoformat()

        # 创建记忆
        memory = MemoryItem(
            content=content,
            level=level,
            priority=priority,
            tags=tags or [],
            user_id=user_id,
            session_id=session_id,
            group_id=group_id,
            platform=platform,
            source=source,
            role=role,
            event_type=event_type,
            location=location,
            conversation_partner=conversation_partner,
            emotional_tone=emotional_tone,
            significance=significance,
            expires_at=expires_at,
            metadata=metadata or {},
            subject=subject,
            predicate=predicate,
            obj=obj,
        )

        # 保存到后端
        await self.backend.save(memory)

        # 更新缓存和索引
        self._cache[memory.id] = memory
        self._user_index[user_id].add(memory.id)
        for tag in memory.tags:
            self._tag_index[tag].add(memory.id)

        # 同步到Redis
        if self.redis_client and level == MemoryLevel.SHORT_TERM:
            await self._sync_to_redis(memory)

        # 同步到向量库
        if self.milvus_client and level in [
            MemoryLevel.SEMANTIC,
            MemoryLevel.LONG_TERM,
        ]:
            await self._sync_to_milvus(memory)

        # 同步到图谱
        if self.neo4j_client and (level == MemoryLevel.KNOWLEDGE or subject):
            await self._sync_to_neo4j(memory)

        # 备份
        if self.enable_backup:
            await self._backup_memory(memory)

        self._stats["total_stored"] += 1

        logger.debug(
            f"[MiyaMemoryCore] 存储: {memory.id}, level={level.value}, user={user_id}"
        )
        return memory.id

    def _auto_classify(
        self,
        content: str,
        tags: Optional[List[str]],
        source: MemorySource,
        significance: float = 0.5,
        emotional_tone: str = "",
        event_type: str = "",
    ) -> MemoryLevel:
        """自动分类 - 基于内容、情感、重要性和事件类型"""
        content_lower = content.lower()

        # 基于主观重要性 - 高重要性直接长期存储
        if significance >= 0.8:
            return MemoryLevel.LONG_TERM

        # 基于情感强度 - 强烈情感（无论正面负面）倾向长期记忆
        strong_emotions = ["愤怒", "恐惧", "惊讶", "悲伤", "极度兴奋", "创伤"]
        if any(emotion in emotional_tone for emotion in strong_emotions):
            if significance >= 0.6:  # 情感强且重要性中等以上
                return MemoryLevel.LONG_TERM

        # 基于事件类型 - 某些事件类型应被长期记住
        long_term_events = [
            "生日",
            "纪念日",
            "毕业",
            "结婚",
            "工作面试",
            "重要决定",
            "医疗诊断",
            "法律事务",
        ]
        if any(event in event_type for event in long_term_events):
            return MemoryLevel.LONG_TERM

        # 重要信息 -> 长期（保持原有逻辑作为后备）
        important_tags = [
            "生日",
            "电话",
            "邮箱",
            "地址",
            "记住",
            "我叫",
            "喜欢",
            "讨厌",
            "important",
            "contact",
            "birthday",
        ]
        if tags:
            for tag in tags:
                if any(kw in tag.lower() for kw in important_tags):
                    return MemoryLevel.LONG_TERM

        for kw in ["生日", "电话", "邮箱", "地址", "记住", "我叫", "喜欢"]:
            if kw in content:
                return MemoryLevel.LONG_TERM

        # 对话 -> 对话层（但带有强情感或高重要性的对话可能升级）
        if source == MemorySource.DIALOGUE:
            # 如果对话有高重要性或强烈情感，考虑升级到长期
            if significance >= 0.6 or any(
                emotion in emotional_tone
                for emotion in ["极度愉快", "深度悲伤", "强烈焦虑"]
            ):
                return MemoryLevel.LONG_TERM
            return MemoryLevel.DIALOGUE

        # 自动提取 -> 短期
        if source == MemorySource.AUTO_EXTRACT:
            return MemoryLevel.SHORT_TERM

        # 手动添加 -> 长期（但低重要性可能放在短期）
        if source == MemorySource.MANUAL:
            if significance >= 0.4:
                return MemoryLevel.LONG_TERM
            else:
                return MemoryLevel.SHORT_TERM

        # 默认短期
        return MemoryLevel.SHORT_TERM

    # ==================== 检索方法 ====================

    async def retrieve(
        self,
        query: Union[str, MemoryQuery],
        level: Optional[MemoryLevel] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 20,
        # 对话详情过滤
        event_type: Optional[str] = None,
        location: Optional[str] = None,
        conversation_partner: Optional[str] = None,
        emotional_tone: Optional[str] = None,
        min_significance: float = 0.0,
        max_significance: float = 1.0,
    ) -> List[MemoryItem]:
        """
        检索记忆 - 统一检索入口
        """
        # 构建查询
        if isinstance(query, str):
            q = MemoryQuery(
                query=query,
                level=level,
                user_id=user_id,
                session_id=session_id,
                tags=tags,
                limit=limit,
                event_type=event_type,
                location=location,
                conversation_partner=conversation_partner,
                emotional_tone=emotional_tone,
                min_significance=min_significance,
                max_significance=max_significance,
            )
        else:
            # 如果已经是MemoryQuery对象，更新其字段
            q = query
            if level is not None:
                q.level = level
            if user_id is not None:
                q.user_id = user_id
            if session_id is not None:
                q.session_id = session_id
            if tags is not None:
                q.tags = tags
            if event_type is not None:
                q.event_type = event_type
            if location is not None:
                q.location = location
            if conversation_partner is not None:
                q.conversation_partner = conversation_partner
            if emotional_tone is not None:
                q.emotional_tone = emotional_tone
            if min_significance != 0.0:  # 只在非默认值时更新
                q.min_significance = min_significance
            if max_significance != 1.0:  # 只在非默认值时更新
                q.max_significance = max_significance

        # 先从缓存搜索
        results = self._search_from_cache(q)

        # 从后端搜索
        if len(results) < q.limit:
            backend_results = await self.backend.query(q)
            # 合并去重
            existing_ids = {r.id for r in results}
            for r in backend_results:
                if r.id not in existing_ids:
                    results.append(r)

        # 更新访问
        for r in results:
            r.update_access()

        self._stats["total_retrieved"] += len(results)

        return results[: q.limit]

    def _search_from_cache(self, query: MemoryQuery) -> List[MemoryItem]:
        """从缓存搜索"""
        results = []

        for memory in self._cache.values():
            if not memory.is_valid():
                continue

            if self._match_query(memory, query):
                results.append(memory)

        # 排序
        results = self._sort_results(results, query.sort_by, query.sort_order)

        return results[query.offset : query.offset + query.limit]

    def _match_query(self, memory: MemoryItem, query: MemoryQuery) -> bool:
        """匹配查询"""
        if query.user_id and memory.user_id != query.user_id:
            return False
        if query.session_id and memory.session_id != query.session_id:
            return False
        if query.level and memory.level != query.level:
            return False
        if query.tags:
            if not any(tag in memory.tags for tag in query.tags):
                return False
        if memory.priority < query.min_priority:
            return False
        if query.query:
            q = query.query.lower()
            if q not in memory.content.lower():
                if not any(q in tag.lower() for tag in memory.tags):
                    return False
        # 对话详情过滤
        if query.event_type and memory.event_type != query.event_type:
            return False
        if query.location and memory.location != query.location:
            return False
        if (
            query.conversation_partner
            and memory.conversation_partner != query.conversation_partner
        ):
            return False
        if query.emotional_tone and memory.emotional_tone != query.emotional_tone:
            return False
        if (
            memory.significance < query.min_significance
            or memory.significance > query.max_significance
        ):
            return False
        return True

    def _sort_results(
        self, results: List[MemoryItem], sort_by: str, order: str
    ) -> List[MemoryItem]:
        """排序"""
        reverse = order == "desc"
        if sort_by == "priority":
            results.sort(key=lambda x: x.priority, reverse=reverse)
        elif sort_by == "created_at":
            results.sort(key=lambda x: x.created_at, reverse=reverse)
        return results

    # ==================== 便捷方法 ====================

    async def get_by_id(self, memory_id: str) -> Optional[MemoryItem]:
        """按ID获取"""
        # 先从缓存
        if memory_id in self._cache:
            return self._cache[memory_id]

        # 从后端加载
        memory = await self.backend.load(memory_id)
        if memory:
            self._cache[memory_id] = memory
        return memory

    async def get_recent(
        self,
        user_id: Optional[str] = None,
        level: Optional[MemoryLevel] = None,
        limit: int = 20,
    ) -> List[MemoryItem]:
        """获取最近的记忆"""
        q = MemoryQuery(
            user_id=user_id,
            level=level,
            limit=limit,
            sort_by="created_at",
            sort_order="desc",
        )
        return await self.retrieve(q)

    async def search_by_tag(
        self,
        tag: str,
        user_id: Optional[str] = None,
        limit: int = 20,
    ) -> List[MemoryItem]:
        """按标签搜索"""
        q = MemoryQuery(
            tags=[tag],
            user_id=user_id,
            limit=limit,
        )
        return await self.retrieve(q)

    async def search_by_user(
        self,
        user_id: str,
        level: Optional[MemoryLevel] = None,
        limit: int = 20,
    ) -> List[MemoryItem]:
        """按用户搜索"""
        q = MemoryQuery(
            user_id=user_id,
            level=level,
            limit=limit,
        )
        return await self.retrieve(q)

    async def get_dialogue(
        self,
        session_id: str,
        platform: str = "unknown",
        limit: int = 50,
    ) -> List[MemoryItem]:
        """获取对话历史"""
        q = MemoryQuery(
            session_id=session_id,
            level=MemoryLevel.DIALOGUE,
            limit=limit,
            sort_by="created_at",
            sort_order="asc",
        )
        results = await self.retrieve(q)

        # 过滤平台
        if platform:
            results = [r for r in results if r.platform == platform]

        return results

    # ==================== 更新删除 ====================

    async def update(
        self,
        memory_id: str,
        content: Optional[str] = None,
        tags: Optional[List[str]] = None,
        priority: Optional[float] = None,
        is_pinned: Optional[bool] = None,
        is_archived: Optional[bool] = None,
    ) -> bool:
        """更新记忆"""
        memory = await self.get_by_id(memory_id)
        if not memory:
            return False

        # 更新字段
        if content is not None:
            memory.content = content
        if tags is not None:
            # 更新标签索引
            for old_tag in memory.tags:
                self._tag_index[old_tag].discard(memory_id)
            memory.tags = tags
            for new_tag in memory.tags:
                self._tag_index[new_tag].add(memory_id)
        if priority is not None:
            memory.priority = priority
        if is_pinned is not None:
            memory.is_pinned = is_pinned
        if is_archived is not None:
            memory.is_archived = is_archived

        memory.updated_at = datetime.now().isoformat()

        # 保存
        await self.backend.save(memory)
        self._cache[memory_id] = memory

        self._stats["total_updated"] += 1
        return True

    async def delete(self, memory_id: str) -> bool:
        """删除记忆"""
        memory = await self.get_by_id(memory_id)
        if not memory:
            return False

        # 从缓存移除
        if memory_id in self._cache:
            del self._cache[memory_id]

        # 从索引移除
        self._user_index[memory.user_id].discard(memory_id)
        for tag in memory.tags:
            self._tag_index[tag].discard(memory_id)

        # 从后端删除
        await self.backend.delete(memory_id)

        # 从Redis删除
        if self.redis_client:
            try:
                self.redis_client.delete(f"memory:{memory_id}")
            except:
                pass

        self._stats["total_deleted"] += 1
        return True

    # ==================== 批量操作 ====================

    async def delete_expired(self) -> int:
        """删除过期记忆"""
        count = 0
        expired_ids = []

        for memory_id, memory in self._cache.items():
            if memory.is_expired():
                expired_ids.append(memory_id)

        for memory_id in expired_ids:
            await self.delete(memory_id)
            count += 1

        if count > 0:
            logger.info(f"[MiyaMemoryCore] 清理了 {count} 条过期记忆")

        return count

    async def archive_old(self, days: int = 90) -> int:
        """归档旧记忆"""
        count = 0
        cutoff = datetime.now() - timedelta(days=days)

        for memory in self._cache.values():
            if memory.level != MemoryLevel.DIALOGUE:
                continue

            try:
                created = datetime.fromisoformat(memory.created_at)
                if created < cutoff:
                    memory.is_archived = True
                    await self.backend.save(memory)
                    count += 1
            except:
                pass

        logger.info(f"[MiyaMemoryCore] 归档了 {count} 条旧对话")
        return count

    # ==================== 用户画像 ====================

    async def get_user_profile(self, user_id: str) -> Dict:
        """获取用户画像"""
        memories = await self.search_by_user(user_id, limit=500)

        profile = {
            "user_id": user_id,
            "total_memories": len(memories),
            "by_level": defaultdict(int),
            "by_tag": defaultdict(int),
            "preferences": [],
            "birthdays": [],
            "contacts": [],
            "sessions": set(),
            "platforms": set(),
        }

        for mem in memories:
            profile["by_level"][mem.level.value] += 1

            for tag in mem.tags:
                profile["by_tag"][tag] += 1

            if "偏好" in mem.tags or "喜欢" in mem.tags:
                profile["preferences"].append(mem.content)
            if "生日" in mem.tags:
                profile["birthdays"].append(mem.content)
            if "联系" in mem.tags:
                profile["contacts"].append(mem.content)

            if mem.session_id:
                profile["sessions"].add(mem.session_id)
            if mem.platform:
                profile["platforms"].add(mem.platform)

        profile["by_level"] = dict(profile["by_level"])
        profile["by_tag"] = dict(profile["by_tag"])
        profile["sessions"] = list(profile["sessions"])
        profile["platforms"] = list(profile["platforms"])

        return profile

    # ==================== 统计 ====================

    async def get_statistics(self) -> Dict:
        """获取统计"""
        return {
            "total_cached": len(self._cache),
            "total_indexed": await self.backend.count(),
            "by_level": {
                "dialogue": len(
                    [m for m in self._cache.values() if m.level == MemoryLevel.DIALOGUE]
                ),
                "short_term": len(
                    [
                        m
                        for m in self._cache.values()
                        if m.level == MemoryLevel.SHORT_TERM
                    ]
                ),
                "long_term": len(
                    [
                        m
                        for m in self._cache.values()
                        if m.level == MemoryLevel.LONG_TERM
                    ]
                ),
                "semantic": len(
                    [m for m in self._cache.values() if m.level == MemoryLevel.SEMANTIC]
                ),
                "knowledge": len(
                    [
                        m
                        for m in self._cache.values()
                        if m.level == MemoryLevel.KNOWLEDGE
                    ]
                ),
            },
            "by_user": len(self._user_index),
            "by_tag": len(self._tag_index),
            "stats": self._stats,
        }

    # ==================== 同步方法 ====================

    async def _sync_to_redis(self, memory: MemoryItem):
        """同步到Redis"""
        if not self.redis_client:
            return

        try:
            ttl = self.short_term_ttl
            if memory.expires_at:
                exp = datetime.fromisoformat(memory.expires_at)
                ttl = max(1, int((exp - datetime.now()).total_seconds()))

            key = f"memory:{memory.id}"
            self.redis_client.setex(
                key, ttl, json.dumps(memory.to_dict(), ensure_ascii=False)
            )
        except Exception as e:
            logger.warning(f"[MiyaMemoryCore] Redis同步失败: {e}")

    async def _sync_to_milvus(self, memory: MemoryItem):
        """同步到Milvus"""
        if not self.milvus_client:
            return

        try:
            # 生成向量
            vector = memory.vector or self._simple_embed(memory.content)

            # 插入数据
            data = [
                [memory.id],  # memory_id
                [vector],  # vector
                [memory.content[:4000]],  # content
                [memory.user_id],  # user_id
            ]

            self.milvus_client.insert(data)
            self.milvus_client.flush()

        except Exception as e:
            logger.warning(f"[MiyaMemoryCore] Milvus同步失败: {e}")

    async def _sync_to_neo4j(self, memory: MemoryItem):
        """同步到Neo4j"""
        if not self.neo4j_client:
            return

        try:
            if memory.subject and memory.predicate:
                self.neo4j_client.create_memory_quintuple(
                    memory.subject,
                    memory.predicate,
                    memory.obj or memory.content[:100],
                    context=memory.content[:200],
                    emotion=memory.metadata.get("emotion", "neutral"),
                )
        except Exception as e:
            logger.warning(f"[MiyaMemoryCore] Neo4j同步失败: {e}")

    async def _backup_memory(self, memory: MemoryItem):
        """备份记忆"""
        backup_dir = self.data_dir / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)

        date = datetime.now().strftime("%Y%m%d")
        backup_file = backup_dir / f"{date}.json"

        try:
            # 读取现有备份
            backups = []
            if backup_file.exists():
                with open(backup_file, "r", encoding="utf-8") as f:
                    backups = json.load(f)

            # 添加新备份
            backups.append(memory.to_dict())

            # 保留最近30天
            if len(backups) > 1000:
                backups = backups[-1000:]

            # 保存
            with open(backup_file, "w", encoding="utf-8") as f:
                json.dump(backups, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"[MiyaMemoryCore] 备份失败: {e}")

    def _simple_embed(self, text: str) -> List[float]:
        """生成伪向量"""
        import math
        from hashlib import sha256

        dimension = 1536
        vector = []

        for i in range(dimension):
            digest = sha256((text + str(i)).encode("utf-8")).digest()
            hash_val = int.from_bytes(digest[:8], "big", signed=False)
            vector.append((hash_val % 10000) / 10000.0)

        norm = math.sqrt(sum(x * x for x in vector))
        if norm > 0:
            vector = [x / norm for x in vector]

        return vector


# ==================== 全局单例 ====================

_global_core: Optional[MiyaMemoryCore] = None


async def get_memory_core(
    data_dir: Union[str, Path] = "data/memory",
    redis_client=None,
    milvus_client=None,
    neo4j_client=None,
) -> MiyaMemoryCore:
    """获取全局核心实例"""
    global _global_core

    if _global_core is None:
        _global_core = MiyaMemoryCore(
            data_dir=data_dir,
            redis_client=redis_client,
            milvus_client=milvus_client,
            neo4j_client=neo4j_client,
        )
        await _global_core.initialize()

    return _global_core


def reset_memory_core():
    """重置全局核心"""
    global _global_core
    _global_core = None
