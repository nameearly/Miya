"""
QQ交互子网 - 核心子网逻辑
从原 qq.py 中拆分出来的核心网络逻辑
"""

import asyncio
import json
import logging
import os
from typing import Any, Callable, Dict, List, Optional, Set
from datetime import datetime

from .models import QQMessage, QQNotice
from .client import QQOneBotClient
from .message_handler import QQMessageHandler
from .tts_handler import QQTTsHandler
from .active_chat_manager import (
    IntelligentActiveChatManager,
    TriggerType,
    MessagePriority,
)
from .unified_config import get_qq_config, get_connection_config, get_multimedia_config

logger = logging.getLogger(__name__)

# 使用增强版图片处理器（支持多模型）
try:
    from .enhanced_image_handler import QQImageHandler

    logger.info("[QQNet] 使用增强版多模型图片处理器")
except ImportError:
    from .image_handler import QQImageHandler

    logger.warning("[QQNet] 使用简化版图片处理器，多模型系统不可用")


class QQNet:
    """
    QQ交互子网
    完全吸收Undefined的QQ机器人能力，作为弥娅的一个子网运行
    """

    def __init__(self, miya_core, mlink=None, memory_net=None, tts_net=None):
        """
        初始化QQ子网

        Args:
            miya_core: 弥娅核心实例
            mlink: M-Link 核心实例（用于全局记忆系统）
            memory_net: MemoryNet 全局记忆子网实例
            tts_net: TTSNet TTS子网实例
        """
        self.miya_core = miya_core
        self.mlink = mlink
        self.memory_net = memory_net
        self.tts_net = tts_net
        self.net_id = "qq_net"
        self.capabilities = [
            "qq_group_chat",
            "qq_private_chat",
            "qq_command",
            "qq_message_history",
            "qq_poke",
            "qq_multimedia",
            "qq_tts",
        ]

        # 配置
        self.onebot_ws_url = None
        self.onebot_token = None
        self.bot_qq = None
        self.superadmin_qq = None

        # 客户端
        self.onebot_client: Optional[QQOneBotClient] = None

        # 缓存管理器（新增）
        from .cache_manager import get_qq_cache_manager

        self.cache_manager = get_qq_cache_manager()
        logger.info("[QQNet] 缓存管理器已集成")

        # 处理模块
        self.message_handler = QQMessageHandler(self)
        self.tts_handler = QQTTsHandler(self)
        self.image_handler = QQImageHandler(self)
        # 使用智能主动聊天管理器（支持上下文感知）
        self.active_chat_manager = IntelligentActiveChatManager(self)
        logger.info("[QQNet] 智能主动聊天管理器已集成")

        # 访问控制
        self.group_whitelist: Set[int] = set()
        self.group_blacklist: Set[int] = set()
        self.user_whitelist: Set[int] = set()
        self.user_blacklist: Set[int] = set()

        # 配置加载
        self._load_default_config()

        # 消息处理回调
        self.on_message_callback: Optional[Callable] = None

    def _load_default_config(self):
        """加载默认配置"""
        # 从配置文件加载
        self._load_config_from_file()

    def _load_config_from_file(self):
        """从配置文件加载配置（使用统一配置系统）"""
        try:
            # 使用统一配置系统
            qq_config = get_qq_config()

            # 基础连接配置
            self.onebot_ws_url = qq_config.get("onebot_ws_url", "ws://localhost:3001")
            self.onebot_token = qq_config.get("onebot_token", "")
            self.bot_qq = qq_config.get("bot_qq", 0)
            self.superadmin_qq = qq_config.get("superadmin_qq", 0)

            # 连接配置
            self.reconnect_interval = qq_config.get("reconnect_interval", 5.0)
            self.ping_interval = qq_config.get("ping_interval", 20)
            self.ping_timeout = qq_config.get("ping_timeout", 30)
            self.max_message_size = qq_config.get("max_message_size", 104857600)

            # 访问控制（从环境变量解析）
            group_whitelist_str = qq_config.get("group_whitelist", "")
            group_blacklist_str = qq_config.get("group_blacklist", "")
            user_whitelist_str = qq_config.get("user_whitelist", "")
            user_blacklist_str = qq_config.get("user_blacklist", "")

            self.group_whitelist = (
                set(map(int, filter(None, group_whitelist_str.split(","))))
                if group_whitelist_str
                else set()
            )
            self.group_blacklist = (
                set(map(int, filter(None, group_blacklist_str.split(","))))
                if group_blacklist_str
                else set()
            )
            self.user_whitelist = (
                set(map(int, filter(None, user_whitelist_str.split(","))))
                if user_whitelist_str
                else set()
            )
            self.user_blacklist = (
                set(map(int, filter(None, user_blacklist_str.split(","))))
                if user_blacklist_str
                else set()
            )

            # 多媒体配置
            multimedia_config = qq_config.get("multimedia", {})
            self.image_config = multimedia_config.get("image", {})
            self.file_config = multimedia_config.get("file", {})

            # 图片识别配置
            image_recognition_config = qq_config.get("image_recognition", {})
            self.ocr_config = {
                "enabled": image_recognition_config.get("ocr_enabled", True),
                "engine": image_recognition_config.get("ocr_engine", "auto"),
            }

            # 主动聊天配置
            active_chat_config = qq_config.get("active_chat", {})
            self.active_chat_enabled = active_chat_config.get("enabled", True)
            self.active_chat_limits = {
                "max_daily_messages": active_chat_config.get("max_daily_messages", 10),
                "min_interval": active_chat_config.get("min_interval", 300),
            }

            # 任务调度配置
            task_scheduler_config = qq_config.get("task_scheduler", {})
            self.task_scheduler_enabled = task_scheduler_config.get("enabled", True)

            # TTS配置（保持向后兼容）
            self.tts_enabled = True  # 默认启用TTS
            self.tts_voice_mode = "text"  # text 或 voice, 默认文本
            self.smart_tts_enabled = False  # 智能TTS判断开关，默认关闭

            # QQ消息分段配置
            self.qq_message_split = True
            self.qq_max_message_length = 200

            # 本地播放配置
            self.local_playback_enabled = False
            self.local_playback_volume = 1.0

            # 音频播放器
            self.audio_player = None

            logger.info(
                f"[QQNet] 统一配置加载成功，WebSocket地址: {self.onebot_ws_url}"
            )

            # 记录关键配置
            logger.info(f"[QQNet] 配置摘要:")
            logger.info(f"  - Bot QQ: {self.bot_qq}")
            logger.info(f"  - 重连间隔: {self.reconnect_interval}s")
            logger.info(f"  - OCR启用: {self.ocr_config.get('enabled')}")
            logger.info(f"  - 主动聊天启用: {self.active_chat_enabled}")

        except Exception as e:
            logger.error(f"[QQNet] 加载统一配置失败，使用默认配置: {e}")
            # 使用硬编码的默认值
            self.onebot_ws_url = "ws://localhost:3001"  # 注意：默认端口改为3001
            self.onebot_token = ""
            self.bot_qq = 0
            self.superadmin_qq = 0
            self.reconnect_interval = 5.0
            self.ping_interval = 20
            self.ping_timeout = 30
            self.max_message_size = 104857600

            self.group_whitelist = set()
            self.group_blacklist = set()
            self.user_whitelist = set()
            self.user_blacklist = set()

            self.image_config = {
                "max_size": 10485760,
                "allowed_formats": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"],
            }
            self.file_config = {"max_size": 52428800}
            self.ocr_config = {"enabled": True, "engine": "auto"}
            self.active_chat_enabled = True
            self.active_chat_limits = {"max_daily_messages": 10, "min_interval": 300}
            self.task_scheduler_enabled = True

            self.tts_enabled = True
            self.tts_voice_mode = "text"
            self.smart_tts_enabled = False
            self.qq_message_split = True
            self.qq_max_message_length = 200
            self.local_playback_enabled = False
            self.local_playback_volume = 1.0
            self.audio_player = None

    def configure(
        self,
        onebot_ws_url: str,
        onebot_token: str = "",
        bot_qq: int = 0,
        superadmin_qq: int = 0,
        group_whitelist: List[int] = None,
        group_blacklist: List[int] = None,
        user_whitelist: List[int] = None,
        user_blacklist: List[int] = None,
        tts_enabled: bool = True,
        tts_voice_mode: str = "text",
        smart_tts_enabled: bool = False,
        qq_message_split: bool = True,
        qq_max_message_length: int = 200,
        local_playback_enabled: bool = False,
        local_playback_volume: float = 1.0,
    ) -> None:
        """配置QQ子网"""
        self.onebot_ws_url = onebot_ws_url
        self.onebot_token = onebot_token
        self.bot_qq = bot_qq
        self.superadmin_qq = superadmin_qq

        if group_whitelist:
            self.group_whitelist = set(group_whitelist)
        if group_blacklist:
            self.group_blacklist = set(group_blacklist)
        if user_whitelist:
            self.user_whitelist = set(user_whitelist)
        if user_blacklist:
            self.user_blacklist = set(user_blacklist)

        self.tts_enabled = tts_enabled
        self.tts_voice_mode = tts_voice_mode
        self.smart_tts_enabled = smart_tts_enabled

        # QQ消息分段配置
        self.qq_message_split = qq_message_split
        self.qq_max_message_length = qq_max_message_length

        # 本地播放配置
        self.local_playback_enabled = local_playback_enabled
        self.local_playback_volume = local_playback_volume

        # 初始化音频播放器
        if local_playback_enabled:
            from core.audio_player import get_audio_player

            self.audio_player = get_audio_player()
            self.audio_player.set_volume(local_playback_volume)

        # 更新处理模块配置
        self.message_handler.configure(
            group_whitelist=self.group_whitelist,
            group_blacklist=self.group_blacklist,
            user_whitelist=self.user_whitelist,
            user_blacklist=self.user_blacklist,
            bot_qq=self.bot_qq,
            enable_image_ocr=False,  # 禁用OCR，仅使用视觉模型
            enable_ai_image_analysis=True,  # 启用AI图片分析
            image_handler=self.image_handler,  # 传递图片处理器实例
        )

        # 配置图片处理器 - 仅使用视觉模型
        self.image_handler.configure()

        self.tts_handler.configure(
            tts_enabled=self.tts_enabled,
            tts_voice_mode=self.tts_voice_mode,
            smart_tts_enabled=self.smart_tts_enabled,
            qq_message_split=self.qq_message_split,
            qq_max_message_length=self.qq_max_message_length,
            local_playback_enabled=self.local_playback_enabled,
            local_playback_volume=self.local_playback_volume,
            audio_player=self.audio_player,
        )

        logger.info(
            f"[QQNet] 配置完成: bot_qq={bot_qq}, "
            f"superadmin={superadmin_qq}, "
            f"groups={len(self.group_whitelist)}/{len(self.group_blacklist)}, "
            f"tts_enabled={tts_enabled}, tts_mode={tts_voice_mode}, "
            f"smart_tts={smart_tts_enabled}, "
            f"message_split={self.qq_message_split}, max_length={self.qq_max_message_length}, "
            f"local_playback={self.local_playback_enabled}, local_volume={self.local_playback_volume}"
        )

    def set_message_callback(self, callback: Callable) -> None:
        """设置消息处理回调"""
        self.on_message_callback = callback
        if self.onebot_client:
            self.onebot_client.set_message_handler(self._handle_qq_message)

    async def connect(self) -> None:
        """连接到QQ"""
        if not self.onebot_ws_url:
            raise RuntimeError("未配置OneBot WebSocket URL")

        self.onebot_client = QQOneBotClient(self.onebot_ws_url, self.onebot_token)
        self.onebot_client.set_message_handler(self._handle_qq_message)

        await self.onebot_client.connect()
        logger.info("[QQNet] 已连接到QQ")

    async def start(self) -> None:
        """启动QQ子网"""
        if not self.onebot_client:
            await self.connect()

        # 启动主动聊天管理器
        await self.active_chat_manager.start()

        # 启动消息接收循环
        await self.onebot_client.run_with_reconnect()

    async def stop(self) -> None:
        """停止QQ子网"""
        # 停止主动聊天管理器
        await self.active_chat_manager.stop()

        # 停止QQ客户端
        if self.onebot_client:
            self.onebot_client.stop()
            await self.onebot_client.disconnect()

    async def _handle_qq_message(self, event: Dict) -> None:
        """处理QQ消息事件"""
        # 委托给消息处理器
        qq_message = await self.message_handler.handle_event(event)

        # 【新增】提取上下文用于智能主动聊天
        if qq_message and hasattr(
            self.active_chat_manager, "extract_context_from_message"
        ):
            try:
                # 从用户消息中提取上下文
                user_id = qq_message.user_id or qq_message.sender_id
                group_id = qq_message.group_id
                message_text = qq_message.message

                # 提取上下文
                context = self.active_chat_manager.extract_context_from_message(
                    user_id=user_id, message=message_text, group_id=group_id
                )

                if context:
                    self.active_chat_manager.add_context(context)
                    logger.info(f"[QQNet] 提取到上下文: {context.content[:30]}...")

            except Exception as e:
                logger.warning(f"[QQNet] 提取上下文失败: {e}")

        if qq_message and self.on_message_callback:
            await self.on_message_callback(qq_message)

    async def send_group_message(
        self, group_id: int, message: str | List[Dict], use_tts: bool = None
    ) -> bool:
        """发送群消息"""
        return await self.tts_handler.send_group_message(
            group_id=group_id, message=message, use_tts=use_tts
        )

    async def send_private_message(
        self, user_id: int, message: str | List[Dict], use_tts: bool = None
    ) -> bool:
        """发送私聊消息"""
        return await self.tts_handler.send_private_message(
            user_id=user_id, message=message, use_tts=use_tts
        )

    def get_history(self, chat_id: int, limit: int = 20) -> List[Dict]:
        """获取历史消息"""
        return self.message_handler.get_history(chat_id, limit)

    def set_tts_mode(self, mode: str):
        """设置TTS模式 (text 或 voice)"""
        self.tts_handler.set_tts_mode(mode)

    def toggle_tts(self, enabled: bool = None):
        """切换TTS开关"""
        return self.tts_handler.toggle_tts(enabled)

    def toggle_local_playback(self, enabled: bool = None):
        """切换本地播放开关"""
        return self.tts_handler.toggle_local_playback(enabled)

    def set_local_playback_volume(self, volume: float):
        """设置本地播放音量"""
        self.tts_handler.set_local_playback_volume(volume)

    def toggle_smart_tts(self, enabled: bool = None):
        """切换智能TTS判断开关"""
        return self.tts_handler.toggle_smart_tts(enabled)

    async def process_request(self, request: Dict) -> Dict:
        """处理QQ子网请求"""
        req_type = request.get("type")

        if req_type == "send_group":
            success = await self.send_group_message(
                request.get("group_id"), request.get("message")
            )
            return {"success": success}

        elif req_type == "send_private":
            success = await self.send_private_message(
                request.get("user_id"), request.get("message")
            )
            return {"success": success}

        elif req_type == "get_history":
            history = self.get_history(request.get("chat_id"), request.get("limit", 20))
            return {"history": history}

        elif req_type == "get_connection_status":
            if self.onebot_client:
                return {"status": self.onebot_client.connection_status()}
            return {"status": {"connected": False}}

        elif req_type == "toggle_smart_tts":
            enabled = request.get("enabled")
            result = self.toggle_smart_tts(enabled)
            return {"success": True, "enabled": result}

        elif req_type == "get_tts_status":
            return {
                "tts_enabled": self.tts_enabled,
                "tts_voice_mode": self.tts_voice_mode,
                "smart_tts_enabled": self.smart_tts_enabled,
                "local_playback_enabled": self.local_playback_enabled,
                "local_playback_volume": self.local_playback_volume,
            }

        else:
            return {"error": "Unknown request type"}

    # ========== 主动聊天方法 ==========

    async def schedule_active_message(
        self,
        target_type: str,
        target_id: int,
        content: str,
        trigger_type: str = "time",
        trigger_config: Optional[Dict] = None,
        priority: int = 2,
        metadata: Optional[Dict] = None,
    ) -> str:
        """
        安排主动消息

        Args:
            target_type: 目标类型，"group" 或 "private"
            target_id: 目标ID（群号或用户QQ号）
            content: 消息内容
            trigger_type: 触发类型，"time", "event", "condition", "manual"
            trigger_config: 触发器配置
            priority: 优先级，1-4（低-紧急）
            metadata: 额外元数据

        Returns:
            消息ID
        """
        try:
            # 转换枚举类型
            trigger_enum = TriggerType(trigger_type)
            priority_enum = MessagePriority(priority)

            message_id = await self.active_chat_manager.schedule_message(
                target_type=target_type,
                target_id=target_id,
                content=content,
                trigger_type=trigger_enum,
                trigger_config=trigger_config or {},
                priority=priority_enum,
                metadata=metadata or {},
            )

            return message_id

        except Exception as e:
            logger.error(f"[QQNet] 安排主动消息失败: {e}")
            raise

    def set_user_preference(self, user_id: int, preferences: Dict[str, Any]):
        """
        设置用户偏好

        Args:
            user_id: 用户QQ号
            preferences: 偏好设置字典
        """
        self.active_chat_manager.set_user_preference(user_id, preferences)

    def get_user_preference(self, user_id: int) -> Dict[str, Any]:
        """
        获取用户偏好

        Args:
            user_id: 用户QQ号

        Returns:
            用户偏好字典
        """
        return self.active_chat_manager.get_user_preference(user_id)

    def get_active_chat_stats(self) -> Dict[str, Any]:
        """
        获取主动聊天统计

        Returns:
            统计数据字典
        """
        return self.active_chat_manager.get_stats()

    def get_pending_messages(self) -> List[Dict[str, Any]]:
        """
        获取待发消息列表

        Returns:
            待发消息列表
        """
        messages = self.active_chat_manager.get_pending_messages()
        return [msg.to_dict() for msg in messages]

    def get_sent_messages(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取已发消息列表

        Args:
            limit: 限制数量

        Returns:
            已发消息列表
        """
        messages = self.active_chat_manager.get_sent_messages(limit)
        return [msg.to_dict() for msg in messages]

    def cancel_active_message(self, message_id: str) -> bool:
        """
        取消主动消息

        Args:
            message_id: 消息ID

        Returns:
            是否成功取消
        """
        return self.active_chat_manager.cancel_message(message_id)

    def cleanup_expired_messages(self):
        """清理过期消息"""
        self.active_chat_manager.cleanup_expired_messages()
