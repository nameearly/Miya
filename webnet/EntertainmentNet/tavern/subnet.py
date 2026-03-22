"""
TavernNet 子网基类
酒馆子网的核心实�?
"""

from typing import Dict, Any, Optional
import asyncio
import json
import os
from datetime import datetime
from pathlib import Path

from mlink.mlink_core import MLinkCore
from .memory import TavernMemory
from .character import CharacterManager


class TavernNet:
    """弥娅酒馆子网"""

    def __init__(
        self,
        mlink: Optional[MLinkCore] = None,
        ai_client=None,
        personality=None,
        storage_path: str = "data/tavern"
    ):
        self.mlink = mlink
        self.ai_client = ai_client
        self.personality = personality

        # 初始化核心组�?
        self.memory = TavernMemory()
        self.character_manager = CharacterManager()

        # 当前会话状�?
        self.active_sessions: Dict[str, Dict] = {}

        # 状态持久化路径
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # 文件路径
        self.characters_file = self.storage_path / "characters.json"
        self.memory_file = self.storage_path / "memory.json"
        self.sessions_file = self.storage_path / "sessions.json"

    async def initialize(self):
        """初始化酒馆子�?""
        # 加载保存的角色和记忆
        await self._load_state()

    async def shutdown(self):
        """关闭酒馆子网"""
        # 保存状�?
        await self._save_state()

    async def _load_state(self):
        """加载保存的状�?""
        try:
            # 加载角色数据
            if self.characters_file.exists():
                with open(self.characters_file, 'r', encoding='utf-8') as f:
                    characters_data = json.load(f)
                    # 恢复角色管理器状�?
                    if hasattr(self.character_manager, 'characters'):
                        for char_id, char_data in characters_data.items():
                            self.character_manager.characters[char_id] = char_data
                print(f"[TavernNet] 已加�?{len(characters_data)} 个角�?)

            # 加载记忆数据
            if self.memory_file.exists():
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    memory_data = json.load(f)
                    # 恢复记忆系统状�?
                    if hasattr(self.memory, 'memory'):
                        self.memory.memory = memory_data
                print(f"[TavernNet] 已加载记忆数�?)

            # 加载会话状�?
            if self.sessions_file.exists():
                with open(self.sessions_file, 'r', encoding='utf-8') as f:
                    self.active_sessions = json.load(f)
                print(f"[TavernNet] 已加�?{len(self.active_sessions)} 个会�?)

        except Exception as e:
            print(f"[TavernNet] 加载状态失�? {e}")

    async def _save_state(self):
        """保存状�?""
        try:
            # 保存角色数据
            if hasattr(self.character_manager, 'characters'):
                characters_data = self.character_manager.characters
                with open(self.characters_file, 'w', encoding='utf-8') as f:
                    json.dump(characters_data, f, indent=2, ensure_ascii=False)
                print(f"[TavernNet] 已保�?{len(characters_data)} 个角�?)

            # 保存记忆数据
            if hasattr(self.memory, 'memory'):
                memory_data = self.memory.memory
                with open(self.memory_file, 'w', encoding='utf-8') as f:
                    json.dump(memory_data, f, indent=2, ensure_ascii=False)
                print(f"[TavernNet] 已保存记忆数�?)

            # 保存会话状�?
            with open(self.sessions_file, 'w', encoding='utf-8') as f:
                json.dump(self.active_sessions, f, indent=2, ensure_ascii=False)
            print(f"[TavernNet] 已保�?{len(self.active_sessions)} 个会�?)

        except Exception as e:
            print(f"[TavernNet] 保存状态失�? {e}")

    def get_session_state(self, chat_id: str) -> Dict:
        """获取会话状�?""
        return self.active_sessions.get(chat_id, {})

    def set_session_state(self, chat_id: str, state: Dict):
        """设置会话状�?""
        self.active_sessions[chat_id] = state

    def clear_session_state(self, chat_id: str):
        """清除会话状�?""
        if chat_id in self.active_sessions:
            del self.active_sessions[chat_id]
