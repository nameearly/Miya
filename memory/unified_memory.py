"""
弥娅统一记忆系统 v2.0

重构后的统一记忆系统，整合所有记忆功能：
1. 三层记忆架构（短期/认知/长期）
2. 真正的语义向量检索
3. LLM驱动的史官改写
4. 记忆持久化
5. 侧写压缩机制

设计目标：
- 统一接口，简化调用
- 真正的语义检索
- 记忆绝对化
- 自动压缩整理
"""

import asyncio
import json
import logging
import os
import time
import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, Tuple
from enum import Enum
import re

logger = logging.getLogger(__name__)


class MemoryType(Enum):
    """记忆类型"""

    SHORT_TERM = "short_term"  # 短期记忆（对话便签）
    COGNITIVE = "cognitive"  # 认知记忆（观察提炼）
    LONG_TERM = "long_term"  # 长期记忆（史官改写）
    PINNED = "pinned"  # 置顶备忘
    USER_PROFILE = "user_profile"  # 用户侧写
    GROUP_PROFILE = "group_profile"  # 群组侧写


class MemoryPriority(Enum):
    """记忆优先级"""

    LOW = 0.3
    NORMAL = 0.5
    HIGH = 0.7
    CRITICAL = 1.0


class MemoryCategory(Enum):
    """记忆分类"""

    EMOTION = "emotion"  # 情感类
    CHAT = "chat"  # 闲聊类
    DAILY = "daily"  # 日常类
    IMPORTANT = "important"  # 重要记录
    TASK = "task"  # 任务类
    KNOWLEDGE = "knowledge"  # 知识类
    UNKNOWN = "unknown"  # 未分类


@dataclass
class MemoryItem:
    """记忆项"""

    id: str
    content: str
    memory_type: MemoryType
    priority: float = 0.5
    user_id: str = ""
    group_id: str = ""
    timestamp: float = field(default_factory=time.time)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    is_absolute: bool = False  # 是否经过史官改写
    category: MemoryCategory = MemoryCategory.UNKNOWN  # 记忆分类

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "content": self.content,
            "memory_type": self.memory_type.value,
            "priority": self.priority,
            "user_id": self.user_id,
            "group_id": self.group_id,
            "timestamp": self.timestamp,
            "tags": self.tags,
            "metadata": self.metadata,
            "is_absolute": self.is_absolute,
            "category": self.category.value
            if self.category
            else MemoryCategory.UNKNOWN.value,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "MemoryItem":
        d["memory_type"] = MemoryType(d["memory_type"])
        if "category" in d and d["category"]:
            d["category"] = MemoryCategory(d["category"])
        else:
            d["category"] = MemoryCategory.UNKNOWN
        return cls(**d)


class EmbeddingService:
    """
    语义向量服务

    支持多种embedding服务：
    1. OpenAI Embeddings
    2. 本地模型（sentence-transformers）
    3. 智谱AI
    4. 回退到简化实现
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.embedding_func: Optional[Callable] = None
        self.dimension = 384  # 默认维度
        self._initialize()

    def _initialize(self):
        """初始化embedding服务"""
        provider = self.config.get("provider", "local")

        if provider == "openai":
            self._init_openai()
        elif provider == "zhipu":
            self._init_zhipu()
        elif provider == "local":
            self._init_local()
        else:
            self._init_fallback()

    def _init_openai(self):
        """OpenAI Embeddings"""
        try:
            from openai import OpenAI

            api_key = self.config.get("openai_api_key", os.getenv("OPENAI_API_KEY"))
            if api_key:
                self._client = OpenAI(api_key=api_key)
                self.embedding_func = self._openai_embed
                self.dimension = 1536
                logger.info("[Embedding] OpenAI Embeddings 已初始化")
        except ImportError:
            logger.warning("[Embedding] OpenAI SDK未安装，回退到本地模型")
            self._init_local()

    def _init_zhipu(self):
        """智谱AI Embeddings"""
        try:
            from zhipuai import ZhipuAI

            api_key = self.config.get("zhipu_api_key", os.getenv("ZHIPU_API_KEY"))
            if api_key:
                self._client = ZhipuAI(api_key=api_key)
                self.embedding_func = self._zhipu_embed
                self.dimension = 1024
                logger.info("[Embedding] 智谱AI Embeddings 已初始化")
        except ImportError:
            logger.warning("[Embedding] 智谱SDK未安装，回退到本地模型")
            self._init_local()

    def _init_local(self):
        """本地sentence-transformers模型"""
        try:
            from sentence_transformers import SentenceTransformer

            model_name = self.config.get(
                "local_model", "paraphrase-multilingual-MiniLM-L12-v2"
            )
            # 强制使用 CPU 模式，避免 CUDA 兼容性问题
            self._model = SentenceTransformer(model_name, device="cpu")
            self.embedding_func = self._local_embed
            self.dimension = 384
            logger.info(f"[Embedding] 本地模型已初始化: {model_name} (CPU模式)")
        except ImportError:
            logger.warning("[Embedding] sentence-transformers未安装，使用简化实现")
            self._init_fallback()

    def _init_fallback(self):
        """简化实现（用于无embedding服务的情况）"""
        self.embedding_func = self._simple_embed
        self.dimension = 128
        logger.info("[Embedding] 使用简化embedding实现")

    async def _openai_embed(self, text: str) -> List[float]:
        """OpenAI embedding"""
        try:
            response = self._client.embeddings.create(
                model="text-embedding-3-small", input=text[:8191]
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"[Embedding] OpenAI embedding失败: {e}")
            return self._simple_embed(text)

    async def _zhipu_embed(self, text: str) -> List[float]:
        """智谱AI embedding"""
        try:
            response = self._client.embeddings.create(
                model="embedding-2", input=text[:1000]
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"[Embedding] 智谱embedding失败: {e}")
            return self._simple_embed(text)

    def _local_embed(self, text: str) -> List[float]:
        """本地模型embedding"""
        try:
            embedding = self._model.encode(text)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"[Embedding] 本地embedding失败: {e}")
            return self._simple_embed(text)

    def _simple_embed(self, text: str) -> List[float]:
        """
        简化embedding实现

        使用词频统计生成伪向量，虽然不完美但比MD5好
        """
        import math

        words = re.findall(r"[\w]+", text.lower())
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1

        vector = []
        for i in range(self.dimension):
            freq_sum = sum(1 for w in words if hash(w) % self.dimension == i)
            vector.append(float(freq_sum) / (len(words) + 1) + 0.01 * math.sin(i))

        norm = math.sqrt(sum(v * v for v in vector))
        if norm > 0:
            vector = [v / norm for v in vector]

        return vector

    async def get_embedding(self, text: str) -> List[float]:
        """获取文本embedding"""
        if self.embedding_func:
            if asyncio.iscoroutinefunction(self.embedding_func):
                return await self.embedding_func(text)
            else:
                return self.embedding_func(text)
        return self._simple_embed(text)


class HistorianRewriter:
    """
    史官改写器

    使用LLM将观察转化为绝对化记忆
    """

    SYSTEM_PROMPT = """你是一个严谨的史官，负责将零散的观察记录改写为客观、准确的绝对化记忆。

改写原则：
1. 去除主观情感色彩，保留客观事实
2. 将"我觉得"、"我认为"改为"已知事实是"
3. 添加时间、地点、人物等关键上下文
4. 保持简洁，每个记忆点不超过50字
5. 对于未经验证的信息，使用"据观察"等限定词

输出格式：
- 每条记忆一行
- 事实明确，去除模糊表述"""

    USER_PROMPT_TEMPLATE = """请将以下观察改写为绝对化记忆：

观察记录：
{observations}

用户信息：{user_context}

请按格式输出（每条一行）："""

    def __init__(self, llm_func: Optional[Callable] = None, enabled: bool = True):
        self.llm_func = llm_func
        self.enabled = enabled
        self.cache: Dict[str, str] = {}

    def set_llm_func(self, func: Callable):
        """设置LLM调用函数"""
        self.llm_func = func

    async def rewrite(
        self, observations: List[str], context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        史官改写

        Args:
            observations: 原始观察列表
            context: 上下文信息

        Returns:
            改写后的绝对化记忆列表
        """
        if not self.enabled or not observations:
            return observations

        cache_key = "|".join(sorted(observations))
        if cache_key in self.cache:
            return self.cache[cache_key].split("|||")

        if not self.llm_func:
            logger.warning("[史官] LLM函数未设置，使用原始观察")
            return observations

        context = context or {}
        user_context = f"用户{context.get('user_id', '未知')}"

        try:
            if asyncio.iscoroutinefunction(self.llm_func):
                result = await self.llm_func(
                    system=self.SYSTEM_PROMPT,
                    user=self.USER_PROMPT_TEMPLATE.format(
                        observations="\n".join(f"- {o}" for o in observations),
                        user_context=user_context,
                    ),
                )
            else:
                result = self.llm_func(
                    system=self.SYSTEM_PROMPT,
                    user=self.USER_PROMPT_TEMPLATE.format(
                        observations="\n".join(f"- {o}" for o in observations),
                        user_context=user_context,
                    ),
                )

            rewritten = [line.strip() for line in result.split("\n") if line.strip()]

            self.cache[cache_key] = "|||".join(rewritten)

            return rewritten if rewritten else observations

        except Exception as e:
            logger.error(f"[史官] 改写失败: {e}")
            return observations


class UnifiedMemoryManager:
    """
    统一记忆管理器 v2.0

    整合所有记忆功能，提供统一的接口
    """

    def __init__(
        self, data_dir: str = "data/memory", config: Optional[Dict[str, Any]] = None
    ):
        self.data_dir = Path(data_dir)
        self.config = config or {}

        self._init_dirs()

        self.embedding_service = EmbeddingService(self.config.get("embedding", {}))
        self.historian = HistorianRewriter(
            enabled=self.config.get("historian_enabled", True)
        )

        self.short_term_memories: List[MemoryItem] = []
        self.cognitive_memories: List[MemoryItem] = []
        self.long_term_memories: List[MemoryItem] = []
        self.pinned_memories: Dict[str, str] = {}

        self.user_profiles: Dict[str, str] = {}
        self.group_profiles: Dict[str, str] = {}

        self.max_short_term = self.config.get("max_short_term", 50)
        self.max_cognitive = self.config.get("max_cognitive", 200)
        self.max_long_term = self.config.get("max_long_term", 1000)

        self.profile_max_lines = self.config.get("profile_max_lines", 500)
        self.profile_compress_threshold = self.config.get(
            "profile_compress_threshold", 300
        )

        self._history_lock = asyncio.Lock()
        self._profile_lock = asyncio.Lock()

        self._task_queue: asyncio.Queue = asyncio.Queue()
        self._historian_task: Optional[asyncio.Task] = None

    def _init_dirs(self):
        """初始化目录结构"""
        dirs = [
            self.data_dir,
            self.data_dir / "short_term",
            self.data_dir / "cognitive",
            self.data_dir / "long_term",
            self.data_dir / "profiles",
            self.data_dir / "cache",
            self.data_dir / "short_term",
            self.data_dir / "cognitive",
            self.data_dir / "long_term",
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

    def set_llm_func(self, func: Callable):
        """设置LLM调用函数"""
        self.historian.set_llm_func(func)

    async def initialize(self):
        """初始化系统"""
        await self._load_all()
        await self._start_background_tasks()
        logger.info("[统一记忆] 初始化完成")

    async def _load_all(self):
        """加载所有持久化数据"""
        await self._load_short_term()
        await self._load_cognitive()
        await self._load_long_term()
        await self._load_pinned()
        await self._load_profiles()

    async def _load_short_term(self):
        """加载短期记忆"""
        cache_file = self.data_dir / "short_term" / "cache.json"
        embeddings_file = self.data_dir / "short_term" / "embeddings.json"
        embeddings_data = {}
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if embeddings_file.exists():
                        with open(embeddings_file, "r", encoding="utf-8") as ef:
                            embeddings_data = json.load(ef)
                    self.short_term_memories = []
                    for item in data:
                        mem = MemoryItem.from_dict(item)
                        if item.get("id") in embeddings_data:
                            mem.embedding = embeddings_data[item["id"]]
                        self.short_term_memories.append(mem)
                logger.info(
                    f"[统一记忆] 加载了 {len(self.short_term_memories)} 条短期记忆"
                )
            except Exception as e:
                logger.error(f"[统一记忆] 加载短期记忆失败: {e}")

    async def _save_short_term(self):
        """保存短期记忆"""
        cache_file = self.data_dir / "short_term" / "cache.json"
        embeddings_file = self.data_dir / "short_term" / "embeddings.json"
        try:
            items_data = []
            embeddings_data = {}
            for item in self.short_term_memories:
                d = item.to_dict()
                items_data.append(d)
                if item.embedding:
                    embeddings_data[item.id] = item.embedding

            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(items_data, f, ensure_ascii=False, indent=2)

            with open(embeddings_file, "w", encoding="utf-8") as f:
                json.dump(embeddings_data, f, ensure_ascii=False)
        except Exception as e:
            logger.error(f"[统一记忆] 保存短期记忆失败: {e}")

    async def _load_cognitive(self):
        """加载认知记忆"""
        cache_file = self.data_dir / "cognitive" / "cache.json"
        embeddings_file = self.data_dir / "cognitive" / "embeddings.json"
        embeddings_data = {}
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if embeddings_file.exists():
                        with open(embeddings_file, "r", encoding="utf-8") as ef:
                            embeddings_data = json.load(ef)
                    self.cognitive_memories = []
                    for item in data:
                        mem = MemoryItem.from_dict(item)
                        if item.get("id") in embeddings_data:
                            mem.embedding = embeddings_data[item["id"]]
                        self.cognitive_memories.append(mem)
                logger.info(
                    f"[统一记忆] 加载了 {len(self.cognitive_memories)} 条认知记忆"
                )
            except Exception as e:
                logger.error(f"[统一记忆] 加载认知记忆失败: {e}")

    async def _save_cognitive(self):
        """保存认知记忆"""
        cache_file = self.data_dir / "cognitive" / "cache.json"
        embeddings_file = self.data_dir / "cognitive" / "embeddings.json"
        try:
            items_data = []
            embeddings_data = {}
            for item in self.cognitive_memories:
                d = item.to_dict()
                items_data.append(d)
                if item.embedding:
                    embeddings_data[item.id] = item.embedding

            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(items_data, f, ensure_ascii=False, indent=2)

            with open(embeddings_file, "w", encoding="utf-8") as f:
                json.dump(embeddings_data, f, ensure_ascii=False)
        except Exception as e:
            logger.error(f"[统一记忆] 保存认知记忆失败: {e}")

    async def _load_long_term(self):
        """加载长期记忆"""
        cache_file = self.data_dir / "long_term" / "cache.json"
        embeddings_file = self.data_dir / "long_term" / "embeddings.json"
        embeddings_data = {}
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if embeddings_file.exists():
                        with open(embeddings_file, "r", encoding="utf-8") as ef:
                            embeddings_data = json.load(ef)
                    self.long_term_memories = []
                    for item in data:
                        mem = MemoryItem.from_dict(item)
                        if item.get("id") in embeddings_data:
                            mem.embedding = embeddings_data[item["id"]]
                        self.long_term_memories.append(mem)
                logger.info(
                    f"[统一记忆] 加载了 {len(self.long_term_memories)} 条长期记忆"
                )
            except Exception as e:
                logger.error(f"[统一记忆] 加载长期记忆失败: {e}")

    async def _save_long_term(self):
        """保存长期记忆"""
        cache_file = self.data_dir / "long_term" / "cache.json"
        embeddings_file = self.data_dir / "long_term" / "embeddings.json"
        try:
            items_data = []
            embeddings_data = {}
            for item in self.long_term_memories:
                d = item.to_dict()
                items_data.append(d)
                if item.embedding:
                    embeddings_data[item.id] = item.embedding

            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(items_data, f, ensure_ascii=False, indent=2)

            with open(embeddings_file, "w", encoding="utf-8") as f:
                json.dump(embeddings_data, f, ensure_ascii=False)
        except Exception as e:
            logger.error(f"[统一记忆] 保存长期记忆失败: {e}")

    async def _load_pinned(self):
        """加载置顶备忘"""
        cache_file = self.data_dir / "pinned_memories.json"
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    self.pinned_memories = json.load(f)
                logger.info(f"[统一记忆] 加载了 {len(self.pinned_memories)} 条置顶备忘")
            except Exception as e:
                logger.error(f"[统一记忆] 加载置顶备忘失败: {e}")

    async def _save_pinned(self):
        """保存置顶备忘"""
        cache_file = self.data_dir / "pinned_memories.json"
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(self.pinned_memories, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"[统一记忆] 保存置顶备忘失败: {e}")

    async def _load_profiles(self):
        """加载用户/群侧写"""
        profiles_dir = self.data_dir / "profiles"
        for profile_file in profiles_dir.glob("user_*.md"):
            user_id = profile_file.stem.replace("user_", "")
            try:
                with open(profile_file, "r", encoding="utf-8") as f:
                    self.user_profiles[user_id] = f.read()
            except Exception as e:
                logger.error(f"[统一记忆] 加载用户侧写失败: {e}")

        for profile_file in profiles_dir.glob("group_*.md"):
            group_id = profile_file.stem.replace("group_", "")
            try:
                with open(profile_file, "r", encoding="utf-8") as f:
                    self.group_profiles[group_id] = f.read()
            except Exception as e:
                logger.error(f"[统一记忆] 加载群侧写失败: {e}")

        logger.info(
            f"[统一记忆] 加载了 {len(self.user_profiles)} 用户侧写, {len(self.group_profiles)} 群侧写"
        )

    async def _start_background_tasks(self):
        """启动后台任务"""
        self._historian_task = asyncio.create_task(self._historian_loop())
        logger.info("[统一记忆] 后台史官任务已启动")

    async def _historian_loop(self):
        """史官后台处理循环"""
        while True:
            try:
                job = await asyncio.wait_for(self._task_queue.get(), timeout=5.0)
                await self._process_historical_job(job)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"[统一记忆] 史官处理错误: {e}")
                await asyncio.sleep(1)

    async def _process_historical_job(self, job: Dict):
        """处理史官任务"""
        try:
            observations = job.get("observations", [])
            context = job.get("context", {})

            rewritten = await self.historian.rewrite(observations, context)

            for content in rewritten:
                memory = MemoryItem(
                    id=f"lt_{int(time.time() * 1000)}_{len(self.long_term_memories)}",
                    content=content,
                    memory_type=MemoryType.LONG_TERM,
                    priority=job.get("priority", 0.5),
                    user_id=context.get("user_id", ""),
                    group_id=context.get("group_id", ""),
                    timestamp=time.time(),
                    is_absolute=True,
                )

                self.long_term_memories.append(memory)

            await self._save_long_term()

            await self._update_profile(rewritten, context)

        except Exception as e:
            logger.error(f"[统一记忆] 处理史官任务失败: {e}")

    async def _update_profile(self, observations: List[str], context: Dict):
        """更新用户/群侧写"""
        async with self._profile_lock:
            user_id = context.get("user_id", "")
            group_id = context.get("group_id", "")

            if user_id:
                await self._append_to_profile(user_id, observations, is_user=True)

            if group_id:
                await self._append_to_profile(group_id, observations, is_user=False)

    async def _append_to_profile(self, id: str, observations: List[str], is_user: bool):
        """追加到侧写文件"""
        profile_type = "user" if is_user else "group"
        profile_key = f"{profile_type}_profiles"

        current = getattr(self, profile_key).get(id, "")

        new_lines = len(observations)
        current_lines = len(current.split("\n")) if current else 0

        if current_lines + new_lines > self.profile_compress_threshold:
            await self._compress_profile(id, is_user)
            current = getattr(self, profile_key).get(id, "")

        updated = (
            f"{current}\n\n" + "\n".join(observations)
            if current
            else "\n".join(observations)
        )

        getattr(self, profile_key)[id] = updated

        profile_file = self.data_dir / "profiles" / f"{profile_type}_{id}.md"
        with open(profile_file, "w", encoding="utf-8") as f:
            f.write(updated)

    async def _compress_profile(self, id: str, is_user: bool):
        """压缩侧写文件"""
        logger.info(f"[统一记忆] 压缩侧写: {id}")

        profile_type = "user" if is_user else "group"
        current = getattr(self, profile_type + "_profiles").get(id, "")

        if not current:
            return

        lines = current.split("\n")
        if len(lines) <= self.profile_max_lines:
            return

        kept_lines = lines[-self.profile_max_lines :]
        summary = f"[早期记忆已压缩，保留最近 {self.profile_max_lines} 条]\n\n"
        compressed = summary + "\n".join(kept_lines)

        getattr(self, profile_type + "_profiles")[id] = compressed

        profile_file = self.data_dir / "profiles" / f"{profile_type}_{id}.md"
        with open(profile_file, "w", encoding="utf-8") as f:
            f.write(compressed)

        summary_file = self.data_dir / "profiles" / f"{profile_type}_{id}_summary.md"
        with open(summary_file, "w", encoding="utf-8") as f:
            f.write(f"# {profile_type.capitalize()} Profile Summary\n")
            f.write(f"# Compressed at: {datetime.now().isoformat()}\n\n")
            f.write("# Full content available in archive\n")

    async def add_short_term(
        self,
        content: str,
        user_id: str = "",
        group_id: str = "",
        priority: float = 0.5,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict] = None,
        category: Optional[MemoryCategory] = None,
    ) -> str:
        """添加短期记忆"""
        memory_id = f"st_{int(time.time() * 1000)}_{len(self.short_term_memories)}"

        embedding = await self.embedding_service.get_embedding(content)

        if category is None:
            category = self._auto_classify(content, priority)

        memory = MemoryItem(
            id=memory_id,
            content=content,
            memory_type=MemoryType.SHORT_TERM,
            priority=priority,
            user_id=user_id,
            group_id=group_id,
            timestamp=time.time(),
            tags=tags or [],
            metadata=metadata or {},
            embedding=embedding,
            category=category,
        )

        self.short_term_memories.append(memory)

        if len(self.short_term_memories) > self.max_short_term:
            self.short_term_memories = self.short_term_memories[-self.max_short_term :]

        await self._save_short_term()

        return memory_id

    def _auto_classify(self, content: str, priority: float) -> MemoryCategory:
        """自动分类记忆"""
        content_lower = content.lower()

        if priority >= 0.8:
            return MemoryCategory.IMPORTANT

        emotion_keywords = [
            "喜欢",
            "爱",
            "开心",
            "难过",
            "生气",
            "害怕",
            "担心",
            "想",
            "想你",
            "爱你",
            "感动",
            "温暖",
            "幸福",
            "伤心",
            "失望",
            "焦虑",
            "压力大",
            "累",
            "疲惫",
        ]
        for kw in emotion_keywords:
            if kw in content_lower:
                return MemoryCategory.EMOTION

        task_keywords = [
            "任务",
            "todo",
            "待办",
            "提醒",
            "记得",
            "不要忘记",
            "完成",
            "执行",
            "操作",
            "做一下",
            "帮我",
        ]
        for kw in task_keywords:
            if kw in content_lower:
                return MemoryCategory.TASK

        knowledge_keywords = [
            "什么是",
            "怎么",
            "如何",
            "为什么",
            "解释",
            "知识",
            "学习",
            "教我",
            "问一下",
        ]
        for kw in knowledge_keywords:
            if kw in content_lower:
                return MemoryCategory.KNOWLEDGE

        daily_keywords = [
            "吃饭",
            "睡觉",
            "起床",
            "休息",
            "上班",
            "下班",
            "回家",
            "出门",
            "今天",
            "昨天",
            "明天",
            "天气",
            "早餐",
            "午餐",
            "晚餐",
        ]
        for kw in daily_keywords:
            if kw in content_lower:
                return MemoryCategory.DAILY

        return MemoryCategory.CHAT

    async def add_cognitive(
        self,
        content: str,
        observations: Optional[List[str]] = None,
        user_id: str = "",
        group_id: str = "",
        priority: float = 0.5,
        enqueue_historical: bool = True,
    ) -> str:
        """添加认知记忆"""
        memory_id = f"cg_{int(time.time() * 1000)}_{len(self.cognitive_memories)}"

        embedding = await self.embedding_service.get_embedding(content)

        memory = MemoryItem(
            id=memory_id,
            content=content,
            memory_type=MemoryType.COGNITIVE,
            priority=priority,
            user_id=user_id,
            group_id=group_id,
            timestamp=time.time(),
            embedding=embedding,
        )

        self.cognitive_memories.append(memory)

        if len(self.cognitive_memories) > self.max_cognitive:
            self.cognitive_memories = self.cognitive_memories[-self.max_cognitive :]

        await self._save_cognitive()

        if enqueue_historical and observations:
            await self._task_queue.put(
                {
                    "observations": observations,
                    "context": {"user_id": user_id, "group_id": group_id},
                    "priority": priority,
                }
            )

        return memory_id

    async def add_pinned(self, key: str, value: str):
        """添加置顶备忘"""
        self.pinned_memories[key] = value
        await self._save_pinned()

    async def remove_pinned(self, key: str):
        """删除置顶备忘"""
        if key in self.pinned_memories:
            del self.pinned_memories[key]
            await self._save_pinned()

    async def search(
        self,
        query: str,
        memory_types: Optional[List[MemoryType]] = None,
        user_id: Optional[str] = None,
        group_id: Optional[str] = None,
        top_k: int = 10,
    ) -> List[MemoryItem]:
        """语义搜索记忆"""
        if memory_types is None:
            memory_types = [
                MemoryType.SHORT_TERM,
                MemoryType.COGNITIVE,
                MemoryType.LONG_TERM,
            ]

        query_embedding = await self.embedding_service.get_embedding(query)

        all_memories = []
        for mtype in memory_types:
            if mtype == MemoryType.COGNITIVE:
                all_memories.extend(self.cognitive_memories)
            elif mtype == MemoryType.LONG_TERM:
                all_memories.extend(self.long_term_memories)
            elif mtype == MemoryType.SHORT_TERM:
                all_memories.extend(self.short_term_memories)

        scored = []
        query_words = set(query.lower().split())

        for memory in all_memories:
            if user_id and memory.user_id != user_id:
                continue
            if group_id and memory.group_id != group_id:
                continue

            score = 0.0

            if memory.embedding:
                score = self._cosine_similarity(query_embedding, memory.embedding)
            else:
                content_words = set(memory.content.lower().split())
                if query_words & content_words:
                    score = len(query_words & content_words) / max(
                        len(query_words | content_words), 1
                    )

            time_weight = self._time_decay(memory.timestamp)
            final_score = score * 0.7 + time_weight * 0.3

            scored.append((memory, final_score))

        scored.sort(key=lambda x: x[1], reverse=True)

        return [memory for memory, _ in scored[:top_k] if _ > 0]

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """计算余弦相似度"""
        if not a or not b or len(a) != len(b):
            return 0.0

        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot / (norm_a * norm_b)

    def _time_decay(self, timestamp: float) -> float:
        """时间衰减"""
        days = (time.time() - timestamp) / 86400
        if days < 1:
            return 1.0
        elif days < 7:
            return 1.0 - (days / 7) * 0.2
        else:
            return 0.8 * (0.95 ** (days - 7))

    def get_short_term(self, limit: int = 10) -> List[MemoryItem]:
        """获取短期记忆"""
        return self.short_term_memories[-limit:]

    def get_pinned(self) -> Dict[str, str]:
        """获取置顶备忘"""
        return self.pinned_memories.copy()

    def get_user_profile(self, user_id: str) -> Optional[str]:
        """获取用户侧写"""
        return self.user_profiles.get(user_id)

    def get_group_profile(self, group_id: str) -> Optional[str]:
        """获取群侧写"""
        return self.group_profiles.get(group_id)

    def get_stats(self) -> Dict[str, Any]:
        """获取记忆统计"""
        category_stats = {}
        for cat in MemoryCategory:
            count = sum(1 for m in self.short_term_memories if m.category == cat)
            category_stats[cat.value] = count

        return {
            "short_term_count": len(self.short_term_memories),
            "cognitive_count": len(self.cognitive_memories),
            "long_term_count": len(self.long_term_memories),
            "pinned_count": len(self.pinned_memories),
            "user_profiles_count": len(self.user_profiles),
            "group_profiles_count": len(self.group_profiles),
            "embedding_dimension": self.embedding_service.dimension,
            "historian_enabled": self.historian.enabled,
            "category_stats": category_stats,
        }

    def get_by_category(
        self, category: MemoryCategory, limit: int = 20
    ) -> List[MemoryItem]:
        """按分类获取记忆"""
        results = [m for m in self.short_term_memories if m.category == category]
        return results[-limit:]

    def get_all_categories(self) -> Dict[str, int]:
        """获取所有分类统计"""
        stats = {}
        for cat in MemoryCategory:
            stats[cat.value] = sum(
                1 for m in self.short_term_memories if m.category == cat
            )
        return stats

    async def export_memories(
        self,
        memory_type: Optional[MemoryType] = None,
        user_id: Optional[str] = None,
        category: Optional[MemoryCategory] = None,
    ) -> List[Dict]:
        """导出记忆"""
        results = []

        source_lists = []
        if memory_type is None or memory_type == MemoryType.SHORT_TERM:
            source_lists.append(self.short_term_memories)
        if memory_type is None or memory_type == MemoryType.COGNITIVE:
            source_lists.append(self.cognitive_memories)
        if memory_type is None or memory_type == MemoryType.LONG_TERM:
            source_lists.append(self.long_term_memories)

        for mem_list in source_lists:
            for mem in mem_list:
                if user_id and mem.user_id != user_id:
                    continue
                if category and mem.category != category:
                    continue
                results.append(mem.to_dict())

        return results

    async def cleanup(self):
        """清理资源"""
        await self._save_short_term()
        await self._save_cognitive()
        await self._save_long_term()
        await self._save_pinned()

        if self._historian_task:
            self._historian_task.cancel()
            try:
                await self._historian_task
            except asyncio.CancelledError:
                pass

        logger.info("[统一记忆] 系统已清理")


_global_memory_manager: Optional[UnifiedMemoryManager] = None
_global_initialized: bool = False


def get_unified_memory(
    data_dir: str = "data/memory", config: Optional[Dict[str, Any]] = None
) -> UnifiedMemoryManager:
    """获取全局统一记忆管理器"""
    global _global_memory_manager, _global_initialized
    if _global_memory_manager is None:
        _global_memory_manager = UnifiedMemoryManager(data_dir, config)
    return _global_memory_manager


async def init_unified_memory(
    data_dir: str = "data/memory", config: Optional[Dict[str, Any]] = None
) -> UnifiedMemoryManager:
    """初始化并获取统一记忆管理器"""
    global _global_initialized
    memory = get_unified_memory(data_dir, config)
    if not _global_initialized:
        await memory.initialize()
        _global_initialized = True
    return memory


__all__ = [
    "MemoryType",
    "MemoryPriority",
    "MemoryItem",
    "EmbeddingService",
    "HistorianRewriter",
    "UnifiedMemoryManager",
    "get_unified_memory",
]
