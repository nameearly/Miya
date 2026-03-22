#!/usr/bin/env python3
"""
简单测试弥娅统一缓存系统

验证新缓存系统的核心功能。
"""

import asyncio
import logging

# 配置日志
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_basic_cache() -> None:
    """测试基本缓存功能"""
    print("\n=== 测试基本缓存功能 ===")
    
    try:
        from core.cache import get_cache
        
        # 获取缓存实例
        cache = get_cache("test_basic")
        
        # 设置缓存
        await cache.set("test_key", "test_value", ttl=10)
        print("[OK] 缓存设置成功")
        
        # 获取缓存
        value = await cache.get("test_key")
        assert value == "test_value", f"缓存值不匹配: {value}"
        print("[OK] 缓存获取成功")
        
        # 测试统计信息
        stats = cache.get_stats()
        print(f"[OK] 缓存统计: {stats}")
        
        # 清理
        await cache.clear()
        print("[OK] 缓存清理成功")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] 基本缓存测试失败: {e}")
        return False


async def test_unified_interface() -> None:
    """测试统一接口"""
    print("\n=== 测试统一接口 ===")
    
    try:
        from core.cache import unified_cache_get, unified_cache_set
        
        # 测试统一接口
        await unified_cache_set("test_interface", "key1", "value1", ttl=10)
        print("[OK] 统一接口设置成功")
        
        value = await unified_cache_get("test_interface", "key1")
        assert value == "value1", f"统一接口值不匹配: {value}"
        print("[OK] 统一接口获取成功")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] 统一接口测试失败: {e}")
        return False


async def test_cache_decorator() -> None:
    """测试缓存装饰器"""
    print("\n=== 测试缓存装饰器 ===")
    
    try:
        from core.cache import cached
        
        call_count = 0
        
        @cached(cache_type="decorator_test", ttl=5)
        async def expensive_operation(param: str) -> str:
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.01)  # 模拟耗时操作
            return f"result_for_{param}"
        
        # 第一次调用应该执行函数
        result1 = await expensive_operation("test")
        assert result1 == "result_for_test"
        assert call_count == 1
        print("[OK] 装饰器第一次调用成功")
        
        # 第二次调用应该从缓存获取
        result2 = await expensive_operation("test")
        assert result2 == "result_for_test"
        assert call_count == 1  # 调用次数不应增加
        print("[OK] 装饰器缓存命中成功")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] 缓存装饰器测试失败: {e}")
        return False


async def main() -> None:
    """主测试函数"""
    print("开始测试弥娅统一缓存系统...")
    
    tests = [
        test_basic_cache,
        test_unified_interface,
        test_cache_decorator,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            success = await test_func()
            if success:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            logger.error(f"测试失败: {e}", exc_info=True)
            failed += 1
    
    print(f"\n=== 测试结果 ===")
    print(f"通过: {passed}")
    print(f"失败: {failed}")
    print(f"总计: {passed + failed}")
    
    if failed == 0:
        print("\n[SUCCESS] 所有测试通过！弥娅缓存系统工作正常。")
    else:
        print(f"\n[FAILURE] {failed} 个测试失败。")
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())
