# 弥娅缓存系统培训指南

## 培训概述

**培训对象**：弥娅系统开发团队成员
**培训目标**：掌握新统一缓存系统的使用和最佳实践
**培训时长**：1小时

## 第一部分：新缓存系统介绍

### 1.1 为什么需要统一缓存系统？

**旧系统问题**：
- 多个分散的缓存模块（cache_manager.py, prompt_cache.py）
- 接口不统一，学习成本高
- 维护困难，代码重复
- 性能不一致

**新系统优势**：
- ✅ 统一接口，易于使用
- ✅ 性能优化，速度更快
- ✅ 智能管理，自动清理
- ✅ 向后兼容，平滑迁移
- ✅ 监控统计，便于调试

### 1.2 新架构概览

```
core/cache/__init__.py          # 统一入口
├── core/unified_cache.py       # 核心实现
├── core/cache_adapter.py       # 向后兼容适配器
└── core/config_cache.py        # 配置专用缓存
```

## 第二部分：基本使用

### 2.1 导入方式

**推荐方式（新代码）**：
```python
# 基本缓存
from core.cache import get_cache

# 统一接口
from core.cache import unified_cache_get, unified_cache_set

# 缓存装饰器
from core.cache import cached
```

**兼容方式（旧代码迁移）**：
```python
# 使用适配器保持兼容
from core.cache import get_cache_manager, get_global_prompt_cache
from core.cache import cached_decorator
```

### 2.2 基本操作示例

#### 示例1：基本缓存操作
```python
import asyncio
from core.cache import get_cache

async def main():
    # 获取缓存实例
    cache = get_cache("user_data")
    
    # 设置缓存（带TTL）
    await cache.set("user:123", {"name": "Alice", "age": 30}, ttl=3600)
    
    # 获取缓存
    user_data = await cache.get("user:123")
    print(f"User data: {user_data}")
    
    # 获取统计信息
    stats = cache.get_stats()
    print(f"Cache stats: {stats}")
    
    # 清理缓存
    await cache.clear()

asyncio.run(main())
```

#### 示例2：使用装饰器
```python
from core.cache import cached
import asyncio

@cached(cache_type="api_cache", ttl=60, key_prefix="weather")
async def get_weather(city: str):
    # 模拟API调用
    await asyncio.sleep(1)
    return f"Weather in {city}: Sunny, 25°C"

async def main():
    # 第一次调用会执行函数并缓存结果
    weather1 = await get_weather("Beijing")
    print(weather1)
    
    # 第二次调用会直接从缓存获取
    weather2 = await get_weather("Beijing")
    print(weather2)

asyncio.run(main())
```

#### 示例3：统一接口
```python
from core.cache import unified_cache_get, unified_cache_set
import asyncio

async def main():
    # 设置缓存
    await unified_cache_set("my_cache", "key1", "value1", ttl=300)
    
    # 获取缓存
    value = await unified_cache_get("my_cache", "key1")
    print(f"Cached value: {value}")

asyncio.run(main())
```

## 第三部分：高级功能

### 3.1 缓存配置

```python
from core.cache import get_cache
from core.unified_cache import CacheConfig

# 自定义配置
config = CacheConfig(
    max_size=5000,           # 最大缓存条目数
    default_ttl=1800,        # 默认过期时间（秒）
    max_memory_mb=50,        # 最大内存使用（MB）
    enable_stats=True,       # 启用统计
    async_mode=True,         # 异步模式
    enable_persist=False,    # 是否持久化
    persist_dir="data/cache" # 持久化目录
)

# 使用自定义配置
cache = get_cache("custom_cache", config)
```

### 3.2 批量操作

```python
from core.cache import get_cache
import asyncio

async def main():
    cache = get_cache("batch_cache")
    
    # 批量设置
    items = {
        "key1": "value1",
        "key2": "value2",
        "key3": "value3",
    }
    
    for key, value in items.items():
        await cache.set(key, value, ttl=300)
    
    # 批量获取
    keys = ["key1", "key2", "key3", "key4"]
    for key in keys:
        value = await cache.get(key)
        print(f"{key}: {value}")

asyncio.run(main())
```

### 3.3 监控和调试

```python
from core.cache import get_cache

# 获取缓存实例
cache = get_cache("my_cache")

# 获取统计信息
stats = cache.get_stats()
print(f"缓存统计: {stats}")

# 检查缓存内容
keys = await cache.keys()
print(f"缓存键: {keys}")

# 清理过期条目
expired_count = await cache.cleanup()
print(f"清理了 {expired_count} 个过期条目")
```

## 第四部分：迁移指南

### 4.1 从旧系统迁移

#### 旧代码：
```python
from core.cache_manager import CacheManager
from core.prompt_cache import PromptCache, cached_prompt

cache_manager = CacheManager()
cached_value = cache_manager.get("key")
cache_manager.set("key", "value", ttl=3600)

prompt_cache = PromptCache()
prompt = prompt_cache.get(context)
prompt_cache.set(context, "prompt content")

@cached_prompt()
def generate_prompt(context):
    return prompt
```

#### 新代码：
```python
# 方式1：使用新缓存系统（推荐）
from core.cache import get_cache

cache = get_cache("my_cache")
await cache.set("key", "value", ttl=3600)
value = await cache.get("key")

# 方式2：使用适配器（保持兼容）
from core.cache import get_cache_manager, get_global_prompt_cache

cache_manager = get_cache_manager()
await cache_manager.set("key", "value", ttl=3600)
value = await cache_manager.get("key")

prompt_cache = get_global_prompt_cache()
prompt = prompt_cache.get(context)
prompt_cache.set(context, "prompt content")

# 使用新的缓存装饰器
from core.cache import cached

@cached(cache_type="memory", ttl=300)
async def generate_prompt(context):
    return prompt
```

### 4.2 常见迁移问题

#### 问题1：异步/同步
- 新系统默认使用异步操作
- 旧代码如果是同步的，可以使用适配器的同步模式

#### 问题2：键生成方式
- 新系统使用统一的键生成算法
- 如果旧代码有自定义键生成逻辑，需要调整

#### 问题3：配置差异
- 新系统的配置参数可能不同
- 参考 CacheConfig 类进行调整

## 第五部分：最佳实践

### 5.1 缓存策略

1. **合理设置TTL**
   - 频繁变化的数据：短TTL（60-300秒）
   - 稳定数据：长TTL（3600+秒）
   - 配置数据：很长TTL或不过期

2. **键命名规范**
   ```python
   # 好的键名
   "user:123:profile"
   "config:app:settings"
   "api:weather:beijing"
   
   # 避免的键名
   "key1"  # 太简单，容易冲突
   "data"  # 太通用
   ```

3. **内存管理**
   - 监控内存使用情况
   - 设置合理的 max_memory_mb
   - 定期清理不需要的缓存

### 5.2 性能优化

1. **使用批量操作**
   - 减少锁竞争
   - 提高吞吐量

2. **合理选择缓存类型**
   - 小数据：内存缓存
   - 大数据：考虑磁盘或Redis
   - 分布式：Redis缓存

3. **监控命中率**
   - 目标：80%+ 命中率
   - 低命中率需要调整缓存策略

### 5.3 错误处理

```python
from core.cache import get_cache
import logging

logger = logging.getLogger(__name__)

async def safe_cache_operation():
    try:
        cache = get_cache("safe_cache")
        value = await cache.get("key")
        if value is None:
            # 缓存未命中，从源获取
            value = await fetch_from_source()
            await cache.set("key", value, ttl=300)
        return value
    except Exception as e:
        logger.error(f"缓存操作失败: {e}")
        # 降级：直接返回源数据
        return await fetch_from_source()
```

## 第六部分：工具和资源

### 6.1 可用工具

1. **性能监控脚本**
   ```bash
   python monitor_cache_performance.py
   ```
   - 测试缓存性能
   - 生成性能报告

2. **代码审查工具**
   ```bash
   # 检查遗留的旧缓存导入
   grep -r "from core\\.cache_manager" --include="*.py" .
   grep -r "from core\\.prompt_cache" --include="*.py" .
   ```

3. **清理工具**
   - 已删除旧缓存模块
   - 自动检查遗留导入

### 6.2 文档资源

1. **迁移指南**：`CACHE_MIGRATION_GUIDE.md`
2. **性能报告**：`cache_performance_report.json`
3. **代码审查报告**：`CACHE_CODE_REVIEW_REPORT.md`
4. **升级总结**：`CACHE_SYSTEM_UPGRADE_SUMMARY.md`

### 6.3 技术支持

- **问题反馈**：团队内部沟通渠道
- **紧急修复**：联系核心开发人员
- **功能建议**：提交GitHub Issue

## 第七部分：实战练习

### 练习1：缓存用户数据

**任务**：
1. 创建一个缓存用户信息的函数
2. 使用缓存装饰器优化性能
3. 添加适当的错误处理

**参考代码**：
```python
from core.cache import cached
import asyncio

@cached(cache_type="user_data", ttl=300, key_prefix="user")
async def get_user_info(user_id: str):
    """获取用户信息（带缓存）"""
    # 模拟数据库查询
    await asyncio.sleep(0.5)
    return {
        "id": user_id,
        "name": f"User {user_id}",
        "email": f"user{user_id}@example.com"
    }

async def main():
    # 测试缓存效果
    import time
    
    start = time.time()
    user1 = await get_user_info("123")
    print(f"第一次获取: {time.time()-start:.3f}秒")
    
    start = time.time()
    user2 = await get_user_info("123")
    print(f"第二次获取（缓存）: {time.time()-start:.3f}秒")
    
    assert user1 == user2

asyncio.run(main())
```

### 练习2：配置缓存

**任务**：
1. 创建一个配置缓存系统
2. 支持配置热更新
3. 添加缓存失效机制

## 第八部分：考核要点

### 8.1 知识掌握程度

✅ **初级**：
- 了解新缓存系统的基本使用
- 能够进行简单的缓存操作
- 知道如何迁移旧代码

✅ **中级**：
- 掌握缓存配置和调优
- 能够设计合理的缓存策略
- 熟练使用缓存装饰器

✅ **高级**：
- 理解缓存系统内部原理
- 能够进行性能优化和问题排查
- 可以扩展缓存功能

### 8.2 实践能力评估

1. **代码质量**：
   - 是否正确使用缓存API
   - 是否有适当的错误处理
   - 是否遵循最佳实践

2. **性能意识**：
   - 是否考虑缓存命中率
   - 是否合理设置TTL
   - 是否监控内存使用

3. **问题解决**：
   - 能否诊断缓存相关问题
   - 能否优化缓存性能
   - 能否设计缓存方案

## 总结

### 关键要点

1. **统一接口**：所有缓存操作通过 `core/cache` 模块
2. **性能优异**：读取>100万操作/秒，写入>42万操作/秒
3. **向后兼容**：适配器支持旧代码平滑迁移
4. **智能管理**：自动TTL、LRU驱逐、内存监控
5. **易于监控**：完整的统计信息和调试工具

### 下一步行动

1. **个人学习**：完成实战练习
2. **项目应用**：在负责的模块中应用新缓存系统
3. **经验分享**：在团队内部分享使用经验
4. **持续优化**：根据实际使用情况调整缓存策略

---

**培训完成标志**：
- ✅ 阅读并理解本指南
- ✅ 完成实战练习
- ✅ 在实际项目中应用新缓存系统
- ✅ 通过团队内部知识分享

**最后更新**：2024年
**培训负责人**：弥娅系统开发团队
