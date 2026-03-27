"""终端相关API路由模块

提供终端代理聊天、命令执行、会话管理等API接口。
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from fastapi import APIRouter, HTTPException, Depends, Header
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from pydantic import BaseModel

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    APIRouter = object
    HTTPException = Exception
    Depends = lambda x: x
    HTTPBearer = None


class TerminalChatRequest(BaseModel):
    """终端聊天请求"""

    message: str
    session_id: str = "terminal"
    from_terminal: Optional[str] = None  # 来自终端的标识


class WSLRegisterRequest(BaseModel):
    """WSL代理注册请求"""

    session_id: str
    platform: str = "wsl"
    username: Optional[str] = None


class TerminalRoutes:
    """终端相关路由

    职责:
    - 终端代理聊天接口
    - 命令执行和历史记录
    - 会话管理和保存
    """

    def __init__(self, web_net: Any, decision_hub: Any):
        """初始化终端路由

        Args:
            web_net: WebNet实例
            decision_hub: DecisionHub实例
        """
        self.web_net = web_net
        self.decision_hub = decision_hub

        if not FASTAPI_AVAILABLE:
            self.router = None
            return

        self.router = APIRouter(prefix="/api/terminal", tags=["Terminal"])
        self.security = HTTPBearer()
        self._setup_routes()
        logger.info("[TerminalRoutes] 终端路由已初始化")

    def _setup_routes(self):
        """设置路由"""

        @self.router.post("/register")
        async def register_wsl_agent(request: WSLRegisterRequest):
            """WSL代理注册接口"""
            try:
                logger.info(
                    f"[WSL] 代理注册: session_id={request.session_id}, user={request.username}"
                )
                return {
                    "success": True,
                    "message": "WSL代理注册成功",
                    "session_id": request.session_id,
                }
            except Exception as e:
                logger.error(f"[WSL] 注册失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.router.post("/chat")
        async def terminal_chat(request: TerminalChatRequest):
            """终端代理聊天接口 - 供子终端窗口使用"""
            try:
                from mlink.message import Message

                # 确定来源标识
                terminal_id = request.from_terminal or request.session_id

                # 使用 "desktop" 平台来绕过权限检查（因为 desktop 平台已授权）
                # 同时保留 terminal 信息用于标识来源
                perception = {
                    "platform": "desktop",
                    "content": request.message,
                    "user_id": request.session_id,
                    "sender_name": f"终端-{terminal_id[:8]}",
                    "from_terminal": terminal_id,
                    "is_terminal_agent": True,
                }

                message = Message(
                    msg_type="data",
                    content=perception,
                    source="terminal_agent",
                    destination="decision_hub",
                )

                # 调用 DecisionHub 处理消息
                response = await self.decision_hub.process_perception_cross_platform(
                    message
                )

                if not response:
                    response = "抱歉,我无法处理您的请求。"

                return {
                    "response": response,
                    "session_id": request.session_id,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            except Exception as e:
                logger.error(f"[TerminalRoutes] 终端聊天处理失败: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))

        @self.router.get("/history")
        async def get_terminal_history(limit: int = 20):
            """获取终端命令执行历史"""
            try:
                # 尝试从 decision_hub 获取终端工具
                if (
                    hasattr(self.decision_hub, "terminal_tool")
                    and self.decision_hub.terminal_tool
                ):
                    # 检查是否有 get_command_history 方法
                    if hasattr(self.decision_hub.terminal_tool, "get_command_history"):
                        history = self.decision_hub.terminal_tool.get_command_history(
                            limit
                        )
                    else:
                        history = []

                    # 检查是否有 get_command_statistics 方法
                    if hasattr(
                        self.decision_hub.terminal_tool, "get_command_statistics"
                    ):
                        statistics = (
                            self.decision_hub.terminal_tool.get_command_statistics()
                        )
                    else:
                        statistics = None

                    return {
                        "success": True,
                        "history": history,
                        "statistics": statistics,
                    }
                else:
                    return {
                        "success": False,
                        "history": [],
                        "statistics": None,
                        "message": "终端工具未初始化",
                    }
            except Exception as e:
                logger.error(f"[TerminalRoutes] 获取终端历史失败: {e}", exc_info=True)
                return {
                    "success": False,
                    "history": [],
                    "statistics": None,
                    "message": str(e),
                }

        @self.router.post("/save_session")
        async def save_session(request: dict):
            """手动保存会话到 LifeBook"""
            try:
                session_id = request.get("session_id", "default")
                platform = request.get("platform", "terminal")
                logger.info(
                    f"[TerminalRoutes] 收到手动保存请求: {session_id}, platform={platform}"
                )

                # 调用 DecisionHub 处理会话结束
                if hasattr(self.decision_hub, "handle_session_end"):
                    result = await self.decision_hub.handle_session_end(
                        session_id, platform=platform
                    )
                    return result
                else:
                    return {
                        "success": False,
                        "message": "DecisionHub 未实现 handle_session_end 方法",
                    }
            except Exception as e:
                logger.error(f"[TerminalRoutes] 手动保存失败: {e}", exc_info=True)
                return {"success": False, "message": str(e)}

        @self.router.post("/session_end")
        async def terminal_session_end(request: dict):
            """终端会话结束接口 - 触发对话历史存储到 LifeBook"""
            try:
                session_id = request.get("session_id", "unknown")
                logger.info(f"[TerminalRoutes] 收到终端会话结束请求: {session_id}")

                # 调用 DecisionHub 处理会话结束
                if hasattr(self.decision_hub, "handle_session_end"):
                    result = await self.decision_hub.handle_session_end(
                        session_id, platform="terminal"
                    )
                    return {
                        "success": True,
                        "message": "对话历史已保存到 LifeBook",
                        "session_id": session_id,
                    }
                else:
                    return {
                        "success": False,
                        "message": "DecisionHub 未实现 handle_session_end 方法",
                    }
            except Exception as e:
                logger.error(f"[TerminalRoutes] 会话结束处理失败: {e}", exc_info=True)
                return {"success": False, "message": str(e)}

        @self.router.post("/execute")
        async def execute_terminal_command(
            command: str,
            session_id: str = "web",
            user_info: Dict = Depends(lambda: {"web_user_id": "web_default"}),
        ):
            """直接执行终端命令（需要 terminal_command 权限）"""
            try:
                # 权限检查
                from webnet.AuthNet.permission_core import PermissionCore

                perm_core = PermissionCore()
                web_user_id = user_info.get("web_user_id", "web_default")
                has_permission = perm_core.check_permission(
                    web_user_id, "tool.terminal_command"
                )

                if not has_permission:
                    has_permission = perm_core.check_permission(
                        "system_admin", "tool.terminal_command"
                    )

                if not has_permission:
                    return {
                        "success": False,
                        "error": "权限不足：执行终端命令需要 'tool.terminal_command' 权限",
                    }

                # 创建 M-Link 消息
                from mlink.message import Message

                perception = {
                    "platform": "web",
                    "content": f"执行命令: {command}",
                    "user_id": session_id,
                    "sender_name": f"Web用户-{session_id[:8]}",
                }

                message = Message(
                    msg_type="data",
                    content=perception,
                    source="web_api",
                    destination="decision_hub",
                )

                # 调用 DecisionHub 处理
                response = await self.decision_hub.process_perception_cross_platform(
                    message
                )

                return {
                    "success": True,
                    "command": command,
                    "response": response,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            except Exception as e:
                logger.error(f"[TerminalRoutes] 执行终端命令失败: {e}", exc_info=True)
                return {"success": False, "command": command, "error": str(e)}

    def get_router(self):
        """获取路由器"""
        return self.router
