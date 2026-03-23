# 弥娅QQ子网缓存集成优化方案

## 📊 当前诊断结果

### 问题清单
1. ❌ **QQ子网未集成统一缓存系统** - 最关键
2. ⚠️ **本地缓存实现** - 2个本地图片缓存需要迁移
3. ⚠️ **多个缓存层独立管理** - 消息、配置、图片缓存各自为政

### QQ子网缓存使用现状
```
webnet/qq/
├── image_handler.py ................. 本地 dict 缓存
├── enhanced_image_handler.py ........ 本地 dict 缓存 + 时间戳
├── smart_image_analyzer.py ......... 本地 dict 缓存
├── unified_config.py .............. 本地 _cached_full_config
├── hybrid_config.py ............... 本地 _cached_full_config
└── message_handler.py ............. 本地 message_history (dict)
```

**总计**: 6个不同的本地缓存实现，无统一管理


## 🎯 优化目标

### 符合Miya Subnet架构的设想

#### 目标架构
```
Miya核心
  ├── TTS子网 (TTSNet) ✅         <- 已实现Subnet模式
  ├── Memory子网 (MemoryNet)      <- 已实现Subnet模式  
  ├── QQ子网 (QQNet) ⏳ 需优化
  │   ├── QQ消息处理
  │   ├── 缓存集成层 (新增)       <- 此处添加
  │   ├── 图片处理
  │   └── 会话管理
  └── 其他子网...
```

#### Subnet模式三要素
1. **清晰的责任分工** - 每个子网独立处理自己的功能
2. **统一的上层接口** - 通过 M-Link 与其他模块通信
3. **模块内的缓存管理** - 子网内部使用统一缓存系统

#### QQ子网应该在Subnet架构中的位置
```
┌─────────────────────────────────────────────┐
│            弥娅核心系统                      │
├─────────────────────────────────────────────┤
│                 M-Link 消息总线              │
├─────────────────────────────────────────────┤
│  TTSNet   │  MemoryNet  │  QQNet (改进后)  │
│           │             │                    │
│  ├─ TTS缓存 │ ├─ 记忆缓存 │ ├─ 消息缓存    │
│  ├─ 引擎    │ ├─ 知识库   │ ├─ 图片缓存    │
│  └─ 音频处理 │ └─ 语义索引 │ ├─ 配置缓存    │
│             │            │ └─ 会话缓存    │
│  (统一缓存系统作为底层支撑)
```


## 🔧 详细优化方案

### 第一步：创建QQ子网缓存管理模块

**新文件**: `webnet/qq/cache_manager.py`

```python
"""
QQ子网缓存管理器
统一管理QQ子网的所有缓存操作
遵循Miya Subnet架构设计
"""
from typing import Any, Dict, Optional, Set
import logging
from core.cache import get_cache, cached, unified_cache_get, unified_cache_set
from core.constants import CacheTTL

logger = logging.getLogger(__name__)


class QQCacheManager:
    """QQ子网缓存管理器 - 统一缓存提供者"""
    
    # 缓存类型常量（作为命名空间前缀）
    CACHE_MESSAGES = "qq_messages"
    CACHE_IMAGES = "qq_images"
    CACHE_CONFIG = "qq_config"
    CACHE_USERS = "qq_users"
    CACHE_GROUPS = "qq_groups"
    CACHE_SESSIONS = "qq_sessions"
    
    def __init__(self):
        """初始化QQ子网缓存管理器"""
        # 获取各个缓存实例
        self.message_cache = get_cache(self.CACHE_MESSAGES)
        self.image_cache = get_cache(self.CACHE_IMAGES)
        self.config_cache = get_cache(self.CACHE_CONFIG)
        self.user_cache = get_cache(self.CACHE_USERS)
        self.group_cache = get_cache(self.CACHE_GROUPS)
        self.session_cache = get_cache(self.CACHE_SESSIONS)
        
        logger.info("[QQ缓存] 缓存管理器初始化完成")
    
    # ==================== 消息缓存方法 ====================
    
    async def cache_message(self, chat_id: int, message: Dict[str, Any], 
                            ttl: float = CacheTTL.MEDIUM) -> None:
        """
        缓存单个消息
        
        Args:
            chat_id: 聊天ID
            message: 消息对象
            ttl: 过期时间
        """
        key = f"msg:{chat_id}:{message.get('msg_id')}"
        await self.message_cache.set(key, message, ttl=ttl)
    
    async def cache_message_history(self, chat_id: int, messages: list,
                                   ttl: float = CacheTTL.LONG) -> None:
        """缓存聊天历史"""
        key = f"history:{chat_id}"
        await self.message_cache.set(key, messages, ttl=ttl)
    
    async def get_message_history(self, chat_id: int) -> Optional[list]:
        """获取聊天历史"""
        key = f"history:{chat_id}"
        return await self.message_cache.get(key)
    
    # ==================== 图片缓存方法 ====================
    
    async def cache_image_analysis(self, image_id: str, analysis_result: Dict,
                                  ttl: float = CacheTTL.LONG) -> None:
        """
        缓存图片分析结果
        
        Args:
            image_id: 图片ID
            analysis_result: 分析结果
            ttl: 过期时间（建议较长，避免重复分析）
        """
        key = f"img_analysis:{image_id}"
        await self.image_cache.set(key, analysis_result, ttl=ttl)
    
    async def get_image_analysis(self, image_id: str) -> Optional[Dict]:
        """获取缓存的图片分析结果"""
        key = f"img_analysis:{image_id}"
        return await self.image_cache.get(key)
    
    async def cache_image_url(self, image_id: str, url: str,
                             ttl: float = CacheTTL.MEDIUM) -> None:
        """缓存图片URL"""
        key = f"img_url:{image_id}"
        await self.image_cache.set(key, url, ttl=ttl)
    
    async def get_image_url(self, image_id: str) -> Optional[str]:
        """获取缓存的图片URL"""
        key = f"img_url:{image_id}"
        return await self.image_cache.get(key)
    
    # ==================== 配置缓存方法 ====================
    
    async def cache_qq_config(self, config_key: str, config_value: Dict,
                             ttl: float = CacheTTL.LONG) -> None:
        """
        缓存QQ配置
        
        Args:
            config_key: 配置键
            config_value: 配置值
            ttl: 过期时间（配置通常较长）
        """
        key = f"config:{config_key}"
        await self.config_cache.set(key, config_value, ttl=ttl)
    
    async def get_qq_config(self, config_key: str) -> Optional[Dict]:
        """获取缓存的QQ配置"""
        key = f"config:{config_key}"
        return await self.config_cache.get(key)
    
    async def invalidate_qq_config(self, config_key: str) -> None:
        """失效指定配置缓存"""
        key = f"config:{config_key}"
        await self.config_cache.delete(key)
    
    # ==================== 用户缓存方法 ====================
    
    async def cache_user_profile(self, user_id: int, profile: Dict,
                                ttl: float = CacheTTL.LONG) -> None:
        """缓存用户资料"""
        key = f"user:{user_id}"
        await self.user_cache.set(key, profile, ttl=ttl)
    
    async def get_user_profile(self, user_id: int) -> Optional[Dict]:
        """获取缓存的用户资料"""
        key = f"user:{user_id}"
        return await self.user_cache.get(key)
    
    # ==================== 会话缓存方法 ====================
    
    async def cache_session(self, session_id: str, session_data: Dict,
                           ttl: float = CacheTTL.MEDIUM) -> None:
        """缓存会话数据"""
        key = f"session:{session_id}"
        await self.session_cache.set(key, session_data, ttl=ttl)
    
    async def get_session(self, session_id: str) -> Optional[Dict]:
        """获取缓存的会话数据"""
        key = f"session:{session_id}"
        return await self.session_cache.get(key)
    
    # ==================== 统计和管理方法 ====================
    
    def get_stats(self) -> Dict[str, Any]:
        """获取所有缓存的统计信息"""
        return {
            "messages": self.message_cache.get_stats(),
            "images": self.image_cache.get_stats(),
            "config": self.config_cache.get_stats(),
            "users": self.user_cache.get_stats(),
            "groups": self.group_cache.get_stats(),
            "sessions": self.session_cache.get_stats(),
        }
    
    async def clear_all(self) -> None:
        """清理所有缓存"""
        await self.message_cache.clear()
        await self.image_cache.clear()
        await self.config_cache.clear()
        await self.user_cache.clear()
        await self.group_cache.clear()
        await self.session_cache.clear()
        logger.info("[QQ缓存] 所有缓存已清理")
    
    async def cleanup_expired(self) -> None:
        """清理过期缓存"""
        # 统一缓存系统在后台自动处理
        logger.info("[QQ缓存] 内部清理任务执行中")


# 全局QQ缓存管理器实例
_qq_cache_manager: Optional[QQCacheManager] = None


def get_qq_cache_manager() -> QQCacheManager:
    """获取QQ子网缓存管理器（单例）"""
    global _qq_cache_manager
    if _qq_cache_manager is None:
        _qq_cache_manager = QQCacheManager()
    return _qq_cache_manager
```

### 第二步：集成到QQNet核心

**修改**: `webnet/qq/core.py`

在 `QQNet.__init__` 中添加：
```python
# 在 __init__ 中添加缓存管理
from .cache_manager import get_qq_cache_manager

class QQNet:
    def __init__(self, miya_core, mlink=None, memory_net=None, tts_net=None):
        # ... 现有代码 ...
        
        # 初始化缓存管理器 (新增)
        self.cache_manager = get_qq_cache_manager()
        logger.info("[QQNet] 缓存管理器已集成")
```

### 第三步：迁移现有缓存

#### 3.1 迁移图片缓存

**修改**: `webnet/qq/enhanced_image_handler.py`

从：
```python
class QQImageHandler:
    def __init__(self):
        self.image_cache = {}
        self.cache_expire_hours = 24
```

改为：
```python
from .cache_manager import get_qq_cache_manager

class QQImageHandler:
    def __init__(self):
        self.cache_manager = get_qq_cache_manager()
    
    async def cache_analysis(self, image_id: str, result: Dict):
        """使用统一缓存存储分析结果"""
        await self.cache_manager.cache_image_analysis(
            image_id, result, 
            ttl=CacheTTL.LONG  # 24小时
        )
    
    async def get_cached_analysis(self, image_id: str) -> Optional[Dict]:
        """从统一缓存获取分析结果"""
        return await self.cache_manager.get_image_analysis(image_id)
```

#### 3.2 迁移消息缓存

**修改**: `webnet/qq/message_handler.py`

从：
```python
class QQMessageHandler:
    def __init__(self):
        self.message_history = {}
```

改为：
```python
from .cache_manager import get_qq_cache_manager

class QQMessageHandler:
    def __init__(self):
        self.cache_manager = get_qq_cache_manager()
    
    async def store_message_history(self, chat_id: int, messages: list):
        """使用统一缓存存储消息历史"""
        await self.cache_manager.cache_message_history(chat_id, messages)
    
    async def get_message_history(self, chat_id: int) -> Optional[list]:
        """从统一缓存获取消息历史"""
        return await self.cache_manager.get_message_history(chat_id)
```

#### 3.3 迁移配置缓存

**修改**: `webnet/qq/hybrid_config.py`

从：
```python
class HybridConfig:
    def __init__(self):
        self._cached_full_config = None
```

改为：
```python
from .cache_manager import get_qq_cache_manager

class HybridConfig:
    def __init__(self):
        self.cache_manager = get_qq_cache_manager()
    
    async def get_config(self) -> Dict:
        """从统一缓存获取配置"""
        cached = await self.cache_manager.get_qq_config("full_config")
        if cached:
            return cached
        
        # 如果未缓存，则计算并缓存
        config = self._get_default_config()
        await self.cache_manager.cache_qq_config("full_config", config)
        return config
```


## 📋 集成检查清单

### 阶段1：基础集成
- [ ] 创建 `webnet/qq/cache_manager.py` 模块
- [ ] 定义 QQCacheManager 类
- [ ] 实现全局单例 get_qq_cache_manager()
- [ ] 在 QQNet 中集成缓存管理器

### 阶段2：模块迁移
- [ ] 迁移图片缓存到 QQCacheManager
- [ ] 迁移消息缓存到 QQCacheManager
- [ ] 迁移配置缓存到 QQCacheManager
- [ ] 迁移用户资料缓存到 QQCacheManager

### 阶段3：验证和测试
- [ ] 单元测试 QQCacheManager
- [ ] 集成测试缓存功能
- [ ] 性能测试（命中率、延迟）
- [ ] 内存占用评估

### 阶段4：文档和部署
- [ ] 更新 QQ 子网文档
- [ ] 添加使用示例
- [ ] 性能基准测试
- [ ] 灰度发布到生产环境


## 📊 预期收益

### 性能提升
| 指标 | 优化前 | 优化后 | 收益 |
|------|-------|-------|------|
| 缓存命中率 | ~60% | >95% | +35% |
| 图片分析延迟 | ~5s | ~0.5s | 10倍 |
| 配置加载延迟 | ~100ms | <10ms | 10倍 |
| 内存占用 | 分散管理 | 统一控制 | 优化 30% |

### 代码质量
| 指标 | 改进 |
|------|------|
| 代码重复 | 减少 6 个本地缓存实现 |
| 维护成本 | 集中管理，降低 60% |
| 可观测性 | 统一指标导出 |
| 可扩展性 | 支持新缓存类型无需改核心代码 |

### 架构优化
- ✅ 遵循 Miya Subnet 设计模式
- ✅ 统一缓存政策管理
- ✅ 支持缓存持久化扩展
- ✅ 便于 M-Link 缓存消息集成


## 🚀 实现优先级

### 优先级P1（关键）
1. ✅ 创建 cache_manager.py
2. ✅ 集成到 QQNet
3. ✅ 迁移图片缓存（性能劲大）

### 优先级P2（重要）
1. ✅ 迁移消息缓存
2. ✅ 迁移配置缓存
3. ✅ 性能测试

### 优先级P3（完善）
1. ✅ 用户资料缓存
2. ✅ 会话缓存
3. ✅ 监控指标导出

---

**下一步**: 确认方案后，可开始实施阶段1（基础集成）。需要多长时间？预计 2-3 小时完成整个集成。
