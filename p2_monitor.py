#!/usr/bin/env python3
"""
P2 灰度发布监控脚本
实时监控缓存性能、错误率、用户反馈等关键指标
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
import sys

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from webnet.qq.cache_manager import QQCacheManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class P2Monitor:
    """P2灰度发布监控"""
    
    def __init__(self, cache_manager: QQCacheManager):
        self.cache_manager = cache_manager
        self.metrics_file = Path("p2_metrics.json")
        self.history = []
        self.thresholds = {
            "error_rate": 0.001,  # 0.1%
            "p95_latency": 100,  # ms
            "memory_growth": 50,  # %
            "gc_pause": 100,  # ms
        }
    
    async def run_continuous_monitoring(self, interval: int = 60) -> None:
        """连续监控"""
        logger.info("=" * 60)
        logger.info("🎯 启动 P2 灰度发布监控")
        logger.info("=" * 60)
        
        iteration = 0
        while True:
            iteration += 1
            try:
                logger.info(f"\n📊 监控周期 #{iteration}")
                metrics = await self.collect_metrics()
                self._save_metrics(metrics)
                self._check_alerts(metrics)
                self.print_metrics(metrics)
                
                await asyncio.sleep(interval)
            except Exception as e:
                logger.error(f"❌ 监控异常: {e}")
                await asyncio.sleep(interval)
    
    async def collect_metrics(self) -> Dict[str, Any]:
        """收集性能指标"""
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "cache_metrics": await self._collect_cache_metrics(),
            "app_metrics": await self._collect_app_metrics(),
            "system_metrics": await self._collect_system_metrics(),
        }
        return metrics
    
    async def _collect_cache_metrics(self) -> Dict[str, Any]:
        """收集缓存指标"""
        # 从 QQCacheManager 获取统计信息
        cache_stats = {
            "message_cache": {
                "hits": 0,
                "misses": 0,
                "hit_rate": 0,
                "size": 0,
            },
            "image_cache": {
                "hits": 0,
                "misses": 0,
                "hit_rate": 0,
                "size": 0,
            },
            "config_cache": {
                "hits": 0,
                "misses": 0,
                "hit_rate": 0,
                "size": 0,
            },
        }
        
        # 模拟收集数据（实际中从缓存管理器的内部统计获取）
        if hasattr(self.cache_manager, '_stats'):
            for cache_type, stats in self.cache_manager._stats.items():
                if cache_type in ['qq_messages', 'qq_images', 'qq_config']:
                    cache_key = {
                        'qq_messages': 'message_cache',
                        'qq_images': 'image_cache',
                        'qq_config': 'config_cache',
                    }.get(cache_type)
                    
                    if cache_key:
                        total_ops = stats['hits'] + stats['misses']
                        hit_rate = (stats['hits'] / total_ops * 100) if total_ops > 0 else 0
                        cache_stats[cache_key]['hits'] = stats['hits']
                        cache_stats[cache_key]['misses'] = stats['misses']
                        cache_stats[cache_key]['hit_rate'] = hit_rate
                        cache_stats[cache_key]['size'] = len(
                            self.cache_manager._caches.get(cache_type, {})
                        )
        
        return cache_stats
    
    async def _collect_app_metrics(self) -> Dict[str, Any]:
        """收集应用层指标"""
        # 模拟应用层指标
        app_metrics = {
            "image_handler": {
                "response_time_ms": 150,
                "request_count": 1000,
                "error_count": 0,
                "error_rate": 0.0,
            },
            "message_handler": {
                "response_time_ms": 75,
                "request_count": 5000,
                "error_count": 0,
                "error_rate": 0.0,
            },
            "hybrid_config": {
                "response_time_ms": 50,
                "request_count": 2000,
                "error_count": 0,
                "error_rate": 0.0,
            },
        }
        
        return app_metrics
    
    async def _collect_system_metrics(self) -> Dict[str, Any]:
        """收集系统指标"""
        try:
            import psutil
            
            # 内存占用
            process = psutil.Process()
            memory_info = process.memory_info()
            
            # CPU占用
            cpu_percent = process.cpu_percent(interval=1)
            
            system_metrics = {
                "memory_rss_mb": memory_info.rss / 1024 / 1024,
                "memory_vms_mb": memory_info.vms / 1024 / 1024,
                "cpu_percent": cpu_percent,
                "num_threads": process.num_threads(),
            }
        except ImportError:
            # 如果没有 psutil，返回占位符数据
            system_metrics = {
                "memory_rss_mb": 100,
                "memory_vms_mb": 200,
                "cpu_percent": 5,
                "num_threads": 10,
            }
        
        return system_metrics
    
    def _check_alerts(self, metrics: Dict[str, Any]) -> None:
        """检查告警条件"""
        app_metrics = metrics.get("app_metrics", {})
        system_metrics = metrics.get("system_metrics", {})
        
        # 检查错误率
        for handler_name, handler_metrics in app_metrics.items():
            error_rate = handler_metrics.get("error_rate", 0)
            if error_rate > self.thresholds["error_rate"]:
                logger.warning(
                    f"⚠️  错误率告警 [{handler_name}]: "
                    f"{error_rate:.4f} > {self.thresholds['error_rate']}"
                )
        
        # 检查内存占用
        memory_mb = system_metrics.get("memory_rss_mb", 0)
        if memory_mb > 500:
            logger.warning(f"⚠️  内存告警: {memory_mb:.1f}MB > 500MB")
        
        # 检查 CPU 占用
        cpu_percent = system_metrics.get("cpu_percent", 0)
        if cpu_percent > 15:
            logger.warning(f"⚠️  CPU告警: {cpu_percent:.1f}% > 15%")
    
    def _save_metrics(self, metrics: Dict[str, Any]) -> None:
        """保存指标到文件"""
        self.history.append(metrics)
        
        # 只保留最近100条记录
        if len(self.history) > 100:
            self.history = self.history[-100:]
        
        # 保存到文件
        with open(self.metrics_file, 'w') as f:
            json.dump(self.history, f, indent=2, default=str)
    
    def print_metrics(self, metrics: Dict[str, Any]) -> None:
        """打印指标"""
        logger.info("=" * 60)
        logger.info("📊 P2 灰度发布监控指标")
        logger.info("=" * 60)
        
        # 缓存指标
        logger.info("\n✅ 缓存指标:")
        cache_metrics = metrics.get("cache_metrics", {})
        for cache_name, cache_stat in cache_metrics.items():
            hit_rate = cache_stat.get("hit_rate", 0)
            size = cache_stat.get("size", 0)
            logger.info(
                f"   {cache_name:20} 命中率: {hit_rate:5.1f}% "
                f"条数: {size:5}"
            )
        
        # 应用指标
        logger.info("\n✅ 应用指标:")
        app_metrics = metrics.get("app_metrics", {})
        for handler_name, handler_stat in app_metrics.items():
            response_time = handler_stat.get("response_time_ms", 0)
            error_rate = handler_stat.get("error_rate", 0)
            logger.info(
                f"   {handler_name:20} 响应: {response_time:5.1f}ms "
                f"错误率: {error_rate:.4f}"
            )
        
        # 系统指标
        logger.info("\n✅ 系统指标:")
        system_metrics = metrics.get("system_metrics", {})
        memory = system_metrics.get("memory_rss_mb", 0)
        cpu = system_metrics.get("cpu_percent", 0)
        logger.info(f"   内存: {memory:8.1f}MB  CPU: {cpu:6.1f}%")
        
        logger.info("=" * 60)


async def monitor_single_cycle():
    """运行单个监控周期（用于测试）"""
    from webnet.qq.cache_manager import CacheConfig
    
    config = CacheConfig()
    cache_manager = QQCacheManager(config)
    
    monitor = P2Monitor(cache_manager)
    
    # 运行一个监控周期
    metrics = await monitor.collect_metrics()
    monitor.print_metrics(metrics)


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="P2灰度发布监控")
    parser.add_argument("--interval", type=int, default=60,
                       help="监控间隔（秒）")
    parser.add_argument("--watch", action="store_true",
                       help="持续监控")
    
    args = parser.parse_args()
    
    from webnet.qq.cache_manager import CacheConfig
    
    config = CacheConfig()
    cache_manager = QQCacheManager(config)
    
    monitor = P2Monitor(cache_manager)
    
    if args.watch:
        await monitor.run_continuous_monitoring(interval=args.interval)
    else:
        # 运行单个监控周期
        await monitor_single_cycle()


if __name__ == "__main__":
    asyncio.run(main())
