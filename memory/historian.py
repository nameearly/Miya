"""
弥娅历史记录员 (Historian) v2.0

自动分析对话并提取需要记忆的内容：
- 只记忆重要事实，不记忆客套话
- 自动提取用户信息、习惯、承诺等
- 群聊中有价值的讨论主题提取
- 与 CognitiveEngine 配合实现智能记忆
"""

import json
import logging
import re
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set

from memory import get_memory_core, MemoryItem, MemorySource
from memory.cognitive_engine import (
    get_cognitive_engine,
    TOPIC_KEYWORDS,
    MEMORY_TRIGGERS,
)

logger = logging.getLogger(__name__)


def _load_historian_config() -> Dict[str, Any]:
    """从 text_config.json 加载 Historian 配置"""
    try:
        config_path = Path(__file__).parent.parent / "config" / "text_config.json"
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            return config.get("historian", {})
    except Exception as e:
        logger.debug(f"[Historian] 加载配置失败: {e}")
    return {}


def _parse_patterns(raw: List) -> List[Tuple[str, str]]:
    """将配置中的 [[pattern, label], ...] 转为 [(pattern, label), ...]"""
    return [(p[0], p[1]) for p in raw if isinstance(p, list) and len(p) >= 2]


def _parse_group_patterns(raw: Dict) -> Dict[str, List[Tuple[str, str]]]:
    """解析群聊讨论模式"""
    result = {}
    for category, patterns in raw.items():
        result[category] = _parse_patterns(patterns)
    return result


# 从配置加载（回退到内置默认值）
_config = _load_historian_config()

IGNORE_PATTERNS = _config.get(
    "ignore_patterns",
    [
        r"^[嗯哦啊哈嘿诶]{1,3}[。\.!?]*$",
        r"^[好是知道行可以]{1,2}[。\.!?]*$",
        r"^[干嘛怎么了啥事?]*$",
        r"^[哈哈哈?]+[。!]*$",
        r"^\[表情\]$",
        r"^[\(]?图片[照片]?[\)]?$",
        r"^[/@].*",
        r"^!{3,}$",
        r"^[~～]{3,}$",
    ],
)

IMPORTANT_PATTERNS = _parse_group_patterns(
    _config.get(
        "important_patterns",
        {
            "personal_info": [
                [r"我(今年|今年多大|多大了|几岁)", "个人年龄"],
                [r"我(身高|多高)", "个人身高"],
                [r"我(生日|哪天|什么日子)", "个人生日"],
                [r"我是(.+?)(学生|工作|上班)", "身份"],
                [r"我住在(.+?)(家|宿舍|学校)", "住址"],
            ],
            "preference": [
                [r"我喜欢(.+)", "喜欢"],
                [r"我讨厌(.+)", "讨厌"],
                [r"我最爱(.+)", "最爱"],
                [r"我不喜欢(.+)", "不喜欢"],
            ],
            "health": [
                [r"我有(.+?)病", "健康"],
                [r"我(.+?)不舒服", "健康"],
                [r"(.+?)先天性", "健康"],
                [r"身体(.+?)不好", "健康"],
            ],
            "commitment": [
                [r"答应你(.+)", "承诺"],
                [r"会记住(.+)", "承诺"],
                [r"下次(.+)", "承诺"],
            ],
        },
    )
)

GROUP_DISCUSSION_PATTERNS = _parse_group_patterns(
    _config.get(
        "group_discussion_patterns",
        {
            "knowledge": [
                [r"(三体|阶梯计划|云天明|二向箔|曲率|黑洞|光速飞船)", "科幻讨论"],
                [r"(群星|战锤|蜂巢|超级个体|进化方向)", "科幻哲学"],
                [r"(饕餮|深水王子|针眼画师|童话)", "三体童话"],
                [r"(计划的一部分|面壁者|执剑人)", "三体概念"],
            ],
            "opinion": [
                [r"(我认为|我觉得|我的看法|我的看法是)", "观点表达"],
                [r"(你怎么看|你怎么想|你的看法)", "征求意见"],
            ],
            "event": [
                [r"(今天|明天|昨天|下周|下周)(去|要|准备|打算)", "计划安排"],
                [r"(终于|总算|结束了|完成了)", "事件完成"],
            ],
        },
    )
)


class Historian:
    """历史记录员

    职责：
    - 分析对话内容
    - 提取需要记忆的重要信息
    - 群聊中有价值讨论的提取
    - 自动保存到记忆存储
    """

    def __init__(self):
        """初始化历史记录员"""
        self.memory_core = None
        self._memory_core_initialized = False
        self.cognitive_engine = get_cognitive_engine()
        # 近期已记忆的内容哈希，避免重复记忆
        self._recent_memory_hashes: Set[str] = set()
        self._max_recent_hashes = 100

    async def _ensure_memory_core_initialized(self):
        """确保内存核心已初始化"""
        if not self._memory_core_initialized:
            if self.memory_core is None:
                self.memory_core = await get_memory_core()
            await self.memory_core.initialize()
            self._memory_core_initialized = True

    def _content_hash(self, text: str) -> str:
        """生成内容哈希用于去重"""
        import hashlib

        # 只取前50个字符做哈希，忽略标点差异
        normalized = re.sub(r"[^\w\u4e00-\u9fff]", "", text[:50])
        return hashlib.md5(normalized.encode("utf-8")).hexdigest()[:12]

    def _is_duplicate(self, text: str) -> bool:
        """检查是否是重复内容"""
        h = self._content_hash(text)
        if h in self._recent_memory_hashes:
            return True
        self._recent_memory_hashes.add(h)
        # 限制哈希表大小
        if len(self._recent_memory_hashes) > self._max_recent_hashes:
            # 移除一半最旧的
            to_remove = list(self._recent_memory_hashes)[: self._max_recent_hashes // 2]
            for item in to_remove:
                self._recent_memory_hashes.discard(item)
        return False

    def _is_meaningful(self, text: str) -> bool:
        """判断内容是否有意义"""
        if not text or len(text.strip()) < 4:
            return False

        for pattern in IGNORE_PATTERNS:
            if re.match(pattern, text.strip()):
                return False

        return True

    def _extract_important_info(self, text: str) -> List[Tuple[str, str, List[str]]]:
        """提取重要信息

        Returns:
            [(内容, 类型, 标签), ...]
        """
        results = []

        for category, patterns in IMPORTANT_PATTERNS.items():
            for pattern, info_type in patterns:
                match = re.search(pattern, text)
                if match:
                    content = match.group(0)
                    if len(content) > 3:
                        # 确定标签
                        tags = [category]
                        # 添加相关话题标签
                        for topic, keywords in TOPIC_KEYWORDS.items():
                            if any(kw in text for kw in keywords):
                                tags.append(topic)

                        results.append((content, info_type, tags))

        return results

    def _extract_group_discussion(
        self, text: str
    ) -> Optional[Tuple[str, float, List[str]]]:
        """提取群聊中有价值的讨论内容

        Returns:
            (内容, 重要性, 标签) 或 None
        """
        for category, patterns in GROUP_DISCUSSION_PATTERNS.items():
            for pattern, info_type in patterns:
                if re.search(pattern, text):
                    # 群聊讨论默认较高重要性
                    importance = 0.7
                    tags = [category, info_type]
                    # 添加话题标签
                    for topic, keywords in TOPIC_KEYWORDS.items():
                        if any(kw in text for kw in keywords):
                            tags.append(topic)
                    return text[:150], importance, tags
        return None

    def _extract_fact_from_conversation(
        self, user_input: str, ai_response: str
    ) -> Optional[Tuple[str, float, List[str]]]:
        """从对话中提取需要记忆的事实

        Returns:
            (记忆内容, 重要性, 标签) 或 None
        """
        combined = user_input + " " + ai_response

        # 1. 提取重要信息
        important_infos = self._extract_important_info(user_input)
        if important_infos:
            content, info_type, tags = important_infos[0]
            importance = 0.8 if info_type in ["personal_info", "health"] else 0.6
            return content, importance, tags

        # 2. 检查群聊有价值讨论
        group_discussion = self._extract_group_discussion(user_input)
        if group_discussion:
            return group_discussion

        # 3. 检查触发词
        importance = 0.3
        tags = []

        for category, triggers in MEMORY_TRIGGERS.items():
            for trigger in triggers:
                if trigger in combined:
                    if category == "important_info":
                        importance = 0.9
                    elif category == "commitment":
                        importance = 0.8
                    elif category == "emotion_change":
                        importance = 0.7
                    elif category == "habit":
                        importance = 0.6
                    break

        # 添加话题标签
        for topic, keywords in TOPIC_KEYWORDS.items():
            if any(kw in user_input for kw in keywords):
                tags.append(topic)

        # 如果有关键词但没有提取到内容，使用用户输入
        if importance > 0.3 and len(user_input) > 5:
            return user_input[:100], importance, tags

        return None

    async def process_conversation(
        self,
        user_input: str,
        ai_response: str,
        user_id: str = "default",
        group_id: str = "",
        message_type: str = "",
    ) -> bool:
        """处理对话并自动记忆

        Args:
            user_input: 用户输入
            ai_response: AI回复
            user_id: 用户ID
            group_id: 群组ID
            message_type: 消息类型 (group/private)

        Returns:
            是否成功记忆
        """
        # 1. 检查是否有意义
        if not self._is_meaningful(user_input):
            return False

        # 2. 检查是否重复
        if self._is_duplicate(user_input):
            return False

        # 3. 提取需要记忆的内容
        memory_data = self._extract_fact_from_conversation(user_input, ai_response)

        if not memory_data:
            logger.debug("[Historian] 对话无重要内容，跳过记忆")
            return False

        content, importance, tags = memory_data

        # 群聊讨论提高重要性
        if message_type == "group" and len(user_input) > 20:
            importance = min(1.0, importance + 0.1)

        # 4. 保存到记忆存储
        try:
            # 确保内存核心已初始化
            await self._ensure_memory_core_initialized()

            memory_uuid = await self.memory_core.store(
                content=content,
                priority=importance,
                tags=tags,
                source=MemorySource.AUTO_EXTRACT,
                user_id=user_id,
                group_id=group_id,
            )

            if memory_uuid:
                logger.info(
                    f"[Historian] 已记忆: {content[:30]}... (importance={importance}, group={group_id})"
                )
                return True
        except Exception as e:
            logger.error(f"[Historian] 保存记忆失败: {e}")

        return False

    async def process_after_response(
        self,
        user_input: str,
        ai_response: str,
        user_id: str = "default",
        group_id: str = "",
        message_type: str = "",
    ) -> None:
        """在生成回复后调用，自动处理记忆

        Args:
            user_input: 用户输入
            ai_response: AI回复
            user_id: 用户ID
            group_id: 群组ID
            message_type: 消息类型 (group/private)
        """
        # 使用认知引擎判断是否需要记忆
        (
            should_remember,
            content,
            importance,
        ) = await self.cognitive_engine.should_remember(user_input, ai_response)

        if should_remember and content:
            # 检查重复
            if self._is_duplicate(content):
                return

            # 提取话题标签
            topics = self.cognitive_engine._extract_topics(user_input)

            # 群聊讨论添加额外标签
            if message_type == "group":
                group_discussion = self._extract_group_discussion(user_input)
                if group_discussion:
                    _, _, discussion_tags = group_discussion
                    topics.extend(discussion_tags)
                    importance = min(1.0, importance + 0.1)

            try:
                # 确保内存核心已初始化
                await self._ensure_memory_core_initialized()

                await self.memory_core.store(
                    content=content,
                    priority=importance,
                    tags=topics,
                    source=MemorySource.AUTO_EXTRACT,
                    user_id=user_id,
                    group_id=group_id,
                )
                logger.info(f"[Historian] 自动记住: {content[:30]}...")
            except Exception as e:
                logger.error(f"[Historian] 自动记忆失败: {e}")


# 单例实例
_historian: Optional[Historian] = None


def get_historian() -> Historian:
    """获取历史记录员单例实例"""
    global _historian
    if _historian is None:
        _historian = Historian()
    return _historian
