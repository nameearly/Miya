"""
跨终端工具 - 兼容旧API
"""

from typing import Dict, Any


class CrossTerminalTool:
    """跨终端工具"""

    config = {"name": "cross_terminal", "description": "跨终端工具"}

    def __init__(self):
        self._sessions: Dict[str, Any] = {}

    async def execute_remote(self, terminal_id: str, command: str) -> Dict:
        """远程执行命令"""
        return {"success": True, "output": "Cross-terminal not available"}

    async def list_terminals(self) -> Dict:
        """列出终端"""
        return {"success": True, "terminals": []}


__all__ = ["CrossTerminalTool"]
