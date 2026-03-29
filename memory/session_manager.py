"""
Legacy session_manager - 已迁移到新版记忆系统
"""

from typing import List, Optional
from enum import Enum


class SessionCategory(Enum):
    """会话类别 - 兼容旧接口"""

    DIALOGUE = "dialogue"
    TASK = "task"
    SYSTEM = "system"
    CREATIVE = "creative"


class SessionManager:
    """会话管理器 - 兼容旧接口"""

    def __init__(self):
        pass

    async def create_session(self, session_id: str, user_id: str) -> str:
        return session_id

    async def get_session(self, session_id: str) -> Optional[dict]:
        return None

    async def get_conversation_messages(
        self, session_id: str, limit: int = 50
    ) -> List[dict]:
        from memory import get_dialogue_history

        mems = await get_dialogue_history(session_id, limit=limit)
        return [{"role": m.role, "content": m.content} for m in mems]


def get_session_manager():
    return SessionManager()


def init_session_manager():
    """初始化会话管理器 - 兼容旧接口"""
    return SessionManager()


__all__ = [
    "SessionManager",
    "get_session_manager",
    "init_session_manager",
    "SessionCategory",
]
