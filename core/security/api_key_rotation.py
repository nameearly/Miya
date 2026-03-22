"""
API密钥轮换系统 - 安全加固模块
================================

该模块提供自动化的API密钥轮换机制，支持定期密钥更新、密钥版本管理、
密钥撤销和审计日志功能。通过密钥轮换减少密钥泄露风险，提高系统安全性。

设计目标:
1. 定期自动轮换API密钥
2. 支持密钥版本管理和回滚
3. 安全的密钥存储和分发
4. 密钥使用审计和监控
5. 无缝的密钥切换（无服务中断）
"""

import asyncio
import base64
import hashlib
import json
import logging
import os
import secrets
import string
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class KeyStatus(Enum):
    """密钥状态"""
    ACTIVE = "active"        # 当前使用中
    PENDING = "pending"      # 已生成，等待激活
    EXPIRED = "expired"     # 已过期
    REVOKED = "revoked"     # 已撤销
    DEPRECATED = "deprecated"  # 已弃用（历史版本）


class RotationStrategy(Enum):
    """轮换策略"""
    TIME_BASED = "time_based"       # 基于时间轮换
    USAGE_BASED = "usage_based"     # 基于使用量轮换
    EVENT_BASED = "event_based"     # 基于事件轮换
    MANUAL = "manual"               # 手动轮换


class KeyType(Enum):
    """密钥类型"""
    API_KEY = "api_key"           # API密钥
    ACCESS_TOKEN = "access_token" # 访问令牌
    SECRET_KEY = "secret_key"     # 加密密钥
    SESSION_KEY = "session_key"   # 会话密钥


@dataclass
class KeyMetadata:
    """密钥元数据"""
    key_id: str
    key_type: KeyType
    status: KeyStatus
    created_at: datetime
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime] = None
    usage_count: int = 0
    rotation_count: int = 0
    tags: Dict[str, str] = field(default_factory=dict)
    description: Optional[str] = None
    
    @property
    def is_expired(self) -> bool:
        """检查是否过期"""
        if not self.expires_at:
            return False
        return datetime.now() > self.expires_at
    
    @property
    def days_until_expiry(self) -> Optional[float]:
        """距离过期的天数"""
        if not self.expires_at:
            return None
        delta = self.expires_at - datetime.now()
        return delta.total_seconds() / 86400  # 转换为天


@dataclass
class RotationConfig:
    """轮换配置"""
    key_type: KeyType
    rotation_interval_days: int = 30  # 轮换间隔（天）
    warning_days_before: int = 7      # 过期前警告天数
    max_active_keys: int = 2          # 最大活跃密钥数
    overlap_hours: int = 24           # 新旧密钥重叠时间（小时）
    rotation_strategy: RotationStrategy = RotationStrategy.TIME_BASED
    max_usage_count: Optional[int] = None  # 最大使用次数（基于使用量轮换）
    auto_revoke_expired: bool = True  # 是否自动撤销过期密钥
    enable_audit_logging: bool = True  # 是否启用审计日志


class KeyGenerator:
    """密钥生成器"""
    
    @staticmethod
    def generate_api_key(length: int = 32) -> str:
        """生成API密钥"""
        # 使用安全的随机字节
        random_bytes = secrets.token_bytes(length)
        
        # 转换为base64编码的字符串
        api_key = base64.urlsafe_b64encode(random_bytes).decode().rstrip('=')
        
        # 确保长度正确
        return api_key[:length]
    
    @staticmethod
    def generate_secret_key(length: int = 64) -> str:
        """生成加密密钥"""
        # 使用更长的密钥用于加密
        random_bytes = secrets.token_bytes(length)
        return base64.urlsafe_b64encode(random_bytes).decode().rstrip('=')
    
    @staticmethod
    def generate_access_token(prefix: str = "token_", length: int = 40) -> str:
        """生成访问令牌"""
        # 组合前缀和随机字符串
        random_part = ''.join(
            secrets.choice(string.ascii_letters + string.digits)
            for _ in range(length)
        )
        return f"{prefix}{random_part}"
    
    @staticmethod
    def generate_key_id(key_type: KeyType) -> str:
        """生成密钥ID"""
        timestamp = int(time.time() * 1000)
        random_part = secrets.token_hex(4)
        return f"{key_type.value}_{timestamp}_{random_part}"
    
    @staticmethod
    def hash_key(key: str) -> str:
        """计算密钥哈希值（用于安全存储）"""
        return hashlib.sha256(key.encode()).hexdigest()


class BaseKeyStore(ABC):
    """密钥存储抽象基类"""
    
    @abstractmethod
    async def save_key(self, key_id: str, key_value: str, metadata: KeyMetadata) -> bool:
        """保存密钥"""
        pass
    
    @abstractmethod
    async def get_key(self, key_id: str) -> Optional[Tuple[str, KeyMetadata]]:
        """获取密钥"""
        pass
    
    @abstractmethod
    async def delete_key(self, key_id: str) -> bool:
        """删除密钥"""
        pass
    
    @abstractmethod
    async def list_keys(self, key_type: Optional[KeyType] = None) -> List[str]:
        """列出所有密钥ID"""
        pass
    
    @abstractmethod
    async def update_metadata(self, key_id: str, metadata: KeyMetadata) -> bool:
        """更新元数据"""
        pass


class FileKeyStore(BaseKeyStore):
    """文件密钥存储"""
    
    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # 密钥文件路径
        self.keys_dir = self.storage_path / "keys"
        self.keys_dir.mkdir(exist_ok=True)
        
        # 元数据文件
        self.metadata_file = self.storage_path / "metadata.json"
        
        # 加载元数据
        self._metadata: Dict[str, KeyMetadata] = {}
        self._load_metadata()
    
    def _load_metadata(self):
        """加载元数据"""
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    for key_id, meta_data in data.items():
                        # 转换日期字符串为datetime对象
                        created_at = datetime.fromisoformat(meta_data['created_at'])
                        expires_at = (
                            datetime.fromisoformat(meta_data['expires_at'])
                            if meta_data.get('expires_at') else None
                        )
                        last_used_at = (
                            datetime.fromisoformat(meta_data['last_used_at'])
                            if meta_data.get('last_used_at') else None
                        )
                        
                        metadata = KeyMetadata(
                            key_id=key_id,
                            key_type=KeyType(meta_data['key_type']),
                            status=KeyStatus(meta_data['status']),
                            created_at=created_at,
                            expires_at=expires_at,
                            last_used_at=last_used_at,
                            usage_count=meta_data.get('usage_count', 0),
                            rotation_count=meta_data.get('rotation_count', 0),
                            tags=meta_data.get('tags', {}),
                            description=meta_data.get('description')
                        )
                        
                        self._metadata[key_id] = metadata
                        
        except Exception as e:
            logger.error(f"加载元数据失败: {e}")
            self._metadata = {}
    
    def _save_metadata(self):
        """保存元数据"""
        try:
            # 转换datetime对象为字符串
            data = {}
            for key_id, metadata in self._metadata.items():
                meta_dict = {
                    'key_type': metadata.key_type.value,
                    'status': metadata.status.value,
                    'created_at': metadata.created_at.isoformat(),
                    'expires_at': metadata.expires_at.isoformat() if metadata.expires_at else None,
                    'last_used_at': metadata.last_used_at.isoformat() if metadata.last_used_at else None,
                    'usage_count': metadata.usage_count,
                    'rotation_count': metadata.rotation_count,
                    'tags': metadata.tags,
                    'description': metadata.description
                }
                data[key_id] = meta_dict
            
            # 保存到文件
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"保存元数据失败: {e}")
    
    async def save_key(self, key_id: str, key_value: str, metadata: KeyMetadata) -> bool:
        """保存密钥"""
        try:
            # 保存密钥值（哈希后存储）
            key_hash = KeyGenerator.hash_key(key_value)
            key_file = self.keys_dir / f"{key_id}.key"
            
            with open(key_file, 'w', encoding='utf-8') as f:
                f.write(key_hash)
            
            # 保存元数据
            self._metadata[key_id] = metadata
            self._save_metadata()
            
            logger.info(f"保存密钥: {key_id}, 类型={metadata.key_type.value}")
            return True
            
        except Exception as e:
            logger.error(f"保存密钥失败: {e}")
            return False
    
    async def get_key(self, key_id: str) -> Optional[Tuple[str, KeyMetadata]]:
        """获取密钥"""
        try:
            # 获取元数据
            metadata = self._metadata.get(key_id)
            if not metadata:
                return None
            
            # 获取密钥哈希值
            key_file = self.keys_dir / f"{key_id}.key"
            if not key_file.exists():
                return None
            
            with open(key_file, 'r', encoding='utf-8') as f:
                key_hash = f.read().strip()
            
            # 注意：我们只返回哈希值，不返回原始密钥
            # 实际验证时使用验证接口
            return key_hash, metadata
            
        except Exception as e:
            logger.error(f"获取密钥失败: {e}")
            return None
    
    async def delete_key(self, key_id: str) -> bool:
        """删除密钥"""
        try:
            # 删除密钥文件
            key_file = self.keys_dir / f"{key_id}.key"
            if key_file.exists():
                key_file.unlink()
            
            # 删除元数据
            if key_id in self._metadata:
                del self._metadata[key_id]
                self._save_metadata()
            
            logger.info(f"删除密钥: {key_id}")
            return True
            
        except Exception as e:
            logger.error(f"删除密钥失败: {e}")
            return False
    
    async def list_keys(self, key_type: Optional[KeyType] = None) -> List[str]:
        """列出所有密钥ID"""
        if key_type:
            return [
                key_id for key_id, metadata in self._metadata.items()
                if metadata.key_type == key_type
            ]
        return list(self._metadata.keys())
    
    async def update_metadata(self, key_id: str, metadata: KeyMetadata) -> bool:
        """更新元数据"""
        try:
            self._metadata[key_id] = metadata
            self._save_metadata()
            return True
        except Exception as e:
            logger.error(f"更新元数据失败: {e}")
            return False


class AuditLogger:
    """审计日志器"""
    
    def __init__(self, log_dir: Path):
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
    
    async def log_rotation(self, key_id: str, old_status: KeyStatus, new_status: KeyStatus, reason: str):
        """记录轮换日志"""
        await self._log_event("rotation", {
            "key_id": key_id,
            "old_status": old_status.value,
            "new_status": new_status.value,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        })
    
    async def log_usage(self, key_id: str, service: str, success: bool):
        """记录使用日志"""
        await self._log_event("usage", {
            "key_id": key_id,
            "service": service,
            "success": success,
            "timestamp": datetime.now().isoformat()
        })
    
    async def log_key_generation(self, key_id: str, key_type: KeyType):
        """记录密钥生成日志"""
        await self._log_event("generation", {
            "key_id": key_id,
            "key_type": key_type.value,
            "timestamp": datetime.now().isoformat()
        })
    
    async def log_key_revocation(self, key_id: str, reason: str):
        """记录密钥撤销日志"""
        await self._log_event("revocation", {
            "key_id": key_id,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        })
    
    async def _log_event(self, event_type: str, data: Dict[str, Any]):
        """记录事件"""
        try:
            # 按日期创建日志文件
            date_str = datetime.now().strftime("%Y-%m-%d")
            log_file = self.log_dir / f"{event_type}_{date_str}.jsonl"
            
            # 追加日志
            log_entry = {
                "event_type": event_type,
                "timestamp": datetime.now().isoformat(),
                "data": data
            }
            
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
                
        except Exception as e:
            logger.error(f"记录审计日志失败: {e}")


class KeyRotationManager:
    """密钥轮换管理器"""
    
    def __init__(
        self,
        storage_path: Optional[Path] = None,
        audit_log_dir: Optional[Path] = None
    ):
        # 存储路径
        if storage_path is None:
            storage_path = Path.home() / ".miya" / "key_rotation"
        self.storage_path = storage_path
        
        # 审计日志目录
        if audit_log_dir is None:
            audit_log_dir = storage_path / "audit_logs"
        self.audit_log_dir = audit_log_dir
        
        # 初始化组件
        self.key_store = FileKeyStore(storage_path)
        self.audit_logger = AuditLogger(audit_log_dir)
        self.key_generator = KeyGenerator()
        
        # 轮换配置
        self._configs: Dict[KeyType, RotationConfig] = {}
        
        # 轮换任务
        self._rotation_tasks: Dict[str, asyncio.Task] = {}
        
        logger.info(f"密钥轮换管理器初始化完成，存储路径: {storage_path}")
    
    def register_config(self, config: RotationConfig):
        """注册轮换配置"""
        self._configs[config.key_type] = config
        logger.info(f"注册密钥轮换配置: {config.key_type.value}")
    
    async def generate_key(
        self,
        key_type: KeyType,
        expires_in_days: Optional[int] = None,
        description: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None
    ) -> Tuple[str, str]:
        """生成新密钥"""
        # 获取配置
        config = self._configs.get(key_type)
        if not config:
            config = RotationConfig(key_type=key_type)
            self.register_config(config)
        
        # 生成密钥ID和值
        key_id = self.key_generator.generate_key_id(key_type)
        
        # 根据类型生成密钥
        if key_type == KeyType.API_KEY:
            key_value = self.key_generator.generate_api_key()
        elif key_type == KeyType.SECRET_KEY:
            key_value = self.key_generator.generate_secret_key()
        elif key_type == KeyType.ACCESS_TOKEN:
            key_value = self.key_generator.generate_access_token()
        elif key_type == KeyType.SESSION_KEY:
            key_value = self.key_generator.generate_api_key(64)
        else:
            key_value = self.key_generator.generate_api_key()
        
        # 计算过期时间
        if expires_in_days is None:
            expires_in_days = config.rotation_interval_days
        
        created_at = datetime.now()
        expires_at = created_at + timedelta(days=expires_in_days)
        
        # 创建元数据
        metadata = KeyMetadata(
            key_id=key_id,
            key_type=key_type,
            status=KeyStatus.PENDING,  # 初始状态为待激活
            created_at=created_at,
            expires_at=expires_at,
            tags=tags or {},
            description=description
        )
        
        # 保存密钥
        success = await self.key_store.save_key(key_id, key_value, metadata)
        if not success:
            raise RuntimeError("保存密钥失败")
        
        # 记录审计日志
        if config.enable_audit_logging:
            await self.audit_logger.log_key_generation(key_id, key_type)
        
        logger.info(f"生成密钥: {key_id}, 类型={key_type.value}")
        
        return key_id, key_value
    
    async def activate_key(self, key_id: str) -> bool:
        """激活密钥"""
        result = await self.key_store.get_key(key_id)
        if not result:
            logger.error(f"密钥不存在: {key_id}")
            return False
        
        key_hash, metadata = result
        
        # 检查状态
        if metadata.status == KeyStatus.ACTIVE:
            logger.warning(f"密钥已是激活状态: {key_id}")
            return True
        
        if metadata.status not in [KeyStatus.PENDING, KeyStatus.DEPRECATED]:
            logger.error(f"密钥无法激活: {key_id}, 状态={metadata.status.value}")
            return False
        
        # 更新状态
        old_status = metadata.status
        metadata.status = KeyStatus.ACTIVE
        
        success = await self.key_store.update_metadata(key_id, metadata)
        if not success:
            return False
        
        # 记录审计日志
        config = self._configs.get(metadata.key_type)
        if config and config.enable_audit_logging:
            await self.audit_logger.log_rotation(
                key_id, old_status, KeyStatus.ACTIVE, "手动激活"
            )
        
        logger.info(f"激活密钥: {key_id}")
        return True
    
    async def revoke_key(self, key_id: str, reason: str = "手动撤销") -> bool:
        """撤销密钥"""
        result = await self.key_store.get_key(key_id)
        if not result:
            logger.error(f"密钥不存在: {key_id}")
            return False
        
        key_hash, metadata = result
        
        # 更新状态
        old_status = metadata.status
        metadata.status = KeyStatus.REVOKED
        
        success = await self.key_store.update_metadata(key_id, metadata)
        if not success:
            return False
        
        # 记录审计日志
        config = self._configs.get(metadata.key_type)
        if config and config.enable_audit_logging:
            await self.audit_logger.log_key_revocation(key_id, reason)
            await self.audit_logger.log_rotation(
                key_id, old_status, KeyStatus.REVOKED, reason
            )
        
        logger.info(f"撤销密钥: {key_id}, 原因={reason}")
        return True
    
    async def validate_key(self, key_id: str, key_value: str) -> Tuple[bool, Optional[str]]:
        """验证密钥"""
        result = await self.key_store.get_key(key_id)
        if not result:
            return False, "密钥不存在"
        
        stored_hash, metadata = result
        
        # 检查状态
        if metadata.status != KeyStatus.ACTIVE:
            return False, f"密钥状态无效: {metadata.status.value}"
        
        # 检查是否过期
        if metadata.is_expired:
            # 自动标记为过期
            metadata.status = KeyStatus.EXPIRED
            await self.key_store.update_metadata(key_id, metadata)
            return False, "密钥已过期"
        
        # 验证密钥哈希
        input_hash = KeyGenerator.hash_key(key_value)
        if input_hash != stored_hash:
            return False, "密钥验证失败"
        
        # 更新使用统计
        metadata.usage_count += 1
        metadata.last_used_at = datetime.now()
        await self.key_store.update_metadata(key_id, metadata)
        
        # 记录使用日志
        config = self._configs.get(metadata.key_type)
        if config and config.enable_audit_logging:
            await self.audit_logger.log_usage(key_id, "validation", True)
        
        return True, None
    
    async def rotate_key(self, key_type: KeyType, force: bool = False) -> bool:
        """轮换密钥"""
        config = self._configs.get(key_type)
        if not config:
            logger.error(f"未找到轮换配置: {key_type.value}")
            return False
        
        try:
            # 获取当前活跃密钥
            all_keys = await self.key_store.list_keys(key_type)
            active_keys = []
            
            for key_id in all_keys:
                result = await self.key_store.get_key(key_id)
                if result:
                    _, metadata = result
                    if metadata.status == KeyStatus.ACTIVE:
                        active_keys.append((key_id, metadata))
            
            # 检查是否需要轮换
            if not force and len(active_keys) < config.max_active_keys:
                logger.debug(f"当前活跃密钥数未达到上限，无需轮换: {len(active_keys)}/{config.max_active_keys}")
                return True
            
            # 找到最旧的活跃密钥进行轮换
            if active_keys:
                # 按创建时间排序
                active_keys.sort(key=lambda x: x[1].created_at)
                oldest_key_id, oldest_metadata = active_keys[0]
                
                # 标记为弃用
                old_status = oldest_metadata.status
                oldest_metadata.status = KeyStatus.DEPRECATED
                await self.key_store.update_metadata(oldest_key_id, oldest_metadata)
                
                # 记录轮换日志
                if config.enable_audit_logging:
                    await self.audit_logger.log_rotation(
                        oldest_key_id, old_status, KeyStatus.DEPRECATED, "自动轮换"
                    )
                
                logger.info(f"弃用旧密钥: {oldest_key_id}")
            
            # 生成新密钥
            new_key_id, new_key_value = await self.generate_key(
                key_type=key_type,
                expires_in_days=config.rotation_interval_days,
                description=f"自动轮换生成，替换{oldest_key_id if active_keys else '无'}",
                tags={"auto_rotated": "true"}
            )
            
            # 激活新密钥
            await self.activate_key(new_key_id)
            
            # 如果配置了自动撤销过期密钥，执行清理
            if config.auto_revoke_expired:
                await self._cleanup_expired_keys(key_type)
            
            logger.info(f"密钥轮换完成: {key_type.value}, 新密钥={new_key_id[:12]}")
            return True
            
        except Exception as e:
            logger.error(f"密钥轮换失败: {e}")
            return False
    
    async def _cleanup_expired_keys(self, key_type: KeyType):
        """清理过期密钥"""
        config = self._configs.get(key_type)
        if not config:
            return
        
        all_keys = await self.key_store.list_keys(key_type)
        
        for key_id in all_keys:
            result = await self.key_store.get_key(key_id)
            if result:
                _, metadata = result
                
                # 检查是否过期且未撤销
                if metadata.is_expired and metadata.status not in [KeyStatus.REVOKED, KeyStatus.EXPIRED]:
                    # 标记为过期
                    old_status = metadata.status
                    metadata.status = KeyStatus.EXPIRED
                    await self.key_store.update_metadata(key_id, metadata)
                    
                    # 记录日志
                    if config.enable_audit_logging:
                        await self.audit_logger.log_rotation(
                            key_id, old_status, KeyStatus.EXPIRED, "自动过期"
                        )
                    
                    logger.info(f"标记过期密钥: {key_id}")
    
    async def start_auto_rotation(self):
        """启动自动轮换"""
        logger.info("启动自动密钥轮换")
        
        for key_type, config in self._configs.items():
            if config.rotation_strategy == RotationStrategy.TIME_BASED:
                task_name = f"rotation_{key_type.value}"
                
                async def rotation_task(key_type=key_type, config=config):
                    """轮换任务"""
                    logger.info(f"启动自动轮换任务: {key_type.value}")
                    
                    while True:
                        try:
                            # 等待轮换间隔
                            await asyncio.sleep(config.rotation_interval_days * 86400)  # 转换为秒
                            
                            # 执行轮换
                            await self.rotate_key(key_type)
                            
                        except asyncio.CancelledError:
                            break
                        except Exception as e:
                            logger.error(f"自动轮换任务异常: {e}")
                            await asyncio.sleep(3600)  # 异常后等待1小时
                
                # 启动任务
                self._rotation_tasks[task_name] = asyncio.create_task(rotation_task())
    
    async def stop_auto_rotation(self):
        """停止自动轮换"""
        logger.info("停止自动密钥轮换")
        
        for task_name, task in self._rotation_tasks.items():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        self._rotation_tasks.clear()
    
    async def get_key_status(self, key_type: Optional[KeyType] = None) -> Dict[str, Any]:
        """获取密钥状态统计"""
        all_keys = await self.key_store.list_keys(key_type)
        
        stats = {
            "total_keys": len(all_keys),
            "by_status": {},
            "by_type": {},
            "expiring_soon": []
        }
        
        current_time = datetime.now()
        
        for key_id in all_keys:
            result = await self.key_store.get_key(key_id)
            if result:
                _, metadata = result
                
                # 按状态统计
                status_key = metadata.status.value
                stats["by_status"][status_key] = stats["by_status"].get(status_key, 0) + 1
                
                # 按类型统计
                type_key = metadata.key_type.value
                stats["by_type"][type_key] = stats["by_type"].get(type_key, 0) + 1
                
                # 检查即将过期的密钥
                if metadata.expires_at:
                    days_left = (metadata.expires_at - current_time).total_seconds() / 86400
                    if 0 < days_left <= 7:  # 7天内过期
                        stats["expiring_soon"].append({
                            "key_id": key_id,
                            "key_type": metadata.key_type.value,
                            "status": metadata.status.value,
                            "days_left": round(days_left, 1)
                        })
        
        return stats
    
    async def export_keys(self, include_values: bool = False) -> Dict[str, Any]:
        """导出密钥（安全方式）"""
        all_keys = await self.key_store.list_keys()
        
        export_data = {
            "export_time": datetime.now().isoformat(),
            "total_keys": len(all_keys),
            "keys": []
        }
        
        for key_id in all_keys:
            result = await self.key_store.get_key(key_id)
            if result:
                key_hash, metadata = result
                
                key_info = {
                    "key_id": key_id,
                    "key_type": metadata.key_type.value,
                    "status": metadata.status.value,
                    "created_at": metadata.created_at.isoformat(),
                    "expires_at": metadata.expires_at.isoformat() if metadata.expires_at else None,
                    "last_used_at": metadata.last_used_at.isoformat() if metadata.last_used_at else None,
                    "usage_count": metadata.usage_count,
                    "rotation_count": metadata.rotation_count,
                    "tags": metadata.tags,
                    "description": metadata.description
                }
                
                if include_values:
                    key_info["key_hash"] = key_hash
                
                export_data["keys"].append(key_info)
        
        return export_data


# 全局密钥轮换管理器实例
_global_key_manager: Optional[KeyRotationManager] = None


def get_key_rotation_manager(
    storage_path: Optional[Path] = None,
    audit_log_dir: Optional[Path] = None
) -> KeyRotationManager:
    """获取全局密钥轮换管理器"""
    global _global_key_manager
    
    if _global_key_manager is None:
        _global_key_manager = KeyRotationManager(storage_path, audit_log_dir)
    
    return _global_key_manager


# 便捷函数
async def generate_api_key(
    expires_in_days: int = 30,
    description: Optional[str] = None,
    tags: Optional[Dict[str, str]] = None
) -> Tuple[str, str]:
    """便捷函数：生成API密钥"""
    manager = get_key_rotation_manager()
    return await manager.generate_key(
        KeyType.API_KEY,
        expires_in_days,
        description,
        tags
    )


async def validate_api_key(key_id: str, key_value: str) -> Tuple[bool, Optional[str]]:
    """便捷函数：验证API密钥"""
    manager = get_key_rotation_manager()
    return await manager.validate_key(key_id, key_value)


async def rotate_api_keys(force: bool = False) -> bool:
    """便捷函数：轮换API密钥"""
    manager = get_key_rotation_manager()
    return await manager.rotate_key(KeyType.API_KEY, force)


async def get_key_statistics() -> Dict[str, Any]:
    """便捷函数：获取密钥统计"""
    manager = get_key_rotation_manager()
    return await manager.get_key_status()


async def test_key_rotation():
    """测试密钥轮换功能"""
    print("=== API密钥轮换系统测试 ===")
    
    # 获取管理器
    manager = get_key_rotation_manager()
    
    # 注册配置
    config = RotationConfig(
        key_type=KeyType.API_KEY,
        rotation_interval_days=7,  # 7天轮换（测试用）
        warning_days_before=1,
        max_active_keys=2
    )
    manager.register_config(config)
    
    # 生成第一个密钥
    print("1. 生成第一个API密钥...")
    key_id1, key_value1 = await generate_api_key(
        expires_in_days=3,  # 3天后过期（测试用）
        description="测试密钥1",
        tags={"env": "test"}
    )
    print(f"   密钥ID: {key_id1}")
    print(f"   密钥值: {key_value1[:16]}...")
    
    # 激活第一个密钥
    print("2. 激活第一个密钥...")
    await manager.activate_key(key_id1)
    
    # 验证第一个密钥
    print("3. 验证第一个密钥...")
    is_valid, error = await validate_api_key(key_id1, key_value1)
    print(f"   验证结果: {'成功' if is_valid else '失败'}")
    if error:
        print(f"   错误: {error}")
    
    # 生成第二个密钥
    print("4. 生成第二个API密钥...")
    key_id2, key_value2 = await generate_api_key(
        expires_in_days=5,
        description="测试密钥2",
        tags={"env": "test"}
    )
    print(f"   密钥ID: {key_id2}")
    
    # 激活第二个密钥
    print("5. 激活第二个密钥...")
    await manager.activate_key(key_id2)
    
    # 获取统计信息
    print("6. 获取密钥统计信息...")
    stats = await get_key_statistics()
    print(f"   总密钥数: {stats['total_keys']}")
    print(f"   按状态统计: {stats['by_status']}")
    
    # 测试轮换（由于最多允许2个活跃密钥，应该会弃用最旧的）
    print("7. 测试密钥轮换...")
    success = await rotate_api_keys(force=True)
    print(f"   轮换结果: {'成功' if success else '失败'}")
    
    # 再次获取统计
    stats = await get_key_statistics()
    print(f"   轮换后按状态统计: {stats['by_status']}")
    
    # 导出密钥信息
    print("8. 导出密钥信息...")
    export_data = await manager.export_keys()
    print(f"   导出密钥数: {export_data['total_keys']}")
    
    # 清理
    print("9. 清理测试密钥...")
    await manager.revoke_key(key_id1, "测试清理")
    await manager.revoke_key(key_id2, "测试清理")
    
    print("\n测试完成！")


if __name__ == "__main__":
    # 运行测试
    asyncio.run(test_key_rotation())