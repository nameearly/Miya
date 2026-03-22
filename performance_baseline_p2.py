#!/usr/bin/env python3
"""
P2 性能基准测试脚本
在生产级数据上验证 P1 迁移的性能表现
"""

import asyncio
import time
import random
import logging
from datetime import datetime
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, field
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from webnet.qq.cache_manager import QQCacheManager, CacheConfig

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """基准测试结果"""
    test_name: str
    operation_count: int
    duration_seconds: float
    ops_per_second: float
    min_latency_ms: float = 0
    max_latency_ms: float = 0
    avg_latency_ms: float = 0
    p95_latency_ms: float = 0
    p99_latency_ms: float = 0
    errors: int = 0


class P2PerformanceBenchmark:
    """P2性能基准测试"""
    
    def __init__(self, cache_manager: QQCacheManager):
        self.cache_manager = cache_manager
        self.results: Dict[str, BenchmarkResult] = {}
        
    async def run_all_benchmarks(self, duration: int = 60, concurrency: int = 10) -> None:
        """运行所有基准测试"""
        logger.info("=" * 60)
        logger.info("🚀 P2 性能基准测试开始")
        logger.info("=" * 60)
        
        await self.benchmark_messages(duration, concurrency)
        await self.benchmark_images(duration, concurrency)
        await self.benchmark_config(duration, concurrency)
        await self.benchmark_users(duration, concurrency)
        
        self.print_results()
    
    async def benchmark_messages(self, duration: int, concurrency: int) -> None:
        """消息缓存基准测试"""
        logger.info("\n📊 测试 1: 消息缓存性能")
        logger.info("-" * 60)
        
        latencies = []
        operation_count = 0
        errors = 0
        
        async def write_message():
            nonlocal operation_count, errors
            try:
                chat_id = random.randint(1, 1000)
                message = {
                    "sender_id": random.randint(1, 10000),
                    "text": "test message content " * 10,
                    "timestamp": int(time.time()),
                }
                
                start = time.perf_counter()
                self.cache_manager.set_message_history(chat_id, [message])
                latency = (time.perf_counter() - start) * 1000
                latencies.append(latency)
                operation_count += 1
            except Exception as e:
                logger.error(f"消息写入错误: {e}")
                errors += 1
        
        async def read_message():
            nonlocal operation_count, errors
            try:
                chat_id = random.randint(1, 1000)
                start = time.perf_counter()
                self.cache_manager.get_message_history(chat_id)
                latency = (time.perf_counter() - start) * 1000
                latencies.append(latency)
                operation_count += 1
            except Exception as e:
                logger.error(f"消息读取错误: {e}")
                errors += 1
        
        # 写操作测试
        start_time = time.time()
        tasks = []
        for _ in range(concurrency):
            for _ in range(duration):
                tasks.append(write_message())
        
        await asyncio.gather(*tasks)
        write_duration = time.time() - start_time
        write_ops = operation_count
        write_latencies = latencies.copy()
        
        operation_count = 0
        latencies = []
        errors = 0
        
        # 读操作测试（先写入数据）
        for i in range(500):
            self.cache_manager.set_message_history(i, [{"text": f"msg {i}"}])
        
        start_time = time.time()
        tasks = []
        for _ in range(concurrency):
            for _ in range(duration):
                tasks.append(read_message())
        
        await asyncio.gather(*tasks)
        read_duration = time.time() - start_time
        read_ops = operation_count
        read_latencies = latencies.copy()
        
        # 输出结果
        write_result = self._calculate_stats(
            "消息写入", write_ops, write_duration, write_latencies
        )
        read_result = self._calculate_stats(
            "消息读取", read_ops, read_duration, read_latencies
        )
        
        self.results["message_write"] = write_result
        self.results["message_read"] = read_result
        self._print_result(write_result)
        self._print_result(read_result)
    
    async def benchmark_images(self, duration: int, concurrency: int) -> None:
        """图片缓存基准测试"""
        logger.info("\n🖼️  测试 2: 图片分析缓存性能")
        logger.info("-" * 60)
        
        latencies = []
        operation_count = 0
        errors = 0
        
        async def write_image():
            nonlocal operation_count, errors
            try:
                image_id = f"img_{random.randint(1, 10000)}"
                analysis = {
                    "objects": ["cat", "dog"],
                    "description": "test image analysis content",
                    "timestamp": int(time.time()),
                }
                
                start = time.perf_counter()
                self.cache_manager.set_image_analysis(image_id, analysis)
                latency = (time.perf_counter() - start) * 1000
                latencies.append(latency)
                operation_count += 1
            except Exception as e:
                logger.error(f"图片写入错误: {e}")
                errors += 1
        
        async def read_image():
            nonlocal operation_count, errors
            try:
                image_id = f"img_{random.randint(1, 10000)}"
                start = time.perf_counter()
                self.cache_manager.get_image_analysis(image_id)
                latency = (time.perf_counter() - start) * 1000
                latencies.append(latency)
                operation_count += 1
            except Exception as e:
                logger.error(f"图片读取错误: {e}")
                errors += 1
        
        # 写操作测试
        start_time = time.time()
        tasks = []
        for _ in range(concurrency):
            for _ in range(duration // 2):  # 图片操作少一些
                tasks.append(write_image())
        
        await asyncio.gather(*tasks)
        write_duration = time.time() - start_time
        write_ops = operation_count
        write_latencies = latencies.copy()
        
        operation_count = 0
        latencies = []
        errors = 0
        
        # 读操作测试
        start_time = time.time()
        tasks = []
        for _ in range(concurrency):
            for _ in range(duration // 2):
                tasks.append(read_image())
        
        await asyncio.gather(*tasks)
        read_duration = time.time() - start_time
        read_ops = operation_count
        read_latencies = latencies.copy()
        
        # 输出结果
        write_result = self._calculate_stats(
            "图片写入", write_ops, write_duration, write_latencies
        )
        read_result = self._calculate_stats(
            "图片读取", read_ops, read_duration, read_latencies
        )
        
        self.results["image_write"] = write_result
        self.results["image_read"] = read_result
        self._print_result(write_result)
        self._print_result(read_result)
    
    async def benchmark_config(self, duration: int, concurrency: int) -> None:
        """配置缓存基准测试"""
        logger.info("\n⚙️  测试 3: 配置缓存性能")
        logger.info("-" * 60)
        
        latencies = []
        operation_count = 0
        errors = 0
        
        async def write_config():
            nonlocal operation_count, errors
            try:
                config_key = f"config_{random.randint(1, 100)}"
                config_value = {
                    "setting": random.choice(["enabled", "disabled"]),
                    "value": random.randint(1, 1000),
                    "timestamp": int(time.time()),
                }
                
                start = time.perf_counter()
                self.cache_manager.set_config(config_key, config_value)
                latency = (time.perf_counter() - start) * 1000
                latencies.append(latency)
                operation_count += 1
            except Exception as e:
                logger.error(f"配置写入错误: {e}")
                errors += 1
        
        async def read_config():
            nonlocal operation_count, errors
            try:
                config_key = f"config_{random.randint(1, 100)}"
                start = time.perf_counter()
                self.cache_manager.get_config(config_key)
                latency = (time.perf_counter() - start) * 1000
                latencies.append(latency)
                operation_count += 1
            except Exception as e:
                logger.error(f"配置读取错误: {e}")
                errors += 1
        
        # 写操作测试
        start_time = time.time()
        tasks = []
        for _ in range(concurrency):
            for _ in range(duration // 4):
                tasks.append(write_config())
        
        await asyncio.gather(*tasks)
        write_duration = time.time() - start_time
        write_ops = operation_count
        write_latencies = latencies.copy()
        
        operation_count = 0
        latencies = []
        errors = 0
        
        # 读操作测试
        start_time = time.time()
        tasks = []
        for _ in range(concurrency):
            for _ in range(duration // 4):
                tasks.append(read_config())
        
        await asyncio.gather(*tasks)
        read_duration = time.time() - start_time
        read_ops = operation_count
        read_latencies = latencies.copy()
        
        # 输出结果
        write_result = self._calculate_stats(
            "配置写入", write_ops, write_duration, write_latencies
        )
        read_result = self._calculate_stats(
            "配置读取", read_ops, read_duration, read_latencies
        )
        
        self.results["config_write"] = write_result
        self.results["config_read"] = read_result
        self._print_result(write_result)
        self._print_result(read_result)
    
    async def benchmark_users(self, duration: int, concurrency: int) -> None:
        """用户信息缓存基准测试"""
        logger.info("\n👤 测试 4: 用户信息缓存性能")
        logger.info("-" * 60)
        
        latencies = []
        operation_count = 0
        
        async def write_user():
            nonlocal operation_count
            try:
                user_id = random.randint(1, 10000)
                user_info = {
                    "nickname": f"user_{user_id}",
                    "level": random.randint(1, 100),
                    "timestamp": int(time.time()),
                }
                
                start = time.perf_counter()
                self.cache_manager.set_user_info(user_id, user_info)
                latency = (time.perf_counter() - start) * 1000
                latencies.append(latency)
                operation_count += 1
            except Exception as e:
                logger.error(f"用户写入错误: {e}")
        
        # 写操作测试
        start_time = time.time()
        tasks = []
        for _ in range(concurrency // 2):
            for _ in range(duration // 4):
                tasks.append(write_user())
        
        await asyncio.gather(*tasks)
        write_duration = time.time() - start_time
        write_ops = operation_count
        write_latencies = latencies.copy()
        
        # 输出结果
        write_result = self._calculate_stats(
            "用户写入", write_ops, write_duration, write_latencies
        )
        self.results["user_write"] = write_result
        self._print_result(write_result)
    
    def _calculate_stats(
        self,
        op_name: str,
        op_count: int,
        duration: float,
        latencies: List[float]
    ) -> BenchmarkResult:
        """计算统计信息"""
        if not latencies:
            latencies = [0]
        
        sorted_latencies = sorted(latencies)
        result = BenchmarkResult(
            test_name=op_name,
            operation_count=op_count,
            duration_seconds=duration,
            ops_per_second=op_count / duration if duration > 0 else 0,
            min_latency_ms=min(latencies),
            max_latency_ms=max(latencies),
            avg_latency_ms=sum(latencies) / len(latencies),
            p95_latency_ms=sorted_latencies[int(len(sorted_latencies) * 0.95)],
            p99_latency_ms=sorted_latencies[int(len(sorted_latencies) * 0.99)],
        )
        return result
    
    def _print_result(self, result: BenchmarkResult) -> None:
        """打印基准测试结果"""
        logger.info(f"   操作: {result.test_name}")
        logger.info(f"   总操作数: {result.operation_count:,}")
        logger.info(f"   总耗时: {result.duration_seconds:.2f}s")
        logger.info(f"   吞吐量: {result.ops_per_second:,.0f} ops/sec")
        logger.info(f"   最小延迟: {result.min_latency_ms:.3f}ms")
        logger.info(f"   最大延迟: {result.max_latency_ms:.3f}ms")
        logger.info(f"   平均延迟: {result.avg_latency_ms:.3f}ms")
        logger.info(f"   P95延迟: {result.p95_latency_ms:.3f}ms")
        logger.info(f"   P99延迟: {result.p99_latency_ms:.3f}ms")
    
    def print_results(self) -> None:
        """打印所有测试结果摘要"""
        logger.info("\n" + "=" * 60)
        logger.info("📋 P2 性能基准测试总结")
        logger.info("=" * 60)
        
        for test_name, result in self.results.items():
            logger.info(f"\n✅ {result.test_name}")
            logger.info(f"   吞吐量: {result.ops_per_second:,.0f} ops/sec")
            logger.info(f"   P95延迟: {result.p95_latency_ms:.3f}ms")
            logger.info(f"   平均延迟: {result.avg_latency_ms:.3f}ms")
        
        # 性能对标
        logger.info("\n" + "=" * 60)
        logger.info("📊 性能对标（与 P1 测试结果）")
        logger.info("=" * 60)
        
        p1_baseline = {
            "message_write": 1_424_018,
            "message_read": 1_883_218,
            "image_write": 1_000_669,
            "image_read": 1_995_862,
            "config_write": 1_000_550,
            "config_read": 1_988_764,
        }
        
        for test_name, baseline in p1_baseline.items():
            if test_name in self.results:
                result = self.results[test_name]
                percentage = (result.ops_per_second / baseline) * 100
                status = "✅" if percentage >= 95 else "⚠️"
                logger.info(f"{status} {result.test_name:15} {percentage:.1f}% of P1 baseline")
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ P2 性能基准测试完成")
        logger.info("=" * 60)


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="P2 性能基准测试")
    parser.add_argument("--duration", type=int, default=10,
                       help="测试持续时间（秒）")
    parser.add_argument("--concurrency", type=int, default=5,
                       help="并发数")
    
    args = parser.parse_args()
    
    # 创建缓存管理器
    config = CacheConfig()
    cache_manager = QQCacheManager(config)
    
    # 运行基准测试
    benchmark = P2PerformanceBenchmark(cache_manager)
    await benchmark.run_all_benchmarks(duration=args.duration, concurrency=args.concurrency)


if __name__ == "__main__":
    asyncio.run(main())
