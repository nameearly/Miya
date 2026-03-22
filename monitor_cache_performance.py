#!/usr/bin/env python3
"""
缓存系统性能监控脚本

监控新缓存系统的性能，包括：
1. 读写性能
2. 内存使用
3. 命中率
4. 错误率
"""

import asyncio
import time
import logging
import statistics
from datetime import datetime
from typing import Dict, List, Any

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class CachePerformanceMonitor:
    """缓存性能监控器"""
    
    def __init__(self, cache_name: str = "performance_monitor"):
        self.cache_name = cache_name
        self.results = {
            "write_times": [],
            "read_times": [],
            "hit_rates": [],
            "memory_usage": [],
            "errors": []
        }
        
    async def test_write_performance(self, iterations: int = 1000) -> Dict[str, Any]:
        """测试写入性能"""
        from core.cache import get_cache
        
        cache = get_cache(f"{self.cache_name}_write")
        write_times = []
        
        for i in range(iterations):
            key = f"test_key_{i}"
            value = f"test_value_{i}" * 10  # 较大的值
            
            start_time = time.perf_counter()
            await cache.set(key, value, ttl=60)
            end_time = time.perf_counter()
            
            write_times.append(end_time - start_time)
            
            # 每100次输出一次进度
            if (i + 1) % 100 == 0:
                avg_time = statistics.mean(write_times[-100:])
                logger.info(f"写入进度: {i+1}/{iterations}, 最近100次平均: {avg_time*1000:.2f}ms")
        
        result = {
            "iterations": iterations,
            "total_time": sum(write_times),
            "avg_time": statistics.mean(write_times),
            "min_time": min(write_times),
            "max_time": max(write_times),
            "ops_per_sec": iterations / sum(write_times),
            "times": write_times
        }
        
        self.results["write_times"].extend(write_times)
        return result
    
    async def test_read_performance(self, iterations: int = 1000) -> Dict[str, Any]:
        """测试读取性能"""
        from core.cache import get_cache
        
        cache = get_cache(f"{self.cache_name}_read")
        read_times = []
        hits = 0
        misses = 0
        
        # 先写入一些数据
        for i in range(iterations):
            key = f"test_key_{i}"
            value = f"test_value_{i}"
            await cache.set(key, value, ttl=60)
        
        # 测试读取
        for i in range(iterations):
            key = f"test_key_{i}"
            
            start_time = time.perf_counter()
            value = await cache.get(key)
            end_time = time.perf_counter()
            
            read_times.append(end_time - start_time)
            
            if value is not None:
                hits += 1
            else:
                misses += 1
            
            # 每100次输出一次进度
            if (i + 1) % 100 == 0:
                avg_time = statistics.mean(read_times[-100:])
                hit_rate = hits / (hits + misses) * 100
                logger.info(f"读取进度: {i+1}/{iterations}, 最近100次平均: {avg_time*1000:.2f}ms, 命中率: {hit_rate:.1f}%")
        
        hit_rate = hits / (hits + misses) * 100 if (hits + misses) > 0 else 0
        
        result = {
            "iterations": iterations,
            "total_time": sum(read_times),
            "avg_time": statistics.mean(read_times),
            "min_time": min(read_times),
            "max_time": max(read_times),
            "ops_per_sec": iterations / sum(read_times),
            "hits": hits,
            "misses": misses,
            "hit_rate": hit_rate,
            "times": read_times
        }
        
        self.results["read_times"].extend(read_times)
        self.results["hit_rates"].append(hit_rate)
        return result
    
    async def test_memory_usage(self) -> Dict[str, Any]:
        """测试内存使用"""
        from core.cache import get_cache
        
        cache = get_cache(f"{self.cache_name}_memory")
        
        # 写入不同大小的数据
        sizes = [10, 100, 1000, 10000]
        memory_results = []
        
        for size in sizes:
            # 清理缓存
            await cache.clear()
            
            # 写入数据
            for i in range(size):
                key = f"key_{i}"
                value = {"data": "x" * 100, "index": i, "timestamp": time.time()}
                await cache.set(key, value, ttl=60)
            
            # 获取统计信息
            stats = cache.get_stats()
            memory_results.append({
                "items": size,
                "total_memory": stats["total_memory"],
                "memory_per_item": stats["total_memory"] / size if size > 0 else 0
            })
            
            logger.info(f"内存测试: {size} 个项目, 总内存: {stats['total_memory']} 字节, 平均: {stats['total_memory']/size:.1f} 字节/项目")
        
        result = {
            "tests": memory_results,
            "summary": {
                "avg_memory_per_item": statistics.mean([r["memory_per_item"] for r in memory_results])
            }
        }
        
        self.results["memory_usage"].extend(memory_results)
        return result
    
    async def test_concurrent_performance(self, concurrent_tasks: int = 10, iterations: int = 100) -> Dict[str, Any]:
        """测试并发性能"""
        from core.cache import get_cache
        
        cache = get_cache(f"{self.cache_name}_concurrent")
        
        async def worker(worker_id: int):
            """工作线程"""
            worker_times = []
            
            for i in range(iterations):
                key = f"worker_{worker_id}_key_{i}"
                value = f"worker_{worker_id}_value_{i}"
                
                # 写入
                start_time = time.perf_counter()
                await cache.set(key, value, ttl=60)
                
                # 读取
                await cache.get(key)
                end_time = time.perf_counter()
                
                worker_times.append(end_time - start_time)
            
            return worker_times
        
        # 创建并发任务
        tasks = [worker(i) for i in range(concurrent_tasks)]
        all_times = await asyncio.gather(*tasks)
        
        # 合并所有时间
        flat_times = [time for worker_times in all_times for time in worker_times]
        
        result = {
            "concurrent_tasks": concurrent_tasks,
            "iterations_per_task": iterations,
            "total_operations": concurrent_tasks * iterations,
            "total_time": sum(flat_times),
            "avg_time": statistics.mean(flat_times),
            "min_time": min(flat_times),
            "max_time": max(flat_times),
            "ops_per_sec": (concurrent_tasks * iterations) / sum(flat_times),
            "times": flat_times
        }
        
        return result
    
    def generate_report(self) -> Dict[str, Any]:
        """生成性能报告"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "cache_system": "弥娅统一缓存系统",
            "summary": {}
        }
        
        # 写入性能总结
        if self.results["write_times"]:
            report["write_performance"] = {
                "total_operations": len(self.results["write_times"]),
                "avg_time_ms": statistics.mean(self.results["write_times"]) * 1000,
                "min_time_ms": min(self.results["write_times"]) * 1000,
                "max_time_ms": max(self.results["write_times"]) * 1000,
                "ops_per_sec": len(self.results["write_times"]) / sum(self.results["write_times"])
            }
        
        # 读取性能总结
        if self.results["read_times"]:
            report["read_performance"] = {
                "total_operations": len(self.results["read_times"]),
                "avg_time_ms": statistics.mean(self.results["read_times"]) * 1000,
                "min_time_ms": min(self.results["read_times"]) * 1000,
                "max_time_ms": max(self.results["read_times"]) * 1000,
                "ops_per_sec": len(self.results["read_times"]) / sum(self.results["read_times"])
            }
        
        # 命中率总结
        if self.results["hit_rates"]:
            report["hit_rate"] = {
                "avg_hit_rate": statistics.mean(self.results["hit_rates"]),
                "min_hit_rate": min(self.results["hit_rates"]),
                "max_hit_rate": max(self.results["hit_rates"])
            }
        
        # 内存使用总结
        if self.results["memory_usage"]:
            memory_per_item = [r["memory_per_item"] for r in self.results["memory_usage"]]
            report["memory_usage"] = {
                "avg_memory_per_item": statistics.mean(memory_per_item),
                "min_memory_per_item": min(memory_per_item),
                "max_memory_per_item": max(memory_per_item)
            }
        
        return report
    
    def save_report(self, filename: str = "cache_performance_report.json"):
        """保存报告到文件"""
        import json
        
        report = self.generate_report()
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"性能报告已保存到: {filename}")
        return report


async def main():
    """主函数"""
    print("弥娅缓存系统性能监控")
    print("=" * 50)
    
    monitor = CachePerformanceMonitor()
    
    try:
        # 1. 测试写入性能
        print("\n1. 测试写入性能...")
        write_result = await monitor.test_write_performance(iterations=500)
        print(f"   写入性能: {write_result['ops_per_sec']:.2f} 操作/秒")
        print(f"   平均时间: {write_result['avg_time']*1000:.2f} 毫秒/操作")
        
        # 2. 测试读取性能
        print("\n2. 测试读取性能...")
        read_result = await monitor.test_read_performance(iterations=500)
        print(f"   读取性能: {read_result['ops_per_sec']:.2f} 操作/秒")
        print(f"   平均时间: {read_result['avg_time']*1000:.2f} 毫秒/操作")
        print(f"   命中率: {read_result['hit_rate']:.1f}%")
        
        # 3. 测试内存使用
        print("\n3. 测试内存使用...")
        memory_result = await monitor.test_memory_usage()
        avg_memory = memory_result["summary"]["avg_memory_per_item"]
        print(f"   平均每个项目内存使用: {avg_memory:.1f} 字节")
        
        # 4. 测试并发性能
        print("\n4. 测试并发性能...")
        concurrent_result = await monitor.test_concurrent_performance(concurrent_tasks=5, iterations=50)
        print(f"   并发性能: {concurrent_result['ops_per_sec']:.2f} 操作/秒")
        print(f"   {concurrent_result['concurrent_tasks']} 个并发任务，每个 {concurrent_result['iterations_per_task']} 次迭代")
        
        # 5. 生成报告
        print("\n5. 生成性能报告...")
        report = monitor.save_report()
        
        print("\n" + "=" * 50)
        print("性能监控完成！")
        print(f"报告已保存到: cache_performance_report.json")
        
        # 显示关键指标
        print("\n关键性能指标:")
        print(f"  • 写入速度: {write_result['ops_per_sec']:.0f} 操作/秒")
        print(f"  • 读取速度: {read_result['ops_per_sec']:.0f} 操作/秒")
        print(f"  • 缓存命中率: {read_result['hit_rate']:.1f}%")
        print(f"  • 并发性能: {concurrent_result['ops_per_sec']:.0f} 操作/秒")
        print(f"  • 内存效率: {avg_memory:.0f} 字节/项目")
        
    except Exception as e:
        logger.error(f"性能监控失败: {e}", exc_info=True)
        print(f"\n[ERROR] 性能监控失败: {e}")
        
        # 尝试生成部分报告
        try:
            report = monitor.save_report("cache_performance_partial_report.json")
            print(f"部分报告已保存到: cache_performance_partial_report.json")
        except:
            pass


if __name__ == "__main__":
    asyncio.run(main())
