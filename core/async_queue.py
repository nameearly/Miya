"""
高级异步队列系统 - 支持优先级、延迟和批量处理

设计目标:
1. 支持优先级队列
2. 支持延迟处理
3. 支持批量批处理
4. 提供背压控制
5. 支持持久化（可选）
"""

import asyncio
import heapq
import logging
import time
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

logger = logging.getLogger(__name__)


class QueuePriority(Enum):
    """队列优先级"""
    HIGH = 0      # 高优先级（立即处理）
    NORMAL = 1    # 正常优先级
    LOW = 2       # 低优先级
    BACKGROUND = 3  # 后台优先级


class QueueMode(Enum):
    """队列模式"""
    FIFO = "fifo"           # 先进先出
    PRIORITY = "priority"   # 优先级
    DELAY = "delay"         # 延迟处理


@dataclass(order=True)
class QueueItem:
    """队列项"""
    priority: int
    timestamp: float
    data: Any = field(compare=False)
    item_id: str = field(compare=False, default="")
    delay_until: float = 0.0
    callback: Optional[Callable] = field(compare=False, default=None)
    batch_key: Optional[str] = field(compare=False, default=None)
    
    @property
    def is_delayed(self) -> bool:
        """检查是否延迟"""
        return self.delay_until > time.time()
    
    @property
    def is_ready(self) -> bool:
        """检查是否就绪"""
        return not self.is_delayed


@dataclass
class BatchConfig:
    """批量配置"""
    max_batch_size: int = 100
    max_batch_delay: float = 1.0  # 秒
    min_batch_size: int = 10
    enable_auto_flush: bool = True


@dataclass
class QueueStats:
    """队列统计"""
    items_enqueued: int = 0
    items_dequeued: int = 0
    items_dropped: int = 0
    batches_processed: int = 0
    avg_queue_time: float = 0.0
    max_queue_size: int = 0
    current_queue_size: int = 0


class AsyncQueue:
    """高级异步队列"""
    
    def __init__(
        self,
        queue_name: str = "default",
        max_size: int = 10000,
        mode: QueueMode = QueueMode.FIFO,
        batch_config: Optional[BatchConfig] = None,
        enable_backpressure: bool = True,
        backpressure_threshold: float = 0.8
    ):
        self.queue_name = queue_name
        self.max_size = max_size
        self.mode = mode
        self.batch_config = batch_config or BatchConfig()
        self.enable_backpressure = enable_backpressure
        self.backpressure_threshold = backpressure_threshold
        
        # 队列存储
        self._queue: List[QueueItem] = []  # 使用heapq实现优先级队列
        self._item_counter = 0
        self._lock = asyncio.Lock()
        
        # 批量处理相关
        self._batch_groups: Dict[str, List[QueueItem]] = defaultdict(list)
        self._batch_timers: Dict[str, asyncio.Task] = {}
        
        # 消费者相关
        self._consumers: List[Callable] = []
        self._is_running = False
        self._process_task: Optional[asyncio.Task] = None
        
        # 统计
        self.stats = QueueStats()
        
        # 事件信号
        self._item_added = asyncio.Event()
        self._queue_empty = asyncio.Event()
        self._queue_empty.set()  # 初始为空
        
        logger.info(f"[异步队列] 初始化: {queue_name}, mode={mode.value}, max_size={max_size}")
    
    async def enqueue(
        self,
        data: Any,
        priority: Union[QueuePriority, int] = QueuePriority.NORMAL,
        delay_seconds: float = 0.0,
        callback: Optional[Callable] = None,
        batch_key: Optional[str] = None,
        item_id: Optional[str] = None
    ) -> bool:
        """入队"""
        async with self._lock:
            # 检查背压
            if self.enable_backpressure:
                current_load = len(self._queue) / self.max_size
                if current_load > self.backpressure_threshold:
                    self.stats.items_dropped += 1
                    logger.warning(f"[异步队列] {self.queue_name} 背压过高，丢弃项")
                    return False
            
            # 生成项ID
            if item_id is None:
                self._item_counter += 1
                item_id = f"{self.queue_name}_{self._item_counter}_{int(time.time() * 1000)}"
            
            # 转换优先级
            if isinstance(priority, QueuePriority):
                priority_value = priority.value
            else:
                priority_value = int(priority)
            
            # 计算延迟时间
            delay_until = 0.0
            if delay_seconds > 0:
                delay_until = time.time() + delay_seconds
            
            # 创建队列项
            item = QueueItem(
                priority=priority_value,
                timestamp=time.time(),
                delay_until=delay_until,
                data=data,
                item_id=item_id,
                callback=callback,
                batch_key=batch_key
            )
            
            # 根据模式入队
            if self.mode == QueueMode.PRIORITY:
                heapq.heappush(self._queue, item)
            elif self.mode == QueueMode.DELAY:
                # 延迟队列：按延迟时间排序
                heapq.heappush(self._queue, item)
            else:  # FIFO
                # FIFO：按时间戳排序
                heapq.heappush(self._queue, item)
            
            # 批量处理逻辑
            if batch_key and self.batch_config.enable_auto_flush:
                await self._handle_batch_enqueue(item, batch_key)
            
            # 更新统计
            self.stats.items_enqueued += 1
            self.stats.current_queue_size = len(self._queue)
            self.stats.max_queue_size = max(self.stats.max_queue_size, self.stats.current_queue_size)
            
            # 触发事件
            self._item_added.set()
            self._queue_empty.clear()
            
            logger.debug(f"[异步队列] {self.queue_name} 入队: {item_id}, priority={priority_value}")
            
            return True
    
    async def dequeue(
        self,
        timeout: Optional[float] = None,
        batch_size: int = 1
    ) -> Union[Optional[QueueItem], List[QueueItem]]:
        """出队"""
        if batch_size > 1:
            return await self._dequeue_batch(batch_size, timeout)
        
        try:
            # 等待项可用
            if timeout:
                await asyncio.wait_for(self._item_added.wait(), timeout)
            else:
                await self._item_added.wait()
        except asyncio.TimeoutError:
            return None
        
        try:
            async with self._lock:
                if not self._queue:
                    self._item_added.clear()
                    self._queue_empty.set()
                    return None
                
                # 获取下一个项
                if self.mode == QueueMode.PRIORITY or self.mode == QueueMode.DELAY:
                    item = heapq.heappop(self._queue)
                else:  # FIFO
                    # 需要找到时间戳最小的项
                    item = heapq.heappop(self._queue)
                
                # 检查延迟项
                if item.is_delayed:
                    # 重新入队并等待
                    heapq.heappush(self._queue, item)
                    
                    # 计算等待时间
                    wait_time = item.delay_until - time.time()
                    if wait_time > 0:
                        await asyncio.sleep(wait_time)
                        # 重新尝试
                        return await self.dequeue(timeout, batch_size)
                    else:
                        # 重新出队
                        heapq.heappop(self._queue)
                
                # 更新统计
                self.stats.items_dequeued += 1
                self.stats.current_queue_size = len(self._queue)
                
                # 更新队列时间统计
                queue_time = time.time() - item.timestamp
                if self.stats.avg_queue_time == 0.0:
                    self.stats.avg_queue_time = queue_time
                else:
                    self.stats.avg_queue_time = (
                        self.stats.avg_queue_time * 0.9 + queue_time * 0.1
                    )
                
                # 检查队列是否为空
                if not self._queue:
                    self._item_added.clear()
                    self._queue_empty.set()
                
                logger.debug(f"[异步队列] {self.queue_name} 出队: {item.item_id}")
                
                return item
            
        except Exception as e:
            logger.error(f"[异步队列] {self.queue_name} 出队失败: {e}")
            return None
    
    async def _dequeue_batch(
        self,
        batch_size: int,
        timeout: Optional[float] = None
    ) -> List[QueueItem]:
        """批量出队"""
        batch_items = []
        start_time = time.time()
        
        while len(batch_items) < batch_size:
            time_remaining = None
            if timeout:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    break
                time_remaining = timeout - elapsed
            
            item = await self.dequeue(time_remaining)
            if item is None:
                break
            
            batch_items.append(item)
        
        if batch_items:
            self.stats.batches_processed += 1
            logger.debug(f"[异步队列] {self.queue_name} 批量出队: {len(batch_items)}项")
        
        return batch_items
    
    async def _handle_batch_enqueue(self, item: QueueItem, batch_key: str):
        """处理批量入队"""
        if not item.batch_key:
            return
        
        async with self._lock:
            # 添加到批处理组
            self._batch_groups[batch_key].append(item)
            
            group_size = len(self._batch_groups[batch_key])
            
            # 检查是否需要刷新
            if group_size >= self.batch_config.max_batch_size:
                await self._flush_batch(batch_key)
            else:
                # 启动/重置定时器
                await self._start_batch_timer(batch_key)
    
    async def _start_batch_timer(self, batch_key: str):
        """启动批处理定时器"""
        # 取消现有定时器
        if batch_key in self._batch_timers:
            task = self._batch_timers[batch_key]
            if not task.done():
                task.cancel()
        
        # 创建新定时器
        async def _batch_timer():
            try:
                await asyncio.sleep(self.batch_config.max_batch_delay)
                async with self._lock:
                    if batch_key in self._batch_groups:
                        group_size = len(self._batch_groups[batch_key])
                        if group_size >= self.batch_config.min_batch_size:
                            await self._flush_batch(batch_key)
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logger.error(f"[异步队列] 批处理定时器失败: {e}")
        
        self._batch_timers[batch_key] = asyncio.create_task(_batch_timer())
    
    async def _flush_batch(self, batch_key: str):
        """刷新批量数据"""
        if batch_key not in self._batch_groups:
            return
        
        items = self._batch_groups.pop(batch_key, [])
        
        # 取消定时器
        if batch_key in self._batch_timers:
            task = self._batch_timers.pop(batch_key)
            if not task.done():
                task.cancel()
        
        if not items:
            return
        
        # 处理批量项（这里可以根据需要实现具体的批量处理逻辑）
        logger.info(f"[异步队列] {self.queue_name} 批量刷新: {batch_key}, 大小={len(items)}")
        
        # 调用每个项的回调（如果存在）
        for item in items:
            if item.callback:
                try:
                    await item.callback(item.data)
                except Exception as e:
                    logger.error(f"[异步队列] 批量回调失败: {e}")
    
    def register_consumer(self, consumer: Callable):
        """注册消费者"""
        self._consumers.append(consumer)
        logger.debug(f"[异步队列] {self.queue_name} 注册消费者: {consumer.__name__}")
    
    async def start_processing(self):
        """启动队列处理"""
        if self._is_running:
            return
        
        self._is_running = True
        
        async def _process_loop():
            logger.info(f"[异步队列] {self.queue_name} 启动处理循环")
            
            while self._is_running:
                try:
                    # 获取项
                    item = await self.dequeue(timeout=1.0)
                    if item is None:
                        continue
                    
                    # 调用消费者
                    for consumer in self._consumers:
                        try:
                            if asyncio.iscoroutinefunction(consumer):
                                await consumer(item.data)
                            else:
                                # 在线程池中运行同步函数
                                loop = asyncio.get_event_loop()
                                await loop.run_in_executor(None, consumer, item.data)
                        except Exception as e:
                            logger.error(f"[异步队列] 消费者处理失败: {e}")
                    
                    # 调用项回调
                    if item.callback:
                        try:
                            if asyncio.iscoroutinefunction(item.callback):
                                await item.callback(item.data)
                            else:
                                loop = asyncio.get_event_loop()
                                await loop.run_in_executor(None, item.callback, item.data)
                        except Exception as e:
                            logger.error(f"[异步队列] 项回调失败: {e}")
                
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"[异步队列] 处理循环异常: {e}")
                    await asyncio.sleep(1.0)
        
        self._process_task = asyncio.create_task(_process_loop())
    
    async def stop_processing(self):
        """停止队列处理"""
        self._is_running = False
        
        if self._process_task:
            self._process_task.cancel()
            try:
                await self._process_task
            except asyncio.CancelledError:
                pass
        
        # 刷新所有批量数据
        for batch_key in list(self._batch_groups.keys()):
            await self._flush_batch(batch_key)
        
        logger.info(f"[异步队列] {self.queue_name} 处理已停止")
    
    async def clear(self):
        """清空队列"""
        async with self._lock:
            self._queue.clear()
            self._batch_groups.clear()
            
            # 取消所有定时器
            for task in self._batch_timers.values():
                if not task.done():
                    task.cancel()
            self._batch_timers.clear()
            
            self.stats.current_queue_size = 0
            self._item_added.clear()
            self._queue_empty.set()
            
            logger.info(f"[异步队列] {self.queue_name} 已清空")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取队列统计"""
        return {
            "queue_name": self.queue_name,
            "mode": self.mode.value,
            "max_size": self.max_size,
            "current_size": self.stats.current_queue_size,
            "max_size_reached": self.stats.max_queue_size,
            "items_enqueued": self.stats.items_enqueued,
            "items_dequeued": self.stats.items_dequeued,
            "items_dropped": self.stats.items_dropped,
            "batches_processed": self.stats.batches_processed,
            "avg_queue_time": self.stats.avg_queue_time,
            "consumers_count": len(self._consumers),
            "is_running": self._is_running,
            "backpressure_enabled": self.enable_backpressure,
            "batch_enabled": self.batch_config.enable_auto_flush,
        }


# 队列管理器
class QueueManager:
    """队列管理器（单例）"""
    
    _instance = None
    _queues: Dict[str, AsyncQueue] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def get_queue(
        cls,
        queue_name: str = "default",
        **kwargs
    ) -> AsyncQueue:
        """获取或创建队列"""
        if queue_name not in cls._queues:
            cls._queues[queue_name] = AsyncQueue(queue_name, **kwargs)
        
        return cls._queues[queue_name]
    
    @classmethod
    async def start_all(cls):
        """启动所有队列"""
        for queue in cls._queues.values():
            await queue.start_processing()
    
    @classmethod
    async def stop_all(cls):
        """停止所有队列"""
        for queue in cls._queues.values():
            await queue.stop_processing()
    
    @classmethod
    def get_all_stats(cls) -> Dict[str, Dict[str, Any]]:
        """获取所有队列统计"""
        return {
            name: queue.get_stats()
            for name, queue in cls._queues.items()
        }


# 便捷函数
def get_queue(queue_name: str = "default", **kwargs) -> AsyncQueue:
    """便捷函数：获取队列"""
    return QueueManager.get_queue(queue_name, **kwargs)


async def enqueue(
    data: Any,
    queue_name: str = "default",
    **kwargs
) -> bool:
    """便捷函数：入队"""
    queue = get_queue(queue_name)
    return await queue.enqueue(data, **kwargs)


def get_queue_stats(queue_name: str = "default") -> Dict[str, Any]:
    """便捷函数：获取队列统计"""
    queue = get_queue(queue_name)
    return queue.get_stats()