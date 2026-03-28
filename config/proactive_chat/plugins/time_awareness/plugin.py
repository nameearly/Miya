# 时间感知插件
# Time Awareness Plugin

import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
from ..base_plugin import BasePlugin


class Plugin(BasePlugin):
    def __init__(self, name: str = "time_awareness", config: Dict = None):
        super().__init__(name, config)

        # 时间段配置
        self.time_slots = self.config.get("time_slots", {})

        # 时间关键词
        self.greeting_keywords = {
            "morning": ["早", "早上好", "早安"],
            "afternoon": ["午", "午安", "下午好"],
            "evening": ["晚", "晚上好", "傍晚"],
            "night": ["晚安", "夜深了", "该睡了"],
        }

    async def collect_context(self, user_id: int, context: Dict = None) -> Dict:
        now = datetime.now()
        hour = now.hour

        # 确定当前时间段
        time_slot = self._get_time_slot(hour)

        return {
            "hour": hour,
            "minute": now.minute,
            "weekday": now.weekday(),
            "time_slot": time_slot,
            "timestamp": now.isoformat(),
        }

    def _get_time_slot(self, hour: int) -> str:
        if 6 <= hour < 12:
            return "morning"
        elif 12 <= hour < 17:
            return "afternoon"
        elif 17 <= hour < 21:
            return "evening"
        else:
            return "night"

    async def generate(self, context_data: Dict) -> str:
        time_context = context_data.get(self.name, {})
        time_slot = time_context.get("time_slot", "morning")

        # 获取时间段配置
        slot_config = self.time_slots.get(time_slot, {})

        # 生成消息
        if time_slot == "morning":
            return "早上好。今天感觉怎么样。"
        elif time_slot == "afternoon":
            return "午安。休息一下。"
        elif time_slot == "evening":
            return "晚上好。今天辛苦了。"
        elif time_slot == "night":
            return "晚安。早点休息。"
        else:
            return "在。"
