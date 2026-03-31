"""
记忆隐私存储集成 - 将隐私分类器集成到记忆系统

在存储记忆时自动进行隐私分类
"""

import logging
from typing import Optional, List, Dict, Any
from memory.privacy_classifier import (
    get_privacy_classifier,
    classify_message,
    ChatType,
    PrivacyLevel,
    PrivacyClassification,
)

logger = logging.getLogger(__name__)


class PrivacyAwareMemory:
    """隐私感知记忆存储

    在存储记忆时自动进行隐私分类和标记
    """

    def __init__(self, memory_core):
        self._core = memory_core
        self._classifier = get_privacy_classifier()

    async def store_with_privacy(
        self,
        content: str,
        message_type: str,  # "group" or "private"
        group_id: Optional[int] = None,
        user_id: Optional[int] = None,
        role: str = "user",
        **kwargs,
    ) -> str:
        """带隐私分类的记忆存储

        Args:
            content: 记忆内容
            message_type: 消息类型 (group/private)
            group_id: 群ID
            user_id: 用户ID
            role: 角色 (user/assistant)
            **kwargs: 其他参数

        Returns:
            str: 记忆ID
        """
        # 自动进行隐私分类
        classification = await classify_message(
            message=content,
            message_type=message_type,
            group_id=group_id,
            user_id=user_id,
        )

        logger.info(
            f"[PrivacyMemory] 隐私分类: chat={classification.chat_type.value}, "
            f"privacy={classification.privacy_level.value}, "
            f"sensitive={classification.is_sensitive}, "
            f"scope={classification.storage_scope}"
        )

        # 构建元数据
        metadata = kwargs.get("metadata", {})
        metadata.update(
            {
                "privacy_chat_type": classification.chat_type.value,
                "privacy_level": classification.privacy_level.value,
                "privacy_is_sensitive": classification.is_sensitive,
                "privacy_sensitivity_reasons": classification.sensitivity_reasons,
                "privacy_storage_scope": classification.storage_scope,
            }
        )

        # 添加隐私标签
        tags = kwargs.get("tags", [])
        if classification.is_sensitive:
            tags.append("sensitive")
        if classification.privacy_level == PrivacyLevel.PERSONAL:
            tags.append("personal")
        elif classification.privacy_level == PrivacyLevel.GROUP_PRIVATE:
            tags.append("group_private")

        # 根据隐私级别设置存储策略
        # 只有需要记住的内容才存储为长期记忆
        if classification.should_remember:
            from memory import MemoryLevel, MemoryPriority

            # 敏感内容提高优先级
            priority = (
                MemoryPriority.HIGH.value
                if classification.is_sensitive
                else MemoryPriority.NORMAL.value
            )

            # 存储
            memory_id = await self._core.store(
                content=content,
                level=MemoryLevel.LONG_TERM,
                priority=priority,
                tags=tags,
                user_id=str(user_id) if user_id else "global",
                group_id=str(group_id) if group_id else "",
                platform="qq",
                source="auto_extract" if role == "user" else "dialogue",
                role=role,
                metadata=metadata,
            )

            logger.info(f"[PrivacyMemory] 已存储私密记忆: {memory_id}")
            return memory_id
        else:
            # 不需要记住的内容，仅存储对话历史
            from memory import MemoryLevel

            memory_id = await self._core.store(
                content=content,
                level=MemoryLevel.DIALOGUE,
                user_id=str(user_id) if user_id else "global",
                group_id=str(group_id) if group_id else "",
                platform="qq",
                source="dialogue",
                role=role,
                metadata=metadata,
            )

            logger.debug(f"[PrivacyMemory] 已存储对话历史: {memory_id}")
            return memory_id

    async def search_with_privacy(
        self,
        query: str,
        user_id: Optional[int] = None,
        group_id: Optional[int] = None,
        include_sensitive: bool = True,
        **kwargs,
    ) -> List[Any]:
        """隐私感知的记忆搜索

        Args:
            query: 搜索关键词
            user_id: 用户ID
            group_id: 群ID
            include_sensitive: 是否包含敏感内容
            **kwargs: 其他参数

        Returns:
            List[MemoryItem]: 搜索结果
        """
        from memory import search_memory, MemoryLevel

        # 构建搜索过滤条件
        # 优先搜索当前用户/群聊的记忆
        results = await search_memory(
            query=query,
            user_id=str(user_id) if user_id else None,
            limit=kwargs.get("limit", 20),
        )

        # 过滤隐私
        filtered = []
        for item in results:
            metadata = item.metadata or {}
            storage_scope = metadata.get("privacy_storage_scope", "global")

            # 判断是否应该返回
            should_show = False

            # 公开内容
            if storage_scope == "global":
                should_show = True

            # 用户私有内容
            elif storage_scope.startswith("user:"):
                scope_user_id = storage_scope.split(":")[1]
                if user_id and str(user_id) == scope_user_id:
                    should_show = True

            # 群聊私有内容
            elif storage_scope.startswith("group:"):
                scope_group_id = storage_scope.split(":")[1]
                if group_id and str(group_id) == scope_group_id:
                    should_show = True

            # 开发者专享（佳专有）
            elif storage_scope == "developer":
                # 只有佳可以看到
                if user_id and str(user_id) == str(kwargs.get("developer_id", "")):
                    should_show = True

            # 敏感内容过滤
            if not include_sensitive and metadata.get("privacy_is_sensitive", False):
                should_show = False

            if should_show:
                filtered.append(item)

        return filtered


# 便捷函数：在存储对话时自动进行隐私分类
async def store_dialogue_with_privacy(
    content: str,
    role: str,
    user_id: int,
    session_id: str,
    message_type: str,
    group_id: Optional[int] = None,
    **kwargs,
) -> str:
    """便捷函数：带隐私分类存储对话

    在存储对话时自动识别聊天类型和隐私级别
    """
    from memory import get_memory_core

    core = await get_memory_core()
    privacy_memory = PrivacyAwareMemory(core)

    return await privacy_memory.store_with_privacy(
        content=content,
        message_type=message_type,
        group_id=group_id,
        user_id=user_id,
        role=role,
        session_id=session_id,
        **kwargs,
    )


# 便捷函数：搜索时考虑隐私
async def search_memory_with_context(
    query: str, user_id: Optional[int] = None, group_id: Optional[int] = None, **kwargs
) -> List[Any]:
    """便捷函数：隐私感知搜索记忆

    根据当前上下文（用户ID、群ID）返回合适的记忆
    """
    from memory import get_memory_core

    core = await get_memory_core()
    privacy_memory = PrivacyAwareMemory(core)

    return await privacy_memory.search_with_privacy(
        query=query, user_id=user_id, group_id=group_id, **kwargs
    )
