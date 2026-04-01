"""
Web API 终端路由
"""

from typing import Dict, Any


class TerminalRoutes:
    """终端路由"""

    def __init__(self, web_net=None, decision_hub=None):
        self.web_net = web_net
        self.decision_hub = decision_hub
        self._routes = {}

    def get_router(self):
        """获取FastAPI路由"""
        try:
            from fastapi import APIRouter

            router = APIRouter(prefix="/api/terminal", tags=["terminal"])

            @router.post("/execute")
            async def execute_command(command: str, cwd: str = None):
                return await self.execute_terminal_command(command, cwd)

            return router
        except ImportError:
            return None

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
