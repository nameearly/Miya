"""
弥娅终端接管模式 - 兼容旧API简化版
"""

import asyncio
from typing import Dict, Optional, Callable, Any


class MiyaTakeoverMode:
    """终端接管模式 - 简化版"""

    def __init__(self, master_controller=None, child_manager=None):
        self._terminals: Dict[str, Dict] = {}
        self._callback: Optional[Callable] = None
        self.master_controller = master_controller
        self.child_manager = child_manager

    def set_miya_callback(self, callback: Callable):
        """设置弥娅回调"""
        self._callback = callback

    def get_all_terminals_status(self) -> Dict[str, Dict]:
        """获取所有终端状态"""
        return self._terminals

    async def handle_input(self, user_input: str, from_terminal: str = "master") -> Any:
        """处理用户输入"""
        if self._callback:
            return await self._callback(user_input)
        return None

    def add_terminal(self, terminal_id: str, name: str, terminal_type: str):
        """添加终端"""
        self._terminals[terminal_id] = {
            "name": name,
            "type": terminal_type,
            "status": "idle",
        }


class ChildTerminalManager:
    """子终端管理器 - 简化版"""

    def __init__(self, local_manager=None, ssh_manager=None):
        self._sessions: Dict[str, Dict] = {}
        self.local_manager = local_manager
        self.ssh_manager = ssh_manager

    def create_session(self, name: str, terminal_type: str) -> str:
        """创建会话"""
        session_id = f"session_{len(self._sessions)}"
        self._sessions[session_id] = {"name": name, "type": terminal_type}
        return session_id


class ChildTerminalConfig:
    """子终端配置"""

    def __init__(self, name: str = "child", terminal_type: str = "cmd"):
        self.name = name
        self.terminal_type = terminal_type


class MasterTerminalController:
    """主终端控制器 - 简化版"""

    def __init__(
        self,
        local_manager=None,
        ssh_manager=None,
        show_thinking=True,
        auto_monitor=True,
        monitor_interval=1.0,
    ):
        self.local_manager = local_manager
        self.ssh_manager = ssh_manager
        self.show_thinking = show_thinking
        self.auto_monitor = auto_monitor
        self.monitor_interval = monitor_interval


__all__ = [
    "MiyaTakeoverMode",
    "ChildTerminalManager",
    "ChildTerminalConfig",
    "MasterTerminalController",
]
