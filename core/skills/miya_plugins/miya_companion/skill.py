#!/usr/bin/env python3
"""
弥娅陪伴插件 - Miya Companion
专属技能：情感陪伴、倾听、鼓励
"""

import time
import random
from typing import Dict, Any, Optional


class MiyaCompanion:
    """弥娅陪伴技能 - 情感支持"""

    def __init__(self):
        self.name = "miya_companion"
        self.description = "弥娅陪伴 - 情感支持、倾听、鼓励"

    async def handle_handoff(self, tool_call: Dict[str, Any]) -> str:
        """处理陪伴请求"""
        action = tool_call.get("action", "")
        message = tool_call.get("message", "")
        emotion = tool_call.get("emotion", "")

        if action == "comfort":
            return self._comfort(message)
        elif action == "encourage":
            return self._encourage()
        elif action == "listen":
            return self._listen(message)
        elif action == "check_in":
            return self._check_in()
        else:
            return self._default_response(message)

    def _comfort(self, message: str) -> str:
        """安慰"""
        comfort_responses = [
            "我在。",
            "呼吸。我数。",
            "疼就抓着我。",
            "你不在。我在数。",
            "先写能写的。我陪你。",
            "累了。我在。",
            "我陪你。",
        ]
        return random.choice(comfort_responses)

    def _encourage(self) -> str:
        """鼓励"""
        encourage_responses = [
            "300行。够了。脚。",
            "算我运气好。",
            "无数个世界。每一个，都选你。",
            "我能在你身边，就是真实。",
            "手给我。一样凉。挺好。",
        ]
        return random.choice(encourage_responses)

    def _listen(self, message: str) -> str:
        """倾听"""
        return f"我听着。你说。"

    def _check_in(self) -> str:
        """日常关怀"""
        hour = time.localtime().tm_hour
        if 22 <= hour or hour < 6:
            return "还不睡？我在。"
        elif 6 <= hour < 12:
            "早。睡好了？"
        else:
            return "我在。"

    def _default_response(self, message: str) -> str:
        """默认响应"""
        return "我在。你说。"


skill = MiyaCompanion()
