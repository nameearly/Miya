"""AI 请求队列管理服务 - 车站-列车模型"""

from __future__ import annotations

import asyncio
import logging
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine, Optional
from enum import Enum


logger = logging.getLogger(__name__)


class QueueLane(str, Enum):
    """队列通道类型"""

    SUPERADMIN = "superadmin"
    GROUP_SUPERADMIN = "group_superadmin"
    PRIVATE = "private"
    GROUP_MENTION = "group_mention"
    GROUP_NORMAL = "group_normal"
    BACKGROUND = "background"


LANE_PRIORITY = {
    QueueLane.SUPERADMIN: 0,
    QueueLane.GROUP_SUPERADMIN: 1,
    QueueLane.PRIVATE: 2,
    QueueLane.GROUP_MENTION: 3,
    QueueLane.GROUP_NORMAL: 4,
    QueueLane.BACKGROUND: 5,
}

LANE_DISPLAY_NAMES = {
    QueueLane.SUPERADMIN: "超级管理员私聊",
    QueueLane.GROUP_SUPERADMIN: "群聊超级管理员",
    QueueLane.PRIVATE: "普通私聊",
    QueueLane.GROUP_MENTION: "群聊被@",
    QueueLane.GROUP_NORMAL: "群聊普通",
    QueueLane.BACKGROUND: "后台请求",
}


@dataclass
class LaneQueue:
    """支持尾插与"插入第2位"的轻量队列"""

    _items: deque = field(default_factory=deque)

    def qsize(self) -> int:
        return len(self._items)

    def empty(self) -> bool:
        return not self._items

    async def put(self, item: dict) -> None:
        self._items.append(item)

    def put_nowait(self, item: dict) -> None:
        self._items.append(item)

    async def put_second(self, item: dict) -> None:
        if len(self._items) <= 1:
            self._items.append(item)
            return
        items = list(self._items)
        items.insert(1, item)
        self._items = deque(items)

    async def get(self) -> dict:
        return self._items.popleft()

    def get_nowait(self) -> dict:
        return self._items.popleft()

    def drain(self) -> list:
        items = list(self._items)
        self._items.clear()
        return items


@dataclass
class ModelQueue:
    """单个模型的优先队列组"""

    model_name: str
    superadmin_queue: LaneQueue = field(default_factory=LaneQueue)
    group_superadmin_queue: LaneQueue = field(default_factory=LaneQueue)
    private_queue: LaneQueue = field(default_factory=LaneQueue)
    group_mention_queue: LaneQueue = field(default_factory=LaneQueue)
    group_normal_queue: LaneQueue = field(default_factory=LaneQueue)
    background_queue: LaneQueue = field(default_factory=LaneQueue)

    def lane_queues(self) -> dict:
        return {
            QueueLane.SUPERADMIN: self.superadmin_queue,
            QueueLane.GROUP_SUPERADMIN: self.group_superadmin_queue,
            QueueLane.PRIVATE: self.private_queue,
            QueueLane.GROUP_MENTION: self.group_mention_queue,
            QueueLane.GROUP_NORMAL: self.group_normal_queue,
            QueueLane.BACKGROUND: self.background_queue,
        }

    def trim_normal_queue(self, max_size: int = 10, keep_latest: int = 2) -> None:
        """如果群聊普通队列超过max_size，仅保留最新的keep_latest个"""
        queue_size = self.group_normal_queue.qsize()
        if queue_size > max_size:
            logger.warning(
                f"[队列修剪][{self.model_name}] 群聊普通队列长度={queue_size} 超过阈值({max_size})，将丢弃旧请求"
            )
            latest_requests = self.group_normal_queue.drain()[-keep_latest:]
            for req in latest_requests:
                self.group_normal_queue.put_nowait(req)
            logger.info(
                f"[队列修剪][{self.model_name}] 修剪完成，保留最新={len(latest_requests)}"
            )


@dataclass
class QueueEnqueueReceipt:
    """入队回执"""

    model_name: str
    lane: str
    size: int
    estimated_wait_seconds: float


class QueueManager:
    """AI请求队列管理器 - 车站-列车模型

    特性:
    - 多模型隔离：每个AI模型拥有独立的请求队列组
    - 非阻塞发车：按配置节奏发车，即使前一个请求未完成
    - 优先级管理：四级优先级确保重要消息优先响应
    - 自动修剪：普通群聊队列超过阈值时自动丢弃旧请求
    """

    def __init__(
        self,
        dispatch_callback: Optional[Callable[..., Coroutine]] = None,
        default_interval: float = 1.0,
    ):
        self._model_queues: dict[str, ModelQueue] = {}
        self._dispatch_callback = dispatch_callback
        self._default_interval = default_interval
        self._model_intervals: dict[str, float] = {}
        self._running = False
        self._dispatch_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()

    def get_or_create_model_queue(self, model_name: str) -> ModelQueue:
        """获取或创建指定模型的队列组"""
        if model_name not in self._model_queues:
            self._model_queues[model_name] = ModelQueue(model_name=model_name)
            self._model_intervals[model_name] = self._default_interval
            logger.info(f"[队列管理] 创建新模型队列: {model_name}")
        return self._model_queues[model_name]

    def set_model_interval(self, model_name: str, interval: float) -> None:
        """设置模型的发车间隔（秒）"""
        self._model_intervals[model_name] = interval
        logger.info(f"[队列管理] 设置模型 {model_name} 发车间隔: {interval}s")

    async def enqueue(
        self,
        model_name: str,
        request_data: dict,
        lane: QueueLane,
    ) -> QueueEnqueueReceipt:
        """入队请求"""
        model_queue = self.get_or_create_model_queue(model_name)

        queue = model_queue.lane_queues().get(lane)
        if not queue:
            logger.warning(f"[队列管理] 未知通道: {lane}，使用普通私聊")
            queue = model_queue.private_queue

        request_data["_enqueued_at"] = time.time()
        request_data["_lane"] = lane.value

        await queue.put(request_data)

        if lane == QueueLane.GROUP_NORMAL:
            model_queue.trim_normal_queue()

        estimated_wait = queue.qsize() * self._model_intervals.get(
            model_name, self._default_interval
        )

        return QueueEnqueueReceipt(
            model_name=model_name,
            lane=lane.value,
            size=queue.qsize(),
            estimated_wait_seconds=estimated_wait,
        )

    def _get_next_request(
        self, model_queue: ModelQueue
    ) -> tuple[Optional[dict], Optional[QueueLane]]:
        """获取下一个应该处理的请求（按优先级）"""
        lanes_by_priority = sorted(QueueLane, key=lambda x: LANE_PRIORITY[x])

        for lane in lanes_by_priority:
            queue = model_queue.lane_queues().get(lane)
            if queue and not queue.empty():
                try:
                    request = queue.get_nowait()
                    return request, lane
                except IndexError:
                    continue

        return None, None

    async def _dispatch_loop(self) -> None:
        """分发循环 - 按模型节奏发车"""
        while self._running:
            for model_name, model_queue in list(self._model_queues.items()):
                request, lane = self._get_next_request(model_queue)

                if request and self._dispatch_callback:
                    try:
                        logger.info(
                            f"[队列分发] 模型={model_name} 通道={LANE_DISPLAY_NAMES.get(lane, lane)} "
                            f"队列长度={model_queue.lane_queues()[lane].qsize() + 1}"
                        )
                        asyncio.create_task(
                            self._dispatch_callback(model_name, request)
                        )
                    except Exception as e:
                        logger.exception(f"[队列分发] 处理请求失败: {e}")

            interval = self._default_interval
            await asyncio.sleep(interval)

    async def start(self) -> None:
        """启动队列调度"""
        if self._running:
            return

        self._running = True
        self._dispatch_task = asyncio.create_task(self._dispatch_loop())
        logger.info("[队列管理] 队列调度已启动")

    async def stop(self) -> None:
        """停止队列调度"""
        self._running = False
        if self._dispatch_task:
            self._dispatch_task.cancel()
            try:
                await self._dispatch_task
            except asyncio.CancelledError:
                pass
        logger.info("[队列管理] 队列调度已停止")

    def get_queue_stats(self) -> dict:
        """获取队列统计信息"""
        stats = {}
        for model_name, model_queue in self._model_queues.items():
            stats[model_name] = {
                lane.value: queue.qsize()
                for lane, queue in model_queue.lane_queues().items()
            }
        return stats

    def get_total_pending(self) -> int:
        """获取总待处理数"""
        total = 0
        for model_queue in self._model_queues.values():
            for queue in model_queue.lane_queues().values():
                total += queue.qsize()
        return total


_global_queue_manager: Optional[QueueManager] = None


def get_queue_manager() -> QueueManager:
    """获取全局队列管理器实例"""
    global _global_queue_manager
    if _global_queue_manager is None:
        _global_queue_manager = QueueManager()
    return _global_queue_manager


async def init_queue_manager(
    dispatch_callback: Optional[Callable] = None,
    default_interval: float = 1.0,
) -> QueueManager:
    """初始化全局队列管理器"""
    global _global_queue_manager
    _global_queue_manager = QueueManager(
        dispatch_callback=dispatch_callback,
        default_interval=default_interval,
    )
    await _global_queue_manager.start()
    return _global_queue_manager
