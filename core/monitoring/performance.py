"""
性能监控模块
"""

import time
import functools
import logging
import asyncio
from typing import Callable, Any, Dict, List, Optional
from collections import deque
import statistics
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class PerformanceLevel(str, Enum):
    """性能等级"""
    OPTIMAL = "optimal"      # 最优：<100ms
    GOOD = "good"           # 良好：100ms-500ms
    WARNING = "warning"     # 警告：500ms-1000ms
    CRITICAL = "critical"   # 危险：>1000ms


@dataclass
class PerformanceMetric:
    """性能指标"""
    function_name: str
    call_count: int = 0
    total_time: float = 0.0
    success_count: int = 0
    error_count: int = 0
    durations: deque = field(default_factory=lambda: deque(maxlen=100))
    
    @property
    def average_time(self) -> float:
        """平均执行时间"""
        if self.call_count == 0:
            return 0.0
        return self.total_time / self.call_count
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        total = self.success_count + self.error_count
        if total == 0:
            return 0.0
        return self.success_count / total
    
    @property
    def percentile_95(self) -> float:
        """95%分位数"""
        if not self.durations:
            return 0.0
        sorted_durations = sorted(self.durations)
        index = int(len(sorted_durations) * 0.95)
        return sorted_durations[index]
    
    @property
    def level(self) -> PerformanceLevel:
        """性能等级"""
        avg = self.average_time
        if avg < 0.1:
            return PerformanceLevel.OPTIMAL
        elif avg < 0.5:
            return PerformanceLevel.GOOD
        elif avg < 1.0:
            return PerformanceLevel.WARNING
        else:
            return PerformanceLevel.CRITICAL


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, window_size: int = 100):
        self.metrics: Dict[str, PerformanceMetric] = {}
        self.window_size = window_size
        self._start_time = time.time()
    
    def record(self, func_name: str, duration: float, success: bool = True):
        """记录性能指标"""
        if func_name not in self.metrics:
            self.metrics[func_name] = PerformanceMetric(
                function_name=func_name,
                durations=deque(maxlen=self.window_size)
            )
        
        metric = self.metrics[func_name]
        metric.call_count += 1
        metric.total_time += duration
        metric.durations.append(duration)
        
        if success:
            metric.success_count += 1
        else:
            metric.error_count += 1
        
        # 根据性能等级记录日志
        level = metric.level
        if level == PerformanceLevel.CRITICAL:
            logger.warning(f"函数 {func_name} 执行时间过长: {duration:.3f}s")
        elif level == PerformanceLevel.WARNING and duration > 0.5:
            logger.info(f"函数 {func_name} 执行时间偏长: {duration:.3f}s")
    
    def get_stats(self, func_name: str) -> Optional[Dict[str, Any]]:
        """获取统计信息"""
        if func_name not in self.metrics:
            return None
        
        metric = self.metrics[func_name]
        return {
            'function': metric.function_name,
            'calls': metric.call_count,
            'average_time': metric.average_time,
            'total_time': metric.total_time,
            'success_rate': metric.success_rate,
            'percentile_95': metric.percentile_95,
            'level': metric.level.value,
            'error_count': metric.error_count
        }
    
    def get_slow_functions(self, threshold: float = 0.5) -> List[Dict[str, Any]]:
        """获取慢函数列表"""
        slow_functions = []
        
        for func_name in self.metrics:
            metric = self.metrics[func_name]
            if metric.average_time > threshold:
                slow_functions.append({
                    'function': func_name,
                    'average_time': metric.average_time,
                    'calls': metric.call_count,
                    'level': metric.level.value,
                    'percentile_95': metric.percentile_95
                })
        
        return sorted(slow_functions, key=lambda x: x['average_time'], reverse=True)
    
    def get_report(self) -> Dict[str, Any]:
        """获取完整报告"""
        report = {
            'uptime': time.time() - self._start_time,
            'total_functions': len(self.metrics),
            'total_calls': sum(m.call_count for m in self.metrics.values()),
            'metrics': {},
            'summary': {
                'optimal': 0,
                'good': 0,
                'warning': 0,
                'critical': 0
            }
        }
        
        for func_name, metric in self.metrics.items():
            report['metrics'][func_name] = self.get_stats(func_name)
            report['summary'][metric.level.value] += 1
        
        return report
    
    def reset(self):
        """重置监控器"""
        self.metrics.clear()
        self._start_time = time.time()


# 全局监控器实例
performance_monitor = PerformanceMonitor()


def monitor_performance(func):
    """性能监控装饰器"""
    
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        success = True
        
        try:
            result = await func(*args, **kwargs)
            return result
        except Exception:
            success = False
            raise
        finally:
            duration = time.time() - start_time
            performance_monitor.record(func.__name__, duration, success)
            
            # 如果超过1秒，记录详细日志
            if duration > 1.0:
                logger.debug(
                    f"慢函数执行详情: {func.__name__} "
                    f"耗时 {duration:.3f}s, "
                    f"参数: {args}, 关键字参数: {kwargs}"
                )
    
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        success = True
        
        try:
            result = func(*args, **kwargs)
            return result
        except Exception:
            success = False
            raise
        finally:
            duration = time.time() - start_time
            performance_monitor.record(func.__name__, duration, success)
            
            if duration > 1.0:
                logger.debug(
                    f"慢函数执行详情: {func.__name__} "
                    f"耗时 {duration:.3f}s, "
                    f"参数: {args}, 关键字参数: {kwargs}"
                )
    
    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper


def get_performance_report() -> Dict[str, Any]:
    """获取性能报告"""
    return performance_monitor.get_report()


def get_slow_functions_report(threshold: float = 0.5) -> str:
    """获取慢函数报告（字符串格式）"""
    slow_functions = performance_monitor.get_slow_functions(threshold)
    
    if not slow_functions:
        return "✅ 没有检测到慢函数"
    
    report_lines = ["⚠️  慢函数检测报告:"]
    report_lines.append("=" * 60)
    
    for i, func in enumerate(slow_functions, 1):
        report_lines.append(
            f"{i}. {func['function']}:\n"
            f"   平均耗时: {func['average_time']:.3f}s\n"
            f"   调用次数: {func['calls']}\n"
            f"   性能等级: {func['level']}\n"
            f"   95%分位数: {func['percentile_95']:.3f}s"
        )
        report_lines.append("-" * 40)
    
    report_lines.append("=" * 60)
    return "\n".join(report_lines)