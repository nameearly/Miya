# 上下文感知插件
# Context Awareness Plugin

import logging
import asyncio
import re
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from ..base_plugin import BasePlugin


class Plugin(BasePlugin):
    def __init__(self, name: str = "context_awareness", config: Dict = None):
        super().__init__(name, config)

        # 上下文类型配置
        self.context_types = self.config.get("context_types", {})

        # 跟进参数
        self.follow_up_params = self.config.get("follow_up_params", {})

        # 存储用户上下文
        self.user_contexts = {}

    async def collect_context(self, user_id: int, context: Dict = None) -> Dict:
        # 分析用户消息中的上下文模式
        user_message = context.get("message", "") if context else ""

        detected_contexts = []
        for context_type, type_config in self.context_types.items():
            patterns = type_config.get("patterns", [])
            for pattern_config in patterns:
                regex = pattern_config.get("regex", "")
                follow_ups = pattern_config.get("follow_ups", [])

                if re.search(regex, user_message):
                    detected_contexts.append(
                        {
                            "type": context_type,
                            "name": type_config.get("name", context_type),
                            "follow_ups": follow_ups,
                            "message": user_message,
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

        # 更新用户上下文
        if user_id not in self.user_contexts:
            self.user_contexts[user_id] = []

        for context_item in detected_contexts:
            self.user_contexts[user_id].append(context_item)

        # 清理旧上下文
        self._cleanup_old_contexts(user_id)

        # 获取待跟进的上下文
        pending_contexts = self._get_pending_contexts(user_id)

        return {
            "detected_contexts": detected_contexts,
            "pending_contexts": pending_contexts,
            "has_pending": len(pending_contexts) > 0,
        }

    def _cleanup_old_contexts(self, user_id: int):
        """清理旧上下文"""
        if user_id not in self.user_contexts:
            return

        max_delay_hours = self.follow_up_params.get("max_delay_hours", 24)
        cutoff_time = datetime.now() - timedelta(hours=max_delay_hours)

        self.user_contexts[user_id] = [
            context
            for context in self.user_contexts[user_id]
            if datetime.fromisoformat(context["timestamp"]) > cutoff_time
        ]

    def _get_pending_contexts(self, user_id: int) -> List[Dict]:
        """获取待跟进的上下文"""
        if user_id not in self.user_contexts:
            return []

        min_delay_minutes = self.follow_up_params.get("min_delay_minutes", 30)
        cutoff_time = datetime.now() - timedelta(minutes=min_delay_minutes)

        pending = []
        for context in self.user_contexts[user_id]:
            context_time = datetime.fromisoformat(context["timestamp"])
            if context_time < cutoff_time:
                pending.append(context)

        return pending

    async def generate(self, context_data: Dict) -> str:
        context_plugin = context_data.get(self.name, {})

        if not context_plugin.get("has_pending", False):
            return ""

        pending_contexts = context_plugin.get("pending_contexts", [])
        if not pending_contexts:
            return ""

        # 获取第一个待跟进的上下文
        pending_context = pending_contexts[0]
        follow_ups = pending_context.get("follow_ups", [])

        if follow_ups:
            import random

            return random.choice(follow_ups)

        return ""
