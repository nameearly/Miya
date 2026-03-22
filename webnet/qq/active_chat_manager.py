"""
QQ主动聊天管理器

允许弥娅主动发起聊天，而不是被动响应
"""

import asyncio
import logging
import json
import os
from typing import Dict, Any, Optional, List, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import random

logger = logging.getLogger(__name__)


class MessagePriority(Enum):
    """消息优先级"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


class TriggerType(Enum):
    """触发类型"""
    TIME = "time"          # 定时触发
    EVENT = "event"        # 事件触发
    CONDITION = "condition" # 条件触发
    MANUAL = "manual"      # 手动触发


@dataclass
class ActiveMessage:
    """主动消息定义"""
    message_id: str
    target_type: str  # "group" 或 "private"
    target_id: int
    content: str
    trigger_type: TriggerType
    priority: MessagePriority
    trigger_config: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    scheduled_time: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    status: str = "pending"  # pending, scheduled, sent, failed, cancelled
    retry_count: int = 0
    max_retries: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """检查消息是否已过期"""
        if self.scheduled_time:
            expire_after = self.metadata.get("expire_after_hours", 24)
            expire_time = self.scheduled_time + timedelta(hours=expire_after)
            return datetime.now() > expire_time
        return False
    
    def should_retry(self) -> bool:
        """检查是否应该重试"""
        return self.status == "failed" and self.retry_count < self.max_retries
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "message_id": self.message_id,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "content": self.content,
            "trigger_type": self.trigger_type.value,
            "priority": self.priority.value,
            "trigger_config": self.trigger_config,
            "created_at": self.created_at.isoformat(),
            "scheduled_time": self.scheduled_time.isoformat() if self.scheduled_time else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "status": self.status,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ActiveMessage':
        """从字典创建"""
        # 解析时间
        created_at = datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now()
        scheduled_time = datetime.fromisoformat(data["scheduled_time"]) if data.get("scheduled_time") else None
        sent_at = datetime.fromisoformat(data["sent_at"]) if data.get("sent_at") else None
        
        return cls(
            message_id=data["message_id"],
            target_type=data["target_type"],
            target_id=data["target_id"],
            content=data["content"],
            trigger_type=TriggerType(data["trigger_type"]),
            priority=MessagePriority(data["priority"]),
            trigger_config=data.get("trigger_config", {}),
            created_at=created_at,
            scheduled_time=scheduled_time,
            sent_at=sent_at,
            status=data.get("status", "pending"),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            metadata=data.get("metadata", {}),
        )


class ActiveChatManager:
    """主动聊天管理器"""
    
    def __init__(self, qq_net):
        self.qq_net = qq_net
        self.pending_messages: Dict[str, ActiveMessage] = {}
        self.sent_messages: List[ActiveMessage] = []
        self.user_preferences: Dict[int, Dict[str, Any]] = {}  # 用户聊天偏好
        self.running = False
        
        # 触发器和检查器
        self.triggers: List[Any] = []
        self.check_interval = 60  # 检查间隔（秒）
        
        # 数据持久化路径
        self.data_dir = None
        self._init_data_dir()
        
        # 加载持久化数据
        self._load_persisted_data()
    
    def _init_data_dir(self):
        """初始化数据目录"""
        try:
            from pathlib import Path
            base_dir = Path(__file__).parent.parent.parent.parent / "data" / "active_chat"
            base_dir.mkdir(parents=True, exist_ok=True)
            self.data_dir = base_dir
            logger.info(f"[ActiveChatManager] 数据目录: {self.data_dir}")
        except Exception as e:
            logger.error(f"[ActiveChatManager] 初始化数据目录失败: {e}")
            self.data_dir = None
    
    def _load_persisted_data(self):
        """加载持久化数据"""
        if not self.data_dir:
            return
        
        try:
            # 加载待发消息
            pending_path = self.data_dir / "pending_messages.json"
            if pending_path.exists():
                with open(pending_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for msg_data in data:
                        try:
                            msg = ActiveMessage.from_dict(msg_data)
                            self.pending_messages[msg.message_id] = msg
                        except Exception as e:
                            logger.error(f"[ActiveChatManager] 加载消息失败: {e}")
            
            # 加载已发消息
            sent_path = self.data_dir / "sent_messages.json"
            if sent_path.exists():
                with open(sent_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for msg_data in data:
                        try:
                            msg = ActiveMessage.from_dict(msg_data)
                            self.sent_messages.append(msg)
                        except Exception as e:
                            logger.error(f"[ActiveChatManager] 加载已发消息失败: {e}")
            
            # 加载用户偏好
            prefs_path = self.data_dir / "user_preferences.json"
            if prefs_path.exists():
                with open(prefs_path, 'r', encoding='utf-8') as f:
                    self.user_preferences = json.load(f)
            
            logger.info(f"[ActiveChatManager] 数据加载完成: {len(self.pending_messages)}待发, {len(self.sent_messages)}已发, {len(self.user_preferences)}用户")
            
        except Exception as e:
            logger.error(f"[ActiveChatManager] 加载数据失败: {e}")
    
    def _save_persisted_data(self):
        """保存持久化数据"""
        if not self.data_dir:
            return
        
        try:
            # 保存待发消息
            pending_path = self.data_dir / "pending_messages.json"
            pending_data = [msg.to_dict() for msg in self.pending_messages.values()]
            with open(pending_path, 'w', encoding='utf-8') as f:
                json.dump(pending_data, f, ensure_ascii=False, indent=2)
            
            # 保存已发消息（只保存最近1000条）
            sent_path = self.data_dir / "sent_messages.json"
            recent_sent = self.sent_messages[-1000:] if len(self.sent_messages) > 1000 else self.sent_messages
            sent_data = [msg.to_dict() for msg in recent_sent]
            with open(sent_path, 'w', encoding='utf-8') as f:
                json.dump(sent_data, f, ensure_ascii=False, indent=2)
            
            # 保存用户偏好
            prefs_path = self.data_dir / "user_preferences.json"
            with open(prefs_path, 'w', encoding='utf-8') as f:
                json.dump(self.user_preferences, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"[ActiveChatManager] 数据保存完成")
            
        except Exception as e:
            logger.error(f"[ActiveChatManager] 保存数据失败: {e}")
    
    async def schedule_message(
        self,
        target_type: str,
        target_id: int,
        content: str,
        trigger_type: TriggerType = TriggerType.TIME,
        trigger_config: Optional[Dict[str, Any]] = None,
        priority: MessagePriority = MessagePriority.NORMAL,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        安排主动消息
        
        Args:
            target_type: 目标类型，"group" 或 "private"
            target_id: 目标ID（群号或用户QQ号）
            content: 消息内容
            trigger_type: 触发类型
            trigger_config: 触发器配置
            priority: 消息优先级
            metadata: 额外元数据
            
        Returns:
            消息ID
        """
        import uuid
        
        # 生成消息ID
        message_id = str(uuid.uuid4())
        
        # 检查用户偏好
        if not self._check_user_preference(target_id):
            raise ValueError(f"用户 {target_id} 不允许主动消息")
        
        # 构建消息
        trigger_config = trigger_config or {}
        metadata = metadata or {}
        
        # 设置计划时间
        scheduled_time = None
        if trigger_type == TriggerType.TIME:
            scheduled_time = self._parse_schedule_time(trigger_config)
        
        message = ActiveMessage(
            message_id=message_id,
            target_type=target_type,
            target_id=target_id,
            content=content,
            trigger_type=trigger_type,
            priority=priority,
            trigger_config=trigger_config,
            scheduled_time=scheduled_time,
            metadata=metadata
        )
        
        # 验证消息
        if not self._validate_message(message):
            raise ValueError("消息验证失败")
        
        # 添加到待发队列
        self.pending_messages[message_id] = message
        
        # 持久化保存
        self._save_persisted_data()
        
        logger.info(f"[ActiveChatManager] 消息已安排: {message_id} -> {target_type}:{target_id}")
        
        return message_id
    
    def _check_user_preference(self, user_id: int) -> bool:
        """检查用户是否允许主动消息"""
        user_prefs = self.user_preferences.get(str(user_id), {})
        
        # 默认允许，除非用户明确拒绝
        allow_active = user_prefs.get("allow_active_chat", True)
        
        # 检查静默时段
        if allow_active:
            quiet_hours = user_prefs.get("quiet_hours", [])
            current_hour = datetime.now().hour
            if current_hour in quiet_hours:
                logger.debug(f"[ActiveChatManager] 用户 {user_id} 处于静默时段 {current_hour}点")
                return False
        
        return allow_active
    
    def _parse_schedule_time(self, trigger_config: Dict[str, Any]) -> datetime:
        """解析计划时间"""
        now = datetime.now()
        
        # 解析cron表达式
        if "cron" in trigger_config:
            cron_expr = trigger_config["cron"]
            # 简化实现，只支持基本格式
            # TODO: 实现完整的cron解析
            return now + timedelta(minutes=1)
        
        # 解析具体时间
        elif "time" in trigger_config:
            time_str = trigger_config["time"]
            try:
                if ":" in time_str:
                    # HH:MM 格式
                    hour, minute = map(int, time_str.split(":"))
                    scheduled = datetime(now.year, now.month, now.day, hour, minute)
                    if scheduled <= now:
                        scheduled += timedelta(days=1)
                    return scheduled
                else:
                    # 相对时间，如 "10分钟后"
                    import re
                    match = re.search(r'(\d+)\s*分钟后', time_str)
                    if match:
                        minutes = int(match.group(1))
                        return now + timedelta(minutes=minutes)
            except Exception as e:
                logger.error(f"[ActiveChatManager] 解析时间失败: {e}")
        
        # 默认：1分钟后
        return now + timedelta(minutes=1)
    
    def _validate_message(self, message: ActiveMessage) -> bool:
        """验证消息合法性"""
        # 检查目标ID
        if message.target_id <= 0:
            return False
        
        # 检查消息内容
        if not message.content or len(message.content.strip()) == 0:
            return False
        
        # 检查发送时机
        if message.scheduled_time and message.scheduled_time < datetime.now():
            # 如果计划时间已过，调整为立即发送
            message.scheduled_time = datetime.now() + timedelta(seconds=10)
        
        # 检查每日消息限制
        user_id = message.target_id
        today = datetime.now().date()
        
        # 统计今日已发送消息
        today_sent = sum(
            1 for msg in self.sent_messages 
            if msg.target_id == user_id and msg.sent_at and msg.sent_at.date() == today
        )
        
        max_daily = self.user_preferences.get(str(user_id), {}).get("max_daily_messages", 10)
        if today_sent >= max_daily:
            logger.warning(f"[ActiveChatManager] 用户 {user_id} 今日消息已达上限: {today_sent}/{max_daily}")
            return False
        
        return True
    
    async def start(self):
        """启动主动聊天管理器"""
        if self.running:
            return
        
        self.running = True
        logger.info("[ActiveChatManager] 主动聊天管理器已启动")
        
        # 启动检查循环
        asyncio.create_task(self._check_loop())
    
    async def stop(self):
        """停止主动聊天管理器"""
        self.running = False
        logger.info("[ActiveChatManager] 主动聊天管理器已停止")
    
    async def _check_loop(self):
        """检查循环"""
        while self.running:
            try:
                await self._check_and_send_messages()
                await self._check_triggers()
                
            except Exception as e:
                logger.error(f"[ActiveChatManager] 检查循环异常: {e}")
            
            # 等待下一次检查
            await asyncio.sleep(self.check_interval)
    
    async def _check_and_send_messages(self):
        """检查并发送待发消息"""
        now = datetime.now()
        messages_to_send = []
        
        # 找出需要发送的消息
        for msg_id, message in list(self.pending_messages.items()):
            # 检查消息状态
            if message.status not in ["pending", "scheduled", "failed"]:
                continue
            
            # 检查计划时间
            if message.scheduled_time and message.scheduled_time <= now:
                messages_to_send.append((msg_id, message))
            elif not message.scheduled_time and message.trigger_type == TriggerType.MANUAL:
                # 手动触发的消息立即发送
                messages_to_send.append((msg_id, message))
        
        # 按优先级排序
        messages_to_send.sort(key=lambda x: x[1].priority.value, reverse=True)
        
        # 发送消息
        for msg_id, message in messages_to_send:
            await self._send_message(msg_id, message)
    
    async def _send_message(self, msg_id: str, message: ActiveMessage):
        """发送消息"""
        try:
            # 更新状态
            message.status = "sending"
            
            # 发送消息
            if message.target_type == "group":
                await self.qq_net.send_group_message(
                    message.target_id,
                    message.content
                )
            else:
                await self.qq_net.send_private_message(
                    message.target_id,
                    message.content
                )
            
            # 更新状态
            message.status = "sent"
            message.sent_at = datetime.now()
            
            # 移动到已发列表
            self.pending_messages.pop(msg_id, None)
            self.sent_messages.append(message)
            
            # 限制已发列表大小
            if len(self.sent_messages) > 1000:
                self.sent_messages = self.sent_messages[-1000:]
            
            # 记录发送历史
            await self._record_sent_message(message)
            
            # 保存数据
            self._save_persisted_data()
            
            logger.info(f"[ActiveChatManager] 消息已发送: {msg_id} -> {message.target_type}:{message.target_id}")
            
        except Exception as e:
            # 处理失败
            await self._handle_send_failure(msg_id, message, e)
    
    async def _handle_send_failure(self, msg_id: str, message: ActiveMessage, error: Exception):
        """处理发送失败"""
        logger.error(f"[ActiveChatManager] 消息发送失败 {msg_id}: {error}")
        
        message.status = "failed"
        message.retry_count += 1
        
        # 检查是否需要重试
        if message.should_retry():
            # 安排重试
            retry_delay = min(300 * (2 ** message.retry_count), 3600)  # 指数退避
            message.scheduled_time = datetime.now() + timedelta(seconds=retry_delay)
            message.status = "pending"
            
            logger.info(f"[ActiveChatManager] 消息 {msg_id} 将在 {retry_delay} 秒后重试")
        else:
            # 重试次数用尽
            logger.error(f"[ActiveChatManager] 消息 {msg_id} 重试次数用尽")
            
            # 发送失败通知（可选）
            await self._send_failure_notification(message, error)
        
        # 保存数据
        self._save_persisted_data()
    
    async def _record_sent_message(self, message: ActiveMessage):
        """记录已发送消息到记忆系统"""
        try:
            memory_net = getattr(self.qq_net, 'memory_net', None)
            if not memory_net:
                return
            
            await memory_net.record_active_chat(
                target_id=message.target_id,
                content=message.content,
                message_type=message.target_type,
                trigger_type=message.trigger_type.value,
                priority=message.priority.value,
                timestamp=message.sent_at or datetime.now(),
                metadata=message.metadata
            )
            
        except Exception as e:
            logger.warning(f"[ActiveChatManager] 记录到记忆系统失败: {e}")
    
    async def _send_failure_notification(self, message: ActiveMessage, error: Exception):
        """发送失败通知"""
        # 可以在这里实现失败通知逻辑
        # 例如：发送给管理员，或记录到日志系统
        pass
    
    async def _check_triggers(self):
        """检查触发器"""
        # 这里可以集成各种触发器
        # 例如：定时触发器、事件触发器、条件触发器
        
        # 示例：早安问候触发器
        now = datetime.now()
        if now.hour == 8 and now.minute == 0:
            await self._trigger_morning_greetings()
    
    async def _trigger_morning_greetings(self):
        """触发早安问候"""
        # 这里可以实现早安问候逻辑
        # 例如：向所有允许主动聊天的用户发送早安问候
        pass
    
    def set_user_preference(self, user_id: int, preferences: Dict[str, Any]):
        """设置用户偏好"""
        user_id_str = str(user_id)
        
        if user_id_str not in self.user_preferences:
            self.user_preferences[user_id_str] = {}
        
        self.user_preferences[user_id_str].update(preferences)
        
        # 保存数据
        self._save_persisted_data()
        
        logger.info(f"[ActiveChatManager] 用户 {user_id} 偏好已更新: {preferences}")
    
    def get_user_preference(self, user_id: int) -> Dict[str, Any]:
        """获取用户偏好"""
        return self.user_preferences.get(str(user_id), {}).copy()
    
    def get_pending_messages(self) -> List[ActiveMessage]:
        """获取待发消息列表"""
        return list(self.pending_messages.values())
    
    def get_sent_messages(self, limit: int = 100) -> List[ActiveMessage]:
        """获取已发消息列表"""
        return self.sent_messages[-limit:] if len(self.sent_messages) > limit else self.sent_messages
    
    def cancel_message(self, message_id: str) -> bool:
        """取消消息"""
        if message_id in self.pending_messages:
            message = self.pending_messages[message_id]
            message.status = "cancelled"
            self.pending_messages.pop(message_id, None)
            
            # 保存数据
            self._save_persisted_data()
            
            logger.info(f"[ActiveChatManager] 消息已取消: {message_id}")
            return True
        
        return False
    
    def cleanup_expired_messages(self):
        """清理过期消息"""
        expired_ids = []
        
        for msg_id, message in self.pending_messages.items():
            if message.is_expired():
                expired_ids.append(msg_id)
        
        for msg_id in expired_ids:
            self.pending_messages.pop(msg_id, None)
        
        if expired_ids:
            logger.info(f"[ActiveChatManager] 清理了 {len(expired_ids)} 个过期消息")
            self._save_persisted_data()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计数据"""
        now = datetime.now()
        today = now.date()
        
        # 今日统计数据
        today_sent = sum(
            1 for msg in self.sent_messages 
            if msg.sent_at and msg.sent_at.date() == today
        )
        
        today_failed = sum(
            1 for msg in self.sent_messages 
            if msg.status == "failed" and msg.sent_at and msg.sent_at.date() == today
        )
        
        return {
            "total_pending": len(self.pending_messages),
            "total_sent": len(self.sent_messages),
            "today_sent": today_sent,
            "today_failed": today_failed,
            "total_users": len(self.user_preferences),
            "running": self.running,
            "last_check": now.isoformat()
        }