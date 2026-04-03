"""
弥娅前端意识系统（感知层）

职责：
- 实时时间感知（时刻、星期、时段）
- 地点感知（群聊/私聊、群名、用户角色）
- 活动感知（谛听监听数据注入）
- 用户状态感知（在线、活跃、历史交互）

设计目标：让弥娅像人一样知道“现在是什么时候、在哪里、谁在说话”
"""

import logging
import time
from datetime import datetime
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class TimeAwareness:
    """时间感知"""

    @staticmethod
    def get_current_time_context() -> Dict[str, str]:
        """获取当前时间上下文"""
        now = datetime.now()
        hour = now.hour

        # 时段判断
        if 5 <= hour < 9:
            period = "清晨"
            greeting = "早上好"
        elif 9 <= hour < 12:
            period = "上午"
            greeting = "上午好"
        elif 12 <= hour < 14:
            period = "中午"
            greeting = "中午好"
        elif 14 <= hour < 18:
            period = "下午"
            greeting = "下午好"
        elif 18 <= hour < 22:
            period = "晚上"
            greeting = "晚上好"
        else:
            period = "深夜"
            greeting = "夜深了"

        # 星期
        weekdays = [
            "星期一",
            "星期二",
            "星期三",
            "星期四",
            "星期五",
            "星期六",
            "星期日",
        ]
        weekday = weekdays[now.weekday()]

        return {
            "current_time": now.strftime("%Y-%m-%d %H:%M:%S"),
            "time_period": period,
            "weekday": weekday,
            "greeting": greeting,
            "is_weekend": now.weekday() >= 5,
            "is_night": hour >= 22 or hour < 5,
        }


class LocationAwareness:
    """地点感知"""

    @staticmethod
    def get_location_context(
        message_type: str,
        group_id: int = 0,
        group_name: str = "",
        user_id: int = 0,
        sender_name: str = "",
        sender_role: str = "",
    ) -> Dict[str, str]:
        """获取地点/场景上下文"""
        if message_type == "group":
            location = f"群聊 [{group_name}] ({group_id})"
            scene_type = "group_chat"
            role_desc = f"{sender_name} ({sender_role})"
        else:
            location = f"私聊 ({user_id})"
            scene_type = "private_chat"
            role_desc = sender_name

        return {
            "location": location,
            "scene_type": scene_type,
            "user_role": role_desc,
            "is_group": message_type == "group",
            "is_private": message_type != "group",
            "group_id": group_id,
            "group_name": group_name,
        }


class ActivityAwareness:
    """活动感知（基于谛听）"""

    @staticmethod
    def get_activity_context(group_id: str = "", user_id: str = "") -> Dict[str, str]:
        """获取当前活动上下文"""
        try:
            from memory.diteng_listener import get_diting

            diteng = get_diting()
        except Exception:
            return {"activity_summary": "", "is_active_conversation": False}

        is_active = False
        summary = ""

        if group_id and user_id:
            is_active = diteng.is_user_active_with_bot(group_id, user_id)
            summary = diteng.get_layered_context(group_id)
            if summary:
                summary = f"\n[群聊动态]\n{summary}"
            else:
                summary = "\n[群聊动态] 暂无近期消息"

        return {
            "activity_summary": summary,
            "is_active_conversation": is_active,
        }


class FrontendAwareness:
    """
    前端意识系统（感知层）

    整合时间、地点、活动感知，生成完整的上下文注入数据
    """

    def __init__(self):
        self.time_awareness = TimeAwareness()
        self.location_awareness = LocationAwareness()
        self.activity_awareness = ActivityAwareness()

    def gather_context(
        self,
        message_type: str,
        group_id: int = 0,
        group_name: str = "",
        user_id: int = 0,
        sender_name: str = "",
        sender_role: str = "",
    ) -> Dict[str, any]:
        """
        收集所有感知上下文

        Returns:
            包含时间、地点、活动感知的完整上下文字典
        """
        # 1. 时间感知
        time_ctx = self.time_awareness.get_current_time_context()

        # 2. 地点感知
        loc_ctx = self.location_awareness.get_location_context(
            message_type, group_id, group_name, user_id, sender_name, sender_role
        )

        # 3. 活动感知
        act_ctx = self.activity_awareness.get_activity_context(
            str(group_id), str(user_id)
        )

        # 4. 整合
        context = {
            **time_ctx,
            **loc_ctx,
            **act_ctx,
        }

        # 生成人类可读的感知摘要（用于 Prompt 注入）
        perception_text = (
            f"【当前感知】\n"
            f"时间：{context['current_time']} ({context['time_period']}, {context['weekday']})\n"
            f"地点：{context['location']}\n"
            f"对话对象：{context['user_role']}\n"
            f"对话状态：{'活跃对话中' if context['is_active_conversation'] else '新对话'}"
        )
        if context["activity_summary"]:
            perception_text += context["activity_summary"]

        context["perception_text"] = perception_text

        logger.info(
            f"[意识感知] 时间={context['time_period']}, 地点={context['location']}, 活跃={context['is_active_conversation']}"
        )

        return context


# 全局单例
_awareness: Optional[FrontendAwareness] = None


def get_awareness() -> FrontendAwareness:
    """获取前端意识系统单例"""
    global _awareness
    if _awareness is None:
        _awareness = FrontendAwareness()
    return _awareness
