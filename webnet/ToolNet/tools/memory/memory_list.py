"""
列出所有手动长期记忆（统一接口层）

本工具优先使用新版 MiyaMemoryCore 记忆系统
"""

from typing import Dict, Any
import logging
from webnet.ToolNet.base import BaseTool, ToolContext


logger = logging.getLogger(__name__)


class MemoryList(BaseTool):
    """MemoryList - 统一记忆接口层"""

    @property
    def config(self) -> Dict[str, Any]:
        return {
            "name": "memory_list",
            "description": "列出所有手动长期记忆，支持按标签筛选和限制数量。当用户说'查看记忆'、'列出记忆'、'显示所有记忆'、'记忆列表'、'你记得什么'、'我们都聊过什么'、'昨天聊了什么'等回忆类问题时必须调用此工具。重要：此工具返回的记忆结果包含完整的用户信息(如生日、喜好等)，AI 必须仔细阅读工具返回的内容并基于这些信息回答用户问题。不要重复询问工具中已提供的信息。当工具返回'暂无记忆'时，直接告知用户目前没有相关的长期记忆记录。",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "返回的最大数量，默认10",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 50,
                    },
                    "tag": {"type": "string", "description": "按标签筛选记忆"},
                },
                "required": [],
            },
        }

    async def execute(self, args: Dict[str, Any], context: ToolContext) -> str:
        """执行工具 - 优先使用 MiyaMemoryCore"""
        limit = args.get("limit", 10)
        tag = args.get("tag")
        user_id = str(context.user_id) if context.user_id else None

        # 优先级 1: 新版 MiyaMemoryCore（权威记忆源）
        try:
            from memory import get_memory_core, MemoryLevel

            core = await get_memory_core()

            if tag:
                # 按标签搜索
                results = await core.search_by_tag(tag, user_id=user_id, limit=limit)
            elif user_id and user_id != "global":
                # 按用户搜索
                results = await core.search_by_user(user_id, limit=limit)
            else:
                # 获取所有记忆（包括短期锚点）
                results = await core.retrieve(
                    query="",
                    limit=limit,
                )
                # 保留长期/语义/知识记忆，以及带有 init_anchor 标记的短期记忆（核心锚点）
                filtered = []
                for m in results:
                    level_val = (
                        m.level.value if hasattr(m.level, "value") else str(m.level)
                    )
                    if level_val in ("long_term", "semantic", "knowledge"):
                        filtered.append(m)
                    elif level_val == "short_term":
                        # 检查是否是初始化锚点
                        meta = getattr(m, "metadata", {}) or {}
                        if (
                            meta.get("source") == "init_anchor"
                            or meta.get("importance") == "high"
                        ):
                            filtered.append(m)
                results = filtered[:limit]

            if not results:
                return f"📭 记忆中暂无记录"

            result_lines = [f"📚 记忆列表（共 {len(results)} 条）", "=" * 40]
            for i, mem in enumerate(results, 1):
                content_preview = (
                    mem.content[:120] + "..." if len(mem.content) > 120 else mem.content
                )
                tags_str = ", ".join(mem.tags) if mem.tags else "无"
                level_label = {
                    "long_term": "长期",
                    "short_term": "短期",
                    "dialogue": "对话",
                    "semantic": "语义",
                    "knowledge": "知识",
                }.get(
                    mem.level.value if hasattr(mem.level, "value") else str(mem.level),
                    mem.level.value if hasattr(mem.level, "value") else "?",
                )

                result_lines.append(f"{i}. [{level_label}] {content_preview}")
                result_lines.append(f"   标签: {tags_str}")
                result_lines.append(f"   用户: {mem.user_id}")
                result_lines.append(
                    f"   时间: {mem.created_at[:16] if mem.created_at else '未知'}"
                )
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
                return f"📭 Undefined轻量记忆中暂无记忆"

            result = f"📚 记忆列表（Undefined轻量记忆）\n共 {len(memories)} 条\n\n"
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
                tags_str = ", ".join(tags) if tags else "无"
                result += f"{i}. **{mem_id}**\n"
                result += f"   时间: {created_at}\n"
                result += f"   内容: {content_preview}\n"
                result += f"   标签: {tags_str}\n\n"

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
                    return f"📭 认知记忆系统中暂无记忆"

                result = f"📚 记忆列表（认知记忆系统）\n共 {len(results)} 条\n\n"
                for i, mem in enumerate(results, 1):
                    content_preview = (
                        mem.get("content", "")[:100] + "..."
                        if len(mem.get("content", "")) > 100
                        else mem.get("content", "")
                    )
                    result += f"{i}. **{mem.get('id', 'unknown')}**\n"
                    result += f"   内容: {content_preview}\n"
                    tags = mem.get("tags", [])
                    tag_str = ", ".join(tags) if tags else "无"
                    result += f"   标签: {tag_str}\n\n"

                return result
            except Exception as e:
                logger.error(f"[MemoryList] 认知记忆系统失败: {e}", exc_info=True)

        return "⚠️ 记忆系统未初始化，无法列出记忆"
