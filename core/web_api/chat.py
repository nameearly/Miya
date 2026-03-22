"""
对话相关 API
处理 Web 端对话请求
"""
import logging
from datetime import datetime
from typing import Dict, Any

from fastapi import HTTPException

from .models import ChatRequest

logger = logging.getLogger(__name__)


class ChatRoutes:
    """对话路由"""

    def __init__(self, web_net, decision_hub):
        """初始化对话路由

        Args:
            web_net: WebNet 实例
            decision_hub: DecisionHub 实例
        """
        self.web_net = web_net
        self.decision_hub = decision_hub

    def setup_routes(self, router):
        """设置对话相关路由"""

        @router.post("/chat")
        async def chat_message(request: ChatRequest):
            """发送聊天消息"""
            try:
                # 创建 M-Link 消息对象
                from mlink.message import Message

                # 确定平台类型（优先使用请求中的platform，否则默认为web）
                platform = request.platform or 'web'

                perception = {
                    'platform': platform,
                    'content': request.message,
                    'user_id': request.session_id,
                    'sender_name': f'{platform}用户-{request.session_id[:8]}'
                }

                message = Message(
                    msg_type='data',
                    content=perception,
                    source='web_api',
                    destination='decision_hub'
                )

                # 获取处理前的状态
                emotion_before = self.decision_hub.emotion.get_emotion_state() if self.decision_hub.emotion else None
                personality_before = self.decision_hub.personality.get_profile() if self.decision_hub.personality else None

                # 调用 DecisionHub 处理消息
                response = await self.decision_hub.process_perception_cross_platform(message)

                if not response:
                    response = "抱歉，我无法处理您的请求。"

                # 获取处理后的状态
                emotion_after = self.decision_hub.emotion.get_emotion_state() if self.decision_hub.emotion else None
                personality_after = self.decision_hub.personality.get_profile() if self.decision_hub.personality else None

                # 确保返回正确格式
                emotion_result = None
                if emotion_after:
                    emotion_result = {
                        "dominant": emotion_after.get("dominant", "平静"),
                        "intensity": emotion_after.get("intensity", 0.5)
                    }

                personality_result = None
                if personality_after:
                    # 正确的人格数据格式
                    personality_result = {
                        "state": personality_after.get("dominant", "empathy"),  # 使用主导特质
                        "vectors": personality_after.get("vectors", {
                            "warmth": 0.5,
                            "logic": 0.5,
                            "creativity": 0.5,
                            "empathy": 0.5,
                            "resilience": 0.5
                        })
                    }

                return {
                    "response": response,
                    "timestamp": datetime.utcnow().isoformat(),
                    # 弥娅核心状态
                    "emotion": emotion_result,
                    "personality": personality_result,
                    # 工具调用信息（如果有）
                    "tools_used": getattr(self.decision_hub, '_last_tools_used', []),
                    # 记忆检索信息
                    "memory_retrieved": getattr(self.decision_hub, '_last_memory_retrieved', False)
                }
            except Exception as e:
                logger.error(f"[WebAPI] 聊天处理失败: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))

    def get_router(self):
        """获取路由器（返回None，因为使用setup_routes方式）"""
        return None
