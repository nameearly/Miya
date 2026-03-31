"""跨端消息API路由模块

提供跨终端消息同步、设备管理等API接口。
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

try:
    from fastapi import APIRouter, HTTPException
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    APIRouter = object
    HTTPException = Exception


class CrossTerminalRoutes:
    """跨端消息路由
    
    职责:
    - 跨端消息发送和接收
    - 在线设备管理
    - 状态同步
    """

    def __init__(self, web_net: Any, decision_hub: Any):
        """初始化跨端消息路由
        
        Args:
            web_net: WebNet实例
            decision_hub: DecisionHub实例
        """
        self.web_net = web_net
        self.decision_hub = decision_hub
        
        if not FASTAPI_AVAILABLE:
            self.router = None
            return
        
        self.router = APIRouter(prefix="/api/cross-terminal", tags=["CrossTerminal"])
        self._setup_routes()
        logger.info("[CrossTerminalRoutes] 跨端消息路由已初始化")

    def _setup_routes(self):
        """设置路由"""
        
        @self.router.get("/messages")
        async def get_cross_terminal_messages(
            last_id: str = "",
            limit: int = 20
        ):
            """获取跨端消息（桌面端轮询）"""
            try:
                from webnet.CrossTerminalNet.hub import get_cross_terminal_hub

                hub = get_cross_terminal_hub()
                messages = []

                # 简单的消息队列实现
                if not hasattr(hub, '_desktop_messages'):
                    hub._desktop_messages = []

                # 获取新消息
                new_messages = []
                for msg in hub._desktop_messages:
                    if msg.get('id', '') > last_id:
                        new_messages.append(msg)

                hub._desktop_messages = hub._desktop_messages[-100:]  # 保留最近100条

                return {
                    "success": True,
                    "messages": new_messages[-limit:],
                    "count": len(new_messages)
                }
            except Exception as e:
                logger.error(f"[CrossTerminalRoutes] 获取跨端消息失败: {e}")
                return {
                    "success": False,
                    "messages": [],
                    "error": str(e)
                }

        @self.router.post("/send")
        async def send_cross_terminal_message(
            target: str,  # desktop, qq, terminal, web
            content: str,
            message_type: str = "text"
        ):
            """发送跨端消息"""
            try:
                from webnet.CrossTerminalNet.hub import get_cross_terminal_hub, TerminalType

                hub = get_cross_terminal_hub()

                # 映射目标类型
                target_map = {
                    "desktop": TerminalType.DESKTOP,
                    "qq": TerminalType.QQ,
                    "terminal": TerminalType.TERMINAL,
                    "web": TerminalType.WEB
                }

                target_type = target_map.get(target, TerminalType.DESKTOP)

                message_id = await hub.publish_message(
                    content=content,
                    message_type=message_type,
                    source_type=TerminalType.WEB,
                    target_type=target_type
                )

                return {
                    "success": True,
                    "message_id": message_id,
                    "target": target
                }
            except Exception as e:
                logger.error(f"[CrossTerminalRoutes] 发送跨端消息失败: {e}")
                return {
                    "success": False,
                    "error": str(e)
                }

        @self.router.get("/devices")
        async def get_online_devices():
            """获取在线设备列表"""
            try:
                from webnet.CrossTerminalNet.hub import get_cross_terminal_hub

                hub = get_cross_terminal_hub()
                devices = await hub.get_online_devices()

                return {
                    "success": True,
                    "devices": [
                        {
                            "device_id": d.device_id,
                            "device_type": d.device_type.value,
                            "device_name": d.device_name,
                            "online": d.online
                        }
                        for d in devices
                    ]
                }
            except Exception as e:
                logger.error(f"[CrossTerminalRoutes] 获取设备列表失败: {e}")
                return {
                    "success": False,
                    "devices": [],
                    "error": str(e)
                }

        @self.router.post("/sync-state")
        async def sync_state(key: str, value: str):
            """同步状态到所有终端"""
            try:
                from webnet.CrossTerminalNet.hub import get_cross_terminal_hub

                hub = get_cross_terminal_hub()
                await hub.set_state(key, value)

                return {
                    "success": True,
                    "key": key,
                    "value": value
                }
            except Exception as e:
                logger.error(f"[CrossTerminalRoutes] 状态同步失败: {e}")
                return {
                    "success": False,
                    "error": str(e)
                }

    def get_router(self):
        """获取路由器"""
        return self.router
