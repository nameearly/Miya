#!/usr/bin/env python3
"""
测试弥娅统一缓存系统

验证新缓存系统的功能和兼容性。
"""

import asyncio
import logging
from typing import Dict, Any

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_unified_cache() -> None:
    """测试统一缓存系统"""
    print("\n=== 测试统一缓存系统 ===")
    
    try:
        from core.cache import get_cache, unified_cache_get, unified_cache_set
        
        # 测试基本缓存
        cache = get_cache("test_cache")
        
        # 设置缓存
        await cache.set("test_key", "test_value", ttl=10)
        print("[OK] 缓存设置成功")
        
        # 获取缓存
        value = await cache.get("test_key")
        assert value == "test_value", f"缓存值不匹配: {value}"
        print("[OK] 缓存获取成功")
        
        # 测试统一接口
        await unified_cache_set("test_cache", "unified_key", "unified_value", ttl=10)
        unified_value = await unified_cache_get("test_cache", "unified_key")
        assert unified_value == "unified_value", f"统一接口值不匹配: {unified_value}"
        print("[OK] 统一接口测试成功")
        
        # 测试统计信息
        stats = cache.get_stats()
        print(f"✓ 缓存统计: {stats}")
        
        # 清理
        await cache.clear()
        print("✓ 缓存清理成功")
        
    except Exception as e:
        print(f"✗ 统一缓存测试失败: {e}")
        raise


async def test_cache_adapter() -> None:
    """测试缓存适配器（向后兼容性）"""
    print("\n=== 测试缓存适配器 ===")
    
    try:
        from core.cache import get_cache_manager, get_global_prompt_cache
        
        # 测试缓存管理器适配器
        cache_manager = get_cache_manager()
        
        # 设置缓存
        await cache_manager.set("adapter_key", "adapter_value", ttl=10)
        print("✓ 适配器缓存设置成功")
        
        # 获取缓存
        value = await cache_manager.get("adapter_key")
        assert value == "adapter_value", f"适配器缓存值不匹配: {value}"
        print("✓ 适配器缓存获取成功")
        
        # 测试统计信息
        stats = cache_manager.get_stats()
        print(f"✓ 适配器缓存统计: {stats}")
        
        # 测试提示词缓存适配器
        prompt_cache = get_global_prompt_cache()
        
        context = {"user": "test_user", "query": "test_query"}
        prompt_cache.set(context, "test_prompt")
        print("✓ 提示词缓存设置成功")
        
        prompt = prompt_cache.get(context)
        assert prompt == "test_prompt", f"提示词缓存值不匹配: {prompt}"
        print("✓ 提示词缓存获取成功")
        
        # 清理
        await cache_manager.clear()
        prompt_cache.clear()
        print("✓ 适配器缓存清理成功")
        
    except Exception as e:
        print(f"✗ 缓存适配器测试失败: {e}")
        raise


async def test_cache_decorator() -> None:
    """测试缓存装饰器"""
    print("\n=== 测试缓存装饰器 ===")
    
    try:
        from core.cache import cached, cached_decorator
        
        # 测试新的缓存装饰器
        call_count = 0
        
        @cached(cache_type="decorator_test", ttl=5)
        async def expensive_operation(param: str) -> str:
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.1)  # 模拟耗时操作
            return f"result_for_{param}"
        
        # 第一次调用应该执行函数
        result1 = await expensive_operation("test")
        assert result1 == "result_for_test"
        assert call_count == 1
        print("✓ 装饰器第一次调用成功")
        
        # 第二次调用应该从缓存获取
        result2 = await expensive_operation("test")
        assert result2 == "result_for_test"
        assert call_count == 1  # 调用次数不应增加
        print("✓ 装饰器缓存命中成功")
        
        # 测试兼容装饰器
        @cached_decorator(ttl=5)
        async def legacy_operation(param: str) -> str:
            return f"legacy_{param}"
        
        legacy_result = await legacy_operation("test")
        assert legacy_result == "legacy_test"
        print("✓ 兼容装饰器测试成功")
        
    except Exception as e:
        print(f"✗ 缓存装饰器测试失败: {e}")
        raise


async def test_config_cache() -> None:
    """测试配置缓存"""
    print("\n=== 测试配置缓存 ===")
    
    try:
        from core.cache import get_config_cache
        from pathlib import Path
        import tempfile
        import json
        
        # 创建临时配置文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_data = {"test": "value", "number": 42}
            json.dump(config_data, f)
            temp_file = Path(f.name)
        
        try:
            config_cache = get_config_cache()
            
            # 加载配置（应该从文件读取）
            config = await config_cache.load_config(temp_file)
            assert config["test"] == "value"
            assert config["number"] == 42
            print("✓ 配置加载成功")
            
            # 再次加载（应该从缓存读取）
            config2 = await config_cache.load_config(temp_file)
            assert config2 == config
            print("✓ 配置缓存命中成功")
            
            # 获取统计信息
            stats = config_cache.get_stats()
            print(f"✓ 配置缓存统计: {stats}")
            
            # 使缓存失效
            await config_cache.invalidate_config(temp_file)
            print("✓ 配置缓存失效成功")
            
        finally:
            # 清理临时文件
            temp_file.unlink(missing_ok=True)
            
    except Exception as e:
        print(f"✗ 配置缓存测试失败: {e}")
        raise


async def test_performance() -> None:
    """测试缓存性能"""
    print("\n=== 测试缓存性能 ===")
    
    try:
        from core.cache import get_cache
        import time
        
        cache = get_cache("performance_test")
        
        # 测试写入性能
        start_time = time.time()
        operations = 100
        
        for i in range(operations):
            await cache.set(f"key_{i}", f"value_{i}", ttl=30)
        
        write_time = time.time() - start_time
        write_ops_per_sec = operations / write_time
        print(f"✓ 写入性能: {write_ops_per_sec:.2f} 操作/秒")
        
        # 测试读取性能
        start_time = time.time()
        
        for i in range(operations):
            value = await cache.get(f"key_{i}")
            assert value == f"value_{i}"
        
        read_time = time.time() - start_time
        read_ops_per_sec = operations / read_time
        print(f"✓ 读取性能: {read_ops_per_sec:.2f} 操作/秒")
        
        # 清理
        await cache.clear()
        
    except Exception as e:
        print(f"✗ 性能测试失败: {e}")
        raise


async def main() -> None:
    """主测试函数"""
    print("开始测试弥娅统一缓存系统...")
    
    tests = [
        test_unified_cache,
        test_cache_adapter,
        test_cache_decorator,
        test_config_cache,
        test_performance,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            await test_func()
            passed += 1
        except Exception as e:
            logger.error(f"测试失败: {e}", exc_info=True)
            failed += 1
    
    print(f"\n=== 测试结果 ===")
    print(f"通过: {passed}")
    print(f"失败: {failed}")
    print(f"总计: {passed + failed}")
    
    if failed == 0:
        print("\n✅ 所有测试通过！弥娅缓存系统工作正常。")
    else:
        print(f"\n❌ {failed} 个测试失败，请检查日志。")
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())
