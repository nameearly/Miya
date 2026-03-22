"""
异步性能和并发处理优化模块
"""

import asyncio
import time
from typing import Any, Callable, List, Optional, TypeVar, Union
from functools import wraps
import logging
from dataclasses import dataclass, field
from collections import defaultdict
import threading
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import sys

logger = logging.getLogger(__name__)

T = TypeVar('T')
R = TypeVar('R')


@dataclass
class ConcurrencyConfig:
    """并发配置"""
    max_workers: int = 10
    thread_pool_size: int = 4
    process_pool_size: int = 2
    queue_size: int = 100
    timeout: float = 30.0
    retry_attempts: int = 3
    retry_delay: float = 1.0


@dataclass
class TaskMetrics:
    """任务指标"""
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    total_time: float = 0.0
    avg_time: float = 0.0
    peak_concurrent: int = 0


class AsyncOptimizer:
    """异步优化器"""
    
    def __init__(self, config: Optional[ConcurrencyConfig] = None):
        self.config = config or ConcurrencyConfig()
        self.metrics = TaskMetrics()
        self._active_tasks = 0
        self._peak_concurrent = 0
        self._lock = threading.Lock()
        self._thread_pool = ThreadPoolExecutor(
            max_workers=self.config.thread_pool_size,
            thread_name_prefix="miya_thread"
        )
        self._process_pool = ProcessPoolExecutor(
            max_workers=self.config.process_pool_size
        )
        
    async def execute_concurrent(
        self,
        tasks: List[Callable[..., Any]],
        *args,
        **kwargs
    ) -> List[Any]:
        """并发执行任务列表
        
        Args:
            tasks: 任务函数列表
            *args: 传递给所有任务的参数
            **kwargs: 传递给所有任务的关键字参数
            
        Returns:
            任务结果列表
        """
        self._update_metrics(len(tasks))
        
        semaphore = asyncio.Semaphore(self.config.max_workers)
        results = [None] * len(tasks)
        
        async def execute_with_semaphore(index: int, task: Callable):
            async with semaphore:
                try:
                    if asyncio.iscoroutinefunction(task):
                        result = await task(*args, **kwargs)
                    else:
                        # 在事件循环中运行同步函数
                        result = await asyncio.get_event_loop().run_in_executor(
                            None, task, *args, **kwargs
                        )
                    results[index] = result
                    self._record_success()
                except Exception as e:
                    results[index] = e
                    self._record_failure()
                    logger.error(f"任务 {index} 执行失败: {e}")
        
        # 创建并等待所有任务
        task_coros = [
            execute_with_semaphore(i, task)
            for i, task in enumerate(tasks)
        ]
        
        await asyncio.gather(*task_coros, return_exceptions=True)
        return results
    
    async def execute_batch(
        self,
        items: List[Any],
        process_func: Callable[[Any], Any],
        batch_size: int = 10
    ) -> List[Any]:
        """批量处理数据
        
        Args:
            items: 待处理的数据项列表
            process_func: 处理函数
            batch_size: 每批处理的数量
            
        Returns:
            处理结果列表
        """
        results = []
        total_batches = (len(items) + batch_size - 1) // batch_size
        
        for batch_idx in range(total_batches):
            start_idx = batch_idx * batch_size
            end_idx = min(start_idx + batch_size, len(items))
            batch = items[start_idx:end_idx]
            
            logger.info(f"处理批次 {batch_idx + 1}/{total_batches} ({len(batch)} 项)")
            
            # 并发处理批次内的项目
            batch_tasks = [
                lambda item=item: process_func(item)
                for item in batch
            ]
            
            batch_results = await self.execute_concurrent(batch_tasks)
            results.extend(batch_results)
            
            # 批次间延迟，避免过度并发
            if batch_idx < total_batches - 1:
                await asyncio.sleep(0.1)
        
        return results
    
    async def execute_with_retry(
        self,
        func: Callable[..., Any],
        *args,
        max_retries: Optional[int] = None,
        retry_delay: Optional[float] = None,
        **kwargs
    ) -> Any:
        """带重试的执行
        
        Args:
            func: 要执行的函数
            *args: 函数参数
            max_retries: 最大重试次数
            retry_delay: 重试延迟
            **kwargs: 函数关键字参数
            
        Returns:
            执行结果
        """
        max_retries = max_retries or self.config.retry_attempts
        retry_delay = retry_delay or self.config.retry_delay
        
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
                    
            except Exception as e:
                last_exception = e
                if attempt < max_retries:
                    wait_time = retry_delay * (2 ** attempt)  # 指数退避
                    logger.warning(
                        f"执行失败，第 {attempt + 1} 次重试，等待 {wait_time:.1f} 秒: {e}"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"执行失败，已达到最大重试次数 {max_retries}: {e}")
        
        raise last_exception
    
    async def execute_with_timeout(
        self,
        func: Callable[..., Any],
        timeout: float,
        *args,
        **kwargs
    ) -> Any:
        """带超时的执行
        
        Args:
            func: 要执行的函数
            timeout: 超时时间（秒）
            *args: 函数参数
            **kwargs: 函数关键字参数
            
        Returns:
            执行结果，如果超时则返回TimeoutError
        """
        try:
            if asyncio.iscoroutinefunction(func):
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=timeout
                )
            else:
                # 同步函数在单独的线程中执行
                loop = asyncio.get_event_loop()
                return await asyncio.wait_for(
                    loop.run_in_executor(None, func, *args, **kwargs),
                    timeout=timeout
                )
                
        except asyncio.TimeoutError:
            logger.error(f"执行超时 ({timeout} 秒)")
            raise TimeoutError(f"操作在 {timeout} 秒后超时")
    
    def run_in_thread(self, func: Callable[..., R], *args, **kwargs) -> R:
        """在线程池中运行函数
        
        Args:
            func: 要运行的函数
            *args: 函数参数
            **kwargs: 函数关键字参数
            
        Returns:
            执行结果
        """
        future = self._thread_pool.submit(func, *args, **kwargs)
        return future.result()
    
    async def run_in_process(self, func: Callable[..., R], *args, **kwargs) -> R:
        """在进程池中运行CPU密集型函数
        
        Args:
            func: 要运行的函数
            *args: 函数参数
            **kwargs: 函数关键字参数
            
        Returns:
            执行结果
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._process_pool, func, *args, **kwargs
        )
    
    def _update_metrics(self, new_tasks: int):
        """更新指标"""
        with self._lock:
            self.metrics.total_tasks += new_tasks
            self._active_tasks += new_tasks
            self._peak_concurrent = max(self._peak_concurrent, self._active_tasks)
    
    def _record_success(self):
        """记录成功"""
        with self._lock:
            self.metrics.completed_tasks += 1
            self._active_tasks -= 1
    
    def _record_failure(self):
        """记录失败"""
        with self._lock:
            self.metrics.failed_tasks += 1
            self._active_tasks -= 1
    
    def get_metrics(self) -> TaskMetrics:
        """获取当前指标"""
        with self._lock:
            if self.metrics.completed_tasks > 0:
                self.metrics.avg_time = self.metrics.total_time / self.metrics.completed_tasks
            self.metrics.peak_concurrent = self._peak_concurrent
            return self.metrics
    
    def reset_metrics(self):
        """重置指标"""
        with self._lock:
            self.metrics = TaskMetrics()
            self._active_tasks = 0
            self._peak_concurrent = 0
    
    def shutdown(self):
        """关闭优化器"""
        self._thread_pool.shutdown(wait=True)
        self._process_pool.shutdown(wait=True)


# 装饰器函数
def concurrent_execution(max_concurrent: int = 10):
    """并发执行装饰器
    
    Args:
        max_concurrent: 最大并发数
    """
    def decorator(func):
        semaphore = asyncio.Semaphore(max_concurrent)
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            async with semaphore:
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def with_timeout(timeout: float):
    """超时装饰器
    
    Args:
        timeout: 超时时间（秒）
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=timeout
            )
        return wrapper
    return decorator


def with_retry(max_retries: int = 3, retry_delay: float = 1.0):
    """重试装饰器
    
    Args:
        max_retries: 最大重试次数
        retry_delay: 重试延迟
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        wait_time = retry_delay * (2 ** attempt)  # 指数退避
                        logger.warning(
                            f"函数 {func.__name__} 执行失败，"
                            f"第 {attempt + 1} 次重试，等待 {wait_time:.1f} 秒"
                        )
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(
                            f"函数 {func.__name__} 执行失败，已达到最大重试次数"
                        )
            
            raise last_exception
        
        return wrapper
    return decorator


def track_performance(func):
    """性能跟踪装饰器"""
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            duration = time.time() - start_time
            logger.debug(f"函数 {func.__name__} 执行时间: {duration:.3f}s")
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            duration = time.time() - start_time
            logger.debug(f"函数 {func.__name__} 执行时间: {duration:.3f}s")
    
    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper


# 全局优化器实例
_global_optimizer: Optional[AsyncOptimizer] = None


def get_optimizer() -> AsyncOptimizer:
    """获取全局优化器实例"""
    global _global_optimizer
    if _global_optimizer is None:
        _global_optimizer = AsyncOptimizer()
    return _global_optimizer


async def concurrent_map(
    items: List[Any],
    process_func: Callable[[Any], Any],
    max_concurrent: int = 10
) -> List[Any]:
    """并发映射处理
    
    Args:
        items: 待处理项列表
        process_func: 处理函数
        max_concurrent: 最大并发数
        
    Returns:
        处理结果列表
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    results = [None] * len(items)
    
    async def process_item(index: int, item: Any):
        async with semaphore:
            try:
                if asyncio.iscoroutinefunction(process_func):
                    result = await process_func(item)
                else:
                    result = process_func(item)
                results[index] = result
            except Exception as e:
                results[index] = e
                logger.error(f"处理项 {index} 失败: {e}")
    
    tasks = [process_item(i, item) for i, item in enumerate(items)]
    await asyncio.gather(*tasks, return_exceptions=True)
    
    return results


class RateLimiter:
    """速率限制器"""
    
    def __init__(self, rate_limit: float, burst_limit: int = 1):
        """
        Args:
            rate_limit: 每秒允许的请求数
            burst_limit: 突发请求限制
        """
        self.rate_limit = rate_limit
        self.burst_limit = burst_limit
        self.tokens = burst_limit
        self.last_update = time.time()
        self._lock = asyncio.Lock()
    
    async def acquire(self, tokens: int = 1):
        """获取令牌"""
        async with self._lock:
            now = time.time()
            elapsed = now - self.last_update
            
            # 添加新令牌
            self.tokens = min(
                self.burst_limit,
                self.tokens + elapsed * self.rate_limit
            )
            self.last_update = now
            
            # 检查是否有足够的令牌
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            
            # 计算需要等待的时间
            wait_time = (tokens - self.tokens) / self.rate_limit
            await asyncio.sleep(wait_time)
            
            # 更新令牌
            self.tokens = 0
            self.last_update = time.time() + wait_time
            return True


def rate_limited(rate_limit: float, burst_limit: int = 1):
    """速率限制装饰器"""
    limiter = RateLimiter(rate_limit, burst_limit)
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            await limiter.acquire()
            return await func(*args, **kwargs)
        return wrapper
    return decorator