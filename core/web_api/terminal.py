"""
Web API 终端路由 - 兼容旧API
"""

from typing import Dict, Any


class TerminalRoutes:
    """终端路由"""

    def __init__(self):
        self._routes = {}

    def register_routes(self, router) -> bool:
        """注册路由"""
        return True

    async def execute_terminal_command(
        self, command: str, cwd: str = None
    ) -> Dict[str, Any]:
        """执行终端命令"""
        from core.terminal_ultra import get_terminal_ultra

        ultra = get_terminal_ultra()
        result = await ultra.terminal_exec(command, cwd=cwd)
        return {
            "success": result.success,
            "output": result.output,
            "error": result.error,
        }


__all__ = ["TerminalRoutes"]
