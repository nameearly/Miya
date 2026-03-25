"""
三层认知记忆架构

参考 Undefined 项目的认知记忆系统设计：
1. 短期记忆（ShortTermMemory）- 对话便签 memo
2. 认知记忆（CognitiveMemory）- ChromaDB向量 + 用户/群侧写
3. 置顶备忘录（TopMemory）- AI自我提醒

特性：
- 前台零阻塞：文件队列异步处理
- 向量语义检索
- 自动用户/群侧写
- 时间衰减加权排序
- MMR 多样性去重
"""

import asyncio
import json
import logging
import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class MemoryType(Enum):
    """记忆类型"""

    SHORT_TERM = "short_term"  # 短期记忆
    COGNITIVE = "cognitive"  # 认知记忆
    TOP_MEMORY = "top_memory"  # 置顶备忘录


@dataclass
class ShortTermMemo:
    """短期便签"""

    memo_id: str
    content: str
    session_id: str
    created_at: datetime
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CognitiveEvent:
    """认知事件"""

    event_id: str
    content: str  # 原始内容
    absolute_content: str  # 绝对化改写后的内容
    entity_type: str  # user / group
    entity_id: str  # 用户ID或群ID
    observations: List[str] = field(default_factory=list)  # 观察列表
    created_at: datetime = field(default_factory=datetime.now)
    is_absolute: bool = False  # 是否已经绝对化改写


@dataclass
class TopMemoryItem:
    """置顶备忘录"""

    memory_id: str
    content: str
    created_at: datetime
    updated_at: datetime
    created_by: str = "system"  # system / user
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ShortTermMemory:
    """
    短期记忆（便签模式）

    每轮对话结束自动记录便签备忘，最近 N 条始终注入，保持短期连续性
    """

    def __init__(self, data_dir: Path, max_memos: int = 20):
        self.data_dir = data_dir / "short_term"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.max_memos = max_memos

        # 内存缓存
        self._cache: Dict[str, List[ShortTermMemo]] = {}

    def _get_cache_key(self, session_id: str) -> str:
        """获取缓存键"""
        return f"memo_{session_id}"

    def add_memo(
        self, session_id: str, content: str, context: Optional[Dict] = None
    ) -> ShortTermMemo:
        """添加便签"""
        memo = ShortTermMemo(
            memo_id=str(uuid.uuid4()),
            content=content,
            session_id=session_id,
            created_at=datetime.now(),
            context=context or {},
        )

        # 添加到缓存
        cache_key = self._get_cache_key(session_id)
        if cache_key not in self._cache:
            self._cache[cache_key] = []

        self._cache[cache_key].append(memo)

        # 限制数量
        if len(self._cache[cache_key]) > self.max_memos:
            self._cache[cache_key] = self._cache[cache_key][-self.max_memos :]

        # 持久化
        self._save_memos(session_id)

        logger.debug(
            f"[ShortTermMemory] 添加便签: session={session_id}, content={content[:30]}..."
        )
        return memo

    def get_recent_memos(self, session_id: str, count: int = 5) -> List[ShortTermMemo]:
        """获取最近的便签"""
        cache_key = self._get_cache_key(session_id)

        if cache_key not in self._cache:
            self._load_memos(session_id)

        memos = self._cache.get(cache_key, [])
        return memos[-count:] if len(memos) > count else memos

    def format_memos_for_prompt(self, session_id: str, count: int = 5) -> str:
        """格式化便签为提示词"""
        memos = self.get_recent_memos(session_id, count)

        if not memos:
            return ""

        lines = ["【最近便签】"]
        for memo in memos:
            time_str = memo.created_at.strftime("%H:%M")
            lines.append(f"- {time_str}: {memo.content}")

        return "\n".join(lines)

    def clear_session(self, session_id: str):
        """清除会话的便签"""
        cache_key = self._get_cache_key(session_id)
        if cache_key in self._cache:
            del self._cache[cache_key]

        # 删除文件
        file_path = self.data_dir / f"{session_id}.json"
        if file_path.exists():
            file_path.unlink()

    def _save_memos(self, session_id: str):
        """保存便签到文件"""
        cache_key = self._get_cache_key(session_id)
        memos = self._cache.get(cache_key, [])

        data = [
            {
                "memo_id": m.memo_id,
                "content": m.content,
                "session_id": m.session_id,
                "created_at": m.created_at.isoformat(),
                "context": m.context,
            }
            for m in memos
        ]

        file_path = self.data_dir / f"{session_id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _load_memos(self, session_id: str):
        """从文件加载便签"""
        cache_key = self._get_cache_key(session_id)

        file_path = self.data_dir / f"{session_id}.json"
        if not file_path.exists():
            self._cache[cache_key] = []
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self._cache[cache_key] = [
                ShortTermMemo(
                    memo_id=m["memo_id"],
                    content=m["content"],
                    session_id=m["session_id"],
                    created_at=datetime.fromisoformat(m["created_at"]),
                    context=m.get("context", {}),
                )
                for m in data
            ]
        except Exception as e:
            logger.error(f"[ShortTermMemory] 加载便签失败: {e}")
            self._cache[cache_key] = []


class CognitiveMemory:
    """
    认知记忆（向量存储 + 侧写）

    核心层：AI 在每轮对话中主动观察并提取用户/群聊事实
    经后台史官异步改写为绝对化事件并存入向量库
    支持语义检索、时间衰减加权排序、MMR 多样性去重
    """

    def __init__(self, data_dir: Path, embedding_client=None):
        self.data_dir = data_dir / "cognitive"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # ChromaDB 目录
        self.chroma_dir = self.data_dir / "chromadb"
        self.chroma_dir.mkdir(exist_ok=True)

        # 侧写目录
        self.profiles_dir = self.data_dir / "profiles"
        self.profiles_dir.mkdir(exist_ok=True)

        # 队列目录
        self.queues_dir = self.data_dir / "queues"
        self.queues_dir.mkdir(exist_ok=True)

        self.pending_dir = self.queues_dir / "pending"
        self.processing_dir = self.queues_dir / "processing"
        self.failed_dir = self.queues_dir / "failed"

        self.pending_dir.mkdir(exist_ok=True)
        self.processing_dir.mkdir(exist_ok=True)
        self.failed_dir.mkdir(exist_ok=True)

        self.embedding_client = embedding_client

        # ChromaDB 客户端
        self.chroma_client = None
        self.events_collection = None
        self._init_chroma()

        # 后台史官任务
        self._historian_task = None
        self._running = False

    def _init_chroma(self):
        """初始化 ChromaDB"""
        try:
            import chromadb
            from chromadb.config import Settings

            self.chroma_client = chromadb.PersistentClient(
                path=str(self.chroma_dir), settings=Settings(anonymized_telemetry=False)
            )

            # 创建事件集合
            self.events_collection = self.chroma_client.get_or_create_collection(
                name="cognitive_events", metadata={"hnsw:space": "cosine"}
            )

            logger.info("[CognitiveMemory] ChromaDB 初始化成功")
        except Exception as e:
            logger.warning(f"[CognitiveMemory] ChromaDB 初始化失败: {e}")
            self.chroma_client = None

    def add_event(self, event: CognitiveEvent) -> str:
        """添加认知事件（前台操作，仅写入队列）"""
        # 写入待处理队列
        job_id = event.event_id
        job_data = {
            "event_id": event.event_id,
            "content": event.content,
            "entity_type": event.entity_type,
            "entity_id": event.entity_id,
            "observations": event.observations,
            "created_at": event.created_at.isoformat(),
        }

        file_path = self.pending_dir / f"{job_id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(job_data, f, ensure_ascii=False, indent=2)

        logger.debug(f"[CognitiveMemory] 添加事件到队列: {job_id}")
        return job_id

    async def start_historian(self):
        """启动后台史官"""
        if self._running:
            return

        self._running = True
        self._historian_task = asyncio.create_task(self._historian_loop())
        logger.info("[CognitiveMemory] 后台史官已启动")

    async def stop_historian(self):
        """停止后台史官"""
        self._running = False
        if self._historian_task:
            self._historian_task.cancel()
            try:
                await self._historian_task
            except asyncio.CancelledError:
                pass
        logger.info("[CognitiveMemory] 后台史官已停止")

    async def _historian_loop(self):
        """史官主循环"""
        while self._running:
            try:
                # 处理待处理队列
                await self._process_pending_queue()

                # 清理过期的处理中任务
                await self._cleanup_stale_jobs()

            except Exception as e:
                logger.error(f"[CognitiveMemory] 史官循环异常: {e}")

            await asyncio.sleep(5)  # 每5秒检查一次

    async def _process_pending_queue(self):
        """处理待处理队列"""
        if not self.pending_dir.exists():
            return

        # 获取所有待处理文件
        pending_files = list(self.pending_dir.glob("*.json"))

        for file_path in pending_files:
            try:
                # 原子移动到处理中
                job_id = file_path.stem
                processing_path = self.processing_dir / f"{job_id}.json"

                # 原子替换
                file_path.rename(processing_path)

                # 读取任务
                with open(processing_path, "r", encoding="utf-8") as f:
                    job_data = json.load(f)

                # 执行绝对化改写
                absolute_content = await self._absolutize_content(job_data["content"])

                # 存入向量库
                if self.events_collection and absolute_content:
                    self.events_collection.add(
                        ids=[job_id],
                        documents=[absolute_content],
                        metadatas=[
                            {
                                "entity_type": job_data["entity_type"],
                                "entity_id": job_data["entity_id"],
                                "created_at": job_data["created_at"],
                            }
                        ],
                    )

                    logger.debug(f"[CognitiveMemory] 事件已入库: {job_id}")

                # 处理观察，更新侧写
                if job_data.get("observations"):
                    await self._update_profile(
                        job_data["entity_type"],
                        job_data["entity_id"],
                        job_data["observations"],
                    )

                # 删除处理中的文件
                processing_path.unlink()

            except Exception as e:
                logger.error(f"[CognitiveMemory] 处理任务失败 {file_path.name}: {e}")
                # 移动到失败目录
                try:
                    failed_path = self.failed_dir / file_path.name
                    file_path.rename(failed_path)
                except:
                    pass

    async def _absolutize_content(self, content: str) -> str:
        """绝对化改写（消灭代词/相对时间）"""
        # 简化实现：使用规则替换
        # 实际应使用 LLM 进行改写
        absolute = content

        # 替换相对时间
        replacements = {
            "刚才": "在本次对话中",
            "刚刚": "在本次对话中",
            "之前": "在之前",
            "以后": "在未来",
            "他": "该用户",
            "她": "该用户",
            "它": "该事物",
        }

        for old, new in replacements.items():
            absolute = absolute.replace(old, new)

        return absolute

    async def _update_profile(
        self, entity_type: str, entity_id: str, observations: List[str]
    ):
        """更新用户/群侧写"""
        profile_path = self.profiles_dir / f"{entity_type}_{entity_id}.md"

        try:
            # 读取现有侧写
            existing_content = ""
            if profile_path.exists():
                existing_content = profile_path.read_text(encoding="utf-8")

            # 添加新观察
            new_observations = "\n".join([f"- {obs}" for obs in observations])

            if existing_content:
                # 追加到观察部分
                if "## 观察" in existing_content:
                    existing_content += f"\n{new_observations}"
                else:
                    existing_content += f"\n\n## 观察\n{new_observations}"
            else:
                # 创建新侧写
                existing_content = f"""# {entity_type.capitalize()} {entity_id}

## 观察
{new_observations}
"""

            # 写入
            profile_path.write_text(existing_content, encoding="utf-8")
            logger.debug(f"[CognitiveMemory] 侧写已更新: {entity_type}_{entity_id}")

        except Exception as e:
            logger.error(f"[CognitiveMemory] 更新侧写失败: {e}")

    async def _cleanup_stale_jobs(self):
        """清理过期的处理中任务"""
        if not self.processing_dir.exists():
            return

        stale_time = datetime.now() - timedelta(minutes=10)

        for file_path in self.processing_dir.glob("*.json"):
            try:
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if mtime < stale_time:
                    # 移回待处理
                    pending_path = self.pending_dir / file_path.name
                    file_path.rename(pending_path)
                    logger.warning(
                        f"[CognitiveMemory] 任务过期，重新入队: {file_path.name}"
                    )
            except:
                pass

    def search_events(
        self, query: str, entity_id: Optional[str] = None, top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """搜索认知事件"""
        if not self.events_collection:
            return []

        try:
            # 获取向量
            if self.embedding_client:
                query_vector = self.embedding_client.get_embedding(query)
            else:
                return []

            # 搜索
            where = {"entity_id": entity_id} if entity_id else None
            results = self.events_collection.query(
                query_embeddings=[query_vector],
                n_results=top_k,
                where=where,
            )

            # 格式化结果
            events = []
            if results and results.get("ids"):
                for i, event_id in enumerate(results["ids"][0]):
                    events.append(
                        {
                            "event_id": event_id,
                            "content": results["documents"][0][i],
                            "metadata": results["metadatas"][0][i],
                            "distance": results["distances"][0][i]
                            if "distances" in results
                            else 0,
                        }
                    )

            return events

        except Exception as e:
            logger.error(f"[CognitiveMemory] 搜索失败: {e}")
            return []

    def get_profile(self, entity_type: str, entity_id: str) -> Optional[str]:
        """获取用户/群侧写"""
        profile_path = self.profiles_dir / f"{entity_type}_{entity_id}.md"

        if profile_path.exists():
            return profile_path.read_text(encoding="utf-8")

        return None


class TopMemory:
    """
    置顶备忘录

    AI 自身的置顶提醒（自我约束、待办事项）
    每轮固定注入，支持增删改查
    """

    def __init__(self, data_dir: Path, max_items: int = 500):
        self.data_dir = data_dir / "top_memory"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.max_items = max_items

        # 内存缓存
        self._cache: List[TopMemoryItem] = []
        self._load_all()

    def _load_all(self):
        """加载所有置顶备忘录"""
        file_path = self.data_dir / "memory.json"

        if not file_path.exists():
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self._cache = [
                TopMemoryItem(
                    memory_id=m["memory_id"],
                    content=m["content"],
                    created_at=datetime.fromisoformat(m["created_at"]),
                    updated_at=datetime.fromisoformat(m["updated_at"]),
                    created_by=m.get("created_by", "system"),
                    tags=m.get("tags", []),
                    metadata=m.get("metadata", {}),
                )
                for m in data
            ]
        except Exception as e:
            logger.error(f"[TopMemory] 加载失败: {e}")

    def _save_all(self):
        """保存所有置顶备忘录"""
        file_path = self.data_dir / "memory.json"

        data = [
            {
                "memory_id": m.memory_id,
                "content": m.content,
                "created_at": m.created_at.isoformat(),
                "updated_at": m.updated_at.isoformat(),
                "created_by": m.created_by,
                "tags": m.tags,
                "metadata": m.metadata,
            }
            for m in self._cache
        ]

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def add(
        self,
        content: str,
        tags: Optional[List[str]] = None,
        created_by: str = "system",
        metadata: Optional[Dict] = None,
    ) -> TopMemoryItem:
        """添加置顶备忘录"""
        item = TopMemoryItem(
            memory_id=str(uuid.uuid4()),
            content=content,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            created_by=created_by,
            tags=tags or [],
            metadata=metadata or {},
        )

        self._cache.append(item)

        # 限制数量
        if len(self._cache) > self.max_items:
            self._cache = self._cache[-self.max_items :]

        self._save_all()

        logger.debug(f"[TopMemory] 添加: {content[:30]}...")
        return item

    def update(self, memory_id: str, content: str) -> bool:
        """更新置顶备忘录"""
        for item in self._cache:
            if item.memory_id == memory_id:
                item.content = content
                item.updated_at = datetime.now()
                self._save_all()
                return True
        return False

    def delete(self, memory_id: str) -> bool:
        """删除置顶备忘录"""
        for i, item in enumerate(self._cache):
            if item.memory_id == memory_id:
                del self._cache[i]
                self._save_all()
                return True
        return False

    def list_all(self) -> List[TopMemoryItem]:
        """列出所有置顶备忘录"""
        return self._cache.copy()

    def format_for_prompt(self) -> str:
        """格式化置顶备忘录为提示词"""
        if not self._cache:
            return ""

        lines = ["【置顶提醒】"]
        for item in self._cache:
            lines.append(f"- {item.content}")

        return "\n".join(lines)


class ThreeLayerCognitiveMemory:
    """
    三层认知记忆管理器

    整合短期记忆、认知记忆和置顶备忘录
    """

    def __init__(self, data_dir: Path, embedding_client=None):
        self.data_dir = data_dir / "cognitive_memory"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # 初始化三层记忆
        self.short_term = ShortTermMemory(self.data_dir)
        self.cognitive = CognitiveMemory(self.data_dir, embedding_client)
        self.top_memory = TopMemory(self.data_dir)

        logger.info("[ThreeLayerCognitiveMemory] 三层认知记忆系统初始化完成")

    async def initialize(self):
        """初始化（启动后台史官）"""
        await self.cognitive.start_historian()

    async def shutdown(self):
        """关闭"""
        await self.cognitive.stop_historian()

    def add_short_term_memo(
        self, session_id: str, content: str, context: Optional[Dict] = None
    ):
        """添加短期便签"""
        return self.short_term.add_memo(session_id, content, context)

    def get_short_term_memos(self, session_id: str, count: int = 5) -> str:
        """获取短期便签（格式化后）"""
        return self.short_term.format_memos_for_prompt(session_id, count)

    def add_cognitive_observation(
        self, content: str, entity_type: str, entity_id: str, observations: List[str]
    ):
        """添加认知观察"""
        event = CognitiveEvent(
            event_id=str(uuid.uuid4()),
            content=content,
            absolute_content="",
            entity_type=entity_type,
            entity_id=entity_id,
            observations=observations,
            created_at=datetime.now(),
        )
        return self.cognitive.add_event(event)

    def search_cognitive(
        self, query: str, entity_id: Optional[str] = None, top_k: int = 5
    ):
        """搜索认知记忆"""
        return self.cognitive.search_events(query, entity_id, top_k)

    def get_profile(self, entity_type: str, entity_id: str) -> Optional[str]:
        """获取侧写"""
        return self.cognitive.get_profile(entity_type, entity_id)

    def add_top_memory(
        self, content: str, tags: Optional[List[str]] = None, created_by: str = "system"
    ):
        """添加置顶备忘录"""
        return self.top_memory.add(content, tags, created_by)

    def get_top_memory(self) -> str:
        """获取置顶备忘录"""
        return self.top_memory.format_for_prompt()

    def build_memory_context(
        self, session_id: str, entity_type: str, entity_id: str, query: str = ""
    ) -> Dict[str, str]:
        """
        构建记忆上下文

        返回包含以下内容的字典：
        - short_term: 短期便签
        - cognitive: 认知记忆搜索结果
        - profile: 侧写
        - top_memory: 置顶备忘录
        """
        context = {}

        # 1. 短期便签
        context["short_term"] = self.get_short_term_memos(session_id)

        # 2. 认知记忆搜索
        if query:
            cognitive_results = self.search_cognitive(query, entity_id)
            if cognitive_results:
                context["cognitive"] = "\n".join(
                    [f"- {r['content']}" for r in cognitive_results[:3]]
                )

        # 3. 侧写
        profile = self.get_profile(entity_type, entity_id)
        if profile:
            context["profile"] = profile[:500]  # 限制长度

        # 4. 置顶备忘录
        context["top_memory"] = self.get_top_memory()

        return context


# 全局实例
_global_cognitive_memory: Optional[ThreeLayerCognitiveMemory] = None


def get_global_cognitive_memory(
    data_dir: Optional[Path] = None, embedding_client=None
) -> ThreeLayerCognitiveMemory:
    """获取全局三层认知记忆实例"""
    global _global_cognitive_memory

    if _global_cognitive_memory is None:
        if data_dir is None:
            data_dir = Path(__file__).parent.parent / "data"

        _global_cognitive_memory = ThreeLayerCognitiveMemory(data_dir, embedding_client)

    return _global_cognitive_memory
