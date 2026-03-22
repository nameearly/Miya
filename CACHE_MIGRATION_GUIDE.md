# 弥娅缓存系统迁移指南

## 概述

弥娅系统已从多个分散的缓存模块迁移到统一的缓存系统。本指南将帮助您从旧缓存系统迁移到新的统一缓存系统。

## 已废弃的模块

以下模块已废弃，请停止使用：

1. `core/cache_manager.py` - 旧的智能缓存管理系统
2. `core/prompt_cache.py` - 旧的提示词缓存系统

## 新的统一缓存系统

新的缓存系统位于 `core/cache` 模块中，提供统一的接口和更好的性能。

### 主要组件

1. **统一缓存接口** (`core/unified_cache.py`)
2. **缓存适配器** (`core/cache_adapter.py`) - 提供向后兼容性
3. **配置缓存** (`core/config_cache.py`) - 专门用于配置文件的缓存
4. **缓存模块** (`core/cache/__init__.py`) - 统一导出接口

## 迁移步骤

### 步骤1：更新导入语句

#### 旧代码：
```python
from core.cache_manager import CacheManager
from core.prompt_cache import PromptCache, cached_prompt
```

#### 新代码：
```python
# 方式1：使用统一缓存系统
from core.cache import (
    get_cache,
    cached,
    unified_cache_get,
    unified_cache_set,
)

# 方式2：使用适配器（保持兼容性）
from core.cache import (
    get_cache_manager,          # 替代 CacheManager
    get_global_prompt_cache,    # 替代 PromptCache
    cached_decorator,           # 替代 cached_prompt
)
```

### 步骤2：更新缓存使用方式

#### 旧代码：
```python
# 使用旧的CacheManager
cache_manager = CacheManager()
cached_value = cache_manager.get("key")
cache_manager.set("key", "value", ttl=3600)

# 使用旧的PromptCache
prompt_cache = PromptCache()
prompt = prompt_cache.get(context)
prompt_cache.set(context, "prompt content")
```

#### 新代码：
```python
# 方式1：使用统一缓存
from core.cache import get_cache

# 获取缓存实例
cache = get_cache("my_cache")

# 异步操作（推荐）
cached_value = await cache.get("key")
await cache.set("key", "value", ttl=3600)

# 方式2：使用统一接口
from core.cache import unified_cache_get, unified_cache_set

value = await unified_cache_get("cache_type", "key")
await unified_cache_set("cache_type", "key", "value", ttl=3600)

# 方式3：使用适配器（兼容旧代码）
from core.cache import get_cache_manager, get_global_prompt_cache

cache_manager = get_cache_manager()
cached_value = await cache_manager.get("key")
await cache_manager.set("key", "value", ttl=3600)

prompt_cache = get_global_prompt_cache()
prompt = prompt_cache.get(context)
prompt_cache.set(context, "prompt content")
```

### 步骤3：更新装饰器

#### 旧代码：
```python
from core.cache_manager import cached_decorator
from core.prompt_cache import cached_prompt

@cached_decorator(ttl=300)
def expensive_function(param):
    return result

@cached_prompt()
def generate_prompt(context):
    return prompt
```

#### 新代码：
```python
from core.cache import cached, cached_decorator

# 使用新的统一缓存装饰器
@cached(cache_type="memory", ttl=300)
async def expensive_function(param):
    return result

# 使用适配器装饰器（保持兼容）
@cached_decorator(ttl=300)
def expensive_function(param):
    return result
```

### 步骤4：配置缓存

#### 旧代码：
```python
# 可能需要手动实现配置缓存
```

#### 新代码：
```python
from core.cache import get_config_cache, load_config_cached

# 加载配置（带缓存）
config = await load_config_cached("config.yaml")

# 或者直接使用配置缓存
config_cache = get_config_cache()
config = await config_cache.load_config("config.yaml")
```

## 新功能特性

### 1. 统一接口
- 所有缓存类型使用相同的API
- 支持同步和异步操作
- 自动类型转换

### 2. 智能管理
- 自动TTL过期
- LRU驱逐策略
- 内存使用监控
- 统计信息收集

### 3. 多级缓存
- 内存缓存（默认）
- 磁盘缓存（可选）
- Redis缓存（可选）
- 自定义后端支持

### 4. 高级功能
- 缓存预热
- 批量操作
- 持久化支持
- 监控和调试

## 示例代码

### 基本使用
```python
import asyncio
from core.cache import get_cache

async def main():
    # 获取缓存实例
    cache = get_cache("user_data")
    
    # 设置缓存
    await cache.set("user:123", {"name": "Alice", "age": 30}, ttl=3600)
    
    # 获取缓存
    user_data = await cache.get("user:123")
    print(f"User data: {user_data}")
    
    # 获取统计信息
    stats = cache.get_stats()
    print(f"Cache stats: {stats}")

asyncio.run(main())
```

### 装饰器缓存
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

### 批量操作
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

## 故障排除

### 常见问题

1. **导入错误**：确保使用正确的导入路径 `from core.cache import ...`
2. **异步问题**：新的缓存系统默认使用异步操作，确保在async函数中使用
3. **兼容性问题**：如果遇到兼容性问题，可以使用适配器接口 `get_cache_manager()`

### 调试

```python
from core.cache import get_cache

# 获取缓存统计
cache = get_cache("my_cache")
stats = cache.get_stats()
print(f"Cache statistics: {stats}")

# 检查缓存内容
keys = await cache.keys()
print(f"Cache keys: {keys}")

# 清理缓存
await cache.clear()
print("Cache cleared")
```

## 性能优化建议

1. **合理设置TTL**：根据数据更新频率设置合适的过期时间
2. **使用键前缀**：避免键冲突，便于管理和清理
3. **监控内存使用**：定期检查缓存统计，避免内存泄漏
4. **批量操作**：尽可能使用批量操作减少锁竞争
5. **选择合适的缓存类型**：根据数据特点选择内存、磁盘或混合缓存

## 向后兼容性

系统提供了完整的向后兼容性支持：

1. **适配器层**：`core/cache_adapter.py` 提供旧接口的适配
2. **兼容装饰器**：`cached_decorator` 保持与旧代码的兼容
3. **全局实例**：`get_cache_manager()` 和 `get_global_prompt_cache()` 提供全局访问

## 下一步

1. 更新所有导入旧缓存模块的代码
2. 测试新缓存系统的性能
3. 根据实际需求调整缓存配置
4. 监控缓存命中率和内存使用情况

## 支持

如有问题，请参考：
- 源代码：`core/cache/__init__.py`
- 统一缓存实现：`core/unified_cache.py`
- 适配器实现：`core/cache_adapter.py`
- 配置缓存：`core/config_cache.py`

或联系开发团队获取帮助。
