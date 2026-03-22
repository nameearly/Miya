"""
统一连接池管理器 - 支持数据库和API连接复用

设计目标:
1. 统一管理各种类型的连接池
2. 支持连接复用和自动回收
3. 提供连接健康检查
4. 支持负载均衡和故障转移
5. 提供连接统计和监控
"""

import asyncio
import logging
import time
from typing import Any, Callable, Dict, List, Optional, Union, Type
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class ConnectionType(Enum):
    """连接类型"""
    DATABASE = "database"      # 数据库连接
    HTTP_API = "http_api"      # HTTP API连接
    WEBSOCKET = "websocket"    # WebSocket连接
    REDIS = "redis"           # Redis连接
    CUSTOM = "custom"         # 自定义连接


class ConnectionStatus(Enum):
    """连接状态"""
    HEALTHY = "healthy"       # 健康
    DEGRADED = "degraded"     # 降级
    UNHEALTHY = "unhealthy"   # 不健康
    CLOSED = "closed"         # 已关闭


@dataclass
class ConnectionConfig:
    """连接配置"""
    connection_type: ConnectionType
    connection_name: str
    max_connections: int = 10
    min_connections: int = 2
    connection_timeout: float = 5.0
    idle_timeout: float = 300.0  # 5分钟空闲超时
    max_lifetime: float = 3600.0  # 1小时最大生命周期
    health_check_interval: float = 30.0
    retry_count: int = 3
    retry_delay: float = 1.0
    enable_load_balancing: bool = False
    endpoints: List[str] = field(default_factory=list)  # 多端点支持


@dataclass
class ConnectionStats:
    """连接统计"""
    total_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    failed_connections: int = 0
    connection_hits: int = 0
    connection_misses: int = 0
    avg_response_time: float = 0.0
    last_health_check: float = 0.0
    status: ConnectionStatus = ConnectionStatus.HEALTHY


@dataclass
class ConnectionInfo:
    """连接信息"""
    connection_id: str
    connection_type: ConnectionType
    endpoint: str
    created_at: float
    last_used_at: float
    usage_count: int = 0
    status: ConnectionStatus = ConnectionStatus.HEALTHY
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseConnection(ABC):
    """基础连接抽象类"""
    
    def __init__(self, connection_id: str, endpoint: str):
        self.connection_id = connection_id
        self.endpoint = endpoint
        self.created_at = time.time()
        self.last_used_at = time.time()
        self.usage_count = 0
        self.status = ConnectionStatus.HEALTHY
    
    @abstractmethod
    async def connect(self) -> bool:
        """建立连接"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """断开连接"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """健康检查"""
        pass
    
    def touch(self):
        """更新最后使用时间"""
        self.last_used_at = time.time()
        self.usage_count += 1
    
    @property
    def is_idle(self) -> bool:
        """是否空闲"""
        idle_time = time.time() - self.last_used_at
        return idle_time > 300  # 5分钟
    
    @property
    def is_expired(self) -> bool:
        """是否过期"""
        lifetime = time.time() - self.created_at
        return lifetime > 3600  # 1小时


class ConnectionPool:
    """连接池"""
    
    def __init__(
        self,
        config: ConnectionConfig,
        connection_factory: Callable[[str], BaseConnection]
    ):
        self.config = config
        self.connection_factory = connection_factory
        
        # 连接存储
        self._connections: Dict[str, BaseConnection] = {}  # 所有连接
        self._available_connections: List[BaseConnection] = []  # 可用连接
        self._busy_connections: Dict[str, BaseConnection] = {}  # 使用中的连接
        
        # 统计信息
        self.stats = ConnectionStats()
        
        # 锁
        self._lock = asyncio.Lock()
        
        # 健康检查任务
        self._health_check_task: Optional[asyncio.Task] = None
        
        logger.info(f"[连接池] 初始化: {config.connection_name}, type={config.connection_type.value}")
    
    async def initialize(self):
        """初始化连接池"""
        async with self._lock:
            # 创建最小连接数
            for i in range(self.config.min_connections):
                await self._create_connection()
            
            # 启动健康检查任务
            if self.config.health_check_interval > 0:
                self._start_health_check_task()
    
    async def _create_connection(self) -> Optional[BaseConnection]:
        """创建新连接"""
        try:
            # 选择端点（支持负载均衡）
            endpoint = self._select_endpoint()
            
            # 生成连接ID
            connection_id = f"{self.config.connection_name}_{len(self._connections)}_{int(time.time())}"
            
            # 创建连接
            connection = self.connection_factory(connection_id, endpoint)
            
            # 建立连接
            if await connection.connect():
                self._connections[connection_id] = connection
                self._available_connections.append(connection)
                
                self.stats.total_connections += 1
                self.stats.idle_connections += 1
                
                logger.debug(f"[连接池] 创建连接: {connection_id}, endpoint={endpoint}")
                return connection
            else:
                self.stats.failed_connections += 1
                logger.error(f"[连接池] 连接创建失败: {connection_id}")
                return None
                
        except Exception as e:
            self.stats.failed_connections += 1
            logger.error(f"[连接池] 连接创建异常: {e}")
            return None
    
    def _select_endpoint(self) -> str:
        """选择端点（支持负载均衡）"""
        if not self.config.endpoints:
            return "default"
        
        if self.config.enable_load_balancing and len(self.config.endpoints) > 1:
            # 简单的轮询负载均衡
            index = self.stats.total_connections % len(self.config.endpoints)
            return self.config.endpoints[index]
        else:
            return self.config.endpoints[0]
    
    async def acquire(self, timeout: Optional[float] = None) -> Optional[BaseConnection]:
        """获取连接"""
        start_time = time.time()
        
        while True:
            async with self._lock:
                # 检查是否有可用连接
                if self._available_connections:
                    connection = self._available_connections.pop()
                    self._busy_connections[connection.connection_id] = connection
                    
                    self.stats.idle_connections -= 1
                    self.stats.active_connections += 1
                    self.stats.connection_hits += 1
                    
                    connection.touch()
                    logger.debug(f"[连接池] 获取连接: {connection.connection_id}")
                    return connection
                
                # 检查是否可以创建新连接
                if len(self._connections) < self.config.max_connections:
                    connection = await self._create_connection()
                    if connection:
                        self._busy_connections[connection.connection_id] = connection
                        
                        self.stats.idle_connections -= 1
                        self.stats.active_connections += 1
                        self.stats.connection_misses += 1
                        
                        connection.touch()
                        logger.debug(f"[连接池] 创建并获取连接: {connection.connection_id}")
                        return connection
            
            # 检查超时
            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    self.stats.connection_misses += 1
                    logger.warning(f"[连接池] 获取连接超时: {self.config.connection_name}")
                    return None
            
            # 等待重试
            await asyncio.sleep(0.1)
    
    async def release(self, connection: BaseConnection):
        """释放连接"""
        async with self._lock:
            if connection.connection_id in self._busy_connections:
                del self._busy_connections[connection.connection_id]
                
                # 检查连接状态
                if connection.status == ConnectionStatus.HEALTHY:
                    self._available_connections.append(connection)
                    self.stats.idle_connections += 1
                else:
                    # 不健康的连接，关闭并移除
                    await self._close_connection(connection)
                
                self.stats.active_connections -= 1
                
                logger.debug(f"[连接池] 释放连接: {connection.connection_id}")
    
    async def _close_connection(self, connection: BaseConnection):
        """关闭连接"""
        try:
            await connection.disconnect()
            
            # 从所有列表中移除
            self._connections.pop(connection.connection_id, None)
            
            # 从可用列表中移除
            if connection in self._available_connections:
                self._available_connections.remove(connection)
            
            self.stats.total_connections -= 1
            self.stats.idle_connections = max(0, self.stats.idle_connections - 1)
            
            logger.debug(f"[连接池] 关闭连接: {connection.connection_id}")
            
        except Exception as e:
            logger.error(f"[连接池] 关闭连接失败: {e}")
    
    def _start_health_check_task(self):
        """启动健康检查任务"""
        async def _health_check_loop():
            while True:
                try:
                    await asyncio.sleep(self.config.health_check_interval)
                    await self._perform_health_checks()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"[连接池] 健康检查任务异常: {e}")
                    await asyncio.sleep(5)  # 异常后等待5秒
        
        self._health_check_task = asyncio.create_task(_health_check_loop())
        logger.debug(f"[连接池] 启动健康检查任务: {self.config.connection_name}")
    
    async def _perform_health_checks(self):
        """执行健康检查"""
        async with self._lock:
            self.stats.last_health_check = time.time()
            
            connections_to_check = list(self._connections.values())
            
            for connection in connections_to_check:
                try:
                    is_healthy = await connection.health_check()
                    
                    if is_healthy:
                        connection.status = ConnectionStatus.HEALTHY
                    else:
                        connection.status = ConnectionStatus.UNHEALTHY
                        logger.warning(f"[连接池] 连接不健康: {connection.connection_id}")
                        
                        # 如果不健康的连接正在使用中，尝试替换
                        if connection.connection_id in self._busy_connections:
                            await self._replace_unhealthy_connection(connection)
                    
                except Exception as e:
                    logger.error(f"[连接池] 健康检查失败: {connection.connection_id}, error={e}")
                    connection.status = ConnectionStatus.UNHEALTHY
            
            # 清理过期连接
            await self._cleanup_expired_connections()
    
    async def _replace_unhealthy_connection(self, old_connection: BaseConnection):
        """替换不健康的连接"""
        try:
            # 创建新连接
            new_connection = await self._create_connection()
            if new_connection:
                # 转移繁忙状态
                self._busy_connections[new_connection.connection_id] = new_connection
                del self._busy_connections[old_connection.connection_id]
                
                # 关闭旧连接
                await self._close_connection(old_connection)
                
                logger.info(f"[连接池] 替换不健康连接: {old_connection.connection_id} -> {new_connection.connection_id}")
                
                return new_connection
        
        except Exception as e:
            logger.error(f"[连接池] 替换连接失败: {e}")
        
        return None
    
    async def _cleanup_expired_connections(self):
        """清理过期连接"""
        current_time = time.time()
        
        # 检查空闲连接
        idle_to_remove = []
        for connection in self._available_connections:
            # 检查空闲超时
            if current_time - connection.last_used_at > self.config.idle_timeout:
                idle_to_remove.append(connection)
            # 检查生命周期
            elif current_time - connection.created_at > self.config.max_lifetime:
                idle_to_remove.append(connection)
        
        # 移除过期连接
        for connection in idle_to_remove:
            await self._close_connection(connection)
            
            logger.debug(f"[连接池] 清理过期连接: {connection.connection_id}")
    
    async def shutdown(self):
        """关闭连接池"""
        async with self._lock:
            # 停止健康检查任务
            if self._health_check_task:
                self._health_check_task.cancel()
                try:
                    await self._health_check_task
                except asyncio.CancelledError:
                    pass
            
            # 关闭所有连接
            for connection in list(self._connections.values()):
                await self._close_connection(connection)
            
            logger.info(f"[连接池] 已关闭: {self.config.connection_name}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "connection_name": self.config.connection_name,
            "connection_type": self.config.connection_type.value,
            "total_connections": self.stats.total_connections,
            "active_connections": self.stats.active_connections,
            "idle_connections": self.stats.idle_connections,
            "failed_connections": self.stats.failed_connections,
            "connection_hits": self.stats.connection_hits,
            "connection_misses": self.stats.connection_misses,
            "hit_rate": (
                self.stats.connection_hits / 
                (self.stats.connection_hits + self.stats.connection_misses) 
                if (self.stats.connection_hits + self.stats.connection_misses) > 0 else 0
            ),
            "avg_response_time": self.stats.avg_response_time,
            "last_health_check": self.stats.last_health_check,
            "status": self.stats.status.value,
            "max_connections": self.config.max_connections,
            "endpoints": self.config.endpoints,
        }


class ConnectionPoolManager:
    """连接池管理器（单例）"""
    
    _instance = None
    _pools: Dict[str, ConnectionPool] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    async def register_pool(
        cls,
        config: ConnectionConfig,
        connection_factory: Callable[[str, str], BaseConnection]
    ) -> ConnectionPool:
        """注册连接池"""
        if config.connection_name in cls._pools:
            logger.warning(f"[连接池管理器] 连接池已存在: {config.connection_name}")
            return cls._pools[config.connection_name]
        
        pool = ConnectionPool(config, connection_factory)
        await pool.initialize()
        
        cls._pools[config.connection_name] = pool
        logger.info(f"[连接池管理器] 注册连接池: {config.connection_name}")
        
        return pool
    
    @classmethod
    async def get_pool(cls, pool_name: str) -> Optional[ConnectionPool]:
        """获取连接池"""
        return cls._pools.get(pool_name)
    
    @classmethod
    async def acquire_connection(
        cls,
        pool_name: str,
        timeout: Optional[float] = None
    ) -> Optional[BaseConnection]:
        """获取连接"""
        pool = cls._pools.get(pool_name)
        if not pool:
            logger.error(f"[连接池管理器] 连接池不存在: {pool_name}")
            return None
        
        return await pool.acquire(timeout)
    
    @classmethod
    async def release_connection(
        cls,
        pool_name: str,
        connection: BaseConnection
    ):
        """释放连接"""
        pool = cls._pools.get(pool_name)
        if pool:
            await pool.release(connection)
    
    @classmethod
    async def shutdown_all(cls):
        """关闭所有连接池"""
        logger.info("[连接池管理器] 开始关闭所有连接池")
        
        for pool_name, pool in cls._pools.items():
            try:
                await pool.shutdown()
                logger.info(f"[连接池管理器] 已关闭连接池: {pool_name}")
            except Exception as e:
                logger.error(f"[连接池管理器] 关闭连接池失败: {pool_name}, error={e}")
        
        cls._pools.clear()
        logger.info("[连接池管理器] 所有连接池已关闭")
    
    @classmethod
    def get_all_stats(cls) -> Dict[str, Dict[str, Any]]:
        """获取所有连接池统计"""
        return {
            pool_name: pool.get_stats()
            for pool_name, pool in cls._pools.items()
        }


# 上下文管理器支持
class ConnectionContext:
    """连接上下文管理器"""
    
    def __init__(self, pool_name: str, timeout: Optional[float] = None):
        self.pool_name = pool_name
        self.timeout = timeout
        self.connection: Optional[BaseConnection] = None
    
    async def __aenter__(self) -> BaseConnection:
        self.connection = await ConnectionPoolManager.acquire_connection(
            self.pool_name, self.timeout
        )
        if not self.connection:
            raise ConnectionError(f"无法从连接池 {self.pool_name} 获取连接")
        return self.connection
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.connection:
            await ConnectionPoolManager.release_connection(
                self.pool_name, self.connection
            )


# 便捷函数
async def get_connection(
    pool_name: str,
    timeout: Optional[float] = None
) -> ConnectionContext:
    """便捷函数：获取连接上下文"""
    return ConnectionContext(pool_name, timeout)


def get_pool_stats(pool_name: str) -> Optional[Dict[str, Any]]:
    """便捷函数：获取连接池统计"""
    pool = ConnectionPoolManager._pools.get(pool_name)
    if pool:
        return pool.get_stats()
    return None


def get_all_pools_stats() -> Dict[str, Dict[str, Any]]:
    """便捷函数：获取所有连接池统计"""
    return ConnectionPoolManager.get_all_stats()


async def shutdown_all_pools():
    """便捷函数：关闭所有连接池"""
    await ConnectionPoolManager.shutdown_all()