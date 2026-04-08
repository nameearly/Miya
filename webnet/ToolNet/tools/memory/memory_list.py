"""
列出记忆（统一接口层）

支持查询：
- 长期记忆（用户记忆 + 弥娅自记忆）
- 弥娅自记忆（承诺、观点、建议等）
- 按标签/角色/用户筛选

本工具优先使用新版 MiyaMemoryCore 记忆系统
"""

from typing import Dict, Any, List
import logging
from pathlib import Path
from webnet.ToolNet.base import BaseTool, ToolContext


logger = logging.getLogger(__name__)


def _load_self_memory_tags() -> List[str]:
    """从 text_config.json 加载弥娅自记忆标签"""
    try:
        config_path = (
            Path(__file__).parent.parent.parent.parent.parent
            / "config"
            / "text_config.json"
        )
        if config_path.exists():
            import json

            with open(config_path, "r", encoding="utf-8") as f:
                full_config = json.load(f)
            self_config = full_config.get("assistant_self", {})
            tags = self_config.get("self_memory_tags")
            if tags:
                return tags
    except Exception as e:
        logger.warning(f"[MemoryList] 加载自记忆标签配置失败: {e}")
    return []


class MemoryList(BaseTool):
    """MemoryList - 统一记忆接口层"""

    @property
    def config(self) -> Dict[str, Any]:
        return {
            "name": "memory_list",
            "description": "列出记忆，支持按标签、角色（user/assistant）、用户筛选。当用户说'查看记忆'、'列出记忆'、'显示所有记忆'、'记忆列表'、'你记得什么'、'我们都聊过什么'、'昨天聊了什么'、'你说过什么'、'你承诺过什么'等回忆类问题时必须调用此工具。重要：此工具返回的记忆结果包含完整的用户信息和弥娅自记忆，AI 必须仔细阅读工具返回的内容并基于这些信息回答用户问题。参数role='assistant'可专门查询弥娅自己说过的话（承诺、观点、建议等）。",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "返回的最大数量，默认15",
                        "default": 15,
                        "minimum": 1,
                        "maximum": 50,
                    },
                    "tag": {"type": "string", "description": "按标签筛选记忆"},
                    "role": {
                        "type": "string",
                        "description": "按角色筛选：'user'（用户说的）、'assistant'（弥娅说的）、不填则全部",
                        "enum": ["user", "assistant"],
                    },
                    "include_dialogue": {
                        "type": "boolean",
                        "description": "是否包含对话历史（dialogue层），默认false",
                        "default": False,
                    },
                },
                "required": [],
            },
        }

    async def execute(self, context: ToolContext, **kwargs) -> str:
        """执行工具 - 优先使用 MiyaMemoryCore"""
        args = kwargs
        limit = args.get("limit", 15)
        tag = args.get("tag")
        role_filter = args.get("role")
        include_dialogue = args.get("include_dialogue", False)
        user_id = str(context.user_id) if context.user_id else None

        # 从配置加载自记忆标签
        self_memory_tags = _load_self_memory_tags()

        # 优先级 1: 新版 MiyaMemoryCore（权威记忆源）
        try:
            from memory import get_memory_core, MemoryLevel, MemorySource

            core = await get_memory_core()

            if tag:
                # 按标签搜索
                results = await core.search_by_tag(tag, user_id=user_id, limit=limit)
            elif role_filter == "assistant":
                # 【星璇增强】专门查询弥娅自记忆
                all_results = await core.retrieve(
                    query="",
                    limit=limit * 3,
                )
                results = []
                for m in all_results:
                    level_val = (
                        m.level.value if hasattr(m.level, "value") else str(m.level)
                    )
                    source_val = (
                        m.source.value if hasattr(m.source, "value") else str(m.source)
                    )
                    meta = getattr(m, "metadata", {}) or {}
                    # 匹配：弥娅自记忆来源 或 配置中的自记忆标签 或 role=assistant的长期记忆
                    if (
                        source_val == "assistant_self"
                        or any(t in (m.tags or []) for t in self_memory_tags)
                        or (
                            getattr(m, "role", "") == "assistant"
                            and level_val in ("long_term", "semantic")
                        )
                    ):
                        results.append(m)
                    if len(results) >= limit:
                        break
            elif user_id and user_id != "global":
                # 按用户搜索
                results = await core.search_by_user(user_id, limit=limit)
            else:
                # 获取所有记忆
                results = await core.retrieve(
                    query="",
                    limit=limit * 3,
                )
                # 保留长期/语义/知识记忆，以及短期重要记忆
                filtered = []
                for m in results:
                    level_val = (
                        m.level.value if hasattr(m.level, "value") else str(m.level)
                    )
                    source_val = (
                        m.source.value if hasattr(m.source, "value") else str(m.source)
                    )
                    meta = getattr(m, "metadata", {}) or {}
                    # 保留：长期、语义、知识
                    if level_val in ("long_term", "semantic", "knowledge"):
                        filtered.append(m)
                    # 【修复】短期记忆：如果标记为重要/高优先级，也保留
                    elif level_val == "short_term":
                        priority = getattr(m, "priority", 0)
                        importance = meta.get("importance", "")
                        if (
                            priority >= 0.7  # 高优先级
                            or importance == "high"
                            or source_val == "assistant_self"
                            or source_val == "manual"
                            or meta.get("pinned", False)
                        ):
                            filtered.append(m)
                    elif level_val == "dialogue" and include_dialogue:
                        if role_filter is None or getattr(m, "role", "") == role_filter:
                            filtered.append(m)
                results = filtered[:limit]

            if not results:
                if role_filter == "assistant":
                    return "[INFO] 弥娅暂无自记忆记录。弥娅的承诺、观点、建议等会在对话中自动提取并存储。"
                return "[INFO] No memories found"

            result_lines = [
                f"[INFO] Memory list (total {len(results)} memories)",
                "-" * 40,
            ]
            for i, mem in enumerate(results, 1):
                content_preview = (
                    mem.content[:120] + "..." if len(mem.content) > 120 else mem.content
                )
                tags_str = ", ".join(mem.tags) if mem.tags else "none"
                level_label = {
                    "long_term": "long_term",
                    "short_term": "short_term",
                    "dialogue": "dialogue",
                    "semantic": "semantic",
                    "knowledge": "knowledge",
                }.get(
                    mem.level.value if hasattr(mem.level, "value") else str(mem.level),
                    mem.level.value if hasattr(mem.level, "value") else "unknown",
                )

                role_label = getattr(mem, "role", "")
                source_label = ""
                if hasattr(mem.source, "value"):
                    source_label = mem.source.value
                elif hasattr(mem.source, "__str__"):
                    source_label = str(mem.source)

                # 构建展示行
                line_parts = [f"{i}. [{level_label}]"]
                if role_label:
                    line_parts.append(f"[{role_label}]")
                if source_label == "assistant_self":
                    line_parts.append("[自记忆]")
                line_parts.append(content_preview)

                result_lines.append(" ".join(line_parts))
                result_lines.append(f"   tags: {tags_str}")
                result_lines.append(f"   user_id: {mem.user_id}")
                result_lines.append(
                    f"   created_at: {mem.created_at[:16] if mem.created_at else 'unknown'}"
                )
                if source_label:
                    result_lines.append(f"   source: {source_label}")
                result_lines.append("")

            return "\n".join(result_lines)

        except Exception as e:
            logger.error(f"[MemoryList] MiyaMemoryCore 查询失败: {e}", exc_info=True)

        # 优先级 2: Undefined 轻量记忆系统（回退）
        try:
            from memory.undefined_memory import get_undefined_memory_adapter

            adapter = get_undefined_memory_adapter()

            if tag:
                memories = await adapter.get_by_tag(tag, limit)
            else:
                memories = await adapter.get_all(limit)

            if not memories:
                return "[INFO] No memories found in Undefined lightweight memory system"

            result = f"[INFO] Memory list (Undefined lightweight memory system)\nTotal {len(memories)} memories\n\n"
            for i, mem in enumerate(memories, 1):
                if isinstance(mem, dict):
                    content = mem.get("content", "")
                    tags = mem.get("tags", [])
                    mem_id = mem.get("id", mem.get("uuid", "unknown"))
                    created_at = mem.get("created_at", "未知时间")
                else:
                    content = getattr(mem, "fact", getattr(mem, "content", ""))
                    tags = getattr(mem, "tags", [])
                    mem_id = getattr(mem, "uuid", getattr(mem, "id", "unknown"))
                    created_at = getattr(mem, "created_at", "未知时间")

                content_preview = (
                    content[:100] + "..." if len(content) > 100 else content
                )
                tags_str = ", ".join(tags) if tags else "none"
                result += f"{i}. **{mem_id}**\n"
                result += f"   created_at: {created_at}\n"
                result += f"   content: {content_preview}\n"
                result += f"   tags: {tags_str}\n\n"

            return result
        except Exception as e:
            logger.error(f"[MemoryList] Undefined 记忆系统失败: {e}", exc_info=True)

        # 优先级 3: 认知记忆系统
        cognitive_memory = getattr(context, "cognitive_memory", None)
        if cognitive_memory:
            try:
                results = await cognitive_memory.search(
                    query=tag if tag else "", top_k=limit
                )

                if not results:
                    return "[INFO] No memories found in cognitive memory system"

                result = f"[INFO] Memory list (cognitive memory system)\nTotal {len(results)} memories\n\n"
                for i, mem in enumerate(results, 1):
                    content_preview = (
                        mem.get("content", "")[:100] + "..."
                        if len(mem.get("content", "")) > 100
                        else mem.get("content", "")
                    )
                    result += f"{i}. **{mem.get('id', 'unknown')}**\n"
                    result += f"   content: {content_preview}\n"
                    tags = mem.get("tags", [])
                    tag_str = ", ".join(tags) if tags else "none"
                    result += f"   tags: {tag_str}\n\n"

                return result
            except Exception as e:
                logger.error(f"[MemoryList] 认知记忆系统失败: {e}", exc_info=True)

        return "[INFO] Memory system not initialized, unable to list memories"
